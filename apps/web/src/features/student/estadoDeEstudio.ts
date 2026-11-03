/**
 * El estado de estudio de un tema (O2): una etiqueta, no una nota.
 *
 * Sirve para leer el índice de un vistazo —qué está sin empezar, qué en marcha y qué ya se sostiene—
 * y por eso vive en un solo sitio: el umbral es una decisión de interfaz y no puede acabar distinto
 * en cada pantalla.
 *
 * **No es una calificación ni un pronóstico de aprobado.** No se guarda, no viaja a la API y no
 * cambia con el paso del tiempo: se calcula con lo que ya se contestó.
 */

export type EstadoDeEstudio = 'sin-empezar' | 'en-curso' | 'afianzado';

/** Lo mínimo que hace falta del tema; así vale también para el progreso de un bloque. */
export interface DatosDeEstudio {
  answered: number;
  accuracy: number | null;
  due_reviews: number;
}

/**
 * Sin contestar no hay estado que dar. Con contestaciones y nada corregido, está en curso. Y solo se
 * llama afianzado cuando hay acierto medido, alto y sin repasos vencidos: si algo vence hoy, por bien
 * contestado que esté, todavía se está sosteniendo.
 */
export function estadoDeEstudio(datos: DatosDeEstudio): EstadoDeEstudio {
  if (datos.answered === 0) {
    return 'sin-empezar';
  }
  if (datos.accuracy !== null && datos.accuracy >= 0.8 && datos.due_reviews === 0) {
    return 'afianzado';
  }
  return 'en-curso';
}

const ETIQUETAS: Record<EstadoDeEstudio, string> = {
  'sin-empezar': 'Sin empezar',
  'en-curso': 'En curso',
  afianzado: 'Afianzado',
};

export function etiquetaDeEstudio(estado: EstadoDeEstudio): string {
  return ETIQUETAS[estado];
}
