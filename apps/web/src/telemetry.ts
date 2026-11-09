/**
 * Telemetría propia de OpoFuente: qué pantallas se abren y qué errores ve el navegador.
 *
 * Solo existen dos eventos y esta es la lista completa de lo que viaja:
 *
 * - `page_view`: el nombre estable de la pantalla (`inicio`, `bandeja`, …), nunca la URL ni los
 *   identificadores que lleve la ruta;
 * - `error`: ese mismo nombre y un mensaje corto, recortado a 200 caracteres y sin rutas absolutas.
 *
 * Nunca se envía el contenido de documentos, preguntas o respuestas, ni rutas del disco, ni datos
 * de la conexión (IP, `User-Agent`, cookies, `Referer`). El servidor vuelve a sanear y recortar el
 * mensaje como segunda barrera, y los contadores viven en memoria del proceso: se pierden al
 * reiniciar. No hay cuentas ni servicios de terceros.
 *
 * Está activa solo en el build de producción (`import.meta.env.PROD`) o con `VITE_TELEMETRY=on`; en
 * desarrollo y en las pruebas está apagada para no ensuciar la observabilidad de la demo.
 */

import { apiBaseUrl } from './api/client';

/** Nombre estable de pantalla. Debe coincidir con `TelemetryScreen` en la API. */
export type TelemetryScreen =
  | 'inicio'
  | 'bandeja'
  | 'temario'
  | 'tema'
  | 'practica'
  | 'programa'
  | 'biblioteca'
  | 'preguntas'
  | 'estudiar'
  | 'errores'
  | 'cambios'
  | 'ajustes'
  | 'revision'
  | 'buscar'
  | 'no_encontrada';

export type TelemetryEventType = 'page_view' | 'error';

export interface TelemetryEvent {
  readonly type: TelemetryEventType;
  readonly screen: TelemetryScreen;
  readonly message?: string;
}

export interface TelemetryOptions {
  /** Fuerza el envío (o lo apaga) sin mirar el entorno. Las pruebas lo usan; la app no. */
  readonly enabled?: boolean;
  /** URL base de la API. Por defecto, la misma que usa el resto del cliente. */
  readonly baseUrl?: string;
}

/** Ruta del contrato; la misma que `POST /api/v1/telemetry/events`. */
const EVENTS_PATH = '/api/v1/telemetry/events';
const MAX_MESSAGE_CHARS = 200;

/** Rutas fijas → pantalla. Las que llevan identificador se resuelven con expresiones regulares. */
const EXACT_SCREENS: Readonly<Record<string, TelemetryScreen>> = {
  '/': 'inicio',
  '/bandeja': 'bandeja',
  '/temario': 'temario',
  '/programa': 'programa',
  '/biblioteca': 'biblioteca',
  '/preguntas': 'preguntas',
  '/estudiar': 'estudiar',
  '/errores': 'errores',
  '/cambios': 'cambios',
  '/ajustes': 'ajustes',
  '/revision': 'revision',
  '/buscar': 'buscar',
};

const PRACTICE_PATH = /^\/temario\/[^/]+\/practicar$/;
const TOPIC_PATH = /^\/temario\/[^/]+$/;

/** `true` si la telemetría debe enviar. La bandera explícita manda sobre el entorno. */
export function isTelemetryEnabled(
  options: TelemetryOptions = {},
): boolean {
  if (options.enabled !== undefined) {
    return options.enabled;
  }
  return import.meta.env.PROD || import.meta.env.VITE_TELEMETRY === 'on';
}

/**
 * Traduce la ruta actual a un nombre estable. Los identificadores (`/temario/<id>`) se descartan y
 * una ruta desconocida cuenta como `no_encontrada`, nunca como URL.
 */
export function screenForPath(pathname: string): TelemetryScreen {
  const normalized = normalizePath(pathname);
  const exact = EXACT_SCREENS[normalized];
  if (exact !== undefined) {
    return exact;
  }
  if (PRACTICE_PATH.test(normalized)) {
    return 'practica';
  }
  if (TOPIC_PATH.test(normalized)) {
    return 'tema';
  }
  return 'no_encontrada';
}

