import { useState } from 'react';

import type { Version, VersionDiff } from '../../api/library';
import {
  ACCEPTABLE_VERSION_STATUSES,
  SUPERSEDING_VERSION_STATUSES,
  isRestricted,
  versionName,
} from '../../api/library';
import { ErrorState } from '../../components/ErrorState';
import { LoadingState } from '../../components/LoadingState';
import { StatusBadge } from '../../components/StatusBadge';
import { sectionDiffLabel, sectionDiffTone, versionStatusLabel, versionStatusTone } from './labels';

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
  /** Comparación elegida: la versión anterior y la nueva. */
  fromVersionId: string | null;
  toVersionId: string | null;
  onSelectFrom: (versionId: string) => void;
  onSelectTo: (versionId: string) => void;
  diff: VersionDiff | null;
  diffIsPending: boolean;
  diffIsError: boolean;
  onRetryDiff: () => void;
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
 * La comparación entre versiones la sirve la API (`GET /documents/{id}/diff`): aquí se eligen las dos
 * versiones y se muestra **lo que el servidor comparó**, sección a sección, sin fusionar nada. Si el
 * servidor no encuentra secciones que comparar, se dice por qué en lugar de enseñar una tabla vacía
 * como si no hubiera cambios.
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
  fromVersionId,
  toVersionId,
  onSelectFrom,
  onSelectTo,
  diff,
  diffIsPending,
  diffIsError,
  onRetryDiff,
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
      {versions.length < 2 ? (
        <p className="hint">
          Comparar necesita al menos dos versiones del documento, y ahora mismo hay{' '}
          {versions.length}. Cuando entre una segunda edición del mismo material, aquí se verá qué
          cambió sección a sección. Documento consultado:{' '}
          <span className="sample__path">{documentId}</span>.
        </p>
      ) : (
        <>
          <div className="form__row">
            <label className="form__label" htmlFor="diff-desde">
              Versión anterior
            </label>
            <select
              id="diff-desde"
              className="selector__select"
              value={fromVersionId ?? ''}
              onChange={(event) => {
                onSelectFrom(event.target.value);
              }}
            >
              {versions.map((version) => (
                <option key={version.id} value={version.id}>
                  {versionName(version)} · {versionStatusLabel(version.status)}
                </option>
              ))}
            </select>
            <label className="form__label" htmlFor="diff-hasta">
              Versión nueva
            </label>
            <select
              id="diff-hasta"
              className="selector__select"
              value={toVersionId ?? ''}
              onChange={(event) => {
                onSelectTo(event.target.value);
              }}
            >
              {versions.map((version) => (
                <option key={version.id} value={version.id}>
                  {versionName(version)} · {versionStatusLabel(version.status)}
                </option>
              ))}
            </select>
          </div>

          {diffIsPending && <LoadingState label="Comparando las versiones…" />}
          {diffIsError && (
            <ErrorState
              title="No se pudo comparar las versiones"
              message="El servidor no devolvió la comparación de estas dos versiones."
              onRetry={onRetryDiff}
            />
          )}

          {!diffIsPending && !diffIsError && diff !== null && diff.sections.length === 0 && (
            <p className="hint">
              El servidor compara <strong>secciones</strong>, y estas dos versiones no tienen ninguna
              con la que comparar. Le pasa al material que entró como texto plano o pegado: el
              extractor de texto plano todavía no parte secciones (deuda registrada, DEBT-009). No
              significa que los textos sean iguales: significa que no hay nada que enfrentar sección
              a sección, y la comparación no se rellena con suposiciones.
            </p>
          )}

          {!diffIsPending && !diffIsError && diff !== null && diff.sections.length > 0 && (
            <>
              <p className="hint">
                Nuevas: {diff.added} · quitadas: {diff.removed} · con el texto cambiado:{' '}
                {diff.changed} · sin cambios: {diff.unchanged} (sobre {diff.sections.length}{' '}
                secciones comparadas, de la más antigua a la más nueva). Comparar no fusiona nada: no
                se ha modificado ninguna versión.
              </p>
              <table className="table">
                <caption className="table__caption">
                  Comparación de «{etiquetaDe(versions, fromVersionId)}» con «
                  {etiquetaDe(versions, toVersionId)}», sección a sección
                </caption>
                <thead>
                  <tr>
                    <th scope="col">Sección</th>
                    <th scope="col">Qué pasó</th>
                    <th scope="col">Antes</th>
                    <th scope="col">Después</th>
                  </tr>
                </thead>
                <tbody>
                  {diff.sections.map((seccion) => (
                    <tr key={seccion.label}>
                      <th scope="row">
                        <span className="sample__path">{seccion.label}</span>
                      </th>
                      <td>
                        <StatusBadge tone={sectionDiffTone(seccion.kind)}>
                          {sectionDiffLabel(seccion.kind)}
                        </StatusBadge>
                      </td>
                      <td className="hint">
                        {seccion.left ?? '— (no estaba)'}
                        {seccion.left_truncated && ' … recortado'}
                      </td>
                      <td className="hint">
                        {seccion.right ?? '— (no está)'}
                        {seccion.right_truncated && ' … recortado'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {diff.sections.some(
                (seccion) => seccion.left_truncated || seccion.right_truncated,
              ) && (
                <p className="hint">
                  Los textos largos se recortan al mostrarlos (el servidor recorta a 4.000 caracteres
                  por lado y lo marca con «recortado»): la comparación se hizo con el texto completo.
                </p>
              )}
            </>
          )}
        </>
      )}
    </>
  );
}

/** Nombre legible de una versión por su identificador, para el título de la comparación. */
function etiquetaDe(versions: Version[], versionId: string | null): string {
  const encontrada = versions.find((version) => version.id === versionId);
  return encontrada === undefined ? 'sin elegir' : versionName(encontrada);
}
