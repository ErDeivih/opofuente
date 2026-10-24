import { useState } from 'react';

import type { ExportResult } from '../../api/reviews';

export interface ExportPanelProps {
  defaultTitle: string;
  busy: boolean;
  error: string | null;
  conflict: string | null;
  result: ExportResult | undefined;
  onExport: (input: {
    format: 'anki-csv' | 'markdown';
    title: string;
    includeRestricted: boolean;
  }) => void;
}

/** Descarga el fichero que el servidor ya ha escrito, sin volver a pedirlo. */
function download(result: ExportResult): void {
  const blob = new Blob([result.content], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const enlace = document.createElement('a');
  enlace.href = url;
  enlace.download = result.filename;
  enlace.click();
  URL.revokeObjectURL(url);
}

/**
 * Exportación (08_API-CONTRACT §11): Anki CSV y Markdown/Obsidian.
 *
 * Lo que la pantalla **no** hace: exportar sin decir qué se lleva. Antes de ofrecer la descarga se
 * enseñan los avisos del servidor (material con derechos restringidos, preguntas sin respuesta
 * conocida, celdas neutralizadas) y la procedencia; y el interruptor del material restringido está a
 * la vista, no escondido en un ajuste.
 */
export function ExportPanel({
  defaultTitle,
  busy,
  error,
  conflict,
  result,
  onExport,
}: ExportPanelProps) {
  const [titulo, setTitulo] = useState(defaultTitle);
  const [incluirRestringido, setIncluirRestringido] = useState(true);

  return (
    <section className="card" aria-labelledby="exportar">
      <h2 id="exportar">Exportar</h2>
      <p className="hint">
        El fichero se escribe en la carpeta de exportaciones del directorio de datos y lleva la
        procedencia de cada pregunta: conjunto, plantilla, origen, tema y las versiones de los
        documentos citados.
      </p>
      <div className="form__row">
        <label className="form__label" htmlFor="exportar-titulo">
          Título del fichero
        </label>
        <input
          id="exportar-titulo"
          className="selector__select"
          value={titulo}
          onChange={(event) => {
            setTitulo(event.target.value);
          }}
        />
        <label className="form__label" htmlFor="exportar-restringido">
          <input
            id="exportar-restringido"
            type="checkbox"
            checked={incluirRestringido}
            onChange={(event) => {
              setIncluirRestringido(event.target.checked);
            }}
          />{' '}
          Incluir material con derechos restringidos
        </label>
        <button
          className="button"
          type="button"
          aria-label="Anki CSV: exportar el banco para Anki"
          disabled={busy}
          onClick={() => {
            onExport({
              format: 'anki-csv',
              title: titulo,
              includeRestricted: incluirRestringido,
            });
          }}
        >
          Anki CSV
        </button>
        <button
          className="button"
          type="button"
          aria-label="Exportar el banco en Markdown"
          disabled={busy}
          onClick={() => {
            onExport({
              format: 'markdown',
              title: titulo,
              includeRestricted: incluirRestringido,
            });
          }}
        >
          Markdown (Obsidian)
        </button>
      </div>

      {conflict !== null && (
        <p className="hint" role="alert">
          {conflict}
        </p>
      )}
      {error !== null && (
        <p className="hint" role="alert">
          {error}
        </p>
      )}

      {result !== undefined && (
        <>
          <h3>Última exportación</h3>
          <dl className="facts">
            <dt>Fichero</dt>
            <dd>
              <span className="sample__path">{result.filename}</span>
            </dd>
            <dt>Preguntas</dt>
            <dd>{result.item_count}</dd>
            <dt>Tamaño</dt>
            <dd>{result.bytes} bytes</dd>
            <dt>Dónde está</dt>
            <dd>
              <span className="sample__path">{result.path}</span>
            </dd>
          </dl>
          {result.warnings.length > 0 && (
            <div className="notice">
              <h4>Antes de usarlo fuera de aquí</h4>
              <ul className="hint">
                {result.warnings.map((aviso) => (
                  <li key={aviso}>{aviso}</li>
                ))}
              </ul>
            </div>
          )}
          <button
            className="button"
            type="button"
            aria-label="Descargar el fichero exportado"
            onClick={() => {
              download(result);
            }}
          >
            Descargar
          </button>
        </>
      )}
    </section>
  );
}
