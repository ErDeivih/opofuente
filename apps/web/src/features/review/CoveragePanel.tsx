import type { Coverage } from '../../api/classification';
import type { CurriculumNode } from '../../api/profiles';
import { ErrorState } from '../../components/ErrorState';
import { LoadingState } from '../../components/LoadingState';
import { CurriculumTree } from '../profiles/CurriculumTree';

export interface CoveragePanelProps {
  nodes: CurriculumNode[];
  selectedId: string | null;
  onSelect: (node: CurriculumNode) => void;
  coverage: Coverage | undefined;
  isPending: boolean;
  isError: boolean;
  onRetry: () => void;
  /** Nombre de la oposición con la que se lee el programa. */
  oppositionName: string | null;
}

/**
 * Cobertura del programa: provisional y aceptada, siempre separadas (07_UI-UX §5 y §12).
 *
 * El panel **no** suma las dos en un solo número a propósito: lo provisional es lo que el motor
 * aplicó solo y todavía no ha confirmado nadie, y lo aceptado es lo que ha confirmado una persona
 * sobre texto utilizable. Mezclarlas daría una cifra que no significa nada y que haría parecer
 * revisado lo que no lo está.
 */
export function CoveragePanel({
  nodes,
  selectedId,
  onSelect,
  coverage,
  isPending,
  isError,
  onRetry,
  oppositionName,
}: CoveragePanelProps) {
  return (
    <>
      <p className="hint">
        Se cuenta lo que cubre cada nodo con su subárbol. La cobertura <strong>provisional</strong> es
        lo aplicado por el motor sin confirmar; la <strong>aceptada</strong> es lo que has confirmado
        tú sobre texto utilizable. Nunca se suman.
      </p>

      {nodes.length === 0 ? (
        <p className="hint">
          No hay un programa cargado: elige una oposición activa para ver su cobertura.
        </p>
      ) : (
        <>
          <CurriculumTree nodes={nodes} selectedId={selectedId} onSelect={onSelect} />
          {selectedId === null && (
            <p className="hint">Elige un bloque o un tema para ver su cobertura.</p>
          )}
        </>
      )}

      {selectedId !== null && isPending && <LoadingState label="Calculando la cobertura…" />}
      {selectedId !== null && isError && (
        <ErrorState
          title="No se pudo calcular la cobertura"
          message="El nodo ya no existe o la API no responde."
          onRetry={onRetry}
        />
      )}

      {selectedId !== null && coverage !== undefined && (
        <>
          <p className="node__path">{coverage.path}</p>
          <p className="node__title">{coverage.title}</p>
          {oppositionName !== null && <p className="hint">{oppositionName}</p>}

          <dl className="facts">
            <dt>Cobertura provisional</dt>
            <dd>
              {coverage.provisional}{' '}
              <span className="hint">(aplicada por el motor, sin confirmar)</span>
            </dd>
            <dt>Cobertura aceptada</dt>
            <dd>
              {coverage.accepted} <span className="hint">(confirmada por ti)</span>
            </dd>
            <dt>Materiales sin clasificar</dt>
            <dd>
              {coverage.unclassified_subjects}{' '}
              <span className="hint">(material del que todavía no hay ninguna propuesta)</span>
            </dd>
            <dt>Materiales totales</dt>
            <dd>{coverage.materials_total}</dd>
          </dl>

          {coverage.subtree !== undefined && coverage.subtree.length > 0 && (
            <table className="table">
              <caption className="table__caption">
                Nodos del subárbol con su cobertura (provisional y aceptada, por separado)
              </caption>
              <thead>
                <tr>
                  <th scope="col">Nodo</th>
                  <th scope="col">Provisional</th>
                  <th scope="col">Aceptada</th>
                  <th scope="col">Materiales</th>
                </tr>
              </thead>
              <tbody>
                {coverage.subtree.map((node) => (
                  <tr key={node.node_id}>
                    <th scope="row">
                      <span className="tree__code">{node.path}</span> {node.title}
                    </th>
                    <td>{node.provisional}</td>
                    <td>{node.accepted}</td>
                    <td>
                      {node.materials !== undefined && node.materials.length > 0 ? (
                        <ul className="evidence">
                          {node.materials.map((material) => (
                            <li key={material}>{material}</li>
                          ))}
                        </ul>
                      ) : (
                        <span className="hint">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      )}
    </>
  );
}
