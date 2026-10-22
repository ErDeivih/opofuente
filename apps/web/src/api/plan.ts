/**
 * El plan de estudio y «Hoy» (M4 de la fase 3).
 *
 * **Dos llamadas de lectura y una de escritura.** La de hoy es una vista del plan, no un dato aparte:
 * el servidor la calcula con la misma función y la recorta a la semana en curso, así que no pueden
 * decir cosas distintas.
 */
import { apiFetch } from './client';

/** El tipo de una tarea: decide a qué pantalla lleva el botón. */
export type TipoDeTarea = 'leer' | 'test' | 'repaso' | 'simulacro';

export interface Tarea {
  tipo: TipoDeTarea;
  codigo: string | null;
  titulo: string;
  minutos: number;
}

export interface Semana {
  numero: number;
  empieza: string;
  tareas: Tarea[];
}

export interface Plan {
  semanas: Semana[];
  fuera: string[];
  dentro: string[];
  cabe_todo: boolean;
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
}

export async function fetchPlanGuardado(): Promise<PlanGuardado> {
  return apiFetch<PlanGuardado>('/plan');
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
