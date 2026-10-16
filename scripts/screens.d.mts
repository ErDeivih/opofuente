/**
 * Las opciones de `npm run screens`, declaradas para TypeScript.
 *
 * El guion es `.mjs` porque lo ejecuta Node tal cual (`node scripts/screens.mjs`), no Vite: la
 * herramienta de capturas no forma parte del paquete. Esta declaración es la que hace que la prueba de
 * las opciones esté tipada en vez de trabajar con `any`.
 */

export interface OpcionesDeCapturas {
  /** La copia de los datos reales contra la que capturar, o `null` para la siembra de pruebas. */
  datos: string | null;
  /** La carpeta de los PNG y del informe. */
  salida: string;
  /** Las variables de entorno con las que se lanza Playwright. */
  entorno: Record<string, string>;
  /** Los argumentos que no son de esta herramienta, tal cual se le pasan a Playwright. */
  resto: string[];
  /** Lo que se imprime al empezar: contra qué datos se está capturando. */
  mensaje: string;
}

export function leerOpciones(argumentos: string[], raiz: string): OpcionesDeCapturas;
