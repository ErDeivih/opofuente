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
    // **La ruta se normaliza aquí, en el único sitio por el que pasan todas las llamadas.**
    // La base por defecto es `http://127.0.0.1:8765` **sin** `/api/v1`, y el cliente tiene las
    // dos costumbres: unas llamadas pasan `/api/v1/...` y otras `/plan`, `/explanations/...`.
    // **Las que no llevaban prefijo acababan en `http://127.0.0.1:8765/plan`, que es un 404** —
    // y se vio en el recorrido: la portada no cargaba su plan y ocho pantallas no se pudieron
    // fotografiar. Se acepta la que ya lo trae y se le pone a la que no.
    const ruta = path.startsWith('/api/') ? path : `/api/v1${path}`;
    response = await fetch(`${apiBaseUrl()}${ruta}`, {
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

/**
 * Un fichero que devuelve la API (hoy, el PDF de los apuntes de un tema).
 *
 * Es el hermano binario de `apiFetch` y comparte sus reglas: misma base, mismas credenciales, mismo
 * `ApiUnavailableError` cuando no hay red y mismo `ApiError` con el problema RFC 9457 cuando la
 * respuesta es un error. La diferencia es que no interpreta el cuerpo: lo entrega como `Blob`.
 *
 * `filename` sale de `Content-Disposition`, que el servidor sanea; el navegador **solo lo ve si la
 * API lo expone** con `expose_headers` (CORS), así que puede venir `null` y quien llama decide el
 * nombre de reserva. Se acepta la forma `attachment; filename="…"` y la extendida
 * `filename*=UTF-8''…`; se prefiere la segunda, que es la que lleva acentos sin romperlos.
 */
export async function apiFetchBinary(
  path: string,
  init?: RequestInit,
): Promise<{ blob: Blob; filename: string | null }> {
  let response: Response;
  try {
    const ruta = path.startsWith('/api/') ? path : `/api/v1${path}`;
    response = await fetch(`${apiBaseUrl()}${ruta}`, {
      ...init,
      credentials: credentialsMode,
      headers: { Accept: 'application/pdf', ...init?.headers },
    });
  } catch (error) {
    throw new ApiUnavailableError(error);
  }

  if (!response.ok) {
    const contentType = response.headers.get('content-type') ?? '';
    let problem: ProblemDetail | null = null;
    if (contentType.includes('application/problem+json')) {
      problem = (await response.json()) as ProblemDetail;
    }
    throw new ApiError(problemText(problem, 'detail', `La API respondió ${response.status}`), {
      status: response.status,
      code: problemText(problem, 'code', 'unknown'),
      problem,
    });
  }

  return {
    blob: await response.blob(),
    filename: filenameFromDisposition(response.headers.get('content-disposition')),
  };
}

/** El nombre del fichero que anuncia una cabecera `Content-Disposition`, o `null` si no lo dice. */
export function filenameFromDisposition(header: string | null): string | null {
  if (header === null) {
    return null;
  }
  const extendida = /filename\*=UTF-8''([^;]+)/i.exec(header);
  if (extendida?.[1] !== undefined) {
    try {
      return decodeURIComponent(extendida[1].trim());
    } catch {
      // Una cabecera mal codificada no puede romper la descarga: se prueba con la forma simple.
    }
  }
  const simple = /filename="([^"]+)"/i.exec(header) ?? /filename=([^;]+)/i.exec(header);
  const nombre = simple?.[1]?.trim();
  return nombre === undefined || nombre.length === 0 ? null : nombre;
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
