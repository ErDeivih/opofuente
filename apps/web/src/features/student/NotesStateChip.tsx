import type { NotesState } from '../../api/studentStudy';

/**
 * La marca de la versión que el alumno va a leer.
 *
 * Es la frase que la decisión D2 aprobó —«Versión generada · en revisión»— y dice las dos cosas que
 * el alumno tiene que saber antes de fiarse del texto: **la escribió la máquina** y **nadie la ha
 * dado por buena todavía**. Va dentro de un contenedor `data-contenido` a propósito: es una frase
 * sobre el material (su procedencia), no un rótulo de la interfaz, y el detector de lenguaje interno
 * de las capturas busca justo lo contrario —la jerga de la trastienda en los menús y los botones—.
 *
 * Un tema en borrador dice «Borrador»: se lee igual, pero se sabe lo que es.
 */

export const MARCA_VERSION_GENERADA = 'Versión generada · en revisión';

export interface NotesStateChipProps {
  state: NotesState;
}

export function NotesStateChip({ state }: NotesStateChipProps) {
  if (state === 'published') {
    return (
      <span className="marca" data-contenido>
        {MARCA_VERSION_GENERADA}
      </span>
    );
  }
  if (state === 'draft') {
    return <span className="marca marca--borrador">Borrador</span>;
  }
  return <span className="marca marca--vacia">Sin apuntes</span>;
}
