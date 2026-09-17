import type { Mapping, Version } from '../../api/library';
import { versionName } from '../../api/library';
import { ErrorState } from '../../components/ErrorState';
import { LoadingState } from '../../components/LoadingState';
import { StatusBadge } from '../../components/StatusBadge';
import { coverageTypeLabel, mappingStatusLabel, mappingStatusTone } from './labels';

export interface AssignmentsTabProps {
  version: Version | null;
  /** Cuántas versiones tiene el documento: cada una tiene sus propias asignaciones. */
  versionCount: number;
  mappings: Mapping[];
  isPending: boolean;
  isError: boolean;
  onRetry: () => void;
}

/**
 * Asignaciones de programa del documento (07_UI-UX §6).
 *
 * Se leen por **versión**: es lo que el servidor relaciona con un nodo del programa. Se muestran
 * tal y como vienen —provisional o aceptada— sin sumarlas: una asignación provisional no es
 * cobertura confirmada, y la pantalla no la vende como tal.
 */
export function AssignmentsTab({
  version,
  versionCount,
  mappings,
  isPending,
  isError,
  onRetry,
}: AssignmentsTabProps) {
  if (version === null) {
    return (
      <p className="hint">
        Este documento no tiene ninguna versión, así que no puede tener asignaciones de programa.
      </p>
    );
  }

  return (
    <>
      <p className="hint">
        Las asignaciones cuelgan de la versión: aquí se ven las de «{versionName(version)}»
        {versionCount > 1 && (
          <>
            {' '}
            (el documento tiene {versionCount} versiones y cada una lleva las suyas)
          </>
        )}
        .
      </p>

      {isPending && <LoadingState label="Cargando las asignaciones…" />}
      {isError && (
        <ErrorState
          title="No se pudieron cargar las asignaciones"
          message="El servidor de clasificación no respondió a la consulta de mapeos."
          onRetry={onRetry}
        />
      )}

      {!isPending && !isError && mappings.length === 0 && (
        <p className="hint">
          Esta versión no está asignada a ningún nodo del programa. Las asignaciones del motor se
          crean sobre el material al aceptar una propuesta de tema, y las de la versión se dan de
          alta por la API (`POST /document-versions/&lt;id&gt;/mappings`): esta pantalla todavía no
          ofrece ese alta, así que aquí puede estar vacía sin que falte nada por hacer.
        </p>
      )}

      {mappings.length > 0 && (
        <table className="table">
          <caption className="table__caption">
            {mappings.length} asignaciones de programa de la versión
          </caption>
          <thead>
            <tr>
              <th scope="col">Nodo del programa</th>
              <th scope="col">Cobertura</th>
              <th scope="col">Estado</th>
              <th scope="col">Confianza</th>
              <th scope="col">Origen</th>
            </tr>
          </thead>
          <tbody>
            {mappings.map((mapping) => (
              <tr key={mapping.id}>
                <th scope="row">
                  <span className="tree__code">{mapping.node_path}</span> {mapping.node_title}
                </th>
                <td>{coverageTypeLabel(mapping.coverage_type)}</td>
                <td>
                  <StatusBadge tone={mappingStatusTone(mapping.status)}>
                    {mappingStatusLabel(mapping.status)}
                  </StatusBadge>
                </td>
                <td>{Math.round(mapping.confidence * 100)} %</td>
                <td className="hint">
                  {mapping.source_proposal_id ?? 'sin propuesta de origen'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {mappings.some((mapping) => mapping.status === 'provisional') && (
        <p className="hint">
          Lo marcado como provisional lo aplicó el motor y todavía no lo ha confirmado nadie: no
          cuenta como cobertura aceptada.
        </p>
      )}
    </>
  );
}
