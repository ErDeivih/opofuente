import type { components } from '@opofuente/contracts';

const DEFAULT_BASE_URL = 'http://127.0.0.1:8765';

export type ProblemDetail = components['schemas']['ProblemDetail'];

/** Error de la API con el cuerpo RFC 9457 ya interpretado. */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly problem: ProblemDetail | null;

  constructor(
    message: string,
    options: { status: number; code: string; problem: ProblemDetail | null },
  ) {
    super(message);
    this.name = 'ApiError';
    this.status = options.status;
    this.code = options.code;
    this.problem = options.problem;
  }
}

export function apiBaseUrl(): string {
  const configured = import.meta.env.VITE_API_BASE_URL;
  return typeof configured === 'string' && configured.length > 0 ? configured : DEFAULT_BASE_URL;
}

/**
 * Cliente HTTP mínimo. Las páginas no llaman a `fetch` directamente: usan los hooks de
 * `src/api/queries.ts`, que pasan por aquí (02_ARCHITECTURE §4).
 */
export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl()}${path}`, {
    ...init,
    headers: { Accept: 'application/json', ...init?.headers },
  });

  const contentType = response.headers.get('content-type') ?? '';

  if (!response.ok) {
    let problem: ProblemDetail | null = null;
    if (contentType.includes('application/problem+json')) {
      problem = (await response.json()) as ProblemDetail;
    }
    throw new ApiError(problem?.detail ?? `La API respondió ${response.status}`, {
      status: response.status,
      code: problem?.code ?? 'unknown',
      problem,
    });
  }

  return (await response.json()) as T;
}
