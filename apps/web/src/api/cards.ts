/**
 * Las tarjetas de repaso, del lado del alumno (M3 de la fase 3).
 *
 * **Tres llamadas y nada más**: lo que vence, la cola del día y responder una tarjeta. **Generar
 * tarjetas no es una llamada de la pantalla**: se hace por su herramienta, y cuando use el modelo
 * costará dinero, así que no va escondido detrás de un botón que se pulsa por curiosidad.
 */
import { apiFetch } from './client';

/** Las cuatro respuestas de SM-2, tal como las nombra el dominio. */
export type Respuesta = 'otra_vez' | 'dificil' | 'bien' | 'facil';

/** Una tarjeta tal como viaja por la API. */
export interface Tarjeta {
  id: string;
  front: string;
  back: string;
  citation: string | null;
  due_at: string;
  interval_days: number;
  repetitions: number;
}

/** La cola del día: **las tarjetas y el total**, que son dos cosas distintas. */
export interface ColaDeTarjetas {
  tarjetas: Tarjeta[];
  /** **Los fallos vencidos**, entrelazados con las tarjetas y dentro del mismo tope. */
  fallos: FalloVencido[];
  total: number;
}

/** Cuántas vencen, sin traerlas: lo que la pantalla enseña antes de empezar. */
export interface Vencen {
  vencen: number;
}

export async function fetchVencen(): Promise<Vencen> {
  return apiFetch<Vencen>('/cards/pending');
}

export async function fetchCola(): Promise<ColaDeTarjetas> {
  return apiFetch<ColaDeTarjetas>('/cards/queue');
}

/**
 * Responde una tarjeta y devuelve la misma **con su nueva fecha de vuelta**.
 *
 * **La fecha la decide el servidor**: SM-2 no se ejecuta en el navegador, entre otras cosas porque el
 * intervalo depende del historial de la tarjeta y no de lo que el alumno ve.
 */
export async function answerCard(cardId: string, respuesta: Respuesta): Promise<Tarjeta> {
  return apiFetch<Tarjeta>(`/cards/${cardId}/answer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ respuesta }),
  });
}

/**
 * **Corrige un fallo de la cola del día** y devuelve si estaba bien, qué letra valía y por qué.
 *
 * **La explicación llega con la corrección, no antes**: el servidor no la manda hasta que hay una
 * respuesta elegida, que es lo mismo que hace un test.
 */
export async function corregirFallo(
  questionVersionId: string,
  optionKey: string,
): Promise<CorreccionDeFallo> {
  return apiFetch<CorreccionDeFallo>(`/cards/queue/failures/${questionVersionId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ option_key: optionKey }),
  });
}

/** Un fallo vencido tal como lo sirve la cola: **sin la clave**. */
export interface FalloVencido {
  question_version_id: string;
  stem: string;
  options: { key: string; text: string }[];
}

/** La corrección de un fallo. */
export interface CorreccionDeFallo {
  correct: boolean;
  correct_option_keys: string[];
  explanation: string | null;
  citation: string | null;
}
