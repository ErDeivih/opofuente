import { useMemo, useState } from 'react';

import type {
  BulkDecisionResponse,
  Decision,
  DecisionOutcome,
  Proposal,
  ReviewGroup,
} from '../../api/classification';
import { StatusBadge } from '../../components/StatusBadge';
import { axisLabel, countLabel, percent, subjectLabel, subjectTypeLabel, valueLabel } from './labels';

export interface ReviewGroupsProps {
  groups: ReviewGroup[];
  /** Propuestas pendientes: son las filas que el lote puede incluir o dejar fuera. */
  proposals: Proposal[];
  busy: boolean;
  result: BulkDecisionResponse | null;
  onBulk: (input: {
    proposalIds: string[];
    excluded: string[];
    decision: Decision;
    note: string;
  }) => void;
  onUndoBatch: (outcomes: DecisionOutcome[]) => void;
}

/**
 * Cola de revisión por grupos y decisión en lote con excepciones (04 §8, 07_UI-UX §4).
 *
 * El lote agrupa por eje y valor propuesto —lo que el servidor ya agrupa— y **nunca es todo o nada**:
 * antes de confirmar se ven las filas que se van a decidir y se puede dejar fuera una concreta. El
 * botón dice cuántas propuestas va a afectar de verdad, y la respuesta del servidor se cuenta tal
 * cual: aplicadas, conflictos y excepciones, sin redondear ni esconder los conflictos.
 */
