import { useState } from 'react';

import type { Evidence, Section, Version } from '../../api/library';
import { versionName, versionOriginalUrl } from '../../api/library';
import { ErrorState } from '../../components/ErrorState';
import { CopyCitationButton } from './CopyCitationButton';
import { evidencePlace } from './citation';
import { pageLabel } from './labels';

export interface ReaderTabProps {
  documentTitle: string;
  version: Version | null;
  sections: Section[];
  evidence: Evidence[];
  isPending: boolean;
  isError: boolean;
  onRetry: () => void;
  /** Crear un resumen extractivo de esta sección (S11). Sin esto, el lector no lo ofrece. */
  onSummarize?: ((sectionId: string) => void) | undefined;
  summarizePending?: boolean | undefined;
  summarizeNotice?: string | null | undefined;
}

/** Evidencia de una sección: por su identificador y, si no lo trae, por su página. */
function evidenceOfSection(section: Section, evidence: Evidence[]): Evidence[] {
  const porId = evidence.filter((item) => item.section_id === section.id);
  if (porId.length > 0) {
    return porId;
  }
  const desde = section.page_start;
  if (desde === null || desde === undefined) {
    return [];
  }
  const hasta = section.page_end ?? desde;
  return evidence.filter((item) => {
    if (item.page === null || item.page === undefined) {
      return false;
    }
    return item.page >= desde && item.page <= hasta;
  });
}

/**
 * Lector de la versión (07_UI-UX §6): el texto extraído por secciones, sincronizado con la página
 * del original.
 *
 * Lo que se lee es el texto **extraído**, no el original: por eso la página va siempre al lado, y
 * cuando la versión no tiene URL oficial se dice que no se puede abrir en su sitio en lugar de
 * ofrecer un enlace que no lleva a ninguna parte. Cada fragmento se puede citar.
 *
 * El **fichero original** sí está: es el que se copió al almacén y lo sirve la API
 * (`GET /document-versions/{id}/original`), así que se ofrece abrirlo tal cual, sin depender de que la
 * fuente tenga una URL pública.
 */
