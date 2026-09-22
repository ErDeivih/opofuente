import { Link } from 'react-router-dom';

import { useBatches, useStudySessions } from '../../api/queries';
import { ErrorState } from '../../components/ErrorState';
import { LoadingState } from '../../components/LoadingState';
import { modeLabel, statusLabel } from '../study/labels';
import { batchKindLabel, batchStatusLabel } from '../ingestion/labels';

function describeError(error: unknown): string {
  return error instanceof Error ? error.message : 'Error desconocido';
}

/** Cuántos elementos de cada cosa se enseñan: «actividad reciente» son los últimos, no todos. */
const RECIENTES = 3;

/**
 * Actividad reciente (07_UI-UX §3.4): los últimos lotes y las últimas sesiones.
 *
 * La especificación lo pide en Inicio y no existía. Son los datos que ya sirven la Bandeja y Estudiar,
 * leídos de verdad: si no hay nada, se dice; no se enseña una tabla vacía sin explicación.
 */
export function ActivityPanel({ oppositionId }: { oppositionId: string | null }) {
  const lotes = useBatches();
  const sesiones = useStudySessions(oppositionId);

  const ultimosLotes = (lotes.data ?? []).slice(0, RECIENTES);
  const ultimasSesiones = (sesiones.data?.sessions ?? []).slice(0, RECIENTES);
  const cargando = lotes.isPending || sesiones.isPending;
  const fallo = lotes.isError || sesiones.isError;

  return (
    <section className="card" aria-labelledby="actividad-reciente">
      <h2 id="actividad-reciente">Actividad reciente</h2>
      {cargando && <LoadingState label="Mirando lo último que ha pasado…" />}
      {fallo && (
        <ErrorState
          title="No se pudo leer la actividad reciente"
          message={describeError(lotes.error ?? sesiones.error)}
          onRetry={() => {
            void lotes.refetch();
            void sesiones.refetch();
          }}
        />
      )}
      {!cargando && !fallo && ultimosLotes.length === 0 && ultimasSesiones.length === 0 && (
        <p className="hint">
          Todavía no hay actividad: ni lotes en la bandeja ni sesiones de estudio. Lo primero es soltar
          tus carpetas en la bandeja; lo segundo, preparar una sesión en Estudiar.
        </p>
      )}
      {!cargando && !fallo && ultimosLotes.length > 0 && (
        <>
          <h3>Últimos lotes</h3>
          <ul className="check-list">
            {ultimosLotes.map((lote) => (
              <li key={lote.id} className="check-list__item">
                <span className="check-list__detail">
                  <strong>{batchKindLabel(lote.kind)}</strong>: {batchStatusLabel(lote.status)} ·{' '}
                  {lote.total_items} entrada(s) ·{' '}
                  <time dateTime={lote.created_at}>{lote.created_at}</time>
                </span>
                <Link to="/bandeja">Ver en la bandeja</Link>
              </li>
            ))}
          </ul>
        </>
      )}
      {!cargando && !fallo && ultimasSesiones.length > 0 && (
        <>
          <h3>Últimas sesiones</h3>
          <ul className="check-list">
            {ultimasSesiones.map((sesion) => (
              <li key={sesion.id} className="check-list__item">
                <span className="check-list__detail">
                  <strong>{modeLabel(sesion.mode)}</strong>: {statusLabel(sesion.status)} ·{' '}
                  {sesion.answered_questions} de {sesion.total_questions} preguntas
                </span>
                <Link to="/estudiar">Abrir en Estudiar</Link>
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}
