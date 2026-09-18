import { EmptyState } from '../components/EmptyState';
import { LoadingState } from '../components/LoadingState';
import { SystemStatus } from '../features/system/SystemStatus';
import { useOppositions, useStudySessions } from '../api/queries';
import { modeLabel, statusLabel } from '../features/study/labels';

/**
 * Inicio (07_UI-UX §3).
 *
 * «Estado del programa» muestra el perfil realmente sembrado, y «Continuar estudiando» lee las
 * sesiones de verdad: desde S07 hay motor de práctica y examen, así que la tarjeta ya no puede decir
 * que no existe. Si no hay ninguna sesión, lo dice —y explica cómo empezar— en lugar de fingir un
 * resumen.
 */
export function HomePage() {
  const oppositions = useOppositions();
  const active = oppositions.data?.find((opposition) => opposition.active) ?? null;
  const total = oppositions.data?.length ?? 0;
  const sessions = useStudySessions(active?.id ?? null);

  const enMarcha = sessions.data?.sessions.find((sesion) => sesion.status === 'running') ?? null;
  const ultima = sessions.data?.sessions[0] ?? null;

  return (
    <>
      <header className="page__header">
        <h1>Inicio</h1>
        <p className="page__lead">
          Aquí se mostrará la tarea recomendada. Mientras no existan material ni sesiones, esta
          pantalla dice exactamente qué falta y en qué slice llega.
        </p>
      </header>

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
            <dd>{ultima.started_at ?? 'sin empezar'}</dd>
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
                <time dateTime={enMarcha.started_at}>{enMarcha.started_at}</time>
              ) : (
                'sin empezar'
              )}
            </dd>
            <dt>Se retoma en</dt>
            <dd>Estudiar, donde estaba: la sesión vive en el servidor y su cronómetro también.</dd>
          </dl>
        )}
      </section>

      <section className="card" aria-labelledby="acciones-necesarias">
        <h2 id="acciones-necesarias">Acciones necesarias</h2>
        <EmptyState
          title="No hay material importado"
          description="Desde S02 puedes inventariar una carpeta y copiar lo que confirmes, pero esta pantalla todavía no resume esos avisos."
          hint="El resumen de importaciones con errores llega en el slice S12."
        />
      </section>

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
      </section>

      <SystemStatus />
    </>
  );
}
