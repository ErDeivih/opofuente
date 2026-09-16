import type { DecisionOutcome } from '../../api/classification';
import { StatusBadge } from '../../components/StatusBadge';
import { statusLabel } from './labels';

/**
 * Una decisión tomada en esta sesión, con lo justo para poder deshacerla sin volver a buscarla.
 *
 * `id` es con lo que se deshace: el evento de auditoría que devolvió el servidor o, si no lo hubo, la
 * propia propuesta (el contrato admite los dos).
 */
export interface SessionDecision {
  id: string;
  label: string;
  value: string;
  outcome: DecisionOutcome;
  undone: boolean;
  /** Tipo de sujeto, para que dos decisiones del mismo material no compartan nombre accesible. */
  subjectType?: string | undefined;
}

export interface DecisionHistoryProps {
  decisions: SessionDecision[];
  busy: boolean;
  onUndo: (decision: SessionDecision) => void;
}

/**
 * Historial de la sesión: lo que se acaba de decidir y cómo deshacerlo (07_UI-UX §4).
 *
 * Aparece solo cuando hay algo que deshacer, y no se reordena al refrescar la cola: una decisión
 * recién tomada sale de «pendientes», y sin este historial el «Deshacer» que exige la especificación
 * desaparecería con ella.
 */
export function DecisionHistory({ decisions, busy, onUndo }: DecisionHistoryProps) {
  if (decisions.length === 0) {
    return null;
  }

  return (
    <table className="table">
      <caption className="table__caption">
        {decisions.length} decisiones de esta sesión
      </caption>
      <thead>
        <tr>
          <th scope="col">Propuesta</th>
          <th scope="col">Valor</th>
          <th scope="col">Resultado</th>
          <th scope="col">Deshacer</th>
        </tr>
      </thead>
      <tbody>
        {decisions.map((decision) => (
          <tr key={decision.id}>
            <th scope="row">{decision.label}</th>
            <td>{decision.value}</td>
            <td>
              {decision.outcome.applied ? (
                <StatusBadge tone="ok">{statusLabel(decision.outcome.status)}</StatusBadge>
              ) : (
                <>
                  <StatusBadge tone="blocked">no aplicada</StatusBadge>
                  {decision.outcome.reason !== null && decision.outcome.reason !== undefined && (
                    <span className="hint"> {decision.outcome.reason}</span>
                  )}
                </>
              )}
            </td>
            <td>
              {decision.undone ? (
                <span className="hint">deshecha: la propuesta volvió a la cola</span>
              ) : (
                <button
                  className="button"
                  type="button"
                  disabled={busy || !decision.outcome.applied}
                  aria-label={`Deshacer la decisión sobre ${decision.label}${
                    decision.subjectType === undefined
                      ? ''
                      : ` (${decision.subjectType === 'artifact' ? 'material' : 'texto'})`
                  }`}
                  onClick={() => {
                    onUndo(decision);
                  }}
                >
                  Deshacer
                </button>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
