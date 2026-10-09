/**
 * El markdown de los apuntes, partido en bloques y sin adornos.
 *
 * Por qué existe este lector y por qué es tan corto: los apuntes los escribe un modelo en markdown y
 * lo que hay que poder leer son sus títulos, sus listas y, sobre todo, sus **tablas** (que es donde
 * acaban las comparaciones que se confunden). Meter una biblioteca de markdown entera para esto sería
 * una dependencia nueva y una superficie nueva; no meter nada dejaría las tablas como tuberías.
 *
 * Aquí **no hay JSX**: son funciones puras y se prueban sin dibujar nada. Lo que dibuja vive en
 * `NotesMarkdown.tsx`.
 *
 * Lo que **no** se interpreta, a propósito: ni enlaces, ni imágenes, ni HTML. Un texto que traiga
 * `<...>` sale como texto: los apuntes son contenido generado y lo generado no se ejecuta. Las marcas
 * `<!-- revisar: … -->` sí se leen y se enseñan aparte, porque son lo que el propietario tiene que ver.
 */

const COMENTARIO = /<!--\s*revisar:\s*([\s\S]*?)-->/g;

export interface Block {
  kind: 'heading' | 'list' | 'table' | 'quote' | 'paragraph';
  level?: number;
  lines: string[];
}

/** Las marcas de revisión que el redactor dejó dentro del texto, sin los delimitadores. */
export function revisionMarks(markdown: string): string[] {
  return [...markdown.matchAll(COMENTARIO)]
    .map((encontrado) => (encontrado[1] ?? '').trim())
    .filter((texto) => texto.length > 0);
}

/** El markdown sin las marcas de revisión: se enseñan aparte, no dentro del párrafo. */
export function withoutRevisionMarks(markdown: string): string {
  return markdown.replace(COMENTARIO, '').trim();
}

/** El markdown partido en bloques, que es lo que se puede dibujar sin ambigüedad. */
export function notesBlocks(markdown: string): Block[] {
  const bloques: Block[] = [];
  let actual: Block | null = null;
  const cerrar = () => {
    if (actual !== null && actual.lines.length > 0) {
      bloques.push(actual);
    }
    actual = null;
  };
  for (const linea of withoutRevisionMarks(markdown).split('\n')) {
    const texto = linea.trim();
    if (texto.length === 0) {
      cerrar();
      continue;
    }
    if (/^#{1,6}\s/.test(texto)) {
      cerrar();
      const nivel = texto.match(/^#+/)?.[0].length ?? 1;
      bloques.push({
        kind: 'heading',
        level: Math.min(nivel, 6),
        lines: [texto.replace(/^#+\s*/, '')],
      });
      continue;
    }
    if (texto.startsWith('|')) {
      if (actual?.kind !== 'table') {
        cerrar();
        actual = { kind: 'table', lines: [] };
      }
      // La fila de guiones que separa la cabecera del cuerpo no es contenido.
      if (!/^\|[\s:|-]+\|$/.test(texto)) {
        actual.lines.push(texto);
      }
      continue;
    }
    if (/^([-*]|\d+\.)\s+/.test(texto)) {
      if (actual?.kind !== 'list') {
        cerrar();
        actual = { kind: 'list', lines: [] };
      }
      actual.lines.push(texto.replace(/^([-*]|\d+\.)\s+/, ''));
      continue;
    }
    if (texto.startsWith('>')) {
      if (actual?.kind !== 'quote') {
        cerrar();
        actual = { kind: 'quote', lines: [] };
      }
      actual.lines.push(texto.replace(/^>\s*/, ''));
      continue;
    }
    if (actual?.kind !== 'paragraph') {
      cerrar();
      actual = { kind: 'paragraph', lines: [] };
    }
    actual.lines.push(texto);
  }
  cerrar();
  return bloques;
}

/** Una celda de tabla partida por las barras de los extremos. */
export function tableCells(linea: string): string[] {
  return linea
    .replace(/^\|/, '')
    .replace(/\|$/, '')
    .split('|')
    .map((celda) => celda.trim());
}
