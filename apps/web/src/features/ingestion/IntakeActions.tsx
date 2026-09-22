import { useState } from 'react';

import type { Batch } from '../../api/ingestion';
import { useIngestFiles, useIngestPaste, useIngestUrl } from '../../api/queries';
import { ErrorState } from '../../components/ErrorState';
import {
  ficherosDeSelector,
  ficherosSoltados,
  type FicheroParaSubir,
} from './carpetas';

export interface IntakeActionsProps {
  /** Cuando una entrada crea un lote, la bandeja lo selecciona para seguir su progreso. */
  onBatchCreated: (batch: Batch) => void;
}

function describeError(error: unknown): string {
  return error instanceof Error ? error.message : 'Error desconocido';
}

/**
 * Las tres formas de entrada de 04_INGESTION §2 que el usuario tiene delante: ficheros o **carpetas
 * enteras**, texto pegado y URL.
 *
 * Las tres **copian**: ninguna toca el material de origen. La URL pasa por la guarda de red del
 * servidor, así que una dirección interna se rechaza aquí con su motivo en lugar de descargarse.
 *
 * Sobre las carpetas: el navegador no entrega la ruta de una carpeta que se suelta, así que se
 * recorre **en el navegador** y se suben sus ficheros con su ruta relativa. Suelta una carpeta con
 * treinta ficheros y entran los treinta, no cero.
 */
export function IntakeActions({ onBatchCreated }: IntakeActionsProps) {
  const [pasteText, setPasteText] = useState('');
  const [pasteTitle, setPasteTitle] = useState('');
  const [url, setUrl] = useState('');
  const [revisando, setRevisando] = useState(false);
  const [aviso, setAviso] = useState<string | null>(null);

  const files = useIngestFiles();
  const paste = useIngestPaste();
  const remote = useIngestUrl();

  function enviar(seleccion: FicheroParaSubir[]): void {
    setAviso(null);
    if (seleccion.length === 0) {
      setAviso('No había ningún fichero que subir: revisa que la carpeta no esté vacía.');
      return;
    }
    files.mutate(seleccion, { onSuccess: onBatchCreated });
  }

  async function soltar(event: React.DragEvent<HTMLDivElement>): Promise<void> {
    event.preventDefault();
    setRevisando(true);
    try {
      const seleccion = await ficherosSoltados(event.dataTransfer);
      enviar(seleccion);
    } catch (error) {
      setAviso(describeError(error));
    } finally {
      setRevisando(false);
    }
  }

  return (
    <>
      <div className="intake">
        <h3>Ficheros o carpetas enteras</h3>
        <p className="hint">
          Suelta una carpeta y entran todos sus ficheros, conservando su ruta («Tema 3/apuntes.pdf»).
          Un ZIP se copia y se expande al extraer, con límites de tamaño y sin seguir rutas que salgan
          del paquete. Una baraja de Anki (`.apkg`) se lee como baraja.
        </p>
        <div
          className="intake__drop"
          onDragOver={(event) => {
            event.preventDefault();
          }}
          onDrop={(event) => {
            void soltar(event);
          }}
        >
          <label className="form__label" htmlFor="ficheros">
            Suelta aquí ficheros o carpetas
          </label>
          <input
            id="ficheros"
            className="form__input"
            type="file"
            multiple
            onChange={(event) => {
              enviar(ficherosDeSelector(event.target.files ?? []));
              event.target.value = '';
            }}
          />
          <label className="form__label" htmlFor="carpeta">
            O elige una carpeta
          </label>
          <input
            id="carpeta"
            className="form__input"
            type="file"
            multiple
            // Atributo no estándar pero soportado por los navegadores: convierte el selector en un
            // selector de carpetas y rellena `webkitRelativePath`, que es la ruta que se conserva.
            {...{ webkitdirectory: '' }}
            onChange={(event) => {
              enviar(ficherosDeSelector(event.target.files ?? []));
              event.target.value = '';
            }}
          />
        </div>
        {(files.isPending || revisando) && (
          <p className="hint">
            {revisando ? 'Leyendo lo que has soltado…' : 'Copiando los ficheros…'}
          </p>
        )}
        {aviso !== null && <p className="hint">{aviso}</p>}
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
