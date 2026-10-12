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
 * nunca va a tener ese apartado.
 *
 * No toca ninguna pantalla: se monta en el marco del alumno, con el resto del encaminamiento.
 */
const ESPERA_MAXIMA_MS = 5000;

/** El identificador que busca un ancla: `#apartado-redes-tcpip` → `apartado-redes-tcpip`. */
function idDelAncla(hash: string): string {
  try {
    return decodeURIComponent(hash.replace(/^#/, ''));
  } catch {
    // Un ancla con un porcentaje mal formado no es una dirección que se pueda usar: se ignora.
    return '';
  }
}

export function useApartadoDeLaDireccion(): void {
  const { hash, pathname } = useLocation();

  useEffect(() => {
    const id = idDelAncla(hash);
    if (id === '') {
      return;
    }

    let intentos = 0;
    let pendiente = 0;
    const buscar = (): void => {
      const elemento = document.getElementById(id);
      if (elemento !== null) {
        elemento.scrollIntoView({ block: 'start' });
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
  }, [hash, pathname]);
}
