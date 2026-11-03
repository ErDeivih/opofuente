/**
 * El plan de estudio y «Hoy» (M4 de la fase 3).
 *
 * **Dos llamadas de lectura y una de escritura.** La de hoy es una vista del plan, no un dato aparte:
 * el servidor la calcula con la misma función y la recorta a la semana en curso, así que no pueden
 * decir cosas distintas.
 *
 * **El calendario completo tiene su propia llamada** (`/plan/calendario`): «Hoy» enseña la semana en
 * curso y el plan entero se pide solo cuando se abre esa pantalla, sin cargar doce semanas en la
 * portada.
 */
import { apiFetch } from './client';

/** El tipo de una tarea: decide a qué pantalla lleva el botón. */
export type TipoDeTarea = 'leer' | 'test' | 'repaso' | 'supuesto' | 'simulacro';

export interface Tarea {
  tipo: TipoDeTarea;
  codigo: string | null;
  titulo: string;
  minutos: number;
  /** El bloque del tema, para agrupar sin volver a mirar el temario. */
  bloque_codigo: string | null;
  bloque_titulo: string | null;
}

export interface Semana {
  numero: number;
  empieza: string;
  tareas: Tarea[];
  /** `lectura` o `fase-2`. */
  fase: 'lectura' | 'fase-2';
  /** Lo que se quitó o no cabe en las horas declaradas, dicho en palabras. */
  recortes: string[];
}

/** Un tema que no entra antes del examen, **con su nombre**. */
export interface TemaFuera {
  codigo: string;
  titulo: string;
  bloque_codigo: string;
  bloque_titulo: string;
}

/** El modo sale de los números: un tema por semana o dos, y si con ese ritmo cabe todo. */
export type ModoDeEstudio = 'extensivo' | 'intensivo';

export interface Plan {
  semanas: Semana[];
  fuera: string[];
  dentro: string[];
  cabe_todo: boolean;
  fuera_temas: TemaFuera[];
  modo: ModoDeEstudio;
  temas_por_semana: number;
  planificable: boolean;
  motivo: string | null;
  total_semanas: number;
  semanas_de_lectura: number;
  fase_2_desde: number | null;
}

/** Lo que hay guardado, con todo a `null` si nadie ha puesto la fecha. */
export interface PlanGuardado {
  exam_date: string | null;
  hours_per_week: number | null;
  rest_days: number[];
}

/** La semana en curso, o el motivo de que no haya nada. */
export interface LoDeHoy {
  semana: Semana | null;
  motivos: string[];
  /** Puede faltar si aún no hay plan: el servidor devuelve `null`. */
  modo: ModoDeEstudio | null;
  planificable: boolean;
  motivo: string | null;
  fuera_temas: TemaFuera[];
}

/** Como va el alumno en un bloque, **con la frase ya compuesta**. */
export interface ProgresoDeBloque {
  codigo: string;
  titulo: string;
  leidos: number;
  practicados: number;
  esperados: number;
  total: number;
  vas_bien: boolean;
  frase: string;
}

/** Como va el alumno frente al plan, **con la frase ya compuesta**. */
export interface Progreso {
  leidos: number;
  practicados: number;
  esperados: number;
  total: number;
  vas_bien: boolean;
  frase: string;
  bloques: ProgresoDeBloque[];
}

export async function fetchProgreso(): Promise<Progreso> {
  return apiFetch<Progreso>('/plan/progreso');
}

export async function fetchPlanGuardado(): Promise<PlanGuardado> {
  return apiFetch<PlanGuardado>('/plan');
}

/** El plan entero, semana a semana. Responde `404` si todavía no hay fecha. */
export async function fetchCalendario(): Promise<Plan> {
  return apiFetch<Plan>('/plan/calendario');
}

export async function fetchHoy(): Promise<LoDeHoy> {
  return apiFetch<LoDeHoy>('/plan/hoy');
}

/**
 * Pone la fecha del examen y devuelve el plan ya calculado.
 *
 * **Devuelve el plan y no un `204`**: la pantalla lo necesita para pintarlo, y pedirlo otra vez sería
 * una segunda llamada que puede traer otro reparto.
 */
export async function guardarPlan(
  examDate: string,
  hoursPerWeek: number,
  restDays: number[],
): Promise<Plan> {
  return apiFetch<Plan>('/plan', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      exam_date: examDate,
      hours_per_week: hoursPerWeek,
      rest_days: restDays,
    }),
  });
}
