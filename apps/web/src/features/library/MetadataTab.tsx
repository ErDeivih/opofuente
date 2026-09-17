import type { DocumentSummary, Version } from '../../api/library';
import { isRestricted, versionName } from '../../api/library';
import { StatusBadge } from '../../components/StatusBadge';
import {
  authorityLabel,
  documentTypeLabel,
  OWNER_SCOPE_LABEL,
  rightsReviewLabel,
  versionStatusLabel,
  versionStatusTone,
} from './labels';

export interface MetadataTabProps {
  document: DocumentSummary;
  version: Version | null;
}

function texto(value: string | null | undefined): string {
  return value === null || value === undefined || value === '' ? 'no consta' : value;
}

/**
 * Metadatos y procedencia (07_UI-UX §6): de dónde sale el documento, qué autoridad tiene, de quién
 * es y con qué derechos se puede usar.
 *
 * Los derechos se muestran **completos**, incluidos sus avisos: la licencia, la atribución que hay
 * que conservar y si se puede compartir. Cuando no constan, se dice que no constan y se recuerda
 * que lo desconocido se trata como restringido; no se presenta como reutilizable lo que nadie ha
 * revisado (09_SECURITY §8).
 */
export function MetadataTab({ document, version }: MetadataTabProps) {
  const rights = version?.rights ?? null;
  const restringida = version !== null && isRestricted(version);

  return (
    <>
      <h3>Procedencia</h3>
      <dl className="facts">
        <dt>Título lógico</dt>
        <dd>{document.canonical_title}</dd>
        <dt>Identificador canónico</dt>
        <dd>{texto(document.canonical_identifier)}</dd>
        <dt>Tipo documental</dt>
        <dd>
          {documentTypeLabel(document.document_type)}{' '}
          <span className="hint sample__path">{document.document_type}</span>
        </dd>
        <dt>Ámbito</dt>
        <dd>
          {OWNER_SCOPE_LABEL[document.owner_scope]}{' '}
          <span className="hint">
            {document.is_public ? 'marcado como público' : 'no es público'}
          </span>
        </dd>
        <dt>Autoridad</dt>
        <dd>
          {authorityLabel(document.authority_tier)}{' '}
          <span className="hint">
            el nivel lo fija el servidor: aquí solo se muestra, no se otorga
          </span>
        </dd>
        <dt>Creado</dt>
        <dd>{texto(document.created_at)}</dd>
        <dt>Versiones</dt>
        <dd>
          {document.version_count} · {document.mapping_count} mapeos de programa
        </dd>
      </dl>

      {version === null ? (
        <p className="hint">Este documento no tiene ninguna versión promocionada todavía.</p>
      ) : (
        <>
          <h3>Versión consultada: {versionName(version)}</h3>
          <dl className="facts">
            <dt>Estado</dt>
            <dd>
              <StatusBadge tone={versionStatusTone(version.status)}>
                {versionStatusLabel(version.status)}
              </StatusBadge>
              {!version.is_accepted && (
                <span className="hint"> no es la versión aceptada todavía</span>
              )}
            </dd>
            <dt>Artefacto de origen</dt>
            <dd className="sample__path">{version.artifact_id}</dd>
            <dt>Representación (texto extraído)</dt>
            <dd className="sample__path">{texto(version.representation_id)}</dd>
            <dt>Huella de contenido</dt>
            <dd className="sample__path">{texto(version.content_hash)}</dd>
            <dt>Idioma</dt>
            <dd>{texto(version.language)}</dd>
            <dt>Publicada</dt>
            <dd>{texto(version.published_at)}</dd>
            <dt>Recuperada</dt>
            <dd>{texto(version.retrieved_at)}</dd>
            <dt>Vigencia</dt>
            <dd>
              desde {texto(version.valid_from)}
              {version.valid_to !== null && version.valid_to !== undefined
                ? ` hasta ${version.valid_to}`
                : ' sin fecha de fin'}
            </dd>
            <dt>URL oficial</dt>
            <dd>
              {version.official_url === null || version.official_url === undefined ? (
                <span className="hint">
                  no consta: la página original no se puede abrir desde la cita
                </span>
              ) : (
                <a href={version.official_url} target="_blank" rel="noreferrer noopener">
                  {version.official_url}
                </a>
              )}
            </dd>
            <dt>Aprobada</dt>
            <dd>
              {texto(version.approved_at)} {version.approved_by === null ? '' : version.approved_by}
            </dd>
            <dt>Sustituye a</dt>
            <dd className="sample__path">{texto(version.supersedes_id)}</dd>
          </dl>

          <h3>Derechos</h3>
          {restringida && (
            <p>
              <StatusBadge tone="blocked">derechos restringidos: no se puede compartir</StatusBadge>
            </p>
          )}
          <dl className="facts">
            <dt>Código de derechos</dt>
            <dd>{texto(rights?.code)}</dd>
            <dt>Estado de revisión</dt>
            <dd>
              {rights === null ? (
                <span className="hint">
                  no consta ninguna revisión de derechos: se tratan como desconocidos y restringidos
                </span>
              ) : (
                rightsReviewLabel(rights.review_status)
              )}
            </dd>
            <dt>Licencia</dt>
            <dd>{texto(rights?.license_name)}</dd>
            <dt>URL de la licencia</dt>
            <dd>{texto(rights?.license_url)}</dd>
            <dt>Atribución exigida</dt>
            <dd>{texto(rights?.attribution)}</dd>
            <dt>Reutilización comercial</dt>
            <dd>{rights?.commercial_reuse === true ? 'sí' : 'no'}</dd>
            <dt>Compartir</dt>
            <dd>{rights?.sharing === true ? 'sí' : 'no'}</dd>
            <dt>Notas</dt>
            <dd>{texto(rights?.notes)}</dd>
          </dl>
          <p className="hint">
            Los derechos los decide el servidor y aquí se muestran tal cual: la interfaz no concede
            permisos ni convierte un documento en público. Sin revisión explícita, un documento se
            trata como desconocido y restringido.
          </p>
        </>
      )}
    </>
  );
}
