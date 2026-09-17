import type { DocumentSummary } from '../../api/library';
import { isCandidate, isRestricted, versionName } from '../../api/library';
import { StatusBadge } from '../../components/StatusBadge';
import {
  authorityLabel,
  documentTypeLabel,
  OWNER_SCOPE_LABEL,
  versionStatusLabel,
  versionStatusTone,
} from './labels';

export interface DocumentListProps {
  documents: DocumentSummary[];
  selectedId: string | null;
  onOpen: (documentId: string) => void;
}

/**
 * Listado de la biblioteca (07_UI-UX §6).
 *
 * Cada fila lleva el título, la versión activa con su estado y los dos avisos que no se pueden
 * esconder: que la versión activa es una **candidata** (una propuesta de cambio sin aceptar) y que
 * los **derechos están restringidos** (no se puede compartir). El estado viene del servidor: la
 * pantalla no lo deduce.
 */
export function DocumentList({ documents, selectedId, onOpen }: DocumentListProps) {
  if (documents.length === 0) {
    return (
      <p className="hint">
        No hay ningún documento que cumpla estos filtros. Los documentos se crean al promocionar
        material ya copiado: la biblioteca no inventa obras que no existen.
      </p>
    );
  }

  return (
    <table className="table">
      <caption className="table__caption">
        {documents.length} documentos en la biblioteca
      </caption>
      <thead>
        <tr>
          <th scope="col">Título</th>
          <th scope="col">Tipo</th>
          <th scope="col">Versión activa</th>
          <th scope="col">Ámbito y autoridad</th>
          <th scope="col">Recuentos</th>
          <th scope="col">Avisos</th>
          <th scope="col">Ficha</th>
        </tr>
      </thead>
      <tbody>
        {documents.map((document) => {
          const active = document.active_version ?? null;
          const candidata = active !== null && isCandidate(active);
          const restringida = active !== null && isRestricted(active);
          return (
            <tr key={document.id}>
              <th scope="row">{document.canonical_title}</th>
              <td>
                {documentTypeLabel(document.document_type)}{' '}
                <span className="hint sample__path">{document.document_type}</span>
              </td>
              <td>
                {active === null ? (
                  <span className="hint">sin versión activa</span>
                ) : (
                  <>
                    <span className="sample__path">{versionName(active)}</span>{' '}
                    <StatusBadge tone={versionStatusTone(active.status)}>
                      {versionStatusLabel(active.status)}
                    </StatusBadge>
                  </>
                )}
              </td>
              <td>
                {OWNER_SCOPE_LABEL[document.owner_scope]}{' '}
                <span className="hint">{authorityLabel(document.authority_tier)}</span>
                {document.is_public && (
                  <>
                    {' '}
                    <StatusBadge tone="warning">publicado</StatusBadge>
                  </>
                )}
              </td>
              <td>
                {document.version_count} versiones · {document.mapping_count} mapeos de programa
              </td>
              <td>
                {candidata && (
                  <p>
                    <StatusBadge tone="warning">propuesta de cambio, sin aceptar</StatusBadge>{' '}
                    <span className="hint">
                      la versión activa no está aceptada: no es la versión buena todavía.
                    </span>
                  </p>
                )}
                {restringida && (
                  <p>
                    <StatusBadge tone="blocked">derechos restringidos</StatusBadge>{' '}
                    <span className="hint">
                      {active !== null && active.rights === null
                        ? 'no constan derechos: se tratan como desconocidos y restringidos.'
                        : 'el servidor los marca restringidos: no se pueden compartir.'}
                    </span>
                  </p>
                )}
                {!candidata && !restringida && <span className="hint">—</span>}
              </td>
              <td>
                <button
                  className="button"
                  type="button"
                  aria-label={`Abrir la ficha: ${document.canonical_title}`}
                  onClick={() => {
                    onOpen(document.id);
                  }}
                >
                  Abrir la ficha
                </button>
                {document.id === selectedId && <span className="hint"> abierta ahora</span>}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
