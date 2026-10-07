import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

/**
 * Búsqueda global de la cabecera (07_UI-UX §2).
 *
 * No busca aquí: lleva a `/admin/buscar?q=…`, que es la pantalla que enseña los fragmentos con su
 * cita, sus filtros y la opción de preguntar sobre el material. La cabecera no abre un desplegable con
 * «lo más parecido»: no se enseña un resultado sin su procedencia, y para eso hace falta la sección.
 *
 * Vive en el **panel** (F1 del rediseño): buscar en el material recopilado es trabajo de
 * administración. La barra del alumno no la trae, y la dirección antigua `/buscar` sigue llegando a
 * esta pantalla por la redirección.
 *
 * El campo enseña lo escrito **mientras** se escribe y, en cuanto la dirección cambia (aquí o en la
 * propia pantalla de búsqueda), vuelve a lo que se está buscando: una sola verdad, la dirección.
 */
export function GlobalSearch() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const q = params.get('q') ?? '';
  const [borrador, setBorrador] = useState<{ texto: string; para: string } | null>(null);
  const texto = borrador !== null && borrador.para === q ? borrador.texto : q;

  function ir(): void {
    const termino = texto.trim();
    if (termino === '') {
      return;
    }
    void navigate(`/admin/buscar?q=${encodeURIComponent(termino)}`);
  }

  return (
    <form
      className="app__search"
      role="search"
      onSubmit={(event) => {
        event.preventDefault();
        ir();
      }}
    >
      <label className="form__label" htmlFor="busqueda-global">
        Buscar en el corpus
      </label>
      <input
        id="busqueda-global"
        className="app__search-input"
        type="search"
        value={texto}
        onChange={(event) => {
          setBorrador({ texto: event.target.value, para: q });
        }}
        onKeyDown={(event) => {
          // El formulario no lleva botón: la búsqueda se lanza con Intro y el resultado se ve en su
          // sección, que es donde están los filtros, las citas y la recuperación completa.
          if (event.key === 'Enter') {
            event.preventDefault();
            ir();
          }
        }}
      />
    </form>
  );
}
