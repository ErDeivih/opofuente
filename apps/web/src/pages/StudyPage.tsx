import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import {
  useAnswerKeys,
  useAnswerQuestion,
  useClassifyError,
  useConvocation,
  useCreateStudySession,
  useCurrentQuestion,
  useDiagnosticReading,
  useFinishStudySession,
  useNavigateStudy,
  useOppositions,
  useQuestionSets,
  useRecalculateStudySession,
  useStartStudySession,
  useStudyResult,
  useStudyReview,
  useStudySessions,
} from '../api/queries';
import { isApiError } from '../api/client';
import { CAUSE_LABEL } from '../api/reviews';
import type { CreateSession, SessionQuestion, StudySession } from '../api/study';
import { ErrorState } from '../components/ErrorState';
import { LoadingState } from '../components/LoadingState';
import { DiagnosticPanel } from '../features/study/DiagnosticPanel';
import { StudyResultPanel } from '../features/study/StudyResultPanel';
import { StudyRunner } from '../features/study/StudyRunner';
import { StudySetup } from '../features/study/StudySetup';
import { modeLabel, statusLabel } from '../features/study/labels';

function describeError(error: unknown): string {
  return error instanceof Error ? error.message : 'Error desconocido';
}

/**
 * Pantalla de Estudiar (07_UI-UX §8 y contrato §10).
 *
 * Tres estados, y ninguno se simula:
 *
 * 1. **preparar**: se elige modo, parte y conjunto; el servidor decide si la sesión se puede montar y
 *    por qué no (sin clave activa, sin preguntas suficientes, parte que se corrige de otra forma);
 * 2. **sesión en marcha**: pregunta, progreso, cronómetro y navegación; la corrección solo aparece
 *    cuando el servidor la manda;
 * 3. **resultado**: puntuación directa por partes, recuentos y revisión, con la calificación oficial
 *    declarada como no disponible mientras no haya baremo.
 *
 * Recargar la página no pierde nada: la sesión vive en el servidor, y al volver se retoma la última
 * que estuviera en marcha.
 */
