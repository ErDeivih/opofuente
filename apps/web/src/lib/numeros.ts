/**
 * Los números de la interfaz, en español y **en un solo sitio** (§2.2 del cierre del objetivo).
 *
 * El propietario lo vio en las capturas: las notas salían «0.0000» en vez de «0,00». El motivo no era
 * que faltara un `Intl`: era que **convivían tres formatos** —el decimal que manda el servidor (punto
 * y cuatro cifras), un `toFixed(2)` suelto en dos pantallas y un `toFixed(1).replace('.', ',')` en
 * otra—, y cada uno se acordaba de la coma o no según el día.
 *
 * Aquí se decide dos veces y nada más:
 *
 * 1. **una nota** (lo que se puntúa) va con coma y **dos** decimales: `12,50`, `0,00`, `-0,33`;
 * 2. **una escala** (el máximo, el mínimo, un umbral publicado) va como la publica la convocatoria:
 *    `50`, `25,5`, sin ceros que nadie escribió;
 * 3. **un porcentaje** va sin decimales salvo que hagan falta: `90 %`, y `90,2 %` cuando se piden.
 *
 * Y una regla que vale para las tres: **lo que llega del servidor no se enseña tal cual**. El decimal
 * del servidor (`0.3333`) es un dato para leer, no una cifra para mirar; la cifra se calcula de la
 * fracción exacta (`1/3`) o del número, y se formatea aquí.
 */

/** Una nota: dos decimales y coma, siempre. */
const NOTA = new Intl.NumberFormat('es-ES', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

/** Un porcentaje: sin decimales salvo que se pidan. */
function formateadorDePorcentaje(decimales: number): Intl.NumberFormat {
  return new Intl.NumberFormat('es-ES', {
    minimumFractionDigits: decimales,
    maximumFractionDigits: decimales,
  });
}

/** El máximo de dos decimales con el que se formatean las escalas. */
const ESCALA = new Intl.NumberFormat('es-ES', {
  minimumFractionDigits: 0,
  maximumFractionDigits: 2,
});

const PORCENTAJE = formateadorDePorcentaje(0);

/** Una cifra de puntuación: `0,00`, `12,50`, `-0,33`. */
export function formatearNota(valor: number): string {
  return NOTA.format(valor);
}

/**
 * Una referencia de escala —el máximo de la prueba, el mínimo publicado— tal como la publica la
 * convocatoria: `50`, `25,5`, `0,33`.
 *
 * No lleva ceros de más a propósito: «sobre 50» es lo que dice la convocatoria, y «sobre 50,00» sería
 * inventarle una precisión al ejercicio.
 */
export function formatearEscala(valor: number): string {
  return ESCALA.format(valor);
}

/**
 * Un porcentaje a partir de una **proporción** (0–1), que es como viaja la precisión en la API.
 *
 * `formatearPorcentaje(0.9)` → `'90 %'`. Con `{ decimales: 1 }` → `'90,0 %'`, para lo que de verdad
 * necesita la décima (una cobertura medida, por ejemplo).
 */
export function formatearPorcentaje(
  proporcion: number,
  opciones: { decimales?: number } = {},
): string {
  const decimales = opciones.decimales ?? 0;
  const formateador = decimales === 0 ? PORCENTAJE : formateadorDePorcentaje(decimales);
  return `${formateador.format(proporcion * 100)} %`;
}

/**
 * El **valor** de una fracción exacta (`1/3`, `-1/6`, `42`), o `null` si el texto no es una fracción.
 *
 * Es el paso de antes de formatear: hay decisiones —enseñar la puntuación sin bajar de cero, por
 * ejemplo— que se toman sobre el número y no sobre su texto. Devuelve `null` —y no un cero— cuando el
 * texto no es una fracción: `null` significa «aquí no hay cifra que enseñar», y un cero significaría
 * «la puntuación es cero», que es otra cosa.
 */
export function valorDeFraccion(fraccion: string): number | null {
  const limpio = fraccion.trim();
  if (limpio === '') {
    return null;
  }
  const partes = limpio.split('/');
  if (partes.length > 2) {
    return null;
  }
  const numerador = Number(partes[0]);
  const denominador = partes.length === 2 ? Number(partes[1]) : 1;
  if (!Number.isFinite(numerador) || !Number.isFinite(denominador) || denominador === 0) {
    return null;
  }
  return numerador / denominador;
}

/**
 * La puntuación **para mirar**: nunca por debajo de `0,00` (F38, §3.5 del encargo).
 *
 * El recorrido midió «Puntuación directa: -0,21 (estimada)»: los números cuadran —aciertos menos
 * errores por su penalización—, pero un alumno lee ahí una nota que no existe. En pantalla la cifra no
 * baja de cero; la exacta no se pierde, se lee dentro del pliegue (`notaNegativaExacta`).
 *
 * `null` sigue significando «aquí no hay cifra»: un texto que no es una fracción se enseña como llegó
 * y esta función no lo toca.
 */
export function notaNoNegativa(fraccion: string): string | null {
  const valor = valorDeFraccion(fraccion);
  return valor === null ? null : formatearNota(Math.max(0, valor));
}

/**
 * La cifra exacta **cuando es negativa**, para el pliegue que la explica: `-0,33`. Si no hay negativa
 * que explicar devuelve `null`, y entonces el pliegue no la menciona.
 */
export function notaNegativaExacta(fraccion: string): string | null {
  const valor = valorDeFraccion(fraccion);
  return valor === null || valor >= 0 ? null : formatearNota(valor);
}

/** El decimal que manda el servidor (`0.0000`, `1.6667`), leído en español. */
export function notaDeDecimal(decimal: string): string | null {
  const limpio = decimal.trim().replace(',', '.');
  if (limpio === '' || !/^[+-]?\d*\.?\d+$/.test(limpio)) {
    return null;
  }
  const valor = Number(limpio);
  return Number.isFinite(valor) ? formatearNota(valor) : null;
}
