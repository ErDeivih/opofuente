import { useState } from 'react';

import type { Decision, Proposal } from '../../api/classification';
import type { CurriculumNode } from '../../api/profiles';
import { StatusBadge } from '../../components/StatusBadge';
import {
  AXIS_LABEL,
  BAND_LABEL,
  BAND_TONE,
  STATUS_LABEL,
  STATUS_TONE,
  SUBJECT_TYPE_LABEL,
  percent,
  subjectLabel,
  valueLabel,
} from './labels';

export interface ProposalListProps {
  proposals: Proposal[];
  /** Árbol del programa activo: sus temas son las opciones reales para corregir un tema. */
  curriculumNodes: CurriculumNode[];
  busy: boolean;
  onDecide: (input: { proposalId: string; decision: Decision; overrideValue?: string }) => void;
}

/** Los temas del programa, en orden de programa: lo único que se puede proponer en el eje de tema. */
function topicNodes(nodes: CurriculumNode[]): CurriculumNode[] {
  const topics: CurriculumNode[] = [];
  const walk = (items: CurriculumNode[]) => {
    for (const node of items) {
      if (node.node_type === 'topic') {
        topics.push(node);
      }
      walk(node.children);
    }
  };
  walk(nodes);
  return topics;
}

/**
 * Cola de propuestas: qué se propone, con qué confianza, con qué evidencia y qué se puede hacer.
 *
 * La evidencia va en la propia fila a propósito: una propuesta que no se puede comprobar no se puede
 * revisar, y obligar a abrir otra pantalla para ver de dónde sale esconde justo lo que hay que mirar
 * (04 §8). Las propuestas de eje crítico se marcan como «requiere tu confirmación» y las aplicadas
 * provisionalmente se declaran reversibles en lugar de presentarse como hechas.
 */
export function ProposalList({ proposals, curriculumNodes, busy, onDecide }: ProposalListProps) {
  const [corrections, setCorrections] = useState<Record<string, string>>({});
  const topics = topicNodes(curriculumNodes);

  if (proposals.length === 0) {
    return (
      <p className="hint">
        No hay ninguna propuesta esperando tu decisión. Las que ya decidiste están en el historial de
        esta sesión y las descartadas no vuelven a aparecer.
      </p>
    );
  }

  return (
    <div className="table-wrap">
      <table className="table">
        <caption className="table__caption">
          {proposals.length} propuestas esperando tu decisión
        </caption>
        <thead>
          <tr>
            <th scope="col">Material</th>
            <th scope="col">Eje</th>
            <th scope="col">Valor propuesto</th>
            <th scope="col">Confianza</th>
            <th scope="col">Evidencia</th>
            <th scope="col">Alternativas</th>
            <th scope="col">Estado</th>
            <th scope="col" className="table__actions">
              Decisión
            </th>
          </tr>
        </thead>
      <tbody>
        {proposals.map((proposal) => {
          const label = subjectLabel(proposal);
          const tipo = SUBJECT_TYPE_LABEL[proposal.subject_type];
          const axis = AXIS_LABEL[proposal.axis];
          // El nombre accesible de cada acción lleva el material, de qué se trata y su eje: en una
          // tabla con varias propuestas del mismo fichero, «Aceptar» a secas no dice cuál se acepta.
          const sujeto = `${label} (${tipo}) · ${axis}`;
          const correction = corrections[proposal.id] ?? '';
          const provisional = proposal.status === 'auto_applied_provisional';
          return (
            <tr key={proposal.id}>
              <th scope="row">
                {label} ({tipo})
              </th>
              <td>
                {axis}
                {proposal.is_critical && (
                  <>
                    {' '}
                    <StatusBadge tone="warning">requiere tu confirmación</StatusBadge>
                  </>
                )}
              </td>
              <td>
                {valueLabel(proposal)}
              </td>
              <td>
                {percent(proposal.confidence)}{' '}
                <StatusBadge tone={BAND_TONE[proposal.band]}>
                  confianza {BAND_LABEL[proposal.band]}
                </StatusBadge>
              </td>
              <td>
                {proposal.evidence !== undefined && proposal.evidence.length > 0 ? (
                  <ul className="evidence">
                    {proposal.evidence.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                ) : (
                  <span className="hint">Sin evidencia registrada: no la aceptes sin mirar el texto.</span>
                )}
              </td>
              <td>
                {proposal.alternatives !== undefined && proposal.alternatives.length > 0 ? (
                  <ul className="evidence">
                    {proposal.alternatives.map((alternativa) => (
                      <li key={alternativa.value}>
                        <span className="sample__path">{alternativa.value}</span>{' '}
                        <span className="hint">{percent(alternativa.confidence)}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <span className="hint">—</span>
                )}
              </td>
              <td>
                <StatusBadge tone={STATUS_TONE[proposal.status]}>
                  {STATUS_LABEL[proposal.status]}
                </StatusBadge>
                {provisional && (
                  <span className="hint"> sigue siendo reversible: recházala o deshazla.</span>
                )}
              </td>
              <td className="table__actions">
                <div className="form__row">
                  <button
                    className="button"
                    type="button"
                    disabled={busy}
                    aria-label={`${provisional ? 'Confirmar' : 'Aceptar'}: ${sujeto}`}
                    onClick={() => {
                      onDecide({ proposalId: proposal.id, decision: 'accepted' });
                    }}
                  >
                    {provisional ? 'Confirmar' : 'Aceptar'}
                  </button>
                  <button
                    className="button"
                    type="button"
                    disabled={busy}
                    aria-label={`Rechazar: ${sujeto}`}
                    onClick={() => {
                      onDecide({ proposalId: proposal.id, decision: 'rejected' });
                    }}
                  >
                    Rechazar
                  </button>
                </div>
                {/* Solo el eje de tema se corrige aquí: sus valores válidos son los nodos del
                    programa, que el servidor ya sirve. En los vocabularios cerrados (tipo
                    documental, autoridad, derechos) la lista de valores la posee el servidor, y
                    escribirla a mano en la interfaz sería decidir reglas en el cliente. */}
                {proposal.axis === 'topic' && (
                  <div className="form__row">
                    <label className="form__label" htmlFor={`correccion-${proposal.id}`}>
                      Corregir el tema
                    </label>
                    <select
                      id={`correccion-${proposal.id}`}
                      className="selector__select"
                      value={correction}
                      onChange={(event) => {
                        const elegido = event.target.value;
                        setCorrections((previous) => ({ ...previous, [proposal.id]: elegido }));
                      }}
                    >
                      <option value="">Sin corrección: se propone {proposal.proposed_value}</option>
                      {topics.map((topic) => (
                        <option key={topic.id} value={topic.path}>
                          {topic.path} · {topic.title}
                        </option>
                      ))}
                    </select>
                    <button
                      className="button"
                      type="button"
                      disabled={busy || correction === ''}
                      aria-label={`Aceptar con la corrección: ${sujeto}`}
                      onClick={() => {
                        onDecide({
                          proposalId: proposal.id,
                          decision: 'accepted',
                          overrideValue: correction,
                        });
                      }}
                    >
                      Aceptar corregido
                    </button>
                  </div>
                )}
              </td>
            </tr>
          );
        })}
      </tbody>
      </table>
    </div>
  );
}
