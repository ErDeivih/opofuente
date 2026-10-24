import { useState } from 'react';

import type { CoverageType, Mapping, Version } from '../../api/library';
import { COVERAGE_TYPES, versionName } from '../../api/library';
import type { Curriculum, CurriculumNode, Opposition } from '../../api/profiles';
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
  /** Oposiciones conocidas: de la convocatoria activa de cada una sale el programa. */
  oppositions: Opposition[];
  /** Convocatoria cuyo programa se está usando para asignar. */
  convocationId: string | null;
  onConvocationChange: (convocationId: string) => void;
  curriculum: Curriculum | null;
  curriculumIsPending: boolean;
  onAssign: (nodeId: string, coverage: CoverageType) => void;
  onRemove: (mappingId: string) => void;
  /** Hay una asignación o una retirada en curso. */
  busy: boolean;
  /** Motivo del último rechazo del servidor (409) o error de la operación. */
  actionError: string | null;
}

interface NodoAplanado {
  nodo: CurriculumNode;
  profundidad: number;
}

/** El programa llega como árbol y el selector necesita una lista: se aplana sin perder el nivel. */
function aplanar(nodos: CurriculumNode[], profundidad = 0): NodoAplanado[] {
  return nodos.flatMap((nodo) => [
    { nodo, profundidad },
    ...aplanar(nodo.children, profundidad + 1),
  ]);
}

/**
 * Asignaciones de programa del documento (07_UI-UX §6, contrato §7).
 *
 * Se leen por **versión**: es lo que el servidor relaciona con un nodo del programa. Se muestran tal
 * y como vienen —provisional o aceptada— sin sumarlas: una asignación provisional no es cobertura
 * confirmada, y la pantalla no la vende como tal.
 *
 * Asignar y retirar pasan por la API y el servidor decide: si rechaza la operación (409), aquí se
 * muestra su motivo y **nada cambia**; la pantalla no da por hecha una asignación que no consta.
 */
export function AssignmentsTab({
  version,
  versionCount,
  mappings,
  isPending,
  isError,
  onRetry,
  oppositions,
  convocationId,
  onConvocationChange,
  curriculum,
  curriculumIsPending,
  onAssign,
  onRemove,
  busy,
  actionError,
}: AssignmentsTabProps) {
  const [nodoElegido, setNodoElegido] = useState('');
  const [cobertura, setCobertura] = useState<CoverageType>('partial');
  const [quitando, setQuitando] = useState<string | null>(null);

  if (version === null) {
    return (
      <p className="hint">
        Este documento no tiene ninguna versión, así que no puede tener asignaciones de programa.
      </p>
    );
  }

  const convocatorias = oppositions.flatMap((opposition) =>
    opposition.active_convocation === null || opposition.active_convocation === undefined
      ? []
      : [
          {
            id: opposition.active_convocation.id,
            etiqueta: `${opposition.name} (${opposition.code}) · ${opposition.active_convocation.code}`,
          },
        ],
  );
  const opciones = curriculum === null ? [] : aplanar(curriculum.nodes);

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

      {actionError !== null && (
        <ErrorState title="El servidor no aplicó la operación" message={actionError} />
      )}

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
          Esta versión no está asignada a ningún nodo del programa. Se le puede dar una asignación
          aquí debajo: la crea el servidor sobre la <strong>versión</strong> (no sobre el fichero),
          con su traza de auditoría.
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
              <th scope="col">Acciones</th>
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
                <td className="hint">{mapping.source_proposal_id ?? 'sin propuesta de origen'}</td>
                <td>
                  {quitando !== mapping.id && (
                    <button
                      className="button"
                      type="button"
                      disabled={busy}
                      aria-label={`Quitar la asignación: ${mapping.node_path}`}
                      onClick={() => {
                        setQuitando(mapping.id);
                      }}
                    >
                      Quitar…
                    </button>
                  )}
                  {quitando === mapping.id && (
                    <div className="form__row">
                      <p className="hint">
                        ¿Quitar la asignación de «{mapping.node_path} {mapping.node_title}»? El
                        material no se borra: el documento y su versión siguen donde estaban, y la
                        retirada queda auditada.
                      </p>
                      <button
                        className="button"
                        type="button"
                        disabled={busy}
                        aria-label={`Confirmar quitar la asignación: ${mapping.node_path}`}
                        onClick={() => {
                          setQuitando(null);
                          onRemove(mapping.id);
                        }}
                      >
                        Sí, quitar la asignación
                      </button>
                      <button
                        className="button"
                        type="button"
                        onClick={() => {
                          setQuitando(null);
                        }}
                      >
                        Cancelar
                      </button>
                    </div>
                  )}
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

      <h4>Asignar esta versión a un nodo del programa</h4>
      {convocatorias.length === 0 ? (
        <p className="hint">
          No hay ninguna convocatoria activa entre las oposiciones conocidas, y el programa sale de
          la convocatoria: sin ella no hay nodo al que asignar nada. Se activa una desde la pantalla
          de Oposiciones.
        </p>
      ) : (
        <>
          <div className="form__row">
            <label className="form__label" htmlFor="asignar-convocatoria">
              Convocatoria
            </label>
            <select
              id="asignar-convocatoria"
              className="selector__select"
              value={convocationId ?? ''}
              onChange={(event) => {
                setNodoElegido('');
                onConvocationChange(event.target.value);
              }}
            >
              {convocatorias.map((convocatoria) => (
                <option key={convocatoria.id} value={convocatoria.id}>
                  {convocatoria.etiqueta}
                </option>
              ))}
            </select>

            <label className="form__label" htmlFor="asignar-nodo">
              Nodo del programa
            </label>
            <select
              id="asignar-nodo"
              className="selector__select"
              value={nodoElegido}
              disabled={curriculumIsPending || opciones.length === 0}
              onChange={(event) => {
                setNodoElegido(event.target.value);
              }}
            >
              <option value="">
                {curriculumIsPending ? 'cargando el programa…' : 'elige el nodo del programa'}
              </option>
              {opciones.map(({ nodo, profundidad }) => (
                <option key={nodo.id} value={nodo.id}>
                  {`${'— '.repeat(profundidad)}${nodo.official_code} · ${nodo.title}`}
                </option>
              ))}
            </select>

            <label className="form__label" htmlFor="asignar-cobertura">
              Cobertura
            </label>
            <select
              id="asignar-cobertura"
              className="selector__select"
              value={cobertura}
              onChange={(event) => {
                setCobertura(event.target.value as CoverageType);
              }}
            >
              {COVERAGE_TYPES.map((tipo) => (
                <option key={tipo} value={tipo}>
                  {coverageTypeLabel(tipo)}
                </option>
              ))}
            </select>

            <button
              className="button"
              type="button"
              disabled={busy || nodoElegido === ''}
              aria-label="Asignar a la versión: el nodo elegido"
              onClick={() => {
                onAssign(nodoElegido, cobertura);
              }}
            >
              Asignar a la versión
            </button>
          </div>
          <p className="hint">
            La asignación nace <strong>aceptada</strong> —la pide una persona, no el motor— y queda
            auditada. Si el nodo o la versión no existieran, el servidor responde 404 y aquí no se
            escribe nada. El fichero no se duplica: la misma fuente puede asignarse a varias
            oposiciones.
          </p>
        </>
      )}
    </>
  );
}
