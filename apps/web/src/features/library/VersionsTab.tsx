import { useState } from 'react';

import type { Version } from '../../api/library';
import {
  ACCEPTABLE_VERSION_STATUSES,
  SUPERSEDING_VERSION_STATUSES,
  isRestricted,
  versionName,
} from '../../api/library';
import { ErrorState } from '../../components/ErrorState';
import { LoadingState } from '../../components/LoadingState';
import { StatusBadge } from '../../components/StatusBadge';
import { versionStatusLabel, versionStatusTone } from './labels';

export interface VersionsTabProps {
  documentId: string;
  versions: Version[];
  /** Versión cuya aceptación o sustitución está en curso. */
  busy: boolean;
  /** Motivo del último conflicto (409) que devolvió el servidor, con su detalle. */
  conflict: string | null;
  error: string | null;
  isPending: boolean;
  isError: boolean;
  onRetry: () => void;
  onAccept: (versionId: string) => void;
  onSupersede: (versionId: string, supersededId: string) => void;
}

function fecha(value: string | null | undefined): string {
  return value === null || value === undefined || value === '' ? 'no consta' : value;
}

/**
 * Versiones del documento (07_UI-UX §6): qué versiones hay, en qué estado, cuál es la activa y qué
 * se puede hacer con ellas.
 *
 * Aceptar y marcar una sustitución piden confirmación: las dos cambian lo que el producto considera
 * la versión buena, y el servidor las audita como promociones críticas. Un conflicto (409) se
 * muestra con el motivo del servidor y se dice que **nada cambió**.
 *
 * La comparación entre versiones (`diff`) todavía no la expone la API: la pestaña está preparada
 * para mostrarla y, mientras no haya datos, se dice —no se inventa una comparación con el texto de
 * cada versión leído por separado, porque dos textos sueltos no son un diff.
 */
