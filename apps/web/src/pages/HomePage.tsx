import { Link } from 'react-router-dom';

import { EmptyState } from '../components/EmptyState';
import { LoadingState } from '../components/LoadingState';
import { ActivityPanel } from '../features/home/ActivityPanel';
import { PendingActionsPanel } from '../features/home/PendingActionsPanel';
import { StudyReadinessPanel } from '../features/home/StudyReadinessPanel';
import { SystemStatus } from '../features/system/SystemStatus';
import { useOppositions, useMastery, useReviewQueue, useStudySessions } from '../api/queries';
import { queueSummary } from '../api/reviews';
import { modeLabel, statusLabel } from '../features/study/labels';
import { formatDateTime } from '../lib/format';

/**
 * Inicio (07_UI-UX §3).
 *
 * «Estado del programa» muestra el perfil realmente sembrado, y «Continuar estudiando» lee las
 * sesiones de verdad. Desde S10 la tarjeta también mira el **repaso vencido**: §3 pide recomendar la
 * siguiente tarea, y lo que toca hoy manda sobre lo último que se hizo.
 *
 * Desde S12.6 las dos tarjetas que antes no leían nada leen de verdad: «Acciones necesarias» enseña
 * lo que espera una decisión humana (incidencias, propuestas, cambios y material sin aceptar) y
 * «Estado del programa» añade si la oposición está **lista para estudiar**, qué falta y el dominio
 * estimado. El orden es el de §3: qué hacer hoy, qué me espera, cómo va el programa, actividad
 * reciente y, al final, el estado del sistema.
 */
