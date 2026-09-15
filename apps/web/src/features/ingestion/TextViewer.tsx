import { useState } from 'react';

import type { Representation } from '../../api/ingestion';
import { useRepresentationText } from '../../api/queries';
import { ErrorState } from '../../components/ErrorState';
import { LoadingState } from '../../components/LoadingState';
import { StatusBadge } from '../../components/StatusBadge';
import type { StatusTone } from '../../components/StatusBadge';

/** Cuánto texto se lee de una vez. El lector pide más solo si el usuario lo pide. */
const PAGE_CHARS = 20_000;

const QUALITY_TONE: Record<string, StatusTone> = {
  good: 'ok',
  usable_with_warnings: 'warning',
  ocr_unreviewed: 'warning',
  poor: 'blocked',
  failed: 'blocked',
};

const KIND_LABEL: Record<string, string> = {
  native_text: 'texto del documento',
  ocr: 'texto reconocido (OCR)',
  plain_text: 'texto pegado',
  html_text: 'texto de la página',
  csv_preview: 'vista previa de tabla',
  json_preview: 'vista previa de estructura',
  image_metadata: 'metadatos de la imagen',
};

/**
 * Texto extraído de las entradas de un lote (04_INGESTION §5).
 *
 * Cada representación dice de dónde sale su texto, con qué calidad y con qué avisos, y el lector
 * **mantiene los avisos a la vista**: quien lee un texto sin OCR o con calidad pobre tiene que
 * saberlo ahí mismo, no en otra pantalla.
 */
export function TextViewer({ representations }: { representations: Representation[] }) {
  const [selected, setSelected] = useState<string | null>(null);
  const [limit, setLimit] = useState(PAGE_CHARS);
  const active = selected ?? representations[0]?.id ?? null;
  const text = useRepresentationText(active, 0, limit);

  if (representations.length === 0) {
    return (
      <p className="hint">
        Todavía no hay texto extraído en este lote. El trabajo de extracción se ejecuta al terminar
        la copia.
      </p>
    );
  }

  const current = representations.find((item) => item.id === active);
  const warnings = current?.warnings ?? [];

  return (
    <>
      <ul className="sample">
        {representations.map((representation) => {
          const sourcePaths = representation.source_paths ?? [];
          return (
            <li key={representation.id}>
              <button
                className="button button--link"
                type="button"
                aria-pressed={representation.id === active}
                onClick={() => {
                  setSelected(representation.id);
                  setLimit(PAGE_CHARS);
                }}
              >
                {KIND_LABEL[representation.kind] ?? representation.kind}
              </button>
              <StatusBadge tone={QUALITY_TONE[representation.quality] ?? 'info'}>
                {representation.quality}
              </StatusBadge>
              <span className="hint">
                {representation.char_count} caracteres
                {representation.page_count !== null && representation.page_count !== undefined
                  ? ` · ${representation.page_count} páginas`
                  : ''}
                {` · ${representation.extractor}`}
              </span>
              {representation.ocr_candidate && (
                <StatusBadge tone="warning">OCR pendiente</StatusBadge>
              )}
              {/* De qué fichero es el texto. Un mismo contenido copiado dos veces comparte
                  representación: se listan sus dos rutas en lugar de repetir el texto. */}
              {sourcePaths.length > 0 && (
                <span className="hint sample__path">{sourcePaths.join(' · ')}</span>
              )}
            </li>
          );
        })}
      </ul>

      {current !== undefined && (
        <>
          {warnings.length > 0 && (
            <ul className="issues">
              {warnings.map((warning) => (
                <li key={warning} className="issues__item">
                  <StatusBadge tone="warning">{warning}</StatusBadge>
                </li>
              ))}
            </ul>
          )}
          {text.isPending && <LoadingState label="Leyendo el texto…" />}
          {text.isError && (
            <ErrorState
              title="No se pudo leer el texto"
              message={text.error instanceof Error ? text.error.message : 'Error desconocido'}
            />
          )}
          {text.isSuccess && (
            <>
              <pre className="reader" aria-label="Texto extraído">
                {text.data.text}
              </pre>
              {text.data.truncated && (
                <div className="form__row">
                  <span className="hint">
                    Mostrando {text.data.limit} de {text.data.total_chars} caracteres.
                  </span>
                  <button
                    className="button"
                    type="button"
                    onClick={() => {
                      setLimit((value) => value + PAGE_CHARS);
                    }}
                  >
                    Seguir leyendo
                  </button>
                </div>
              )}
            </>
          )}
        </>
      )}
    </>
  );
}