export function VersionsTab({
  documentId,
  versions,
  busy,
  conflict,
  error,
  isPending,
  isError,
  onRetry,
  onAccept,
  onSupersede,
}: VersionsTabProps) {
  const [confirmandoAceptar, setConfirmandoAceptar] = useState<string | null>(null);
  const [sustituir, setSustituir] = useState<string | null>(null);
  const [sustituida, setSustituida] = useState<string>('');

  if (isPending) {
    return <LoadingState label="Cargando las versiones…" />;
  }

  if (isError) {
    return (
      <ErrorState
        title="No se pudieron cargar las versiones"
        message="El documento no está disponible o la API no responde."
        onRetry={onRetry}
      />
    );
  }

  return (
    <>
      {(error !== null || conflict !== null) && (
        <>
          <ErrorState
            title={conflict === null ? 'La operación no se aplicó' : 'El servidor la rechazó'}
            message={conflict ?? error ?? ''}
          />
          {conflict !== null && (
            <p className="hint">
              Un conflicto no cambia nada: la versión se queda como estaba para que puedas revisarla
              con el motivo delante.
            </p>
          )}
        </>
      )}

      <table className="table">
        <caption className="table__caption">
          {versions.length} versiones del documento (la antigua no se borra)
        </caption>
        <thead>
          <tr>
            <th scope="col">Versión</th>
            <th scope="col">Estado</th>
            <th scope="col">Fechas</th>
            <th scope="col">Contenido</th>
            <th scope="col">Sustituye a</th>
            <th scope="col">Acciones</th>
          </tr>
        </thead>
        <tbody>
          {versions.map((version) => {
            const nombre = versionName(version);
            const puedeAceptarse = ACCEPTABLE_VERSION_STATUSES.has(version.status);
            const puedeSustituir = SUPERSEDING_VERSION_STATUSES.has(version.status);
            const otras = versions.filter((otra) => otra.id !== version.id);
            return (
              <tr key={version.id}>
                <th scope="row">
                  <span className="sample__path">{nombre}</span>
                  {version.is_accepted && (
                    <>
                      {' '}
                      <StatusBadge tone="ok">versión activa y aceptada</StatusBadge>
                    </>
                  )}
                </th>
                <td>
                  <StatusBadge tone={versionStatusTone(version.status)}>
                    {versionStatusLabel(version.status)}
                  </StatusBadge>
                </td>
                <td className="hint">
                  publicada: {fecha(version.published_at)}
                  <br />
                  recuperada: {fecha(version.retrieved_at)}
                  <br />
                  vigente desde: {fecha(version.valid_from)}
                  {version.valid_to !== null && version.valid_to !== undefined && (
                    <>
                      <br />
                      vigente hasta: {version.valid_to}
                    </>
                  )}
                </td>
                <td className="hint">
                  {version.section_count} secciones · {version.evidence_count} evidencias
                  <br />
                  hash: {version.content_hash === null ? 'no consta' : version.content_hash}
                  {isRestricted(version) && (
                    <>
                      <br />
                      <StatusBadge tone="blocked">
                        derechos restringidos: no se puede compartir
                      </StatusBadge>
                    </>
                  )}
                </td>
                <td className="hint">{version.supersedes_id ?? 'a ninguna'}</td>
                <td>
                  {puedeAceptarse && confirmandoAceptar !== version.id && (
                    <button
                      className="button"
                      type="button"
                      disabled={busy}
                      aria-label={`Aceptar la versión: ${nombre}`}
                      onClick={() => {
                        setConfirmandoAceptar(version.id);
                      }}
                    >
                      Aceptar esta versión
                    </button>
                  )}
                  {puedeAceptarse && confirmandoAceptar === version.id && (
                    <div className="form__row">
                      <p className="hint">
                        ¿Confirmas que «{nombre}» pasa a ser la versión aceptada del documento? El
                        original y las demás versiones se conservan.
                      </p>
                      <button
                        className="button"
                        type="button"
                        disabled={busy}
                        aria-label={`Confirmar la aceptación de la versión: ${nombre}`}
                        onClick={() => {
                          setConfirmandoAceptar(null);
                          onAccept(version.id);
                        }}
                      >
                        Sí, aceptar esta versión
                      </button>
                      <button
                        className="button"
                        type="button"
                        onClick={() => {
                          setConfirmandoAceptar(null);
                        }}
                      >
                        Cancelar
                      </button>
                    </div>
                  )}

                  {puedeSustituir && otras.length > 0 && sustituir !== version.id && (
                    <button
                      className="button"
                      type="button"
                      disabled={busy}
                      aria-label={`Marcar qué versión sustituye: ${nombre}`}
                      onClick={() => {
                        setSustituir(version.id);
                        setSustituida('');
                      }}
                    >
                      Marcar sustitución…
                    </button>
                  )}
                  {sustituir === version.id && (
                    <div className="form__row">
                      <label className="form__label" htmlFor={`sustituida-${version.id}`}>
                        ¿A qué versión sustituye «{nombre}»?
                      </label>
                      <select
                        id={`sustituida-${version.id}`}
                        className="selector__select"
                        value={sustituida}
                        onChange={(event) => {
                          setSustituida(event.target.value);
                        }}
                      >
                        <option value="">elige la versión sustituida</option>
                        {otras.map((otra) => (
                          <option key={otra.id} value={otra.id}>
                            {versionName(otra)} · {versionStatusLabel(otra.status)}
                          </option>
                        ))}
                      </select>
                      <p className="hint">
                        Confirmar la sustitución no borra la versión antigua: se queda con su estado
                        y su contenido sigue siendo citable.
                      </p>
                      <button
                        className="button"
                        type="button"
                        disabled={busy || sustituida === ''}
                        aria-label={`Confirmar que ${nombre} sustituye a la versión elegida`}
                        onClick={() => {
                          setSustituir(null);
                          onSupersede(version.id, sustituida);
                        }}
                      >
                        Sí, marcar la sustitución
                      </button>
                      <button
                        className="button"
                        type="button"
                        onClick={() => {
                          setSustituir(null);
                          setSustituida('');
                        }}
                      >
                        Cancelar
                      </button>
                    </div>
                  )}
                  {!puedeAceptarse && !puedeSustituir && (
                    <span className="hint">sin acciones: el estado no lo admite</span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      <h3>Comparar dos versiones (diff)</h3>
      <p className="hint">
        La comparación entre versiones todavía no la expone la API: no hay ruta que devuelva qué
        cambió de una versión a otra. Esta pestaña está preparada para mostrarla y, mientras no
        exista, no se rellena con nada: comparar aquí dos textos leídos por separado sería inventar
        un diff.
      </p>
      <p className="hint">
        Documento consultado: <span className="sample__path">{documentId}</span>. Mientras tanto, se
        pueden ver los estados y las fechas de cada versión, y aceptar la que corresponda.
      </p>
    </>
  );
}
