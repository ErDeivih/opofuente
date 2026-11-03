import type { Tarea } from '../../api/plan';

/**
 * A dónde lleva cada tipo de tarea del plan.
 *
 * **Una tarea de leer lleva a sus apuntes y una de test al test de ese tema**: si todas llevaran a
 * una pantalla genérica, la tarea no se podría tachar «sola», que es lo que pide el hito. Vive aquí
 * y no en cada pantalla para que «Hoy» y el calendario no manden al mismo tipo a sitios distintos.
 */
export function destinoDeTarea(tarea: Tarea): string {
  switch (tarea.tipo) {
    case 'leer':
      return `/temario/${tarea.codigo ?? ''}`;
    case 'test':
      return `/tests?tema=${encodeURIComponent(tarea.codigo ?? '')}`;
    case 'repaso':
      return '/repaso';
    case 'supuesto':
    case 'simulacro':
      return '/simulacros';
  }
}
