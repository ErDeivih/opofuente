import { useEffect, useState } from 'react';

import type {
  AnswerRequest,
  CurrentQuestion,
  SessionQuestion,
  SessionQuestionCorrection,
  StudySession,
} from '../../api/study';
import { CONFIDENCES, formatScore } from '../../api/study';
import { ErrorState } from '../../components/ErrorState';
import { StatusBadge } from '../../components/StatusBadge';
import {
  CONFIDENCE_LABEL,
  clock,
  elapsedSeconds,
  modeLabel,
  outcomeLabel,
  outcomeTone,
  statusLabel,
  statusTone,
} from './labels';

export interface StudyRunnerProps {
  current: CurrentQuestion;
  /** La pregunta que se acaba de responder, con su corrección: se enseña antes de pasar a la otra. */
  answered: SessionQuestion | null;
  busy: boolean;
  conflict: string | null;
  error: string | null;
  onAnswer: (answer: AnswerRequest) => void;
  onNavigate: (position: number | 'next' | 'previous') => void;
  onFinish: () => void;
}

/** Corrección de la pregunta: solo existe cuando el servidor la ha mandado (nunca antes). */
function Correction({ correction }: { correction: SessionQuestionCorrection }) {
  return (
    <section className="card notice" aria-labelledby="correccion-pregunta">
      <h3 id="correccion-pregunta">Corrección</h3>
      <p>
        <StatusBadge tone={outcomeTone(correction.outcome)}>
          {outcomeLabel(correction.outcome)}
        </StatusBadge>{' '}
        {correction.correct_option_keys.length > 0 && (
          <>
            Respuesta correcta:{' '}
            <span className="sample__path">
              {correction.correct_option_keys.join(', ').toUpperCase()}
            </span>{' '}
          </>
        )}
        <span className="hint">({formatScore(correction.score)} puntos)</span>
      </p>
      {correction.reason !== null && correction.reason !== undefined && (
        <p className="hint">{correction.reason}</p>
      )}
      {correction.explanation !== null && correction.explanation !== undefined && (
        <p>{correction.explanation}</p>
      )}
      {correction.evidence.length > 0 ? (
        <>
          <h4>Evidencia que la sostiene</h4>
          <ul className="evidence">
            {correction.evidence.map((cita) => (
              <li key={`${cita.span_id}-${cita.role}`}>
                <StatusBadge tone={cita.status === 'accepted' ? 'ok' : 'warning'}>
                  {cita.role}
                </StatusBadge>{' '}
                {cita.citation_label ?? `página ${String(cita.page ?? 'sin página')}`}
                <blockquote className="reader">{cita.text}</blockquote>
              </li>
            ))}
          </ul>
        </>
      ) : (
        <p className="hint">
          Esta pregunta no tiene documento de origen adjunto, así que no hay cita que abrir: la
          evidencia se crea al importar preguntas desde un documento (DEBT-010).
        </p>
      )}
    </section>
  );
}

function Question({ question }: { question: SessionQuestion }) {
  return (
    <section className="card" aria-labelledby="pregunta-actual">
      <h3 id="pregunta-actual">
        Pregunta {question.position}
        {question.is_reserve && (
          <>
            {' '}
            <StatusBadge tone="info">
              reserva{question.reserve_order !== null && ` ${String(question.reserve_order)}`}
            </StatusBadge>
          </>
        )}
      </h3>
      <p className="reader">{question.stem}</p>
      <ul className="options">
        {question.options.map((opcion) => (
          <li key={opcion.id}>
            <span className="sample__path">{opcion.stable_key.toUpperCase()}</span> {opcion.text}
          </li>
        ))}
      </ul>
    </section>
  );
}

/**
 * La sesión en marcha (07_UI-UX §8).
 *
 * Lo que esta pantalla **no** puede hacer, y por qué:
 *
 * 1. **no enseña la corrección antes de tiempo**: solo pinta `question.correction` cuando el servidor
 *    la manda (corrección inmediata de algo ya respondido, o sesión terminada). La pantalla no tiene
 *    la clave en ningún otro sitio;
 * 2. **no reescribe un intento**: si se vuelve a enviar lo mismo, el servidor devuelve el intento que
 *    ya había; si se cambia, la pantalla explica el 409 y deja claro que no se ha tocado nada;
 * 3. **el cronómetro cuenta desde el inicio real de la sesión** (que lo puso el servidor), no desde
 *    que se abrió la pantalla.
 */
