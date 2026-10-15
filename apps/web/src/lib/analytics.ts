import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

import { recordAnalyticsEvent } from '../api/platform';
import { usePolicy } from '../app/policy';

/**
 * La analítica propia, contada desde la pantalla (§10 del objetivo vivo).
 *
 * **Aquí no se decide nada.** Se manda el suceso y el servidor contesta: si la analítica está apagada
 * o no hay permiso, responde 409 o 403 y no se cuenta nada. La pantalla **no** comprueba el permiso
 * antes de mandarlo, y es a propósito: una comprobación en la pantalla es una promesa, y la promesa
 * se puede romper; la comprobación del servidor es un hecho. Lo que sí hace la pantalla es no mandar
 * nada cuando la política dice que no hay analítica, para no llenar la consola de errores de algo que
 * nadie ha pedido.
 *
 * **Y nada de identificadores**: no se manda ni quién, ni desde dónde, ni un número de visita. Solo
 * qué pantalla y qué acción, con las etiquetas de una lista cerrada.
 */

/** El nombre de pantalla de cada dirección. Las direcciones con identificador dentro valen por su nombre. */
const PANTALLAS: readonly { patron: RegExp; etiqueta: string }[] = [
  { patron: /^\/$/, etiqueta: 'inicio' },
  { patron: /^\/temario$/, etiqueta: 'temario' },
  { patron: /^\/temario\/[^/]+$/, etiqueta: 'tema' },
  { patron: /^\/tests$/, etiqueta: 'tests' },
  { patron: /^\/test\/[^/]+$/, etiqueta: 'test_en_curso' },
  { patron: /^\/resultado\/[^/]+$/, etiqueta: 'resultado' },
  { patron: /^\/simulacros$/, etiqueta: 'simulacros' },
  { patron: /^\/examenes$/, etiqueta: 'examenes' },
  { patron: /^\/fallos$/, etiqueta: 'fallos' },
  { patron: /^\/progreso$/, etiqueta: 'progreso' },
  { patron: /^\/acceso$/, etiqueta: 'acceso' },
  { patron: /^\/recuperar$/, etiqueta: 'recuperar' },
  { patron: /^\/cuenta$/, etiqueta: 'mi_cuenta' },
  { patron: /^\/legal\/aviso-legal$/, etiqueta: 'aviso_legal' },
  { patron: /^\/legal\/privacidad$/, etiqueta: 'privacidad' },
  { patron: /^\/legal\/cookies$/, etiqueta: 'cookies' },
];

/** El nombre con el que se cuenta una dirección. `null` si no es ninguna de las conocidas. */
export function etiquetaDePantalla(pathname: string, search = ''): string | null {
  if (pathname === '/tests' && search.length > 0) {
    // La pantalla de tests con la elección puesta sigue siendo la misma pantalla; lo que cambia es
    // con qué se abre, y eso no se cuenta: sería contar qué temas estudia alguien.
    return 'tests';
  }
  for (const { patron, etiqueta } of PANTALLAS) {
    if (patron.test(pathname)) {
      return etiqueta;
    }
  }
  return null;
}

/** Cuenta la pantalla cada vez que cambia la dirección. No hace nada si no hay analítica. */
export function usePageView(): void {
  const politica = usePolicy();
  const { pathname, search } = useLocation();

  useEffect(() => {
    if (politica?.analytics.enabled !== true) {
      return;
    }
    const etiqueta = etiquetaDePantalla(pathname, search);
    if (etiqueta === null) {
      return;
    }
    // El error no se enseña: que la analítica falle no puede romper una pantalla de estudio. Si el
    // servidor dice que no hay permiso, no se cuenta y ya está.
    void recordAnalyticsEvent('page_view', etiqueta).catch(() => undefined);
  }, [politica?.analytics.enabled, pathname, search]);
}

/** Cuenta una acción del recorrido. Mismas reglas: la decide el servidor. */
export function contarAccion(etiqueta: string): void {
  void recordAnalyticsEvent('action', etiqueta).catch(() => undefined);
}
