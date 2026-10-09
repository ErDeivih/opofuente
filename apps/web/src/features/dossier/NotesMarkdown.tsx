import type { ReactNode } from 'react';

import type { Block } from './notesMarkdownParser';
import { notesBlocks, tableCells } from './notesMarkdownParser';

/**
 * El texto de un párrafo con su énfasis y su código, sin interpretar nada más.
 *
 * Se resuelve con expresiones regulares y no con un analizador porque el vocabulario es minúsculo
 * (`**negrita**`, `*cursiva*`, `` `código` ``) y un analizador de verdad aquí sería más código que el
 * problema. Lo que no encaje en esos tres sale tal cual.
 */
function renderInline(texto: string): ReactNode[] {
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

/** Un bloque de apuntes dibujado. */
function BlockView({ block }: { block: Block }) {
  if (block.kind === 'heading') {
    return <h4 className="notes__heading">{renderInline(block.lines[0] ?? '')}</h4>;
  }
  if (block.kind === 'list') {
    return (
      <ul className="notes__list">
        {block.lines.map((linea) => (
          <li key={linea}>{renderInline(linea)}</li>
        ))}
      </ul>
    );
  }
  if (block.kind === 'quote') {
    return <blockquote className="reader">{renderInline(block.lines.join(' '))}</blockquote>;
  }
  if (block.kind === 'table') {
    const [cabecera, ...filas] = block.lines.map(tableCells);
    if (cabecera === undefined) {
      return null;
    }
    return (
      <table className="notes__table">
        <thead>
          <tr>
            {cabecera.map((celda) => (
              <th key={celda} scope="col">
                {renderInline(celda)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {filas.map((fila) => (
            <tr key={fila.join('|')}>
              {fila.map((celda, indice) =>
                indice === 0 ? (
                  <th key={`${String(indice)}-${celda}`} scope="row">
                    {renderInline(celda)}
                  </th>
                ) : (
                  <td key={`${String(indice)}-${celda}`}>{renderInline(celda)}</td>
                ),
              )}
            </tr>
          ))}
        </tbody>
      </table>
    );
  }
  return <p>{renderInline(block.lines.join(' '))}</p>;
}

/** El texto de un apartado de los apuntes, tal como se lee. */
export function NotesMarkdown({ markdown }: { markdown: string }) {
  return (
    <>
      {notesBlocks(markdown).map((block, indice) => (
        <BlockView key={`${block.kind}-${String(indice)}`} block={block} />
      ))}
    </>
  );
}
