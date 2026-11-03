import type { StudentNoteSection } from '../../api/studentStudy';
import { notesBlocks, tableCells } from '../dossier/notesMarkdownParser';

/**
 * El texto de los apuntes preparado para **oírse**, capítulo a capítulo (O7).
 *
 * La lectura en voz la pone el aparato, no la aplicación: el navegador trae `speechSynthesis` y sus
 * voces instaladas, así que el tema se lee **sin salir del equipo** —no hay servicio de nube, no hay
 * dependencia nueva y no se guarda ningún audio—. Lo único que hace falta aquí es lo que un sintetizador
 * no puede adivinar: qué trozos de markdown son adorno (`**`, `` ` ``, `##`) y dónde termina una idea.
 *
 * De ahí las tres piezas de este módulo, todas puras y probables sin navegador:
 *
 * 1. **`sinAdornos`**: el markdown convertido en lo que se pronuncia. Las tablas se leen por celdas
 *    («Capa: Transporte; unidad: Segmento»), no con sus barras verticales.
 * 2. **`frases`**: un párrafo partido en frases y agrupado en trozos de tamaño razonable. Un trozo es
 *    la unidad que se sintetiza: cuanto más corto, antes responde «pausa» y mejor se retoma.
 * 3. **`fragmentosDelCapitulo`**: el capítulo entero en orden, con el apartado de cada trozo, que es
 *    lo que permite decir «apartado 3 de 12» y parar donde toca.
 *
 * Las marcas `<!-- revisar: … -->` **se quitan**: son una nota para el propietario, no texto del tema.
 */

/** Un trozo del capítulo tal y como se pronuncia, con el apartado al que pertenece. */
export interface FragmentoEnVoz {
  /** Estable dentro del capítulo: sirve de `key` y de sitio donde reanudar. */
  key: string;
  /** Lo que se sintetiza, sin marcas de markdown. */
  text: string;
  /** El número del apartado (`1..N`) al que pertenece el trozo. */
  sectionNumber: number;
  /** El título del apartado, para decir por dónde va la lectura. */
  sectionTitle: string;
}

/** La parte de una voz del sistema que se usa para elegir: así se prueba con objetos escritos a mano. */
export interface VozDelSistema {
  name: string;
  lang: string;
  localService?: boolean;
}

/** Una velocidad de lectura ofrecida en la pantalla. */
export interface VelocidadDeLectura {
  valor: number;
  etiqueta: string;
  /** Lo que se dice del control, para que no sea solo un número. */
  descripcion: string;
}

/** Las tres velocidades: dos más lentas que lo normal para repasar y una rápida para releer. */
export const VELOCIDADES: readonly VelocidadDeLectura[] = [
  { valor: 0.8, etiqueta: 'Lenta', descripcion: 'Lee más despacio, para estudiar de oído' },
  { valor: 1, etiqueta: 'Normal', descripcion: 'La velocidad de la voz del sistema' },
  { valor: 1.25, etiqueta: 'Rápida', descripcion: 'Lee más deprisa, para repasar' },
];

/** El tamaño máximo de un trozo sintetizado: una frase larga se deja entera antes que cortarla. */
const TROZO_MAXIMO = 240;