export function StudyRunner({
  current,
  answered,
  busy,
  conflict,
  error,
  onAnswer,
  onNavigate,
  onFinish,
}: StudyRunnerProps) {
  const session: StudySession = current.session;
  // Lo que se enseña es la pregunta que se acaba de responder (con su corrección) y, si no hay
  // ninguna pendiente de leer, la que toca según el servidor. Es el ciclo de 06_QUESTIONS §6:
  // responder, corregir y ver el resultado antes de pasar a la siguiente.
  const question = answered ?? current.question ?? null;
  const [marcadas, setMarcadas] = useState<string[]>([]);
  const [confidence, setConfidence] = useState<NonNullable<AnswerRequest['confidence']> | null>(
    null,
  );
  const [ahora, setAhora] = useState(() => Date.now());

  // El cronómetro late cada segundo, pero la hora la da el reloj: lo que se enseña es el tiempo
  // transcurrido desde el inicio de la sesión, no un contador que sigue sumando en segundo plano.
  useEffect(() => {
    const temporizador = setInterval(() => {
      setAhora(Date.now());
    }, 1000);
    return () => {
      clearInterval(temporizador);
    };
  }, []);

  const yaRespondida = question?.answered ?? false;
  const segundos = elapsedSeconds(session.started_at ?? null, ahora);
  const minutosLimite = session.time_limit_minutes ?? null;
  const limite = minutosLimite === null ? null : minutosLimite * 60;
  const restante = limite === null ? null : Math.max(0, limite - segundos);

  return (
    <>
      <section className="card" aria-labelledby="estado-sesion">
        <h2 id="estado-sesion">Sesión en marcha</h2>
        <dl className="facts">
          <dt>Modo</dt>
          <dd>
            {modeLabel(session.mode)}{' '}
            <StatusBadge tone={statusTone(session.status)}>{statusLabel(session.status)}</StatusBadge>
          </dd>
          <dt>Clave con la que se corrige</dt>
          <dd>{session.key_label ?? 'sin clave activa'}</dd>
          <dt>Progreso</dt>
          <dd>
            {current.answered} de {current.total} respondidas
            {current.pending > 0 && ` · ${String(current.pending)} pendientes`}
          </dd>
          <dt>Tiempo</dt>
          <dd>
            <time>{clock(segundos)}</time>
            {restante !== null && (
              <>
                {' · queda '}
                <time>{clock(restante)}</time>
              </>
            )}
          </dd>
        </dl>
        {restante === 0 && (
          <p className="hint">
            Se ha agotado el tiempo de la convocatoria. La aplicación no cierra la sesión sola: se
            termina cuando tú lo decidas.
          </p>
        )}
      </section>

      {conflict !== null && (
        <>
          <ErrorState title="El servidor rechazó la operación" message={conflict} />
          <p className="hint">Nada ha cambiado: la sesión sigue como estaba.</p>
        </>
      )}
      {error !== null && <ErrorState title="La operación no se aplicó" message={error} />}

      {question === null ? (
        <section className="card">
          <p className="hint">
            No queda ninguna pregunta por responder. Termina la sesión para ver el resultado.
          </p>
        </section>
      ) : (
        <>
          <Question question={question} />

          {!yaRespondida && (
            <fieldset className="card">
              <legend>Tu respuesta</legend>
              {question.options.map((opcion) => (
                <label className="form__label" key={opcion.id} htmlFor={`opcion-${opcion.id}`}>
                  <input
                    id={`opcion-${opcion.id}`}
                    type="radio"
                    name="respuesta"
                    value={opcion.stable_key}
                    checked={marcadas.includes(opcion.stable_key)}
                    onChange={() => {
                      setMarcadas([opcion.stable_key]);
                    }}
                  />{' '}
                  {opcion.stable_key.toUpperCase()}) {opcion.text}
                </label>
              ))}
              <label className="form__label" htmlFor="confianza">
                Confianza (opcional)
              </label>
              <select
                id="confianza"
                className="selector__select"
                value={confidence ?? ''}
                onChange={(event) => {
                  setConfidence(
                    event.target.value === ''
                      ? null
                      : (event.target.value as NonNullable<AnswerRequest['confidence']>),
                  );
                }}
              >
                <option value="">sin declarar</option>
                {CONFIDENCES.map((valor) => (
                  <option key={valor} value={valor}>
                    {CONFIDENCE_LABEL[valor]}
                  </option>
                ))}
              </select>
              <div className="form__row">
                <button
                  className="button"
                  type="button"
                  disabled={busy || marcadas.length === 0}
                  aria-label="Enviar la respuesta"
                  onClick={() => {
                    onAnswer({
                      question_version_id: question.question_version_id,
                      chosen_option_keys: marcadas,
                      elapsed_ms: 0,
                      confidence,
                      client_sequence: null,
                    });
                  }}
                >
                  Responder
                </button>
                <button
                  className="button"
                  type="button"
                  disabled={busy}
                  aria-label="Dejar la pregunta en blanco"
                  onClick={() => {
                    onAnswer({
                      question_version_id: question.question_version_id,
                      chosen_option_keys: [],
                      elapsed_ms: 0,
                      confidence,
                      client_sequence: null,
                    });
                  }}
                >
                  Dejarla en blanco
                </button>
              </div>
            </fieldset>
          )}

          {question.correction !== null && question.correction !== undefined && (
            <Correction correction={question.correction} />
          )}

          {yaRespondida && question.correction === null && (
            <p className="hint">
              Respuesta guardada. La corrección de esta sesión se muestra al terminar: así el examen no
              filtra la solución mientras se hace.
            </p>
          )}
        </>
      )}

      <section className="card">
        <div className="form__row">
          <button
            className="button"
            type="button"
            disabled={busy || question === null || question.position <= 1}
            aria-label="Ir a la pregunta anterior"
            onClick={() => {
              onNavigate('previous');
            }}
          >
            Anterior
          </button>
          <button
            className="button"
            type="button"
            disabled={busy || question === null || question.position >= current.total}
            aria-label="Ir a la pregunta siguiente"
            onClick={() => {
              onNavigate('next');
            }}
          >
            Siguiente
          </button>
          <button
            className="button"
            type="button"
            disabled={busy}
            aria-label="Terminar la sesión"
            onClick={onFinish}
          >
            Terminar y corregir
          </button>
        </div>
        <p className="hint">
          Se puede terminar con preguntas pendientes: las que no se contesten salen como no respondidas
          y no puntúan.
        </p>
      </section>
    </>
  );
}