export function HomePage() {
  const oppositions = useOppositions();
  const active = oppositions.data?.find((opposition) => opposition.active) ?? null;
  const total = oppositions.data?.length ?? 0;
  const sessions = useStudySessions(active?.id ?? null);
  const repaso = useReviewQueue(active?.id ?? null);
  const mastery = useMastery(active?.id ?? null);

  const enMarcha = sessions.data?.sessions.find((sesion) => sesion.status === 'running') ?? null;
  const ultima = sessions.data?.sessions[0] ?? null;
  const vencidos = repaso.data?.stats.due ?? 0;

  return (
    <>
      <header className="page__header">
        <h1>Inicio</h1>
        <p className="page__lead">
          La siguiente tarea de hoy: el repaso vencido manda; si no hay nada vencido, se continúa la
          sesión que quedó a medias.
        </p>
      </header>

      <section className="card" aria-labelledby="siguiente-tarea">
        <h2 id="siguiente-tarea">Siguiente tarea</h2>
        {repaso.isPending && <LoadingState label="Mirando lo que toca hoy…" />}
        {repaso.isError && (
          <EmptyState
            title="No se pudo leer la cola de repaso"
            description="La API no responde o la base de datos no está migrada."
          />
        )}
        {repaso.isSuccess && vencidos > 0 && (
          <>
            <p>
              <strong>
                {vencidos} pregunta(s) vencida(s) de repaso
              </strong>{' '}
              <span className="hint">{queueSummary(repaso.data)}</span>
            </p>
            <p className="hint">
              Se repasan en una sesión compuesta con lo vencido: la solución no se enseña antes de
              contestar.
            </p>
            <Link className="button" to="/errores">
              Ir al repaso de errores
            </Link>
          </>
        )}
        {repaso.isSuccess && vencidos === 0 && enMarcha !== null && (
          <>
            <p>
              <strong>Tienes una sesión sin terminar</strong>{' '}
              <span className="hint">
                {modeLabel(enMarcha.mode)} · {enMarcha.answered_questions} de{' '}
                {enMarcha.total_questions} preguntas
              </span>
            </p>
            <Link className="button" to="/estudiar">
              Continuar la sesión
            </Link>
          </>
        )}
        {repaso.isSuccess && vencidos === 0 && enMarcha === null && (
          <p className="hint">
            Nada vencido y ninguna sesión a medias. Lo siguiente es practicar: una sesión de práctica
            sobre el banco que tengas, o un examen oficial si el material está completo.
          </p>
        )}
      </section>

      <section className="card" aria-labelledby="continuar-estudiando">
        <h2 id="continuar-estudiando">Continuar estudiando</h2>
        {sessions.isPending && <LoadingState label="Cargando las sesiones…" />}
        {sessions.isError && (
          <EmptyState
            title="No se pudieron cargar las sesiones"
            description="La API no responde o la base de datos no está migrada."
          />
        )}
        {sessions.isSuccess && enMarcha === null && ultima === null && (
          <EmptyState
            title="Sin sesiones de estudio"
            description="No hay ninguna sesión previa que continuar. Se empieza desde la sección Estudiar, con el banco de preguntas de la oposición."
            hint="Hace falta un conjunto de preguntas con su clave activa: sin clave no hay corrección."
          />
        )}
        {sessions.isSuccess && enMarcha === null && ultima !== null && (
          <dl className="facts">
            <dt>Última sesión</dt>
            <dd>
              {modeLabel(ultima.mode)} · {statusLabel(ultima.status)} ·{' '}
              {ultima.answered_questions} de {ultima.total_questions} preguntas
            </dd>
            <dt>Empezó</dt>
            <dd>{ultima.started_at ? formatDateTime(ultima.started_at) : 'sin empezar'}</dd>
            <dt>Sesiones</dt>
            <dd>{sessions.data?.total ?? 0}</dd>
          </dl>
        )}
        {sessions.isSuccess && enMarcha !== null && (
          <dl className="facts">
            <dt>Sesión en marcha</dt>
            <dd>
              {modeLabel(enMarcha.mode)} · {enMarcha.answered_questions} de{' '}
              {enMarcha.total_questions} preguntas
            </dd>
            <dt>Empezó</dt>
            <dd>
              {enMarcha.started_at !== null && enMarcha.started_at !== undefined ? (
                <time dateTime={enMarcha.started_at}>{formatDateTime(enMarcha.started_at)}</time>
              ) : (
                'sin empezar'
              )}
            </dd>
            <dt>Se retoma en</dt>
            <dd>Estudiar, donde estaba: la sesión vive en el servidor y su cronómetro también.</dd>
          </dl>
        )}
      </section>

      <PendingActionsPanel />

      <section className="card" aria-labelledby="estado-programa">
        <h2 id="estado-programa">Estado del programa</h2>
        {oppositions.isPending && <LoadingState label="Cargando perfiles…" />}
        {oppositions.isError && (
          <EmptyState
            title="No se pudieron cargar los perfiles"
            description="La API no responde o la base de datos no está migrada."
            hint="Comprueba el estado del sistema, más abajo."
          />
        )}
        {oppositions.isSuccess && active === null && (
          <EmptyState
            title={total === 0 ? 'Sin oposiciones sembradas' : 'Ninguna oposición activa'}
            description="Los perfiles oficiales se siembran desde los fixtures versionados."
            hint="Ejecuta scripts/seed.ps1 para sembrar TAI 2025 y Guardia Civil 2026."
          />
        )}
        {oppositions.isSuccess && active !== null && (
          <dl className="facts">
            <dt>Oposición activa</dt>
            <dd>
              {active.name} <span className="tag">{active.code}</span>
            </dd>
            <dt>Convocatoria</dt>
            <dd>
              {active.active_convocation?.code ?? 'sin convocatoria activa'}
              {active.active_convocation && (
                <>
                  {' · publicada el '}
                  <time dateTime={active.active_convocation.published_at}>
                    {active.active_convocation.published_at}
                  </time>
                </>
              )}
            </dd>
            <dt>Perfiles disponibles</dt>
            <dd>{total}</dd>
          </dl>
        )}
        {oppositions.isSuccess && active !== null && (
          <StudyReadinessPanel oppositionId={active.id} />
        )}
        {oppositions.isSuccess && active !== null && (
          <p className="hint">
            Dominio estimado por tema:{' '}
            {mastery.data === undefined
              ? 'contando lo que has practicado…'
              : `${mastery.data.nodes_with_estimate} de ${mastery.data.nodes_total} temas con datos suficientes`}
            . Sin intentos no hay dominio, y con pocos es «evidencia insuficiente»:{' '}
            <Link to="/programa">verlo tema a tema en el Programa</Link>.
          </p>
        )}
      </section>

      <ActivityPanel oppositionId={active?.id ?? null} />

      <SystemStatus />
    </>
  );
}
