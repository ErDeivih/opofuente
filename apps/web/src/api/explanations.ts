import type { components } from '@opofuente/contracts';

import { apiFetch } from './client';

/**
 * La bandeja de explicaciones generadas, para el panel (M1 de la fase 3).
 *
 * Lo que se lee aquí es **la cola de trabajo del propietario**: las explicaciones que un modelo escribió
 * y que nadie ha revisado todavía. **Las privadas y las oficiales no salen nunca** — no las escribió un
 * modelo y no hay nada que aprobar —, y eso lo decide el servidor, no esta pantalla.
 *
 * El enunciado viaja con cada fila para que se pueda revisar sin abrir otra página: aprobar una
 * explicación sin saber de qué pregunta es se hace a ciegas.
 */
export type ExplanationTrayItem = components['schemas']['ExplanationTrayItemSchema'];

/** Las que esperan revisión, de la más antigua a la más reciente. */
export async function fetchPendingExplanations(): Promise<ExplanationTrayItem[]> {
  return apiFetch<ExplanationTrayItem[]>('/explanations/pending');
}

/** Los dos estados a los que se puede llevar una explicación desde la bandeja. */
export type ExplanationDecision = 'reviewed' | 'rejected';

/**
 * Aprueba o rechaza una explicación (M1).
 *
 * **Solo el estado**: el texto y la cita se corrigen por otra ruta, y **regenerar** es otra cosa — pide
 * al modelo una nueva y gasta, así que no se esconde detrás de un cambio de estado.
 *
 * La ruta responde **204 sin cuerpo**, y por eso el tipo es `void`: leer un cuerpo que no viene es la
 * clase de error que se descubre en producción.
 */
export async function decideExplanation(
  explanationId: string,
  decision: ExplanationDecision,
): Promise<void> {
  await apiFetch<void>(`/explanations/${explanationId}/status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status: decision }),
  });
}

