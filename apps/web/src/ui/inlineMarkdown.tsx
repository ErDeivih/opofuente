import type { ReactNode } from 'react';

/**
 * El texto de un párrafo con su énfasis y su código, sin interpretar nada más.
 *
 * Se resuelve con expresiones regulares y no con un analizador porque el vocabulario es minúsculo
 * (`**negrita**`, `*cursiva*`, `` `código` ``) y un analizador de verdad aquí sería más código que el
 * problema. Lo que no encaje en esos tres sale tal cual.
 *
 * Vive en `ui/` desde F13 y no dentro de una pantalla porque lo usan dos: los apuntes del dueño (la
 * ficha del tema del panel) y la pantalla de lectura del alumno. Dos copias del mismo renderizador
 * acabarían pintando distinto el mismo texto.
 */
export function renderInline(texto: string): ReactNode[] {
  const piezas: ReactNode[] = [];
  const patron = /(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)/g;
  let ultimo = 0;
  let clave = 0;
  for (const encontrado of texto.matchAll(patron)) {
    const indice = encontrado.index ?? 0;
    if (indice > ultimo) {
      piezas.push(texto.slice(ultimo, indice));
    }
    const trozo = encontrado[0];
    clave += 1;
    if (trozo.startsWith('**')) {
      piezas.push(<strong key={`f${String(clave)}`}>{trozo.slice(2, -2)}</strong>);
    } else if (trozo.startsWith('`')) {
      piezas.push(<code key={`f${String(clave)}`}>{trozo.slice(1, -1)}</code>);
    } else {
      piezas.push(<em key={`f${String(clave)}`}>{trozo.slice(1, -1)}</em>);
    }
    ultimo = indice + trozo.length;
  }
  if (ultimo < texto.length) {
    piezas.push(texto.slice(ultimo));
  }
  return piezas;
}
