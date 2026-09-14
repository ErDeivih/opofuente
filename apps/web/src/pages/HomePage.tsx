import { EmptyState } from '../components/EmptyState';
import { LoadingState } from '../components/LoadingState';
import { SystemStatus } from '../features/system/SystemStatus';
import { useOppositions } from '../api/queries';

/**
 * Inicio (07_UI-UX §3).
 *
 * «Estado del programa» muestra el perfil realmente sembrado (oposición activa, convocatoria,
 * fecha de publicación y enlace oficial). Las demás tarjetas siguen siendo estados vacíos honestos:
 * no hay sesiones ni material importado porque esos slices no existen todavía.
 */
export function HomePage() {
  const oppositions = useOppositions();
  const active = oppositions.data?.find((opposition) => opposition.active) ?? null;
  const total = oppositions.data?.length ?? 0;

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
        <EmptyState
          title="Sin sesiones de estudio"
          description="No hay repasos vencidos ni sesiones previas que continuar."
          hint="El motor de práctica, examen y repaso llega en el slice S07."
        />
      </section>

      <section className="card" aria-labelledby="acciones-necesarias">
        <h2 id="acciones-necesarias">Acciones necesarias</h2>
        <EmptyState
          title="No hay material importado"
          description="Tampoco hay clasificaciones pendientes ni fuentes cambiadas."
          hint="La bandeja de inventario e importación llega en el slice S02."
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
