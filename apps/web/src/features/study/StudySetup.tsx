import { useState } from 'react';

import type { QuestionSet } from '../../api/questions';
import type { CreateSession, SessionSource } from '../../api/study';
import { FEEDBACKS, SESSION_MODES } from '../../api/study';
import { ErrorState } from '../../components/ErrorState';
import { StatusBadge } from '../../components/StatusBadge';
import type { ConvocationDetail } from '../../api/profiles';
import { feedbackLabel, modeLabel } from './labels';

export interface StudySetupProps {
  convocation: ConvocationDetail | null;
  sets: readonly QuestionSet[];
  busy: boolean;
  conflict: string | null;
  error: string | null;
  onCreate: (input: CreateSession) => void;
}

/** Una parte se puede practicar si el servidor sabe corregirla: respuesta única y con penalización. */
function isPracticeable(part: ConvocationDetail['parts'][number]): boolean {
  return (
    part.kind === 'test' &&
    (part.format === 'single_choice' || part.format === null) &&
    part.wrong_penalty_fraction !== null
  );
}

function whyNotPracticeable(part: ConvocationDetail['parts'][number]): string {
  if (part.kind === 'group') {
    return 'agrupa partes: se practica sobre cada parte, no sobre el grupo';
  }
  if (part.format !== 'single_choice' && part.format !== null) {
    return `se corrige como «${part.format}», que llega en S08`;
  }
  if (part.wrong_penalty_fraction === null) {
    return 'la convocatoria no publica su penalización';
  }
  return 'no se puede practicar todavía';
}

/**
 * Configuración de una sesión (07_UI-UX §8).
 *
 * Tres cosas que esta pantalla no hace:
 *
 * 1. **no deja elegir parámetros que la convocatoria fija**: en un examen oficial el tamaño, las
 *    reservas y el tiempo los pone el perfil, y la pantalla lo dice en lugar de ofrecer campos que el
 *    servidor ignoraría (o rechazaría);
 * 2. **no ofrece una parte que el servidor no sepa corregir**: las que se corrigen de otra forma se
 *    listan con su motivo y deshabilitadas, para que se vea qué falta y por qué;
 * 3. **no crea la sesión sin clave activa**: sin plantilla activa no hay corrección, y se dice antes
 *    de intentarlo.
 */
