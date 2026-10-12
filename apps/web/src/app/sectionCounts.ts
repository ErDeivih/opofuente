import {
  useConflictingQuestions,
  useNoteReportCounters,
  useOppositions,
  usePendingActions,
  useReviewQueue,
} from '../api/queries';

/**
 * Los contadores del menú de administración (07_UI-UX §2, movidos a `/admin` en F1).
 *
 * Son la respuesta a «¿dónde me espera trabajo?» sin tener que entrar pantalla por pantalla: avisos
 * de importación sin resolver, preguntas en conflicto, repasos vencidos y cambios sin confirmar. Eso
 * es trabajo del propietario, así que viven en el panel y **no** en la barra del alumno, que solo
 * tiene que saber qué estudiar.
 *
 * Cada cifra sale de **donde ya se cuenta**: el resumen de pendientes (avisos e importaciones sin
 * resolver y cambios sin confirmar), la cola de repaso —que es la misma que alimenta la tarjeta
 * «Repasar fallos» de Inicio— y el total que sirve el propio banco. Aquí no se cuenta nada a mano ni
 * se suman cosas distintas de sitios distintos para que el número cuadre.
 */

export interface SectionCount {
  /** El número que se enseña. Nunca se enseña un cero: un contador a cero es ruido. */
  readonly count: number;
  /** Qué son esos números, para quien no ve la insignia (lectores de pantalla). */
  readonly label: string;
}

/** Los contadores por ruta del menú de administración; solo aparecen las rutas que tienen algo. */
export type SectionCounts = Readonly<Record<string, SectionCount>>;

export function useSectionCounts(): SectionCounts {
  const oppositions = useOppositions();
  const active = oppositions.data?.find((opposition) => opposition.active) ?? null;
  const pendientes = usePendingActions();
  const repaso = useReviewQueue(active?.id ?? null);
  const conflictos = useConflictingQuestions();
  const avisosApendientes = useNoteReportCounters();

  const contadores: Record<string, SectionCount> = {};

  // Importaciones: lo que pide una mirada son las incidencias de importación sin resolver —los
  // ficheros que no entraron y por qué—, no los lotes que ya terminaron bien.
  const avisos = pendientes.data?.actions.find((accion) => accion.key === 'importaciones')?.count ?? 0;
  if (avisos > 0) {
    contadores['/admin/importar'] = { count: avisos, label: `${avisos} avisos o errores de importación` };
  }

  const enConflicto = conflictos.data?.total ?? 0;
  if (enConflicto > 0) {
    contadores['/admin/preguntas'] = {
      count: enConflicto,
      label: `${enConflicto} preguntas en conflicto`,
    };
  }

  const vencidos = repaso.data?.stats.due ?? 0;
  if (vencidos > 0) {
    contadores['/admin/errores'] = { count: vencidos, label: `${vencidos} repasos vencidos` };
  }

  const cambios = pendientes.data?.actions.find((accion) => accion.key === 'cambios')?.count ?? 0;
  if (cambios > 0) {
    contadores['/admin/cambios'] = { count: cambios, label: `${cambios} cambios sin confirmar` };
  }

  // Los avisos del alumno (F16): lo que ha marcado como error en los apuntes y nadie ha mirado. Solo
  // los `open`: un aviso «en curso» ya está en la mano de alguien y no espera una decisión.
  const avisosAlumno = avisosApendientes.data?.pending ?? 0;
  if (avisosAlumno > 0) {
    contadores['/admin/avisos'] = {
      count: avisosAlumno,
      label: `${avisosAlumno} avisos de los apuntes sin mirar`,
    };
  }

  return contadores;
}
