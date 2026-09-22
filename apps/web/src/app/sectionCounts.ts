import { useConflictingQuestions, useOppositions, usePendingActions, useReviewQueue } from '../api/queries';

/**
 * Los contadores de la navegación (07_UI-UX §2).
 *
 * La especificación pide cuatro: `[pendientes]` en Bandeja, `[conflictos]` en Preguntas, `[vencidos]`
 * en Errores y `[revisar]` en Cambios. No son decoración: son la respuesta a «¿dónde me espera
 * trabajo?» sin tener que entrar pantalla por pantalla, que es la mitad de la experiencia sencilla.
 *
 * Cada cifra sale de **donde ya se cuenta**: el resumen de pendientes (avisos e importaciones sin
 * resolver y cambios sin confirmar), la cola de repaso —que es la misma que alimenta la tarjeta
 * «Siguiente tarea» de Inicio— y el total que sirve el propio banco. Aquí no se cuenta nada a mano ni
 * se suman cosas distintas de sitios distintos para que el número cuadre.
 */

export interface SectionCount {
  /** El número que se enseña. Nunca se enseña un cero: un contador a cero es ruido. */
  readonly count: number;
  /** Qué son esos números, para quien no ve la insignia (lectores de pantalla). */
  readonly label: string;
}

/** Los contadores por ruta de la navegación; solo aparecen las rutas que tienen algo. */
export type SectionCounts = Readonly<Record<string, SectionCount>>;

export function useSectionCounts(): SectionCounts {
  const oppositions = useOppositions();
  const active = oppositions.data?.find((opposition) => opposition.active) ?? null;
  const pendientes = usePendingActions();
  const repaso = useReviewQueue(active?.id ?? null);
  const conflictos = useConflictingQuestions();

  const contadores: Record<string, SectionCount> = {};

  // Bandeja: lo que pide una mirada en la bandeja son las incidencias de importación sin resolver
  // —los ficheros que no entraron y por qué—, no los lotes que ya terminaron bien.
  const avisos = pendientes.data?.actions.find((accion) => accion.key === 'importaciones')?.count ?? 0;
  if (avisos > 0) {
    contadores['/bandeja'] = { count: avisos, label: `${avisos} avisos o errores de importación` };
  }

  const enConflicto = conflictos.data?.total ?? 0;
  if (enConflicto > 0) {
    contadores['/preguntas'] = {
      count: enConflicto,
      label: `${enConflicto} preguntas en conflicto`,
    };
  }

  const vencidos = repaso.data?.stats.due ?? 0;
  if (vencidos > 0) {
    contadores['/errores'] = { count: vencidos, label: `${vencidos} repasos vencidos` };
  }

  const cambios = pendientes.data?.actions.find((accion) => accion.key === 'cambios')?.count ?? 0;
  if (cambios > 0) {
    contadores['/cambios'] = { count: cambios, label: `${cambios} cambios sin confirmar` };
  }

  return contadores;
}
