/**
 * Lo que **nunca** debe verse en la zona del alumno.
 *
 * Hay dos listas porque son dos problemas distintos (revisión de F0, 6 de octubre de 2026):
 *
 * 1. **Datos que no se pueden ver nunca** (`DATOS_PROHIBIDOS`): rutas de las carpetas del propietario,
 *    nombres de bancos privados y otras oposiciones. Si aparecen, es una fuga venga de donde venga,
 *    también dentro de una pregunta o de unos apuntes.
 * 2. **Vocabulario de la interfaz** (`LENGUAJE_INTERNO`): «bandeja», «revisión», «fuente», «tramo»…
 *    Solo se busca **fuera del contenido**. Medido sobre los 16.743 enunciados de TAI: «versión» sale
 *    en 264 (control de versiones), «clave» en 163 (clave primaria), «fuente» en 151 (código fuente),
 *    «SAS» en 161 (discos SAS) y «Representación» está en el título del tema II.1. Buscarlas dentro del
 *    temario sería marcar como fuga el propio temario.
 *
 * Las palabras se buscan **completas** (con límites de letra, no como trozos: «sas» dentro de «casas»
 * no cuenta) y **sin distinguir acentos** («revision» encuentra «revisión»). Las siglas van sensibles a
 * mayúsculas: «SAS» sí, «sas» no.
 */

/** Rutas y nombres del propietario: si salen, es una fuga. */
export const RUTAS_PROHIBIDAS: readonly string[] = ['F:\\', 'C:\\Users', 'Users\\', 'Oposiciones\\'];

/** Bancos privados y material de terceros que no se pueden ofrecer. */
export const BANCOS_PROHIBIDOS: readonly string[] = ['Rojo', 'GSI', 'Preparatic', 'Adams'];

/** Oposiciones que no son TAI: esta zona es solo de TAI. */
export const OPOSICIONES_PROHIBIDAS: readonly string[] = ['Celador', 'Guardia Civil', 'BOCYL'];

/** Lo que se busca en **toda** la pantalla, contenido incluido. */
export const DATOS_PROHIBIDOS: readonly string[] = [
  ...RUTAS_PROHIBIDAS,
  ...BANCOS_PROHIBIDOS,
  ...OPOSICIONES_PROHIBIDAS,
];

/** Vocabulario de la aplicación por dentro: solo se busca **fuera del contenido**. */
export const LENGUAJE_INTERNO: readonly string[] = [
  'bandeja',
  'revision',
  'fuente',
  'fuentes',
  'tramo',
  'tramos',
  'mapeo',
  'mapeos',
  'representacion',
  'conjunto',
  'conjuntos',
  'clave',
  'claves',
  'version',
  'versiones',
  'evidencia',
  'evidencias',
  'artefacto',
  'artefactos',
  'corpus',
  'dossier',
  'ingesta',
  'cuarentena',
];

/** Las siglas se buscan tal cual: «SAS» (la oposición) sí, «sas» de «casas» no. */
export const SIGLAS_INTERNAS: readonly string[] = ['SAS'];

/** Extensiones de fichero: en la interfaz delatan material del propietario. */
export const EXTENSIONES_PROHIBIDAS: readonly string[] = ['.pdf', '.docx', '.zip', '.xlsx', '.epub'];

/** Un UUID visible: en la zona del alumno las direcciones llevan `I-1`, `IV-10`. */
export const UUID_VISIBLE = /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i;

/**
 * Casos legítimos que no cuentan como fuga: rutas del sistema que una pregunta de informática puede
 * nombrar sin enseñar nada del propietario.
 */
export const EXCEPCIONES: readonly string[] = ['C:\\Windows', 'C:\\Program Files', 'C:\\ProgramData'];

export interface Encontrado {
  /** La palabra o el patrón que aparece. */
  palabra: string;
  /** Dónde aparece, con un poco de contexto para poder buscarlo. */
  contexto: string;
}

/** Quita los acentos para comparar: «revision» tiene que encontrar «revisión». */
function sinAcentos(texto: string): string {
  return texto.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
}

/**
 * Busca una palabra **completa**: los caracteres de los lados no pueden ser letras ni números.
 *
 * Con `\b` no vale: en JavaScript `\b` solo entiende `[A-Za-z0-9_]`, así que «sas» dentro de «casas»
 * contaría como palabra completa. Aquí los límites se escriben con clases Unicode.
 */
function buscarPalabra(texto: string, palabra: string, sensible: boolean): number {
  const patron = new RegExp(
    `(?<![\\p{L}\\p{N}])${escapar(palabra)}(?![\\p{L}\\p{N}])`,
    sensible ? 'u' : 'iu',
  );
  return texto.search(patron);
}

function escapar(texto: string): string {
  return texto.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function recortar(texto: string, indice: number, largo: number): string {
  return texto.slice(Math.max(0, indice - 40), indice + largo + 40).trim();
}

/** ¿La entrada es una palabra (para exigirle límites) o un trozo (una ruta, una extensión)? */
function esPalabra(entrada: string): boolean {
  return /^[\p{L}][\p{L}\p{N}]*$/u.test(entrada);
}

/** Las palabras de una lista que aparecen en un texto. */
function buscarLista(
  texto: string,
  palabras: readonly string[],
  { sensible = false }: { sensible?: boolean } = {},
): Encontrado[] {
  const normalizado = sinAcentos(texto);
  const encontrados: Encontrado[] = [];
  for (const palabra of palabras) {
    const buscada = sensible ? palabra : sinAcentos(palabra);
    // Las palabras se buscan completas; las rutas y las extensiones, tal cual: `F:\` va seguido de una
    // letra (`F:\Oposiciones`) y `.pdf` precedido de una (`tema.pdf`), así que exigirles límites de
    // palabra los dejaría sin encontrar nunca.
    const indice = esPalabra(palabra)
      ? buscarPalabra(normalizado, buscada, sensible)
      : normalizado.indexOf(buscada.toLowerCase());
    if (indice >= 0) {
      encontrados.push({ palabra, contexto: recortar(texto, indice, palabra.length) });
    }
  }
  return encontrados;
}

/**
 * Lo que no puede salir **en ninguna parte**: rutas, bancos, otras oposiciones y UUID.
 *
 * `excepciones` sirve para lo que sí es legítimo dentro del temario (una pregunta de sistemas
 * operativos puede nombrar `C:\Windows`).
 */
export function datosEnElTexto(
  texto: string,
  excepciones: readonly string[] = EXCEPCIONES,
): Encontrado[] {
  let limpio = texto;
  for (const excepcion of excepciones) {
    limpio = limpio.split(excepcion).join(' ');
  }
  return [
    ...buscarLista(limpio, DATOS_PROHIBIDOS),
    ...buscarLista(limpio, EXTENSIONES_PROHIBIDAS),
    ...(UUID_VISIBLE.test(limpio)
      ? [{ palabra: 'uuid visible', contexto: UUID_VISIBLE.exec(limpio)?.[0] ?? '' }]
      : []),
  ];
}

/** Lo que no puede salir **en la interfaz** (menús, botones, avisos): la jerga de la aplicación. */
export function lenguajeInternoEnElTexto(texto: string): Encontrado[] {
  return [
    ...buscarLista(texto, LENGUAJE_INTERNO),
    ...buscarLista(texto, SIGLAS_INTERNAS, { sensible: true }),
  ];
}

/** Las dos comprobaciones juntas: el texto de la interfaz y el de toda la pantalla. */
export function revisarPantalla(interfaz: string, todo: string): Encontrado[] {
  return [...datosEnElTexto(todo), ...lenguajeInternoEnElTexto(interfaz)];
}
