import { Link } from 'react-router-dom';

import { usePendingActions } from '../../api/queries';
import { ErrorState } from '../../components/ErrorState';
import { LoadingState } from '../../components/LoadingState';
import { StatusBadge } from '../../components/StatusBadge';

function describeError(error: unknown): string {
  return error instanceof Error ? error.message : 'Error desconocido';
}

/**
 * «Acciones necesarias» (07_UI-UX §3.2): lo que sigue esperando a una persona.
 *
 * Antes esta tarjeta enseñaba un texto fijo —«No hay material importado… esta pantalla todavía no
 * resume esos avisos»— que no leía nada y decía lo mismo con la biblioteca llena o vacía. Ahora
 * enseña lo que el servidor cuenta de verdad: incidencias de importación, propuestas de clasificación,
 * cambios de fuente sin confirmar y material sin aceptar, cada uno con su cifra y su enlace.
 *
 * Cuando no hay nada, lo dice: es información, no un hueco vacío.
 */
export function PendingActionsPanel() {
  const pendientes = usePendingActions();

  return (
    <section className="card" aria-labelledby="acciones-necesarias">
      <h2 id="acciones-necesarias">Acciones necesarias</h2>
      {pendientes.isPending && <LoadingState label="Mirando qué espera tu decisión…" />}
      {pendientes.isError && (
        <ErrorState
          title="No se pudo leer lo que espera tu decisión"
          message={describeError(pendientes.error)}
          onRetry={() => {
            void pendientes.refetch();
          }}
        />
      )}
      {pendientes.isSuccess && pendientes.data.actions.length === 0 && (
        <p className="hint">
          Nada esperando tu decisión: no hay incidencias de importación abiertas, ninguna propuesta sin
          decidir, ningún cambio de fuente sin confirmar y ningún material sin aceptar.
        </p>
      )}
      {pendientes.isSuccess && pendientes.data.actions.length > 0 && (
        <>
          <p className="hint">
            La aplicación ya ha hecho lo que puede hacer sola. Esto es lo que no puede decidir por ti
            (ADR-017): cada línea lleva a la pantalla donde se resuelve.
          </p>
          <ul className="check-list">
            {pendientes.data.actions.map((accion) => (
              <li key={accion.key} className="check-list__item">
                <StatusBadge tone="warning">{`${accion.count} pendiente(s)`}</StatusBadge>
                <span className="check-list__detail">
                  <strong>{accion.title}</strong>: {accion.detail}
                </span>
                <Link to={accion.href}>{accion.label}</Link>
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}