function normalizePath(pathname: string): string {
  const withoutQuery = pathname.split('?')[0] ?? '';
  const trimmed = withoutQuery.replace(/\/+$/, '');
  return trimmed.length === 0 ? '/' : trimmed;
}

/** Recorta y sanea un mensaje antes de que salga del navegador. */
export function sanitizeMessage(message: string): string {
  // `\p{Cc}` es la categoría Unicode de caracteres de control: sin saltos de línea ni binarios.
  const withoutControl = message.replace(/\p{Cc}/gu, ' ');
  const cleaned = withoutControl
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/\b[a-z]:[\\/][^\s"'<>|]*/gi, '[ruta]')
    .replace(/\\\\[^\s"'<>|]+/g, '[ruta]')
    .replace(/(?<![\w.:/])\/(?:[^\s/"'<>|]+\/)*[^\s/"'<>|]*/g, '[ruta]');
  return cleaned.slice(0, MAX_MESSAGE_CHARS);
}

/** Envía un evento. No lanza nunca: la observabilidad no puede romper la pantalla. */
export function sendTelemetryEvent(event: TelemetryEvent, options: TelemetryOptions = {}): void {
  if (!isTelemetryEnabled(options)) {
    return;
  }
  try {
    const payload = JSON.stringify(event);
    const endpoint = `${options.baseUrl ?? apiBaseUrl()}${EVENTS_PATH}`;
    if (typeof navigator !== 'undefined' && typeof navigator.sendBeacon === 'function') {
      // Blob `text/plain` para que el navegador no tenga que hacer preflight; el cuerpo sigue siendo
      // JSON y la API lo lee igual (no exige `Content-Type: application/json`).
      const queued = navigator.sendBeacon(
        endpoint,
        new Blob([payload], { type: 'text/plain;charset=UTF-8' }),
      );
      if (queued) {
        return;
      }
    }
    void fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: payload,
      keepalive: true,
    }).catch(() => undefined);
  } catch {
    // Un fallo aquí no puede cambiar el comportamiento de la aplicación.
  }
}

/** Cuenta una vista de la pantalla correspondiente a `pathname`. */
export function trackPageView(pathname: string, options: TelemetryOptions = {}): void {
  sendTelemetryEvent({ type: 'page_view', screen: screenForPath(pathname) }, options);
}

/** Cuenta un error con el mensaje ya recortado y saneado. */
export function trackError(message: string, options: TelemetryOptions = {}): void {
  sendTelemetryEvent(
    { type: 'error', screen: currentScreen(), message: sanitizeMessage(message) },
    options,
  );
}

function currentScreen(): TelemetryScreen {
  if (typeof window === 'undefined') {
    return 'no_encontrada';
  }
  return screenForPath(window.location.pathname);
}

/**
 * Instala la captura de `error` sin capturar y `unhandledrejection` como eventos `error`.
 *
 * Devuelve la función de limpieza. Usa `addEventListener` para no pisar `window.onerror` si otro
 * código ya lo usa; el efecto es el mismo y no se pierde ningún fallo de la aplicación.
 */
export function installGlobalErrorTelemetry(options: TelemetryOptions = {}): () => void {
  if (typeof window === 'undefined' || !isTelemetryEnabled(options)) {
    return () => undefined;
  }
  const onError = (event: ErrorEvent): void => {
    if (event.message.length > 0) {
      trackError(event.message, options);
    }
  };
  const onUnhandledRejection = (event: PromiseRejectionEvent): void => {
    trackError(messageFromReason(event.reason), options);
  };
  window.addEventListener('error', onError);
  window.addEventListener('unhandledrejection', onUnhandledRejection);
  return () => {
    window.removeEventListener('error', onError);
    window.removeEventListener('unhandledrejection', onUnhandledRejection);
  };
}

function messageFromReason(reason: unknown): string {
  if (reason instanceof Error) {
    return reason.message;
  }
  if (typeof reason === 'string') {
    return reason;
  }
  // Un objeto arbitrario podría contener contenido de la pantalla: se descarta.
  return 'Promesa rechazada sin mensaje';
}
