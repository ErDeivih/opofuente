/**
 * El consentimiento de las cookies, en el navegador (§9 del objetivo vivo).
 *
 * **Este fichero es la puerta de las cookies que no son necesarias.** Todo lo que la aplicación
 * quiera guardar en el navegador pasa por `setNonEssentialCookie`, y esa función **no escribe nada**
 * si no hay consentimiento para ese fin. No es una comprobación que cada pantalla tenga que
 * acordarse de hacer: es la única forma de escribir una cookie que no sea necesaria, así que una
 * pantalla nueva no puede saltársela por descuido.
 *
 * **Y la decisión se guarda en una cookie propia, no en `localStorage`.** Dos motivos: el servidor
 * tiene que poder leerla —es él quien decide si cuenta un suceso de analítica—, y el día que alguien
 * borre el almacén del navegador, la decisión se va con él en vez de quedarse en un sitio donde nadie
 * la busca.
 */

/** La cookie con la decisión: `v1.a0.p1.t1730000000`. Lleva **fines**, no identificadores. */
export const CONSENT_COOKIE = 'opofuente_consent';

/** La cookie que ponen estas funciones cuando hay permiso: el tamaño del texto de lectura. */
export const PREFERENCES_COOKIE = 'opofuente_prefs';

export type Purpose = 'necessary' | 'preferences' | 'analytics';

export interface ConsentDecisionState {
  policyVersion: number;
  analytics: boolean;
  preferences: boolean;
  decidedAt: Date;
}

const PATRON = /^v(\d+)\.a([01])\.p([01])\.t(\d+)$/;

/** Los días que vale la decisión. Los mismos que declara el servidor (seis meses). */
export const CONSENT_DAYS = 180;

/** Lee una cookie del navegador. Devuelve `null` si no está. */
export function readCookie(name: string): string | null {
  const partes = document.cookie.split(';');
  for (const parte of partes) {
    const [clave, ...resto] = parte.trim().split('=');
    if (clave === name) {
      return resto.join('=');
    }
  }
  return null;
}

/**
 * La decisión guardada, o `null` si no se ha decidido nada.
 *
 * `null` **no** es «ha rechazado»: es «no se ha preguntado o no ha contestado», y de esa diferencia
 * depende que se pueda enseñar el aviso otra vez sin tratar a nadie como si hubiera dicho que no.
 */
export function readConsent(): ConsentDecisionState | null {
  const crudo = readCookie(CONSENT_COOKIE);
  if (crudo === null) {
    return null;
  }
  const encontrado = PATRON.exec(crudo.trim());
  if (encontrado === null) {
    return null;
  }
  const segundos = Number(encontrado[4]);
  if (!Number.isFinite(segundos)) {
    return null;
  }
  const decidido = new Date(segundos * 1000);
  if (Number.isNaN(decidido.getTime())) {
    return null;
  }
  if (Date.now() - decidido.getTime() > CONSENT_DAYS * 24 * 60 * 60 * 1000) {
    // Caducada: hay que volver a preguntar. Se trata como si no hubiera decisión.
    return null;
  }
  return {
    policyVersion: Number(encontrado[1]),
    analytics: encontrado[2] === '1',
    preferences: encontrado[3] === '1',
    decidedAt: decidido,
  };
}

/** ¿Hay permiso para este fin? Lo necesario siempre; lo demás, solo si se concedió. */
export function isGranted(purpose: Purpose, decision = readConsent()): boolean {
  if (purpose === 'necessary') {
    return true;
  }
  if (decision === null) {
    return false;
  }
  return purpose === 'analytics' ? decision.analytics : decision.preferences;
}

/** Guarda la decisión en su cookie. Se pone **igual** al aceptar y al rechazar: la misma llamada. */
export function writeConsent(decision: {
  policyVersion: number;
  analytics: boolean;
  preferences: boolean;
}): ConsentDecisionState {
  const decidido = new Date();
  const valor =
    `v${String(decision.policyVersion)}` +
    `.a${decision.analytics ? '1' : '0'}` +
    `.p${decision.preferences ? '1' : '0'}` +
    `.t${String(Math.floor(decidido.getTime() / 1000))}`;
  document.cookie =
    `${CONSENT_COOKIE}=${valor}; Max-Age=${String(CONSENT_DAYS * 24 * 60 * 60)}; Path=/; SameSite=Lax`;
  return {
    policyVersion: decision.policyVersion,
    analytics: decision.analytics,
    preferences: decision.preferences,
    decidedAt: decidido,
  };
}

/**
 * Escribe una cookie **no necesaria**, y solo si hay permiso para su fin.
 *
 * Devuelve si se ha escrito. Una llamada sin permiso no es un error: es la aplicación diciendo que no
 * a algo que no puede hacer, y quien la llame no tiene que comprobar nada antes.
 */
export function setNonEssentialCookie(
  name: string,
  value: string,
  purpose: Exclude<Purpose, 'necessary'>,
  days: number,
): boolean {
  if (name === CONSENT_COOKIE) {
    // La cookie de la decisión no se escribe por aquí: la escribe `writeConsent`, después de decidir.
    return false;
  }
  if (!isGranted(purpose)) {
    return false;
  }
  document.cookie =
    `${name}=${value}; Max-Age=${String(days * 24 * 60 * 60)}; Path=/; SameSite=Lax`;
  return true;
}

/** Borra una cookie no necesaria: se usa al rechazar, para no dejar lo puesto antes de aceptar. */
export function clearNonEssentialCookie(name: string): void {
  if (name === CONSENT_COOKIE) {
    return;
  }
  document.cookie = `${name}=; Max-Age=0; Path=/; SameSite=Lax`;
}

/** El tamaño de texto de lectura, si hay permiso para recordarlo. `null` si no lo hay. */
export function readReadingScale(): number | null {
  if (!isGranted('preferences')) {
    return null;
  }
  const crudo = readCookie(PREFERENCES_COOKIE);
  if (crudo === null) {
    return null;
  }
  const valor = Number(crudo);
  return Number.isFinite(valor) && valor >= 0.8 && valor <= 1.6 ? valor : null;
}

/** Recuerda el tamaño de texto. **Solo si hay permiso**: si no, no se guarda nada y no pasa nada. */
export function rememberReadingScale(scale: number): boolean {
  return setNonEssentialCookie(PREFERENCES_COOKIE, scale.toFixed(2), 'preferences', 365);
}