export function StudyPage() {
  const [parametros] = useSearchParams();
  // `?sesion=` llega cuando la sesión la ha montado otra pantalla (la práctica por tema de S13): se
  // abre esa y no la última, que es lo que se acaba de pedir.
  const sesionDeLaUrl = parametros.get('sesion');
  const [sessionIdElegida, setSessionIdElegida] = useState<string | null>(sesionDeLaUrl);
  const [preparandoOtra, setPreparandoOtra] = useState(false);
  const [aviso, setAviso] = useState<string | null>(null);
  // La pregunta recién respondida, con su corrección: se enseña hasta que se navega a otra.
  const [respondida, setRespondida] = useState<SessionQuestion | null>(null);

  const oposiciones = useOppositions();
  const activa = oposiciones.data?.find((oposicion) => oposicion.active) ?? null;
  const sesiones = useStudySessions(activa?.id ?? null);
  const conjuntos = useQuestionSets(activa?.id ?? null);
  const convocatoria = useConvocation(activa?.active_convocation?.id ?? null);

  // La sesión abierta se **deriva**, como el conjunto en el banco: la elegida y, mientras nadie
  // elija, la última (el servidor las devuelve de la más reciente a la más antigua). Así, recargar
  // después de terminar vuelve a enseñar el resultado, y una sesión a medias se retoma donde estaba.
  // Para empezar otra hay una acción explícita: no se esconde el formulario detrás de un estado.
  const sessionId = preparandoOtra
    ? null
    : (sessionIdElegida ?? sesiones.data?.sessions[0]?.id ?? null);
  const session =
    sesiones.data?.sessions.find((candidata) => candidata.id === sessionId) ?? null;

  const enCurso = session?.status === 'running';
  const terminada = session?.status === 'finished';
  const sinEmpezar = session?.status === 'draft';

  const current = useCurrentQuestion(enCurso ? sessionId : null);
  const result = useStudyResult(terminada ? sessionId : null);
  const review = useStudyReview(terminada ? sessionId : null);
  // DEBT-012: la lectura por temas solo se pide si la sesión es un diagnóstico; en otro modo el
  // servidor la niega con un 409 y pedirla sería ruido.
  const diagnostico = useDiagnosticReading(
    terminada && session?.mode === 'diagnostic' ? sessionId : null,
  );
  // Las plantillas del conjunto de la sesión: con ellas se sabe si hay una activa distinta de la que
  // corrigió, y solo entonces tiene sentido ofrecer recalcular (S08).
  const claves = useAnswerKeys(terminada ? (session?.question_set_id ?? null) : null);

  const crear = useCreateStudySession();
  const arrancar = useStartStudySession();
  const responder = useAnswerQuestion();
  const navegar = useNavigateStudy();
  const terminar = useFinishStudySession();
  const recalcular = useRecalculateStudySession();
  // S10: declarar por qué se ha fallado, desde la propia corrección (06_QUESTIONS §8, paso 8). El
  // intento corregido es el que devolvió el servidor al guardar la respuesta; su causa se declara una
  // vez y se puede corregir después desde Errores.
  const clasificar = useClassifyError(activa?.id ?? null);
  const [intentoCorregidoId, setIntentoCorregidoId] = useState<string | null>(null);
  const errorDeclarado =
    clasificar.data !== undefined && clasificar.data.attempt_id === intentoCorregidoId;

  const busy =
    crear.isPending ||
    arrancar.isPending ||
    responder.isPending ||
    navegar.isPending ||
    terminar.isPending ||
    recalcular.isPending;

  const claveActiva = claves.data?.find((clave) => clave.status === 'active') ?? null;
  const hayClaveNueva =
    claveActiva !== null && claveActiva.id !== (session?.answer_key_version_id ?? null);

  // Lo que la aplicación **no** evalúa se dice con las palabras de la convocatoria, no se calla.
  const noEvaluadas: string[] = [];
  for (const regla of convocatoria.data?.rules ?? []) {
    if (regla.code === 'personality_scoring_supported' && regla.value_text === 'false') {
      noEvaluadas.push('el cuestionario de personalidad');
    }
    if (regla.code === 'psychophysical_not_prepared' && regla.value_text === 'true') {
      noEvaluadas.push('las pruebas físicas y el reconocimiento médico');
    }
  }

  const falloCrear = crear.error ?? arrancar.error ?? null;
  const conflictoCrear = isApiError(falloCrear, 409) ? describeError(falloCrear) : null;
  const errorCrear =
    falloCrear === null || conflictoCrear !== null ? null : describeError(falloCrear);

  const falloResponder = responder.error ?? navegar.error ?? null;
  const conflictoResponder = isApiError(falloResponder, 409)
    ? describeError(falloResponder)
    : null;
  const errorResponder =
    falloResponder === null || conflictoResponder !== null ? null : describeError(falloResponder);

  function empezar(input: CreateSession): void {
    crear.mutate(input, {
      onSuccess: (creada) => {
        abrirCreada(creada);
      },
    });
  }

  /** Una sesión creada se abre y se arranca: es lo que espera quien acaba de pulsar «Empezar». */
  function abrirCreada(creada: StudySession): void {
    setAviso(null);
    arrancar.mutate(creada.id, {
      onSuccess: (arrancada) => {
        setPreparandoOtra(false);
        setSessionIdElegida(arrancada.id);
        setAviso(
          `Sesión de ${modeLabel(arrancada.mode)} lista: ` +
            `${String(arrancada.total_questions)} preguntas.`,
        );
      },
    });
  }

  return (
    <>
      <header className="page__header">
        <h1>Estudiar</h1>
        <p className="page__lead">
          Practicar y examinarse con el banco de preguntas. La puntuación la calcula el servidor con la
          clave activa del conjunto y con la penalización que publica la convocatoria.
        </p>
      </header>

      {oposiciones.isPending && <LoadingState label="Cargando perfiles…" />}
      {oposiciones.isError && (
        <ErrorState
          title="No se pudieron cargar los perfiles"
          message="La API no responde o la base de datos no está migrada."
        />
      )}

      {enCurso && session !== null && (
        <p className="hint">
          Tienes una sesión en marcha ({modeLabel(session.mode)}, {statusLabel(session.status)}): se
          retoma donde estaba, con lo respondido y el tiempo ya corrido. Lleva{' '}
          {session.answered_questions} de {session.total_questions} preguntas respondidas
          {session.started_at !== null && session.started_at !== undefined && (
            <>
              {' '}
              y empezó el <time dateTime={session.started_at}>{session.started_at}</time>
            </>
          )}
          .
        </p>
      )}

      {sinEmpezar && session !== null && (
        <section className="card">
          <p className="hint">
            Esta sesión ya está creada con su composición congelada, pero no se ha empezado.
          </p>
          <button
            className="button"
            type="button"
            disabled={busy}
            aria-label="Empezar la sesión pendiente"
            onClick={() => {
              arrancar.mutate(session.id, {
                onSuccess: () => {
                  setAviso('Sesión en marcha.');
                },
              });
            }}
          >
            Empezarla
          </button>
          {conflictoCrear !== null && (
            <ErrorState title="El servidor rechazó la operación" message={conflictoCrear} />
          )}
          {errorCrear !== null && <ErrorState title="La operación no se aplicó" message={errorCrear} />}
        </section>
      )}

      {aviso !== null && <p className="hint">{aviso}</p>}

      {sessionId !== null && (
        <p className="form__row">
          <button
            className="button"
            type="button"
            aria-label="Preparar otra sesión"
            onClick={() => {
              setPreparandoOtra(true);
              setSessionIdElegida(null);
              setAviso(null);
            }}
          >
            Preparar otra sesión
          </button>
          <span className="hint">
            La de ahora no se pierde: sigue en el historial, con lo respondido.
          </span>
        </p>
      )}

      {/* La configuración no se pinta hasta saber si hay una sesión que abrir: si apareciera antes,
          al llegar la lista se sustituiría sola mientras alguien la está rellenando. */}
      {sesiones.isPending && activa !== null && <LoadingState label="Cargando las sesiones…" />}

      {sessionId === null && !sesiones.isPending && (
        <StudySetup
          convocation={convocatoria.data ?? null}
          sets={conjuntos.data?.sets ?? []}
          busy={busy}
          conflict={conflictoCrear}
          error={errorCrear}
          onCreate={empezar}
          onDiagnostic={() => {
            if (activa === null) {
              return;
            }
            crear.mutate(
              {
                opposition_id: activa.id,
                mode: 'diagnostic',
                sources: [],
                convocation_version_id: activa.active_convocation?.id ?? null,
                feedback: null,
                shuffle: false,
                time_limit_minutes: null,
              },
              { onSuccess: abrirCreada },
            );
          }}
        />
      )}

      {enCurso && current.data !== undefined && (
        <StudyRunner
          current={current.data}
          answered={respondida}
          busy={busy}
          conflict={conflictoResponder}
          error={errorResponder}
          attemptId={intentoCorregidoId}
          errorDeclared={errorDeclarado}
          onClassify={(input) => {
            if (intentoCorregidoId === null) {
              return;
            }
            clasificar.mutate(
              {
                attemptId: intentoCorregidoId,
                cause: input.cause,
                conceptLabel: input.conceptLabel,
                curriculumNodeId: null,
                note: input.note,
              },
              {
                onSuccess: (error) => {
                  setAviso(
                    `Causa declarada: ${CAUSE_LABEL[error.cause]}. El fallo queda en la cola de repaso.`,
                  );
                },
              },
            );
          }}
          onAnswer={(answer) => {
            responder.mutate(
              { sessionId: sessionId as string, answer },
              {
                onSuccess: (resultado) => {
                  setRespondida(resultado.question ?? null);
                  setIntentoCorregidoId(resultado.attempt.id);
                  setAviso(
                    resultado.saved
                      ? 'Respuesta guardada.'
                      : 'Esa respuesta ya estaba guardada: el intento no se reescribe.',
                  );
                },
              },
            );
          }}
          onNavigate={(position) => {
            setRespondida(null);
            setIntentoCorregidoId(null);
            navegar.mutate({
              sessionId: sessionId as string,
              navigation: typeof position === 'number' ? { position } : { direction: position },
            });
          }}
          onFinish={() => {
            terminar.mutate(sessionId as string, {
              onSuccess: () => {
                setAviso('Sesión terminada y corregida.');
              },
            });
          }}
        />
      )}

      {enCurso && current.isPending && <LoadingState label="Cargando la pregunta…" />}
      {enCurso && current.isError && (
        <ErrorState
          title="No se pudo cargar la sesión"
          message="El servidor no responde o la sesión no está disponible."
          onRetry={() => {
            void current.refetch();
          }}
        />
      )}

      {terminada && session !== null && session.mode === 'diagnostic' && (
        <DiagnosticPanel
          reading={diagnostico.data ?? null}
          isPending={diagnostico.isPending}
          isError={diagnostico.isError}
          onRetry={() => {
            void diagnostico.refetch();
          }}
        />
      )}

      {terminada && session !== null && (
        <StudyResultPanel
          session={session}
          result={result.data ?? null}
          review={review.data ?? null}
          isPending={result.isPending}
          isError={result.isError}
          onRetry={() => {
            void result.refetch();
          }}
          recalculating={recalcular.isPending}
          newerKeyActive={hayClaveNueva}
          notEvaluated={noEvaluadas}
          onRecalculate={() => {
            recalcular.mutate(session.id, {
              onSuccess: (nuevo) => {
                setAviso(
                  nuevo.recalculation?.changed === true
                    ? 'Sesión recalculada: la puntuación cambió con la plantilla nueva.'
                    : 'Sesión recalculada: la puntuación no cambió.',
                );
              },
            });
          }}
        />
      )}

      {!sesiones.isPending && (sesiones.data?.total ?? 0) > 0 && (
        <section className="card" aria-labelledby="historial-sesiones">
          <h2 id="historial-sesiones">Sesiones</h2>
          <table className="table">
            <caption className="table__caption">
              {sesiones.data?.total ?? 0} sesiones de esta oposición
            </caption>
            <thead>
              <tr>
                <th scope="col">Modo</th>
                <th scope="col">Estado</th>
                <th scope="col">Preguntas</th>
                <th scope="col">Empezó</th>
                <th scope="col">Acción</th>
              </tr>
            </thead>
            <tbody>
              {sesiones.data?.sessions.map((candidata) => (
                <tr key={candidata.id} aria-selected={candidata.id === sessionId}>
                  <th scope="row">{modeLabel(candidata.mode)}</th>
                  <td className="hint">{statusLabel(candidata.status)}</td>
                  <td className="hint">
                    {candidata.answered_questions} de {candidata.total_questions}
                  </td>
                  <td className="hint">{candidata.started_at ?? 'sin empezar'}</td>
                  <td>
                    <button
                      className="button"
                      type="button"
                      aria-label={`Abrir la sesión empezada el ${candidata.started_at ?? candidata.created_at}`}
                      onClick={() => {
                        setPreparandoOtra(false);
                        setSessionIdElegida(candidata.id);
                        setAviso(null);
                      }}
                    >
                      Abrir
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </>
  );
}
