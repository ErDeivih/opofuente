import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

/**
 * Llevar la vista al apartado que dice la dirección (`…/temario/IV.7#apartado-redes-tcpip`).
 *
 * Por qué existe esto y no basta con el ancla del navegador: los apuntes de un tema **llegan por la
 * API después del primer pintado**, así que cuando el navegador busca `#apartado-redes-tcpip` el
 * elemento todavía no está y el desplazamiento se queda en el principio de la página. Medido con
 * Playwright el 11-oct-2026, con el apartado a 5.894 px: `scrollY` seguía en 0.
 *
 * Desde dónde se llega da igual (el índice del tema, la bandeja de avisos del panel): lo que hace
 * falta es que **la dirección manda**, y que si el elemento aparece un poco más tarde se vuelva a
 * intentar. Eso es lo que hace este efecto: busca el elemento, y si no está, lo reintenta mientras
 * haya algo que esperar. Se rinde a los 5 segundos para no dejar un bucle vivo en una pantalla que
 * nunca va a tener ese apartado. Y una vez colocado, **revisa** que siga colocado: la página crece
 * después (las fuentes, las barras de las tablas) y el apartado se iría hacia abajo.
 *
 * No toca ninguna pantalla: se monta en el marco del alumno, con el resto del encaminamiento.
 */
const ESPERA_MAXIMA_MS = 5000;

/**
 * Cuántas veces se vuelve a colocar la vista después de haberla colocado, y cada cuánto.
 *
 * Hace falta porque el apartado se coloca **antes de que la página acabe de medirse**: el texto llega
 * en `Source Serif 4`, que se carga después, y al entrar cambia el alto de todos los párrafos de
 * arriba —y las tablas anchas ganan su barra de desplazamiento—. Medido con los datos reales: la
 * primera colocación dejaba el párrafo a **2.760 px** por debajo, y con estas revisiones acaba a la
 * vista. Son cuatro comprobaciones y ninguna deja un bucle vivo.
 */
const REVISIONES = 4;

/** Lo que se considera «colocado»: el filo del apartado en el filo de arriba de la ventana. */
const TOLERANCIA_PX = 8;

/** El identificador que busca un ancla: `#apartado-redes-tcpip` → `apartado-redes-tcpip`. */
function idDelAncla(hash: string): string {
  try {
    return decodeURIComponent(hash.replace(/^#/, ''));
  } catch {
    // Un ancla con un porcentaje mal formado no es una dirección que se pueda usar: se ignora.
    return '';
  }
}

/**
 * El elemento del apartado, con y sin el prefijo `apartado-`.
 *
 * La convención de la página es `id="apartado-<anclaje>"` y los enlaces de la aplicación la escriben
 * entera (`/temario/IV.7?capitulo=IV.7.2#apartado-udp`). Pero un enlace **guardado** puede traer el
 * anclaje pelado —así lo construía «Ver en apuntes» del resultado hasta F35, que era el defecto
 * medido: `#osi-capas` no bajaba a ninguna parte porque el elemento se llama `apartado-osi-capas`—,
 * y una marca del navegador de antes de este cambio no se puede arreglar desde el servidor. Aceptar
 * las dos formas cuesta una línea y evita que ese enlace vuelva a quedarse arriba.
 */
function elementoDelApartado(id: string): HTMLElement | null {
  return document.getElementById(id) ?? document.getElementById(`apartado-${id}`);
}

export function useApartadoDeLaDireccion(): void {
  const { hash, pathname, search } = useLocation();

  useEffect(() => {
    const id = idDelAncla(hash);
    if (id === '') {
      return;
    }

    let intentos = 0;
    let revisiones = 0;
    let pendiente = 0;

    const colocar = (elemento: HTMLElement): void => {
      elemento.scrollIntoView({ block: 'start' });
    };

    /** Vuelve a colocar la vista si la página ha crecido y el apartado se ha ido hacia abajo. */
    const revisar = (elemento: HTMLElement): void => {
      const arriba = elemento.getBoundingClientRect().top;
      if (Math.abs(arriba) > TOLERANCIA_PX) {
        colocar(elemento);
      }
      revisiones += 1;
      if (revisiones < REVISIONES) {
        pendiente = window.setTimeout(() => {
          revisar(elemento);
        }, 120 * revisiones);
      }
    };

    const buscar = (): void => {
      const elemento = elementoDelApartado(id);
      if (elemento !== null) {
        colocar(elemento);
        revisar(elemento);
        return;
      }
      intentos += 1;
      if (intentos * 100 < ESPERA_MAXIMA_MS) {
        pendiente = window.setTimeout(buscar, 100);
      }
    };
    buscar();

    return () => {
      window.clearTimeout(pendiente);
    };
    // `search` entra en las dependencias desde que los apuntes se leen por capítulos (F35): cambiar el
    // capítulo de la dirección **cambia lo que hay en la página**, así que hay que volver a buscar el
    // ancla aunque la almohadilla sea la misma. Sin esto, una carga lenta podía agotar los cinco
    // segundos de reintentos antes de que llegara el capítulo que contiene el párrafo.
  }, [hash, pathname, search]);
}
