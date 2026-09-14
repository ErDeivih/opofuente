import type { NavItem } from '../app/navigation';
import { StatusBadge } from '../components/StatusBadge';

export interface PendingPageProps {
  item: NavItem;
}

/**
 * Sección anunciada en la navegación pero todavía no implementada.
 *
 * Se muestra una explicación explícita en lugar de una pantalla vacía o un botón que no hace
 * nada (16_TRACEABILITY-AND-DEFINITION-OF-DONE §4).
 */
export function PendingPage({ item }: PendingPageProps) {
  return (
    <>
      <header className="page__header">
        <h1>{item.label}</h1>
        <p className="page__lead">{item.summary}</p>
      </header>

      <section className="card" aria-labelledby="seccion-pendiente">
        <div className="status-summary">
          <StatusBadge tone="info">pendiente</StatusBadge>
        </div>
        <h2 id="seccion-pendiente">Esta sección todavía no está construida</h2>
        <p>
          {item.slice === null
            ? 'No hay slice asignado todavía.'
            : `Está planificada para el slice ${item.slice} de docs/product-spec/11_IMPLEMENTATION-SLICES.md.`}
        </p>
        <p className="hint">
          Hasta que ese slice se entregue, esta pantalla no ofrece datos ni acciones: no se simula
          funcionalidad para que la navegación parezca completa.
        </p>
      </section>
    </>
  );
}
