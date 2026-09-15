import { useState } from 'react';

import type { Batch } from '../../api/ingestion';
import { useIngestFiles, useIngestPaste, useIngestUrl } from '../../api/queries';
import { ErrorState } from '../../components/ErrorState';

export interface IntakeActionsProps {
  /** Cuando una entrada crea un lote, la bandeja lo selecciona para seguir su progreso. */
  onBatchCreated: (batch: Batch) => void;
}

function describeError(error: unknown): string {
  return error instanceof Error ? error.message : 'Error desconocido';
}

/**
 * Las tres formas de entrada de 04_INGESTION §2 que el usuario tiene delante: carpeta (en la
 * pantalla principal), ficheros sueltos, texto pegado y URL.
 *
 * Las tres **copian**: ninguna toca el material de origen. La URL pasa por la guarda de red del
 * servidor, así que una dirección interna se rechaza aquí con su motivo en lugar de descargarse.
 */
export function IntakeActions({ onBatchCreated }: IntakeActionsProps) {
  const [pasteText, setPasteText] = useState('');
  const [pasteTitle, setPasteTitle] = useState('');
  const [url, setUrl] = useState('');

  const files = useIngestFiles();
  const paste = useIngestPaste();
  const remote = useIngestUrl();

  return (
    <>
      <div className="intake">
        <h3>Ficheros sueltos</h3>
        <p className="hint">
          Se copian al almacén por contenido. Un ZIP se copia y se expande al extraer, con límites de
          tamaño y sin seguir rutas que salgan del paquete.
        </p>
        <div
          className="intake__drop"
          onDragOver={(event) => {
            event.preventDefault();
          }}
          onDrop={(event) => {
            event.preventDefault();
            const dropped = Array.from(event.dataTransfer.files);
            if (dropped.length > 0) {
              files.mutate(dropped, { onSuccess: onBatchCreated });
            }
          }}
        >
          <label className="form__label" htmlFor="ficheros">
            Suelta aquí o elige ficheros
          </label>
          <input
            id="ficheros"
            className="form__input"
            type="file"
            multiple
            onChange={(event) => {
              const chosen = Array.from(event.target.files ?? []);
              if (chosen.length > 0) {
                files.mutate(chosen, { onSuccess: onBatchCreated });
              }
            }}
          />
        </div>
        {files.isPending && <p className="hint">Copiando los ficheros…</p>}
        {files.isError && (
          <ErrorState
            title="No se pudieron copiar los ficheros"
            message={describeError(files.error)}
          />
        )}
      </div>

      <div className="intake">
        <h3>Texto pegado</h3>
        <p className="hint">
          Se guarda como material propio con origen «pegado». No sustituye al documento original: es
          texto, y así se declara.
        </p>
        <label className="form__label" htmlFor="pegado">
          Texto
        </label>
        <textarea
          id="pegado"
          className="form__input form__input--area"
          rows={4}
          value={pasteText}
          onChange={(event) => {
            setPasteText(event.target.value);
          }}
        />
        <div className="form__row">
          <label className="form__label" htmlFor="pegado-titulo">
            Título (opcional)
          </label>
          <input
            id="pegado-titulo"
            className="form__input"
            type="text"
            value={pasteTitle}
            onChange={(event) => {
              setPasteTitle(event.target.value);
            }}
          />
          <button
            className="button"
            type="button"
            disabled={paste.isPending || pasteText.trim().length === 0}
            onClick={() => {
              paste.mutate(
                { text: pasteText, title: pasteTitle },
                {
                  onSuccess: (batch) => {
                    setPasteText('');
                    setPasteTitle('');
                    onBatchCreated(batch);
                  },
                },
              );
            }}
          >
            Guardar el texto
          </button>
        </div>
        {paste.isError && (
          <ErrorState title="No se pudo guardar el texto" message={describeError(paste.error)} />
        )}
      </div>

      <div className="intake">
        <h3>Desde una URL</h3>
        <p className="hint">
          Solo <code>http</code> y <code>https</code>. El servidor comprueba cada redirección y
          bloquea direcciones internas; no se eluden controles de acceso ni muros de pago.
        </p>
        <div className="form__row">
          <label className="form__label" htmlFor="url">
            Dirección
          </label>
          <input
            id="url"
            className="form__input"
            type="url"
            value={url}
            placeholder="https://www.boe.es/…"
            onChange={(event) => {
              setUrl(event.target.value);
            }}
          />
          <button
            className="button"
            type="button"
            disabled={remote.isPending || url.trim().length === 0}
            onClick={() => {
              remote.mutate(url, {
                onSuccess: (batch) => {
                  setUrl('');
                  onBatchCreated(batch);
                },
              });
            }}
          >
            Descargar y copiar
          </button>
        </div>
        {remote.isPending && <p className="hint">Descargando…</p>}
        {remote.isError && (
          <ErrorState title="No se pudo descargar" message={describeError(remote.error)} />
        )}
      </div>
    </>
  );
}
