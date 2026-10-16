import { useEffect, useState } from 'react';

import type { StudentNoteChapter } from '../../api/studentStudy';

/**
 * Los capítulos de los apuntes: leer la dirección y decidir qué capítulo se abre (F35, §3.1).
 *
 * Un tema del programa son varios **epígrafes oficiales** y cada uno tiene sus apartados. La pantalla
 * sirve **un capítulo cada vez** —servirlos todos fue lo que hizo que I.1 midiera 314.000 px de alto—
 * y eso obliga a resolver tres cosas que antes no existían, porque el tema entero estaba en la
 * página:
 *
 * 1. **qué capítulo se sirve**: el de `?capitulo=`, o el primero;
 * 2. **qué capítulo contiene un anclaje**: `#apartado-osi-capas` puede estar en un capítulo que no es
 *    el que se ha abierto, y entonces hay que abrir el suyo. Sin esto, un enlace guardado —el aviso de
 *    la bandeja, la ficha de una pregunta, una marca del navegador— dejaría al alumno en un capítulo
 *    donde su párrafo no está;
 * 3. **qué capítulo es el «actual»** en el índice, que es lo que se marca.
 *
 * Las tres viven aquí y no en la pantalla porque son lógica, no dibujo: así se prueban sin navegador.
 */

/** El anclaje de una dirección (`#apartado-osi-capas` → `osi-capas`); vacío si no lo hay. */
export function anclaDeLaDireccion(hash: string): string {
  if (!hash.startsWith('#')) {
    return '';
  }
  try {
    return decodeURIComponent(hash.slice(1)).replace(/^apartado-/, '');
  } catch {
    // Un ancla con un porcentaje mal formado no es una dirección que se pueda usar: se ignora.
    return '';
  }
}

/** El código del capítulo que contiene ese apartado, o `null` si no lo contiene ninguno. */
export function capituloQueContiene(
  chapters: readonly StudentNoteChapter[],
  ancla: string,
): string | null {
  if (ancla === '') {
    return null;
  }
  for (const capitulo of chapters) {
    if (capitulo.sections.some((apartado) => apartado.anchor === ancla)) {
      return capitulo.code;
    }
  }
  return null;
}

/**
 * El capítulo que hay que abrir de verdad, o `null` si la dirección ya dice el que se sirvió.
 *
 * Manda el **anclaje** sobre el `capitulo` pedido: es más específico y es el que lleva la dirección
 * de un aviso o de una pregunta fallada. Y si el `capitulo` pedido ya no existe (el programa se
 * reorganizó), el servidor ha servido otro y la dirección se corrige al que sirvió de verdad: un
 * enlace a un epígrafe que ya no está tiene que llevar a leer, no a un error.
 */
export function capituloQueAbrir(datos: {
  pedido: string | null;
  servido: string | null;
  delAncla: string | null;
}): string | null {
  const { pedido, servido, delAncla } = datos;
  if (servido === null) {
    return null;
  }
  if (delAncla !== null && delAncla !== servido) {
    return delAncla;
  }
  if (pedido !== null && pedido !== servido) {
    return servido;
  }
  return null;
}

/** Un apartado con su distancia al borde de arriba de la ventana. */
export interface PosicionDeApartado {
  anchor: string;
  top: number;
}

/**
 * El apartado que se está leyendo: el último cuyo principio ya ha pasado el límite.
 *
 * Es la función pura de la marca del índice; el gancho de abajo le da las posiciones reales. Se
 * separa para poder probarla con posiciones escritas a mano: en jsdom no hay maquetación y todas las
 * `getBoundingClientRect` valen cero.
 */
export function apartadoALaVista(
  posiciones: readonly PosicionDeApartado[],
  limite: number,
): string | null {
  let elegido: string | null = null;
  for (const { anchor, top } of posiciones) {
    if (top <= limite) {
      elegido = anchor;
    }
  }
  return elegido ?? (posiciones[0]?.anchor ?? null);
}

/** A qué altura de la ventana se considera que un apartado «ya ha empezado». */
const LIMITE_DE_LECTURA = 0.35;

/**
 * El apartado que se está leyendo, mirando el scroll de verdad.
 *
 * No hay `IntersectionObserver` a propósito: con un umbral hace falta contar entradas visibles y
 * decidir a mano cuál manda, y con el scroll son cuatro líneas y una sola regla. `setState` con el
 * mismo valor no vuelve a pintar, así que escuchar cada `scroll` no cuesta nada.
 *
 * La primera medida va en un `requestAnimationFrame` y no en el cuerpo del efecto: medir es leer la
 * maquetación, y hacerlo en el mismo paso que el pintado es lo que React desaconseja (y la regla
 * `react-hooks/set-state-in-effect` marca). Con el fotograma siguiente, la página ya está medida.
 */
export function useApartadoALaVista(anclas: readonly string[]): string | null {
  const clave = anclas.join('|');
  const [actual, setActual] = useState<string | null>(null);

  useEffect(() => {
    const lista = clave === '' ? [] : clave.split('|');
    if (lista.length === 0) {
      return;
    }
    const medir = (): void => {
      const posiciones = lista
        .map((anchor) => {
          const elemento = document.getElementById(`apartado-${anchor}`);
          return elemento === null ? null : { anchor, top: elemento.getBoundingClientRect().top };
        })
        .filter((posicion): posicion is PosicionDeApartado => posicion !== null);
      setActual(apartadoALaVista(posiciones, window.innerHeight * LIMITE_DE_LECTURA));
    };
    const primerFotograma = window.requestAnimationFrame(medir);
    window.addEventListener('scroll', medir, { passive: true });
    window.addEventListener('resize', medir);
    return () => {
      window.cancelAnimationFrame(primerFotograma);
      window.removeEventListener('scroll', medir);
      window.removeEventListener('resize', medir);
    };
  }, [clave]);

  // Sin apartados no hay nada que marcar, y se dice aquí y no con un `setState` en el efecto: el
  // valor se deduce del que se está leyendo, así que no hay dos fuentes para lo mismo.
  return clave === '' ? null : actual;
}
