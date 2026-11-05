import type { CurriculumNode } from '../../api/temario';

/**
 * Búsqueda que perdona tildes.
 *
 * Se normaliza con `NFD` y se quitan los diacríticos: escribir «constitucion» encuentra
 * «Constitución». También se busca por código y por ruta para que «II.3» lleve al tema.
 */
export function normalizeText(text: string): string {
  return text
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim();
}

function matches(node: CurriculumNode, needle: string): boolean {
  if (needle === '') {
    return true;
  }
  return normalizeText(`${node.title} ${node.official_code} ${node.path}`).includes(needle);
}

/**
 * Filtra el árbol conservando el orden oficial.
 *
 * Si coincide el bloque, se enseñan todos sus temas; si solo coinciden algunos temas, el bloque se
 * queda con esos. Los bloques que se quedan sin temas no se pintan.
 */
export function filterTemario(nodes: CurriculumNode[], query: string): CurriculumNode[] {
  const needle = normalizeText(query);
  if (needle === '') {
    return nodes;
  }
  return nodes
    .map((block) => ({
      ...block,
      children: matches(block, needle) ? block.children : block.children.filter((child) => matches(child, needle)),
    }))
    .filter((block) => block.children.length > 0);
}

/** Los temas de un árbol, en orden de lectura, sin recursión implícita en la pantalla. */
export function flattenTopics(nodes: CurriculumNode[]): CurriculumNode[] {
  return nodes.flatMap((node) => [
    ...(node.node_type === 'topic' ? [node] : []),
    ...flattenTopics(node.children),
  ]);
}
