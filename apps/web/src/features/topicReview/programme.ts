import type { CurriculumNode } from '../../api/profiles';

/**
 * El programa vigente, indexado para poder **elegir** un destino al revisar la clasificación.
 *
 * La pantalla no enseña el árbol entero: necesita dos cosas y en este orden —la lista de temas para
 * el selector y los epígrafes del tema elegido—, así que se prepara una vez y se consulta por
 * identificador. Un tema con epígrafes los trae dentro porque el epígrafe no sustituye a su tema:
 * al asignar se escriben los dos.
 */
export interface EpigraphOption {
  readonly id: string;
  /** La ruta del árbol (`I.1.1`), que es el código que se lee en pantalla. */
  readonly path: string;
  readonly title: string;
}

export interface TopicOption {
  readonly id: string;
  readonly path: string;
  readonly title: string;
  readonly blockPath: string;
  readonly blockTitle: string;
  readonly epigraphs: readonly EpigraphOption[];
}

function epigraphsOf(node: CurriculumNode): EpigraphOption[] {
  return node.children
    .filter((child) => child.node_type === 'epigraph')
    .map((child) => ({ id: child.id, path: child.path, title: child.title }));
}

/**
 * Los temas del programa, aplanados y con su bloque.
 *
 * Un programa puede traer los temas colgando de bloques (TAI) o sueltos en la raíz (Celador en el
 * acceso libre de 2022): los dos casos salen, y el tema suelto se queda sin bloque en vez de
 * desaparecer del selector.
 */
export function indexProgramme(nodes: readonly CurriculumNode[]): TopicOption[] {
  const temas: TopicOption[] = [];
  for (const node of nodes) {
    if (node.node_type === 'topic') {
      temas.push({
        id: node.id,
        path: node.path,
        title: node.title,
        blockPath: '',
        blockTitle: '',
        epigraphs: epigraphsOf(node),
      });
      continue;
    }
    for (const child of node.children) {
      if (child.node_type !== 'topic') {
        continue;
      }
      temas.push({
        id: child.id,
        path: child.path,
        title: child.title,
        blockPath: node.path,
        blockTitle: node.title,
        epigraphs: epigraphsOf(child),
      });
    }
  }
  return temas;
}

/** El texto con el que se lee un destino: su ruta y su título, nunca solo un identificador. */
export function topicLabel(tema: TopicOption): string {
  return `${tema.path} · ${tema.title}`;
}

/** Los temas agrupados por bloque, para pintar el selector con `optgroup`. */
export function groupByBlock(temas: readonly TopicOption[]): { title: string; topics: TopicOption[] }[] {
  const grupos: { title: string; topics: TopicOption[] }[] = [];
  for (const tema of temas) {
    const titulo = tema.blockPath === '' ? '' : `${tema.blockPath} · ${tema.blockTitle}`;
    const ultimo = grupos[grupos.length - 1];
    if (ultimo !== undefined && ultimo.title === titulo) {
      ultimo.topics.push(tema);
    } else {
      grupos.push({ title: titulo, topics: [tema] });
    }
  }
  return grupos;
}
