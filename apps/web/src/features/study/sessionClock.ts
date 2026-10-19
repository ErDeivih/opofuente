/**
 * El reloj de un test y las palabras con las que se cuenta (§3.4).
 *
 * Vive aparte de los componentes a propósito: un módulo que exporta componentes y además constantes
 * y funciones obliga a recargar la pantalla entera cada vez que cambia la constante
 * (`react-refresh`).
 *
 * **De dónde sale la hora.** El servidor dice cuándo se arrancó la sesión (`started_at`, en UTC) y
 * cuánto dura (`time_limit_minutes`). El navegador **no** adivina ninguna de las dos cosas, y tampoco
 * enfrenta su reloj con el del servidor: lo que mide con su propio reloj es **el tiempo que pasa desde
 * que llegó la lectura**, y el desfase entre los dos relojes se estima **una sola vez**, comparando la
 * hora de arranque con el instante en el que llegó la sesión. Esa estimación se desvía como mucho lo
 * que tardó la respuesta en llegar; para una petición local es una fracción de segundo, y por eso el
 * aviso de «queda poco» es de cinco minutos y no de cinco segundos.
 *
 * **La referencia viene del contrato, no de un reloj leído al pintar.** La hora del servidor viaja
 * junto a la sesión (`server_now`, un instante UTC del mismo reloj que escribió `started_at`) y es lo
 * que permite estimar el desfase sin depender de que los dos equipos estén en hora. Sin ella —una API
 * antigua— el reloj se calla en lugar de enseñar una cuenta que no se sostiene.
 */

/** Un minuto, en milisegundos. */
const MINUTO_MS = 60_000;

/** Cuándo avisar de que queda poco: los últimos cinco minutos (diseño v0). */
const AVISO_MS = 5 * MINUTO_MS;

export interface RelojDeSesion {
  /** El tiempo que queda, en milisegundos. `null` cuando el test no lleva reloj o no se sabe. */
  readonly restanteMs: number | null;
  /** El tiempo que se lleva, en milisegundos. `null` cuando no se puede saber. */
  readonly transcurridoMs: number | null;
  /** Si el límite ya pasó. No bloquea nada: lo dice. */
  readonly vencido: boolean;
  /** Si queda poco, para pintarlo con aviso. */
  readonly apurado: boolean;
}

/** Lo que hace falta para poner el reloj en hora, tal como llegó del servidor. */
export interface DatosDelReloj {
  readonly startedAt: string | null;
  readonly timeLimitMinutes: number | null;
  /**
   * La hora del **servidor** en el momento de la respuesta (`server_now`), del mismo reloj que
   * `startedAt`. Es la referencia de la cuenta, y sin ella no hay reloj.
   */
  readonly serverNow: string | null;
}

/**
 * El estado del reloj en un instante.
 *
 * El transcurrido es el que ya había cuando el servidor escribió su hora (`server_now - started_at`,
 * con **un solo** reloj) **más** lo que ha pasado desde que llegó la lectura, medido con el reloj del
 * navegador. Esa suma no depende de que los dos relojes coincidan: lo único que se mide localmente es
 * un trozo de tiempo, no una hora.
 */
export function relojDeSesion(datos: {
  readonly startedAt: string | null;
  readonly timeLimitMinutes: number | null;
  readonly serverNow: string | null;
  readonly desdeLaLecturaMs: number;
}): RelojDeSesion {
  if (datos.startedAt === null) {
    return { restanteMs: null, transcurridoMs: null, vencido: false, apurado: false };
  }
  const arranque = Date.parse(datos.startedAt);
  const ahoraDelServidor = datos.serverNow === null ? Number.NaN : Date.parse(datos.serverNow);
  if (Number.isNaN(arranque) || Number.isNaN(ahoraDelServidor)) {
    // Sin las dos horas del servidor no hay reloj: se dice que no se sabe en vez de inventar un cero.
    return { restanteMs: null, transcurridoMs: null, vencido: false, apurado: false };
  }
  const desdeLaLectura = Math.max(0, datos.desdeLaLecturaMs);
  const transcurridoMs = Math.max(0, ahoraDelServidor - arranque) + desdeLaLectura;
  const limiteMs = datos.timeLimitMinutes === null ? null : datos.timeLimitMinutes * MINUTO_MS;
  if (limiteMs === null) {
    return { restanteMs: null, transcurridoMs, vencido: false, apurado: false };
  }
  const restanteMs = Math.max(0, limiteMs - transcurridoMs);
  return {
    restanteMs,
    transcurridoMs,
    vencido: transcurridoMs >= limiteMs,
    apurado: restanteMs > 0 && restanteMs <= AVISO_MS,
  };
}

/** `1:07:30` o `12:05`: el tiempo en horas, minutos y segundos, sin ceros de relleno de más. */
export function tiempoEnPalabras(ms: number): string {
  const total = Math.max(0, Math.floor(ms / 1000));
  const horas = Math.floor(total / 3600);
  const minutos = Math.floor((total % 3600) / 60);
  const segundos = total % 60;
  const dosCifras = (valor: number): string => String(valor).padStart(2, '0');
  if (horas > 0) {
    return `${String(horas)}:${dosCifras(minutos)}:${dosCifras(segundos)}`;
  }
  return `${String(minutos)}:${dosCifras(segundos)}`;
}
