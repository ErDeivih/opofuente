/**
 * El último apartado de los apuntes que abrió el alumno, para poder ofrecerle «Seguir leyendo».
 *
 * **Por qué una marca local y no una tabla.** Lo que hay que recordar es «por dónde ibas», y eso no
 * es un dato de la aplicación: es del aparato en el que se está leyendo (el del salón y el del
 * trabajo no van por el mismo sitio). Guardarlo en el servidor exigiría una cuenta, una tabla y un
 * viaje de red para pintar un enlace; guardarlo aquí cuesta cero, no identifica a nadie y **no
 * requiere cuenta**, que es la regla de la zona del alumno: se puede estudiar sin registrarse.
 *
 * Lo que se guarda es lo justo para componer el enlace —el código del tema, el capítulo
 * (`?capitulo=`) y, si se abrió con un ancla, el apartado— más los títulos, para no tener que pedir
 * el tema a la API solo para escribir su nombre. La marca **caduca sola**: la última visita sustituye
 * a la anterior, no se acumula historial.
 *
 * Todo lo que puede fallar, falla hacia «no hay marca»: el almacenamiento local puede estar lleno,
 * prohibido (ventana privada) o devolver basura de una versión anterior, y ninguna de esas cosas
 * puede romper el Inicio.
 */

/** La clave del almacenamiento local. Lleva el prefijo de la aplicación para no chocar con nada. */
const CLAVE = 'opofuente.ultimoApartado';

/** Lo que se recuerda de la última lectura: dónde estaba y cómo se llama. */
export interface UltimoApartado {
  /** El código del tema, tal como va en la dirección: `IV.7`. */
  codigo: string;
  /** El título del tema (contenido del temario). */
  titulo: string;
  /** El código del capítulo abierto: `IV.7.2`. */
  capitulo: string;
  /** El título del capítulo. */
  tituloCapitulo: string;
  /** El ancla del apartado, si se abrió uno en concreto (`osi-capas`), o `null`. */
  apartado: string | null;
  /** El título del apartado, si se abrió uno en concreto, o `null`. */
  tituloApartado: string | null;
}

/** El tope de caracteres por texto: lo que no quepa es basura, no un título. */
const MAX_TEXTO = 300;

function texto(valor: unknown): string | null {
  if (typeof valor !== 'string') {
    return null;
  }
  const limpio = valor.trim();
  return limpio === '' ? null : limpio.slice(0, MAX_TEXTO);
}

/**
 * Guarda la última lectura. No lanza: si el almacenamiento no está disponible, no se recuerda nada y
 * la aplicación sigue funcionando.
 */
export function guardarUltimoApartado(apartado: UltimoApartado): void {
  try {
    if (typeof window === 'undefined' || window.localStorage === undefined) {
      return;
    }
    window.localStorage.setItem(CLAVE, JSON.stringify(apartado));
  } catch {
    // Un almacenamiento lleno o prohibido no es un error que la pantalla deba enseñar: lo único que
    // se pierde es el atajo, y el Temario sigue estando a un clic.
  }
}

/**
 * Lo último leído, o `null` si no hay nada (o lo que hay no tiene la forma esperada).
 *
 * Se valida campo a campo en lugar de confiar en el `JSON.parse`: la marca la escribe una versión
 * anterior de la aplicación y la lee la siguiente, así que puede faltarle un campo o traerlo de otro
 * tipo. Un objeto a medias se descarta entero, porque componer medio enlace llevaría a una pantalla
 * de error.
 */
export function leerUltimoApartado(): UltimoApartado | null {
  let crudo: unknown;
  try {
    if (typeof window === 'undefined' || window.localStorage === undefined) {
      return null;
    }
    const guardado = window.localStorage.getItem(CLAVE);
    if (guardado === null) {
      return null;
    }
    crudo = JSON.parse(guardado);
  } catch {
    return null;
  }
  if (typeof crudo !== 'object' || crudo === null) {
    return null;
  }
  const datos = crudo as Record<string, unknown>;
  const codigo = texto(datos.codigo);
  const titulo = texto(datos.titulo);
  const capitulo = texto(datos.capitulo);
  const tituloCapitulo = texto(datos.tituloCapitulo);
  if (codigo === null || titulo === null || capitulo === null || tituloCapitulo === null) {
    return null;
  }
  return {
    codigo,
    titulo,
    capitulo,
    tituloCapitulo,
    apartado: texto(datos.apartado),
    tituloApartado: texto(datos.tituloApartado),
  };
}

/**
 * La dirección que sigue la lectura: el capítulo abierto y, si se sabe, el apartado concreto.
 *
 * Es la misma forma de dirección que usan el índice del tema y «Ver en apuntes», así que el enlace
 * de Inicio abre el capítulo y baja al párrafo por el mismo camino que los demás.
 */
export function enlaceDeUltimoApartado(apartado: UltimoApartado): string {
  const base = `/temario/${encodeURIComponent(apartado.codigo)}?capitulo=${encodeURIComponent(apartado.capitulo)}`;
  return apartado.apartado === null ? base : `${base}#apartado-${apartado.apartado}`;
}

/** Se olvida la marca. Existe para las pruebas y para poder empezar de cero sin borrar el navegador. */
export function olvidarUltimoApartado(): void {
  try {
    window.localStorage.removeItem(CLAVE);
  } catch {
    // Igual que al guardar: si no se puede, no hay nada que hacer y nada que contar.
  }
}

/** La clave del almacenamiento, para las pruebas que comprueban que no se escribe otra cosa. */
export const CLAVE_ULTIMO_APARTADO = CLAVE;