const ENLACE = /\[([^\]]*)\]\(([^)]*)\)/g;
const ETIQUETA_HTML = /<\/?[a-z][^>]*>/gi;
const CURSIVA_CON_BAJOS = /(^|[\s(«"'])_{1,2}([^_]+)_{1,2}(?=[\s.,;:!?»"')]|$)/g;

/**
 * El texto de un trozo de markdown **como se pronuncia**: sin negritas, sin código y sin enlaces.
 *
 * No se toca nada más. En particular, no se quitan las barras bajas sueltas de un identificador
 * (`tcp_ip` se dice tal cual): solo la pareja `_…_` que va entre espacios, que es la cursiva.
 */
export function sinAdornos(texto: string): string {
  return texto
    .replace(ENLACE, '$1')
    .replace(ETIQUETA_HTML, ' ')
    .replace(CURSIVA_CON_BAJOS, '$1$2')
    .replace(/\*\*|__|`/g, '')
    .replace(/\*/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

/**
 * Un párrafo partido en los trozos que se sintetizan.
 *
 * Se corta por final de frase (`.!?…` y el espacio siguiente) y se van juntando frases mientras quepan
 * en `TROZO_MAXIMO`. Una frase que por sí sola pase del límite **no se parte**: cortar por donde no hay
 * puntuación deja dos trozos que se oyen a medias.
 */
export function frases(texto: string): string[] {
  const limpio = sinAdornos(texto);
  if (limpio === '') {
    return [];
  }
  const oraciones = limpio.split(/(?<=[.!?…])\s+/).filter((oracion) => oracion !== '');
  const trozos: string[] = [];
  let actual = '';
  for (const oracion of oraciones) {
    const candidato = actual === '' ? oracion : `${actual} ${oracion}`;
    if (actual !== '' && candidato.length > TROZO_MAXIMO) {
      trozos.push(actual);
      actual = oracion;
      continue;
    }
    actual = candidato;
  }
  if (actual !== '') {
    trozos.push(actual);
  }
  return trozos;
}

/** Una fila de tabla, tal y como se lee: «Transporte, segmento». */
function filaHablada(linea: string): string {
  return tableCells(linea)
    .map((celda) => sinAdornos(celda))
    .filter((celda) => celda !== '')
    .join(', ');
}

/**
 * Los trozos de **un apartado**, en el orden en que se leen.
 *
 * Los títulos van cada uno en su trozo y los elementos de una lista también: al oír, una lista de
 * cinco elementos en un solo párrafo se pierde, y un epígrafe suelto avisa de que se cambia de asunto.
 * Una tabla se dice por filas —la primera es la cabecera, igual que en pantalla—.
 */
export function fragmentosDelApartado(apartado: StudentNoteSection): FragmentoEnVoz[] {
  const trozos: FragmentoEnVoz[] = [];
  const añadir = (texto: string): void => {
    const limpio = texto.trim();
    if (limpio === '') {
      return;
    }
    trozos.push({
      key: `${apartado.key}:${String(trozos.length)}`,
      text: limpio,
      sectionNumber: apartado.number,
      sectionTitle: apartado.title,
    });
  };

  for (const bloque of notesBlocks(apartado.body_markdown)) {
    if (bloque.kind === 'heading' || bloque.kind === 'quote') {
      añadir(sinAdornos(bloque.lines.join(' ')));
      continue;
    }
    if (bloque.kind === 'list') {
      for (const linea of bloque.lines) {
        añadir(sinAdornos(linea));
      }
      continue;
    }
    if (bloque.kind === 'table') {
      for (const linea of bloque.lines) {
        añadir(filaHablada(linea));
      }
      continue;
    }
    for (const trozo of frases(bloque.lines.join(' '))) {
      añadir(trozo);
    }
  }
  return trozos;
}

/**
 * El capítulo entero en trozos, en orden, con el título de cada apartado delante.
 *
 * El título se dice aunque el apartado no tenga texto: es lo que da la estructura al oído, y sin él
 * un capítulo largo suena a una sola tirada.
 */
export function fragmentosDelCapitulo(
  apartados: readonly StudentNoteSection[],
): FragmentoEnVoz[] {
  const trozos: FragmentoEnVoz[] = [];
  for (const apartado of apartados) {
    const titulo = sinAdornos(apartado.title);
    if (titulo !== '') {
      trozos.push({
        key: `${apartado.key}:titulo`,
        text: titulo,
        sectionNumber: apartado.number,
        sectionTitle: apartado.title,
      });
    }
    trozos.push(...fragmentosDelApartado(apartado));
  }
  return trozos;
}

/**
 * La voz que hay que usar, o `null` si el aparato no tiene ninguna.
 *
 * Manda el idioma: un tema en castellano leído con una voz inglesa se entiende mal. Entre las voces en
 * español se prefiere la del propio equipo (`localService`), porque es la que no depende de la red y la
 * que suena igual sin conexión. Si no hay ninguna en español **no se inventa**: se devuelve la primera
 * que haya y la pantalla lo advierte.
 *
 * Es genérica a propósito: acepta las voces del sistema tal cual (`SpeechSynthesisVoice`) y devuelve el
 * mismo tipo, así que quien la usa no tiene que convertir nada.
 */
export function vozPreferida<T extends VozDelSistema>(voces: readonly T[]): T | null {
  if (voces.length === 0) {
    return null;
  }
  const puntuacion = (voz: VozDelSistema): number => {
    const idioma = voz.lang.toLowerCase();
    let puntos = 0;
    if (idioma === 'es-es' || idioma.startsWith('es-es-')) {
      puntos += 4;
    } else if (idioma === 'es' || idioma.startsWith('es-')) {
      puntos += 2;
    }
    if (voz.localService === true) {
      puntos += 1;
    }
    return puntos;
  };
  let elegida: T | null = voces[0] ?? null;
  for (const voz of voces) {
    if (elegida === null || puntuacion(voz) > puntuacion(elegida)) {
      elegida = voz;
    }
  }
  return elegida;
}

/** `true` si alguna de las voces del aparato habla español, que es lo que la pantalla comprueba. */
export function hayVozEnEspanol(voces: readonly VozDelSistema[]): boolean {
  return voces.some((voz) => voz.lang.toLowerCase().startsWith('es'));
}
