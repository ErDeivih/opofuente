import { notesBlocks, tableCells } from '../dossier/notesMarkdownParser';
import { renderInline } from '../../ui/inlineMarkdown';

/**
 * El texto de un apartado de los apuntes, **tal como se lee** (pantalla del alumno, F13).
 *
 * Es el mismo lector que usa el panel (`notesMarkdownParser`) y el mismo texto en línea, pero el
 * dibujo es el del diseño de lectura: headings de sección, listas, tablas con su cabecera y, en el
 * centro, párrafos en Source Serif 4 con su medida de 68 caracteres.
 *
 * Dos decisiones que se ven en el código:
 *
 * 1. **la primera fila de una tabla es la cabecera** y todas las celdas del cuerpo son `td`: las
 *    tablas de los apuntes son datos (puerto, servicio, familia), no una comparación con fila de
 *    encabezado, y marcar la primera columna como `th scope="row"` cambiaría lo que lee un lector de
 *    pantalla;
 * 2. **no se interpretan enlaces ni HTML**: los apuntes son texto generado y lo generado no se
 *    ejecuta. Lo que se ve es lo que hay.
 */
export function NotesBody({ markdown }: { markdown: string }) {
  return (
    <div className="apuntes__prosa">
      {notesBlocks(markdown).map((block, indice) => {
        const clave = `${block.kind}-${String(indice)}`;
        if (block.kind === 'heading') {
          return (
            <h3 className="apuntes__epigrafe" key={clave}>
              {renderInline(block.lines[0] ?? '')}
            </h3>
          );
        }
        if (block.kind === 'list') {
          return (
            <ul className="apuntes__lista" key={clave}>
              {block.lines.map((linea) => (
                <li key={linea}>{renderInline(linea)}</li>
              ))}
            </ul>
          );
        }
        if (block.kind === 'quote') {
          return (
            <blockquote className="apuntes__cita" key={clave}>
              {renderInline(block.lines.join(' '))}
            </blockquote>
          );
        }
        if (block.kind === 'table') {
          const [cabecera, ...filas] = block.lines.map(tableCells);
          if (cabecera === undefined) {
            return null;
          }
          // La tabla no vive dentro de un contenedor que se desplaza a propósito: en el móvil tiene
          // que **caber**, y para eso sus celdas parten las palabras largas (ver `.apuntes__tabla`).
          // Un `overflow-x: auto` aquí sería una región que se desplaza y que nadie puede recorrer
          // con el teclado (axe lo marca, `scrollable-region-focusable`), y arreglarlo con
          // `tabindex` en un elemento no interactivo es justo lo que eslint prohíbe. La tabla cabe.
          return (
            <div className="apuntes__tabla-marco" key={clave}>
              <table className="apuntes__tabla">
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
                      {fila.map((celda, posicion) => (
                        <td key={`${String(posicion)}-${celda}`}>{renderInline(celda)}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          );
        }
        return <p key={clave}>{renderInline(block.lines.join(' '))}</p>;
      })}
    </div>
  );
}