export function ReaderTab({
  documentTitle,
  version,
  sections,
  evidence,
  isPending,
  isError,
  onRetry,
  onSummarize,
  summarizePending = false,
  summarizeNotice = null,
}: ReaderTabProps) {
  const [elegida, setElegida] = useState<string | null>(null);
  // La sección que se lee es la elegida y, mientras nadie elija, la primera del documento: no hace
  // falta sincronizar estado con la carga, se deriva de lo que ya está.
  const seccion = sections.find((item) => item.id === elegida) ?? sections[0] ?? null;
  const fragmentos = seccion === null ? [] : evidenceOfSection(seccion, evidence);
  const url = version?.official_url ?? null;

  if (version === null) {
    return (
      <p className="hint">
        Este documento no tiene ninguna versión: no hay texto que leer. La versión se crea al
        promocionar el material del que sale el documento.
      </p>
    );
  }

  if (isError) {
    return (
      <ErrorState
        title="No se pudo leer la versión"
        message="El texto extraído o la estructura de esta versión no están disponibles."
        onRetry={onRetry}
      />
    );
  }

  return (
    <>
      <p className="hint">
        Se lee el texto extraído de la versión «{versionName(version)}» y, al lado, la página del
        original de la que sale. El original no se modifica ni se muestra aquí.
        {url === null && ' Esta versión no tiene URL oficial registrada.'}
      </p>

      {isPending && (
        <p className="loading" role="status">
          Cargando el texto y la estructura…
        </p>
      )}

      {!isPending && sections.length === 0 && (
        <p className="hint">
          Esta versión no tiene estructura extraída: no se puede citar por secciones. Lo que sí hay
          es la evidencia citable, si la extracción la dejó.
        </p>
      )}

      {seccion !== null && (
        <div className="reader-split">
          <div>
            <h3>Secciones</h3>
            <ul className="sample">
              {sections.map((item) => (
                <li key={item.id}>
                  <button
                    className="button button--link"
                    type="button"
                    aria-pressed={item.id === seccion.id}
                    onClick={() => {
                      setElegida(item.id);
                    }}
                  >
                    {item.title ?? item.label ?? `sección ${item.ordinal}`}
                  </button>{' '}
                  <span className="hint">{pageLabel(item.page_start, item.page_end)}</span>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3>{seccion.title ?? seccion.label ?? `sección ${seccion.ordinal}`}</h3>
            <p className="hint">
              {pageLabel(seccion.page_start, seccion.page_end)} del original
              {url !== null && seccion.page_start !== null && seccion.page_start !== undefined && (
                <>
                  {' · '}
                  <a
                    href={`${url}#page=${seccion.page_start}`}
                    target="_blank"
                    rel="noreferrer noopener"
                  >
                    abrir la página {seccion.page_start} en el original
                  </a>
                </>
              )}
              {url === null && ' · sin URL oficial: la página del original no se puede abrir'}
              {version !== null && (
                <>
                  {' · '}
                  <a href={versionOriginalUrl(version.id)} target="_blank" rel="noreferrer noopener">
                    abrir el fichero original que se copió
                  </a>
                </>
              )}
            </p>

            {onSummarize !== undefined && fragmentos.length > 0 && (
              <div className="form__row">
                <button
                  className="button"
                  type="button"
                  disabled={summarizePending}
                  aria-label={`Resumir la sección ${seccion.title ?? seccion.label ?? String(seccion.ordinal)}`}
                  onClick={() => {
                    onSummarize(seccion.id);
                  }}
                >
                  Crear un resumen de esta sección
                </button>
                <span className="hint">
                  Extractivo: junta el texto de los fragmentos con su cita, sin modelo. El resumen
                  dependerá de esta sección y quedará pendiente de revisar si cambia (S11).
                </span>
              </div>
            )}
            {summarizeNotice !== null && (
              <p className="hint" role="status">
                {summarizeNotice}
              </p>
            )}

            {fragmentos.length === 0 ? (
              <p className="hint">
                No hay evidencia citable guardada para esta sección: se ve la estructura, no el
                texto. No se rellena con texto de otra parte.
              </p>
            ) : (
              fragmentos.map((fragmento) => {
                const lugar = evidencePlace(
                  fragmento.citation_label,
                  fragmento.page,
                  fragmento.ordinal,
                );
                return (
                  <article key={fragmento.id}>
                    <p className="reader">{fragmento.text}</p>
                    <p className="hint">
                      {lugar}
                      {fragmento.quality !== null && fragmento.quality !== undefined && (
                        <> · calidad {fragmento.quality}</>
                      )}
                      {' · '}índice: {fragmento.index_status}
                    </p>
                    <CopyCitationButton
                      title={documentTitle}
                      version={version}
                      place={lugar}
                      label={`${documentTitle}, ${lugar}`}
                    />
                  </article>
                );
              })
            )}
          </div>
        </div>
      )}

      {evidence.length > 0 && (
        <>
          <h3>Índice de evidencia citable de la versión</h3>
          <ul className="evidence">
            {evidence.map((fragmento) => {
              const lugar = evidencePlace(
                fragmento.citation_label,
                fragmento.page,
                fragmento.ordinal,
              );
              return (
                <li key={fragmento.id}>
                  <span className="sample__path">{lugar}</span>{' '}
                  {/* En el índice el nombre lleva el ordinal: la misma evidencia ya tiene su
                      botón en la sección, y dos botones con el mismo nombre accesible no se
                      distinguen. */}
                  <CopyCitationButton
                    title={documentTitle}
                    version={version}
                    place={lugar}
                    label={`${documentTitle}, ${lugar} (evidencia ${fragmento.ordinal})`}
                  />
                </li>
              );
            })}
          </ul>
        </>
      )}

      {!isPending && evidence.length === 0 && (
        <p className="hint">
          Esta versión no tiene evidencia citable: sin fragmentos no hay nada que citar.
        </p>
      )}
    </>
  );
}
