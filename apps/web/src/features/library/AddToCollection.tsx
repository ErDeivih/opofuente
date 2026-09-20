import { useState } from 'react';

import type { Collection } from '../../api/library';

export interface AddToCollectionProps {
  collections: Collection[];
  /** Sujeto que se va a añadir. Por defecto, la versión activa del documento abierto. */
  subjectId: string | null;
  subjectType: 'document_version';
  onAdd: (input: { collectionId: string; subjectType: 'document_version'; subjectId: string }) => void;
  pending: boolean;
  notice: string | null;
  error: string | null;
}

/**
 * Añadir el documento abierto a una colección, desde su ficha.
 *
 * Va en la ficha y no en la lista porque es ahí donde se sabe **qué** se está añadiendo: se añade la
 * versión activa, con su id, y no «el documento» a secas. Sin colecciones creadas no se enseña el
 * control: un selector vacío no es una acción, es un callejón.
 */
export function AddToCollection({
  collections,
  subjectId,
  subjectType,
  onAdd,
  pending,
  notice,
  error,
}: AddToCollectionProps) {
  const [elegida, setElegida] = useState('');

  if (collections.length === 0) {
    return (
      <p className="hint">
        Para agrupar este documento en una colección, crea una arriba (en «Colecciones») y vuelve a
        esta ficha.
      </p>
    );
  }

  return (
    <>
      <div className="form__row">
        <label className="form__label" htmlFor="anadir-coleccion">
          Añadir a una colección
        </label>
        <select
          id="anadir-coleccion"
          className="selector__select"
          value={elegida}
          onChange={(event) => {
            setElegida(event.target.value);
          }}
        >
          <option value="">elige una colección</option>
          {collections.map((coleccion) => (
            <option key={coleccion.id} value={coleccion.id}>
              {coleccion.name}
            </option>
          ))}
        </select>
        <button
          className="button"
          type="button"
          disabled={pending || elegida === '' || subjectId === null}
          onClick={() => {
            if (elegida === '' || subjectId === null) {
              return;
            }
            onAdd({ collectionId: elegida, subjectType, subjectId });
          }}
        >
          Añadir a la colección
        </button>
      </div>
      <p className="hint">
        Se añade la <strong>versión activa</strong> del documento. Añadir dos veces lo mismo no
        duplica el miembro, y el documento puede estar en varias colecciones a la vez.
      </p>
      {notice !== null && <p role="status">{notice}</p>}
      {error !== null && <p className="notice">{error}</p>}
    </>
  );
}
