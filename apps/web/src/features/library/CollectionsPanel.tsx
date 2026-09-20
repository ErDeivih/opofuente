import { useState } from 'react';

import type { Collection } from '../../api/library';
import { SUBJECT_TYPE_LABEL } from '../../api/library';
import { StatusBadge } from '../../components/StatusBadge';

export interface CollectionsPanelProps {
  collections: Collection[];
  /** Colección por la que se está filtrando la lista, o `null` para no filtrar. */
  selectedId: string | null;
  onSelect: (collectionId: string | null) => void;
  onCreate: (input: { name: string; description: string | null }) => void;
  createPending: boolean;
  createError: string | null;
}

/**
 * Colecciones de la biblioteca (07_UI-UX §6: «filtros por … y colección»; 03_DATA-MODEL §«colección»).
 *
 * Una colección agrupa **sujetos** —una versión, un fichero, una representación, una sección o una
 * cita— sin duplicar bytes. Aquí se ven, se crean y sirven de filtro; añadir un documento a una
 * colección se hace desde la ficha del documento, que es donde se sabe qué se está mirando.
 *
 * El filtro lo aplica el servidor: la pantalla manda `collection_id` y no descarta nada por su cuenta.
 */
export function CollectionsPanel({
  collections,
  selectedId,
  onSelect,
  onCreate,
  createPending,
  createError,
}: CollectionsPanelProps) {
  const [nombre, setNombre] = useState('');
  const [descripcion, setDescripcion] = useState('');

  return (
    <>
      <p className="hint">
        Una colección agrupa material sin duplicarlo: el mismo documento puede estar en varias. El
        filtro se aplica en el servidor, así que lo que se ve son los documentos de la colección y no
        los que han quedado fuera de la página.
      </p>

      {collections.length === 0 ? (
        <p className="hint">Todavía no hay colecciones. Crea una para agrupar material.</p>
      ) : (
        <ul className="tag-list">
          <li>
            <button
              className={selectedId === null ? 'button button--active' : 'button'}
              type="button"
              aria-pressed={selectedId === null}
              onClick={() => {
                onSelect(null);
              }}
            >
              Todos los documentos
            </button>
          </li>
          {collections.map((coleccion) => (
            <li key={coleccion.id}>
              <button
                className={coleccion.id === selectedId ? 'button button--active' : 'button'}
                type="button"
                aria-pressed={coleccion.id === selectedId}
                onClick={() => {
                  onSelect(coleccion.id === selectedId ? null : coleccion.id);
                }}
              >
                {coleccion.name}{' '}
                <StatusBadge tone="info">
                  {coleccion.item_count === 1 ? '1 miembro' : `${String(coleccion.item_count)} miembros`}
                </StatusBadge>
              </button>
              {coleccion.description !== null && coleccion.description !== undefined && (
                <p className="hint">{coleccion.description}</p>
              )}
            </li>
          ))}
        </ul>
      )}

      <div className="form__row">
        <label className="form__label" htmlFor="coleccion-nombre">
          Nombre de la colección
        </label>
        <input
          id="coleccion-nombre"
          className="selector__select"
          value={nombre}
          onChange={(event) => {
            setNombre(event.target.value);
          }}
        />
        <label className="form__label" htmlFor="coleccion-descripcion">
          Descripción (opcional)
        </label>
        <input
          id="coleccion-descripcion"
          className="selector__select"
          value={descripcion}
          onChange={(event) => {
            setDescripcion(event.target.value);
          }}
        />
        <button
          className="button"
          type="button"
          disabled={createPending || nombre.trim() === ''}
          onClick={() => {
            onCreate({
              name: nombre.trim(),
              description: descripcion.trim() === '' ? null : descripcion.trim(),
            });
            setNombre('');
            setDescripcion('');
          }}
        >
          Crear la colección
        </button>
      </div>
      {createError !== null && <p className="notice">{createError}</p>}

      {selectedId !== null && (
        <p className="hint">
          Filtrando por una colección. Se aplica a la lista de documentos de abajo; los miembros
          pueden ser {Object.values(SUBJECT_TYPE_LABEL).join(', ')}.
        </p>
      )}
    </>
  );
}