export function ReviewGroups({
  groups,
  proposals,
  busy,
  result,
  onBulk,
  onUndoBatch,
}: ReviewGroupsProps) {
  const [marked, setMarked] = useState<string[]>([]);
  const [excluded, setExcluded] = useState<string[]>([]);
  const [note, setNote] = useState('');

  const byId = useMemo(() => new Map(proposals.map((proposal) => [proposal.id, proposal])), [
    proposals,
  ]);
  const markedGroups = groups.filter((group) => marked.includes(group.key));
  const batchIds = markedGroups.flatMap((group) => group.proposal_ids);
  const included = batchIds.filter((id) => !excluded.includes(id));
  const pendingTotal = groups.reduce((total, group) => total + group.size, 0);
  const conflicts = result?.outcomes.filter((outcome) => !outcome.applied) ?? [];

  if (groups.length === 0) {
    return (
      <p className="hint">
        No hay propuestas pendientes que agrupar. Cuando el motor proponga algo lo verás aquí,
        agrupado por eje y valor, con su tamaño y su confianza.
      </p>
    );
  }

  return (
    <>
      <p className="hint">
        {groups.length} grupos con {pendingTotal} propuestas pendientes. Marca los que quieras decidir
        juntos: el lote se puede completar o dejar fuera filas concretas antes de confirmarlo.
      </p>

      <div className="table-wrap">
        <table className="table">
          <caption className="table__caption">Grupos de revisión</caption>
        <thead>
          <tr>
            <th scope="col">Grupo</th>
            <th scope="col">Sujeto</th>
            <th scope="col">Eje</th>
            <th scope="col">Propuestas</th>
            <th scope="col">Confianza</th>
            <th scope="col">Aviso</th>
          </tr>
        </thead>
        <tbody>
          {groups.map((group) => (
            <tr key={group.key}>
              <td>
                <label>
                  <input
                    type="checkbox"
                    checked={marked.includes(group.key)}
                    aria-label={`Marcar el grupo ${group.label} (${subjectTypeLabel(group.subject_type)}, ${axisLabel(group.axis)}) para decidirlo en lote`}
                    onChange={(event) => {
                      const active = event.target.checked;
                      setMarked((previous) =>
                        active
                          ? [...previous, group.key]
                          : previous.filter((key) => key !== group.key),
                      );
                    }}
                  />{' '}
                  {group.label}
                </label>
                {group.label !== group.proposed_value && (
                  <span className="hint sample__path"> {group.proposed_value}</span>
                )}
              </td>
              <td>{subjectTypeLabel(group.subject_type)}</td>
              <td>{axisLabel(group.axis)}</td>
              <td>{group.size}</td>
              <td>
                {percent(group.min_confidence)}
                {group.min_confidence !== group.max_confidence &&
                  ` – ${percent(group.max_confidence)}`}
              </td>
              <td>
                {group.is_critical ? (
                  <StatusBadge tone="warning">requiere tu confirmación</StatusBadge>
                ) : (
                  <span className="hint">—</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
        </table>
      </div>

      {markedGroups.length > 0 && (
        <>
          <h3>Lote</h3>
          <p className="hint">
            El lote decide <strong>{included.length}</strong> de {batchIds.length} propuestas de{' '}
            {countLabel(markedGroups.length, 'grupo', 'grupos')}. Marca «Dejar fuera del lote» en las
            filas que quieras decidir por separado.
          </p>
          <ul className="sample">
            {batchIds.map((id) => {
              const proposal = byId.get(id);
              return (
                <li key={id}>
                  <label>
                    <input
                      type="checkbox"
                      checked={excluded.includes(id)}
                      aria-label={`Dejar fuera del lote: ${subjectTypeLabel(
                        proposal?.subject_type ?? '',
                      )} ${proposal === undefined ? id : subjectLabel(proposal)}`}
                      onChange={(event) => {
                        const fuera = event.target.checked;
                        setExcluded((previous) =>
                          fuera ? [...previous, id] : previous.filter((item) => item !== id),
                        );
                      }}
                    />{' '}
                    {proposal === undefined ? (
                      <span className="hint">propuesta {id}</span>
                    ) : (
                      <>
                        <span className="hint">{subjectTypeLabel(proposal.subject_type)}</span>{' '}
                        {subjectLabel(proposal)}{' '}
                        <span className="hint">· {valueLabel(proposal)}</span>
                      </>
                    )}
                  </label>
                </li>
              );
            })}
          </ul>

          <div className="form__row">
            <label className="form__label" htmlFor="nota-lote">
              Motivo del lote (opcional)
            </label>
            <input
              id="nota-lote"
              className="form__input"
              type="text"
              value={note}
              onChange={(event) => {
                setNote(event.target.value);
              }}
            />
          </div>

          <div className="form__row">
            <button
              className="button"
              type="button"
              disabled={busy || included.length === 0}
              onClick={() => {
                onBulk({
                  proposalIds: batchIds,
                  excluded,
                  decision: 'accepted',
                  note: note.trim(),
                });
              }}
            >
              Aceptar {countLabel(included.length, 'propuesta', 'propuestas')}
            </button>
            <button
              className="button"
              type="button"
              disabled={busy || included.length === 0}
              onClick={() => {
                onBulk({
                  proposalIds: batchIds,
                  excluded,
                  decision: 'rejected',
                  note: note.trim(),
                });
              }}
            >
              Rechazar {countLabel(included.length, 'propuesta', 'propuestas')}
            </button>
          </div>
        </>
      )}

      {result !== null && (
        <>
          <h3>Resultado del lote</h3>
          <dl className="facts" aria-live="polite">
            <dt>Propuestas pedidas</dt>
            <dd>{result.requested}</dd>
            <dt>Aplicadas</dt>
            <dd>{result.applied}</dd>
            <dt>Conflictos</dt>
            <dd>{result.conflicts}</dd>
            <dt>Excepciones</dt>
            <dd>{result.excluded?.length ?? 0}</dd>
          </dl>
          {conflicts.length > 0 && (
            <ul className="issues">
              {conflicts.map((outcome) => (
                <li key={outcome.proposal_id} className="issues__item">
                  <StatusBadge tone="blocked">no aplicada</StatusBadge>
                  <span>{outcome.reason ?? 'el servidor no dio motivo'}</span>
                </li>
              ))}
            </ul>
          )}
          <div className="form__row">
            <button
              className="button"
              type="button"
              disabled={busy || result.applied === 0}
              onClick={() => {
                onUndoBatch(result.outcomes);
              }}
            >
              Deshacer el lote
            </button>
            <span className="hint">
              Deshacer devuelve a la cola todo lo que aplicó este lote, y queda auditado.
            </span>
          </div>
        </>
      )}
    </>
  );
}
