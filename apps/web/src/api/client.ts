import type { components } from '@opofuente/contracts';

const DEFAULT_BASE_URL = 'http://127.0.0.1:8765';

export type ProblemDetail = components['schemas']['ProblemDetail'];

/**
 * Error de la API con el cuerpo RFC 9457 ya interpretado.
 *
 * El parámetro `TProblem` permite declarar el problema concreto que documenta el contrato para
 * un endpoint (por ejemplo `ReadinessProblem`), en lugar de adivinar campos en el consumidor.
 */
export class ApiError<TProblem = ProblemDetail> extends Error {
  readonly status: number;
  readonly code: string;
  readonly problem: TProblem | null;

  constructor(
    message: string,
    options: { status: number; code: string; problem: TProblem | null },
  ) {
    super(message);
    this.name = 'ApiError';
    this.status = options.status;
    this.code = options.code;
    this.problem = options.problem;
  }
}

/** Comprueba si un error es de la API, opcionalmente con un código HTTP concreto. */
export function isApiError<TProblem = ProblemDetail>(
  error: unknown,
  status?: number,
): error is ApiError<TProblem> {
  return error instanceof ApiError && (status === undefined || error.status === status);
}

/**
 * La API no responde: no es un error suyo con su motivo, es que no está ahí.
 *
 * Se distingue del `ApiError` porque lo que hay que decir es otra cosa («arráncala con
 * `scripts\api.ps1`») y porque la interfaz lo enseña **una vez arriba**, no en cada tarjeta.
 */
export class ApiUnavailableError extends Error {
  override readonly cause: unknown;

  constructor(cause: unknown) {
    super('La aplicación no responde: no se puede hablar con la API local.');
    this.name = 'ApiUnavailableError';
    this.cause = cause;
  }
}

/** ¿Este error es «la API no está»? */
export function isApiUnavailable(error: unknown): error is ApiUnavailableError {
  return error instanceof ApiUnavailableError;
}

export const API_UNAVAILABLE_HELP =
  'Arráncala con scripts\\api.ps1 (o scripts\\dev.ps1) y vuelve a intentarlo.';

export function apiBaseUrl(): string {
  const configured = import.meta.env.VITE_API_BASE_URL;
  return typeof configured === 'string' && configured.length > 0 ? configured : DEFAULT_BASE_URL;
}

/**
 * Cómo viajan las credenciales en cada petición.
 *
 * **Por defecto, como siempre**: `same-origin`, que es lo que hace el navegador cuando no se le dice
 * nada, así que ninguna petición de hoy cambia de comportamiento. Se enciende a `include` **solo**
 * cuando la política de la instalación dice que hay cuentas: entonces la cookie de sesión tiene que
 * viajar entre la web (otro puerto, mismo sitio) y la API, y sin esto el navegador no la mandaría.
 *
 * Se cambia con `setApiCredentials` desde el proveedor de la política, que es quien pregunta al
 * servidor qué configuración hay.
 */
let credentialsMode: RequestCredentials = 'same-origin';

export function setApiCredentials(mode: RequestCredentials): void {
  credentialsMode = mode;
}

/**
 * Cliente HTTP mínimo. Las páginas no llaman a `fetch` directamente: usan los hooks de
 * `src/api/queries.ts`, que pasan por aquí (02_ARCHITECTURE §4).
 *
 * El JSON de error se interpreta según el contrato OpenAPI; es el único punto donde se afirma
 * un tipo sin comprobarlo en ejecución, y está cubierto por las pruebas de contrato del backend.
 */
export async function apiFetch<T, TProblem = ProblemDetail>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl()}${path}`, {
      ...init,
      credentials: credentialsMode,
      headers: { Accept: 'application/json', ...init?.headers },
    });
  } catch (error) {
    // Un fallo de red no es un problema de la API con su cuerpo RFC 9457: es que la API no está.
    // Se lanza como error propio para que la interfaz pueda decir **una vez** qué pasa y cómo
    // arrancarla, en vez de ocho tarjetas con «Failed to fetch» en inglés (5 de octubre de 2026).
    throw new ApiUnavailableError(error);
  }

  const contentType = response.headers.get('content-type') ?? '';

  if (!response.ok) {
    let problem: TProblem | null = null;
    if (contentType.includes('application/problem+json')) {
      problem = (await response.json()) as TProblem;
    }
    throw new ApiError<TProblem>(problemText(problem, 'detail', `La API respondió ${response.status}`), {
      status: response.status,
      code: problemText(problem, 'code', 'unknown'),
      problem,
    });
  }

  // Una respuesta puede no traer cuerpo: `DELETE /curriculum-mappings/{id}` responde 204 a propósito
  // (no hay nada que devolver). Leerlo como JSON reventaría en una operación correcta.
  if (response.status === 204 || response.headers.get('content-length') === '0') {
    return undefined as T;
  }

  return (await response.json()) as T;
}

/** Lee un campo de texto del cuerpo de error sin confiar en su forma. */
function problemText(problem: unknown, key: string, fallback: string): string {
  if (problem !== null && typeof problem === 'object' && key in problem) {
    const value = (problem as Record<string, unknown>)[key];
    if (typeof value === 'string') {
      return value;
    }
  }
  return fallback;
}
