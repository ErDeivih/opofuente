/**
 * **El guardián de las capturas** (fase «lo que ve el alumno», punto 7).
 *
 * **Qué problema resuelve**: dos veces se han entregado capturas que enseñaban la **siembra de pruebas**
 * en vez de la base del propietario —«El Esquema Nacional de Seguridad se regula en el Real Decreto
 * 311/2022 · Verdadero/Falso»—, y las dos veces se detectó **mirando el PNG**. **Una revisión a ojo no
 * es un control**: si mañana vuelve a pasar, tiene que pararlo un programa.
 *
 * **De dónde salen las frases prohibidas**: **de los propios fixtures de la puerta 18**, leídos del
 * código cada vez que se captura. **No hay una lista escrita a mano que se quede vieja**: si mañana
 * alguien cambia una pregunta de la siembra, la frase nueva entra sola y la vieja deja de buscarse.
 *
 * **Qué cuenta como frase de la siembra**: un texto entrecomillado de **ocho palabras o más** dentro de
 * las pruebas de `tests/e2e`. Las cadenas cortas son etiquetas de interfaz —«Iniciar sesión», «Ver la
 * respuesta»—, que **sí** deben salir en una captura buena; las largas son contenido, y **el contenido
 * de la siembra no puede aparecer en una captura de la base real**.
 */

import { readFileSync, readdirSync } from 'node:fs';
import path from 'node:path';

/** Palabras mínimas para que una cadena se considere **contenido** y no una etiqueta. */
const MINIMO_DE_PALABRAS = 8;

/** Minúsculas, sin tildes y con los espacios colapsados: compara lo que se lee, no el byte. */
export function normalizar(texto: string): string {
  return texto
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/\s+/g, ' ')
    .toLowerCase()
    .trim();
}

/** Dónde están los fixtures: `apps/web/tests/e2e` al lado de este fichero. */
function carpetaDeFixtures(): string {
  return path.resolve(process.cwd(), 'tests', 'e2e');
}

/**
 * **Las frases de la siembra**, sacadas de los fixtures de la puerta 18.
 *
 * Se leen las cadenas con comillas simples, dobles o invertidas y se quedan las que tienen ocho
 * palabras o más y no llevan pinta de código (llaves, flechas, paréntesis de llamada).
 */
export function frasesDeLaSiembra(carpeta: string = carpetaDeFixtures()): string[] {
  const frases = new Set<string>();
  let ficheros: string[];
  try {
    ficheros = readdirSync(carpeta).filter((nombre) => nombre.endsWith('.spec.ts'));
  } catch {
    // **Sin fixtures no hay frases y no se bloquea nada**: una máquina sin la carpeta no puede
    // inventarse la siembra, y fallar por eso sería castigar al que no tiene el repo entero.
    return [];
  }
  for (const fichero of ficheros) {
    const codigo = readFileSync(path.join(carpeta, fichero), 'utf8');
    for (const coincidencia of codigo.matchAll(/'([^'\\\n]{20,400})'|"([^"\\\n]{20,400})"|`([^`\\\n]{20,400})`/g)) {
      const bruto = (coincidencia[1] ?? coincidencia[2] ?? coincidencia[3] ?? '').trim();
      // **Fuera la numeración de la opción.** En el fixture una opción se escribe «3. El Esquema
      // Nacional…»; en la pantalla se lee «El Esquema Nacional…», y con el «3.» delante el guardián
      // no encontraría justo la frase que tiene que encontrar.
      const texto = bruto.replace(/^\s*(?:[0-9]{1,2}[.)]|[a-dA-D][.)]|[-*])\s*/, '');
      if (texto.split(/\s+/).length < MINIMO_DE_PALABRAS) {
        continue;
      }
      // **Fuera lo que es código**: interpolaciones, flechas, selectores y expresiones.
      if (/[{}<>()[\]=;]|=>|\$\{/.test(texto)) {
        continue;
      }
      frases.add(texto);
    }
  }
  return [...frases].sort();
}

/**
 * **Las frases de la siembra que aparecen en ese texto**, ya normalizadas.
 *
 * Devuelve la lista de las encontradas: vacía quiere decir que la captura no enseña la siembra.
 */
export function frasesSembradasEn(texto: string, frases: readonly string[]): string[] {
  const heno = normalizar(texto);
  return frases.filter((frase) => {
    // **Se busca el comienzo de la frase, no la frase entera.** La cadena del fixture suele ser más
    // larga que lo que la pantalla enseña —un enunciado con su cierre, un texto con su nota—, y
    // exigir el final haría que el guardián **no viera justo el caso que tiene que ver**.
    const comienzo = normalizar(frase.split(/\s+/).slice(0, MINIMO_DE_PALABRAS).join(' '));
    return comienzo.length > 0 && heno.includes(comienzo);
  });
}

/** El error que se lanza cuando una captura enseña la siembra. */
export class CapturaSembrada extends Error {
  constructor(
    readonly ruta: string,
    readonly anchura: string,
    readonly frases: readonly string[],
  ) {
    super(
      `La captura de ${ruta} (${anchura}) enseña la siembra de pruebas: ` +
        frases.map((frase) => `«${frase}»`).join(', ') +
        '. Una captura solo vale si su texto sale de la base real.',
    );
    this.name = 'CapturaSembrada';
  }
}
