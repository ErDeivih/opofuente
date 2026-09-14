import { EmptyState } from '../components/EmptyState';
import { SystemStatus } from '../features/system/SystemStatus';

/**
 * Inicio (07_UI-UX §3).
 *
 * Las tres primeras tarjetas son estados vacíos honestos: todavía no hay sesiones, material ni
 * perfiles. La cuarta muestra el estado real del sistema, que sí existe en S00.
 */
export function HomePage() {
  return (
    <>
      <header className="page__header">
        <h1>Inicio</h1>
        <p className="page__lead">
          Aquí se mostrará la tarea recomendada. Mientras no existan perfiles, material ni sesiones,
          esta pantalla dice exactamente qué falta y en qué slice llega.
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
        <EmptyState
          title="Sin oposiciones sembradas"
          description="Cobertura documental, preguntas y dominio se calculan sobre el árbol oficial del temario."
          hint="Los perfiles TAI 2025 y Guardia Civil 2026 se siembran en el slice S01 desde fuentes oficiales versionadas."
        />
      </section>

      <SystemStatus />
    </>
  );
}
