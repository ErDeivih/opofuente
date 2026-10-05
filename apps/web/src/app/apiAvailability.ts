import { useSyncExternalStore } from 'react';

import { isApiUnavailable } from '../api/client';

/**
 * ¿Está la API sin responder?
 *
 * Cuando no lo está, cada consulta falla con su propio error y la interfaz acababa enseñando ocho
 * avisos «Failed to fetch» en inglés, uno por tarjeta (5 de octubre de 2026). Aquí se guarda **un
 * solo** estado: el cliente de consultas lo enciende al primer fallo de red y la aplicación enseña un
 * aviso único arriba, con qué hacer.
 *
 * Es un almacén de módulo y no un contexto de React a propósito: quien lo enciende es el manejador de
 * errores de TanStack Query, que no es un componente.
 */
let sinApi = false;
const oyentes = new Set<() => void>();

function avisar(): void {
  for (const oyente of oyentes) {
    oyente();
  }
}

export function markApiUnavailable(): void {
  if (!sinApi) {
    sinApi = true;
    avisar();
  }
}

export function clearApiUnavailable(): void {
  if (sinApi) {
    sinApi = false;
    avisar();
  }
}

/** Enciende o apaga el aviso según el error que acaba de llegar. */
export function noteApiError(error: unknown): void {
  if (isApiUnavailable(error)) {
    markApiUnavailable();
  }
}

function subscribe(oyente: () => void): () => void {
  oyentes.add(oyente);
  return () => oyentes.delete(oyente);
}

function snapshot(): boolean {
  return sinApi;
}

/** Para las pruebas: deja el aviso apagado entre casos. */
export function resetApiAvailability(): void {
  clearApiUnavailable();
}

export function useApiUnavailable(): boolean {
  return useSyncExternalStore(subscribe, snapshot, snapshot);
}
