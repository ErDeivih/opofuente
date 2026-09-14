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

export function apiBaseUrl(): string {
  const configured = import.meta.env.VITE_API_BASE_URL;
  return typeof configured === 'string' && configured.length > 0 ? configured : DEFAULT_BASE_URL;
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
  const response = await fetch(`${apiBaseUrl()}${path}`, {
    ...init,
    headers: { Accept: 'application/json', ...init?.headers },
  });

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
