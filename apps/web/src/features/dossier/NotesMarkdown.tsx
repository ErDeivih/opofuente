import type { Block } from './notesMarkdownParser';
import { notesBlocks, tableCells } from './notesMarkdownParser';
import { renderInline } from '../../ui/inlineMarkdown';

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