export function StudySetup({ convocation, sets, busy, conflict, error, onCreate }: StudySetupProps) {
  const parts = convocation?.parts ?? [];
  const practicables = parts.filter(isPracticeable);
  const [mode, setMode] = useState<CreateSession['mode']>('practice');
  // La parte elegida se **deriva**: la que haya elegido la persona y, mientras no elija, la primera
  // que se pueda practicar. Con un `useState` inicial la elección se quedaba en blanco hasta que
  // llegaba la convocatoria, y el formulario decía tener una parte sin tenerla (el botón quedaba
  // deshabilitado sin explicar por qué).
  const [partCodeElegido, setPartCodeElegido] = useState<string | null>(null);
  const [setId, setSetId] = useState<string>('');
  const [count, setCount] = useState('10');
  const [feedback, setFeedback] = useState<NonNullable<CreateSession['feedback']>>('immediate');
  const [shuffle, setShuffle] = useState(false);

  const partCode = partCodeElegido ?? practicables[0]?.code ?? '';
  const conjunto = sets.find((candidato) => candidato.id === setId) ?? null;
  const parte = practicables.find((candidato) => candidato.code === partCode) ?? null;
  const disponible = parte?.ordinary_items ?? null;
  const sinClave = conjunto !== null && conjunto.active_key_id === null;

  const bloqueado = conjunto === null || sinClave || parte === null || disponible === 0;

  function crear(): void {
    if (conjunto === null || parte === null) {
      return;
    }
    const fuente: SessionSource = {
      question_set_id: conjunto.id,
      part_code: parte.code,
      count: mode === 'practice' ? Number(count) : null,
      include_reserves: mode === 'official_exam',
    };
    onCreate({
      opposition_id: conjunto.opposition_id,
      mode,
      sources: [fuente],
      convocation_version_id: convocation?.id ?? null,
      feedback: mode === 'practice' ? feedback : null,
      shuffle: mode === 'practice' ? shuffle : false,
      time_limit_minutes: null,
    });
  }

  return (
    <section className="card" aria-labelledby="configurar-sesion">
      <h2 id="configurar-sesion">Preparar la sesión</h2>
      <p className="hint">
        El modo decide cómo se corrige: en práctica se puede corregir al responder; un examen oficial
        corrige al terminar, con el tamaño, las reservas y el tiempo de la convocatoria.
      </p>

      <div className="form__row">
        <label className="form__label" htmlFor="sesion-modo">
          Modo
        </label>
        <select
          id="sesion-modo"
          className="selector__select"
          value={mode}
          onChange={(event) => {
            const elegido = event.target.value as CreateSession['mode'];
            setMode(elegido);
            if (elegido === 'official_exam') {
              setShuffle(false);
            }
          }}
        >
          {SESSION_MODES.map((valor) => (
            <option key={valor} value={valor}>
              {modeLabel(valor)}
            </option>
          ))}
        </select>

        <label className="form__label" htmlFor="sesion-parte">
          Parte del examen
        </label>
        <select
          id="sesion-parte"
          className="selector__select"
          value={partCode}
          onChange={(event) => {
            setPartCodeElegido(event.target.value);
          }}
          disabled={practicables.length === 0}
        >
          {practicables.map((candidata) => (
            <option key={candidata.code} value={candidata.code}>
              {candidata.name}
            </option>
          ))}
        </select>
        {practicables.length === 0 && (
          <p className="hint">
            Ninguna parte de esta convocatoria se puede practicar todavía: se corrige con una fórmula
            que llega en S08.
          </p>
        )}
      </div>

      {parts.length > practicables.length && (
        <details>
          <summary>Partes que todavía no se pueden practicar</summary>
          <ul className="hint">
            {parts
              .filter((candidata) => !isPracticeable(candidata))
              .map((candidata) => (
                <li key={candidata.code}>
                  {candidata.name}: {whyNotPracticeable(candidata)}.
                </li>
              ))}
          </ul>
        </details>
      )}

      <div className="form__row">
        <label className="form__label" htmlFor="sesion-conjunto">
          Conjunto de preguntas
        </label>
        <select
          id="sesion-conjunto"
          className="selector__select"
          value={setId}
          onChange={(event) => {
            setSetId(event.target.value);
          }}
        >
          <option value="">Elige un conjunto…</option>
          {sets.map((candidato) => (
            <option key={candidato.id} value={candidato.id}>
              {candidato.title} · {candidato.question_count} preguntas
              {candidato.active_key_id === null ? ' · sin clave activa' : ' · con clave activa'}
            </option>
          ))}
        </select>

        {mode === 'practice' ? (
          <>
            <label className="form__label" htmlFor="sesion-cantidad">
              Cuántas preguntas
            </label>
            <input
              id="sesion-cantidad"
              className="selector__select"
              type="number"
              min={1}
              value={count}
              onChange={(event) => {
                setCount(event.target.value);
              }}
            />
            <label className="form__label" htmlFor="sesion-feedback">
              Corrección
            </label>
            <select
              id="sesion-feedback"
              className="selector__select"
              value={feedback}
              onChange={(event) => {
                setFeedback(event.target.value as NonNullable<CreateSession['feedback']>);
              }}
            >
              {FEEDBACKS.map((valor) => (
                <option key={valor} value={valor}>
                  {feedbackLabel(valor)}
                </option>
              ))}
            </select>
            <label className="form__label" htmlFor="sesion-barajar">
              <input
                id="sesion-barajar"
                type="checkbox"
                checked={shuffle}
                onChange={(event) => {
                  setShuffle(event.target.checked);
                }}
              />{' '}
              barajar el orden
            </label>
          </>
        ) : (
          <p className="hint">
            En un examen oficial no se eligen ni el número de preguntas ni la corrección: los fija la
            convocatoria ({disponible ?? '—'} preguntas ordinarias
            {parte?.reserve_items ? ` y ${String(parte.reserve_items)} de reserva` : ''}
            {parte?.time_minutes ? `, ${String(parte.time_minutes)} minutos` : ''}).
          </p>
        )}
      </div>

      {conjunto !== null && (
        <p className="hint">
          {conjunto.title}: {conjunto.question_count} preguntas, {conjunto.reserve_count} reservas,{' '}
          {conjunto.incomplete_count} incompletas.{' '}
          {conjunto.active_key_id === null ? (
            <StatusBadge tone="warning">sin clave activa: no se puede corregir</StatusBadge>
          ) : (
            <StatusBadge tone="ok">clave activa</StatusBadge>
          )}
        </p>
      )}

      {conflict !== null && (
        <ErrorState title="El servidor rechazó la sesión" message={conflict} />
      )}
      {error !== null && <ErrorState title="La sesión no se creó" message={error} />}

      <button
        className="button"
        type="button"
        disabled={busy || bloqueado}
        aria-label="Crear y empezar la sesión"
        onClick={crear}
      >
        Empezar
      </button>
    </section>
  );
}
