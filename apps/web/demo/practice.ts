/**
 * Progreso de la demo estática, solo en el navegador.
 *
 * Se guarda un resumen por práctica (`best`, `attempts`, `lastScore`) en `localStorage`; no hay
 * servidor, no se envía nada y limpiar los datos del navegador lo borra todo. Este módulo no toca
 * React para poder probarlo por separado.
 */

export interface PracticeResult {
  readonly best: number;
  readonly attempts: number;
  readonly lastScore: number;
  readonly lastTotal: number;
  readonly updatedAt: string;
}

export type DemoProgress = Readonly<Record<string, PracticeResult>>;

const STORAGE_KEY = 'opofuente-demo-progress-v1';

/** Puntuación directa: aciertos sobre el total, sin penalización (es una demo de práctica). */
export function scoreAnswers(
  answers: Readonly<Record<number, string>>,
  questions: readonly { correct: string }[],
): { correct: number; total: number } {
  let correct = 0;
  questions.forEach((question, index) => {
    if (answers[index] === question.correct) {
      correct += 1;
    }
  });
  return { correct, total: questions.length };
}

function storage(): Storage | null {
  try {
    return typeof globalThis.localStorage === 'undefined' ? null : globalThis.localStorage;
  } catch {
    return null;
  }
}

export function loadProgress(): DemoProgress {
  const store = storage();
  if (store === null) {
    return {};
  }
  try {
    const raw = store.getItem(STORAGE_KEY);
    if (raw === null) {
      return {};
    }
    const parsed: unknown = JSON.parse(raw);
    return typeof parsed === 'object' && parsed !== null ? (parsed as DemoProgress) : {};
  } catch {
    return {};
  }
}

export function saveResult(slug: string, correct: number, total: number): PracticeResult {
  const previous = loadProgress()[slug];
  const porcentaje = total === 0 ? 0 : Math.round((correct / total) * 100);
  const resultado: PracticeResult = {
    best: Math.max(previous?.best ?? 0, porcentaje),
    attempts: (previous?.attempts ?? 0) + 1,
    lastScore: correct,
    lastTotal: total,
    updatedAt: new Date().toISOString(),
  };
  const store = storage();
  if (store !== null) {
    const progreso = { ...loadProgress(), [slug]: resultado };
    try {
      store.setItem(STORAGE_KEY, JSON.stringify(progreso));
    } catch {
      // Un navegador sin almacenamiento (modo privado estricto) no rompe la práctica.
    }
  }
  return resultado;
}

export function resetProgress(): void {
  const store = storage();
  if (store !== null) {
    try {
      store.removeItem(STORAGE_KEY);
    } catch {
      // Nada que hacer: la demo sigue funcionando sin persistencia.
    }
  }
}
