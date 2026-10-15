import type { components } from '@opofuente/contracts';

import { apiFetch } from './client';

/**
 * La plataforma desplegable, por la API (§8 a §11 del objetivo vivo).
 *
 * **Las banderas se preguntan, no se suponen.** Este módulo no lleva ninguna constante que diga si
 * hay cuentas o legales: eso lo contesta `GET /api/v1/platform/policy` en cada arranque, porque la
 * web se construye una vez y se sirve en varias configuraciones. Una bandera dentro del paquete
 * obligaría a construir dos veces la misma aplicación para probar los dos casos.
 *
 * **El cliente de las escrituras pone `Content-Type`**, y para las cuentas hace falta algo más que
 * en el resto: la cookie de sesión. Eso se resuelve en `client.ts` (`setApiCredentials`), que la
 * enciende solo cuando la política dice que hay cuentas.
 */

export type PlatformPolicy = components['schemas']['PlatformPolicySchema'];
export type LegalBundle = components['schemas']['LegalBundleSchema'];
export type LegalDocument = components['schemas']['LegalDocumentSchema'];
export type DataInventory = components['schemas']['DataInventorySchema'];
export type CookiesDocument = components['schemas']['CookiesSchema'];
export type ConsentState = components['schemas']['ConsentStateSchema'];
export type ConsentDecision = components['schemas']['ConsentDecisionSchema'];
export type AccountAccepted = components['schemas']['AccountAcceptedSchema'];
export type AccountMe = components['schemas']['AccountMeSchema'];
export type AccountClosed = components['schemas']['AccountClosedSchema'];
export type AccountSessions = components['schemas']['AccountSessionsSchema'];
export type Payments = components['schemas']['PaymentsSchema'];

const JSON_HEADERS = { 'Content-Type': 'application/json' };

/** Qué está encendido en esta instalación. Es la primera llamada de la aplicación. */
export function getPlatformPolicy(): Promise<PlatformPolicy> {
  return apiFetch<PlatformPolicy>('/api/v1/platform/policy');
}

/** Los tres textos legales, con lo que falta por rellenar del titular. */
export function getLegalBundle(): Promise<LegalBundle> {
  return apiFetch<LegalBundle>('/api/v1/legal/documents');
}

/** Un texto legal por su nombre corto. */
export function getLegalDocument(key: string): Promise<LegalDocument> {
  return apiFetch<LegalDocument>(`/api/v1/legal/documents/${encodeURIComponent(key)}`);
}

/** Qué datos se recogen, para qué, dónde y cuánto tiempo. */
export function getDataInventory(): Promise<DataInventory> {
  return apiFetch<DataInventory>('/api/v1/legal/data-inventory');
}

/** Las cookies de la aplicación, con lo que el servidor pide que se acepte. */
export function getCookiesDocument(): Promise<CookiesDocument> {
  return apiFetch<CookiesDocument>('/api/v1/legal/cookies');
}

/** Lo decidido sobre las cookies, o `null` si todavía no se ha decidido nada. */
export function getConsent(): Promise<ConsentState | null> {
  return apiFetch<ConsentState | null>('/api/v1/legal/consent');
}

/** Guarda la decisión. Aceptar y rechazar usan **la misma llamada**: solo cambian dos booleanos. */
export function decideConsent(decision: ConsentDecision): Promise<ConsentState> {
  return apiFetch<ConsentState>('/api/v1/legal/consent', {
    method: 'POST',
    headers: JSON_HEADERS,
    body: JSON.stringify(decision),
  });
}

/** Cuenta una pantalla o una acción. El servidor decide si hay permiso; la pantalla no lo finge. */
export function recordAnalyticsEvent(name: string, label: string): Promise<void> {
  return apiFetch<void>('/api/v1/analytics/events', {
    method: 'POST',
    headers: JSON_HEADERS,
    body: JSON.stringify({ name, label }),
  });
}

/** Qué pagos hay: ninguno, con la propuesta escrita. */
export function getPayments(): Promise<Payments> {
  return apiFetch<Payments>('/api/v1/payments/plans');
}

/** El alta. La respuesta es la misma exista o no la dirección: no se puede deducir de aquí. */
export function registerAccount(email: string, password: string): Promise<AccountAccepted> {
  return apiFetch<AccountAccepted>('/api/v1/accounts/register', {
    method: 'POST',
    headers: JSON_HEADERS,
    body: JSON.stringify({ email, password }),
  });
}

/** El acceso. La sesión llega por una cookie `HttpOnly`, no por el cuerpo. */
export function loginAccount(email: string, password: string): Promise<AccountMe> {
  return apiFetch<AccountMe>('/api/v1/accounts/login', {
    method: 'POST',
    headers: JSON_HEADERS,
    body: JSON.stringify({ email, password }),
  });
}

/** Cerrar la sesión de esta pestaña. */
export function logoutAccount(): Promise<void> {
  return apiFetch<void>('/api/v1/accounts/logout', { method: 'POST' });
}

/** Quién soy. Responde 401 si no hay sesión: es lo que la guarda de rutas mira. */
export function getMe(): Promise<AccountMe> {
  return apiFetch<AccountMe>('/api/v1/accounts/me');
}

/** Cerrar la cuenta y borrar sus datos. Devuelve cuánto se ha borrado. */
export function closeAccount(): Promise<AccountClosed> {
  return apiFetch<AccountClosed>('/api/v1/accounts/me', { method: 'DELETE' });
}

/** Las sesiones abiertas de esta cuenta. */
export function getSessions(): Promise<AccountSessions> {
  return apiFetch<AccountSessions>('/api/v1/accounts/sessions');
}

/** Cerrar otra sesión (nunca la que se está usando). */
export function revokeSession(sessionId: string): Promise<void> {
  return apiFetch<void>(`/api/v1/accounts/sessions/${encodeURIComponent(sessionId)}`, {
    method: 'DELETE',
  });
}

/** Pedir un enlace para cambiar la contraseña. */
export function requestPasswordReset(email: string): Promise<AccountAccepted> {
  return apiFetch<AccountAccepted>('/api/v1/accounts/password-resets', {
    method: 'POST',
    headers: JSON_HEADERS,
    body: JSON.stringify({ email }),
  });
}

/** Cambiar la contraseña con el enlace. */
export function confirmPasswordReset(token: string, password: string): Promise<unknown> {
  return apiFetch<unknown>('/api/v1/accounts/password-resets/confirm', {
    method: 'POST',
    headers: JSON_HEADERS,
    body: JSON.stringify({ token, password }),
  });
}
