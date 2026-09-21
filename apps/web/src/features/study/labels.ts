import type {
  AttemptOutcome,
  Confidence,
  FeedbackName,
  StudySession,
} from '../../api/study';
import { formatScore, type Score } from '../../api/study';
import type { StatusTone } from '../../components/StatusBadge';

/** Nombres de la pantalla para el vocabulario del servidor: la interfaz no lo traduce a otro. */
export const MODE_LABEL: Record<StudySession['mode'], string> = {
  practice: 'práctica',
  error_review: 'repaso de errores',
  official_exam: 'examen oficial',
  mock_exam: 'simulacro',
  diagnostic: 'diagnóstico',
};

export const MODE_TONE: Record<StudySession['mode'], StatusTone> = {
  practice: 'info',
  error_review: 'info',
  official_exam: 'warning',
  // Un simulacro no es un examen oficial (06_QUESTIONS §5): mismo tono de aviso, palabra distinta.
  mock_exam: 'warning',
  diagnostic: 'info',
};

export const STATUS_LABEL: Record<StudySession['status'], string> = {
  draft: 'sin empezar',
  running: 'en marcha',
  finished: 'terminada',
  abandoned: 'abandonada',
};

export const STATUS_TONE: Record<StudySession['status'], StatusTone> = {
  draft: 'info',
  running: 'warning',
  finished: 'ok',
  abandoned: 'blocked',
};

export const FEEDBACK_LABEL: Record<FeedbackName, string> = {
  immediate: 'corrección al responder',
  at_end: 'corrección al terminar',
};

export const OUTCOME_LABEL: Record<AttemptOutcome, string> = {
  correct: 'acertada',
  wrong: 'fallada',
  blank: 'en blanco',
  annulled: 'anulada',
  excluded: 'sin corregir',
  conflicting: 'claves en conflicto',
  unused_reserve: 'reserva sin usar',
};

export const OUTCOME_TONE: Record<AttemptOutcome, StatusTone> = {
  correct: 'ok',
  wrong: 'blocked',
  blank: 'info',
  annulled: 'info',
  excluded: 'warning',
  conflicting: 'warning',
  unused_reserve: 'info',
};

export const CONFIDENCE_LABEL: Record<Confidence, string> = {
  low: 'dudando',
  medium: 'normal',
  high: 'segura',
};

/** Cómo se corrigió una parte, tal como lo declara la convocatoria. */
export const SCORING_LABEL: Record<string, string> = {
  direct: 'puntuación directa (la calificación oficial no está publicada)',
  scaled: 'fórmula publicada de la convocatoria',
  pass_fail: 'apto o no apto, por número de errores',
};

export function scoringLabel(kind: string): string {
  return SCORING_LABEL[kind] ?? kind;
}

/** Veredicto publicado de una parte: `null` significa que no se puede afirmar. */
export function verdictLabel(passed: boolean | null | undefined): string {
  if (passed === null || passed === undefined) {
    return 'no se puede afirmar si se supera';
  }
  return passed ? 'superada' : 'no superada';
}

export function modeLabel(mode: string): string {
  return MODE_LABEL[mode as StudySession['mode']] ?? mode;
}

export function statusLabel(status: string): string {
  return STATUS_LABEL[status as StudySession['status']] ?? status;
}

export function statusTone(status: string): StatusTone {
  return STATUS_TONE[status as StudySession['status']] ?? 'info';
}

export function feedbackLabel(feedback: string): string {
  return FEEDBACK_LABEL[feedback as FeedbackName] ?? feedback;
}

export function outcomeLabel(outcome: string): string {
  return OUTCOME_LABEL[outcome as AttemptOutcome] ?? outcome;
}

export function outcomeTone(outcome: string): StatusTone {
  return OUTCOME_TONE[outcome as AttemptOutcome] ?? 'info';
}

/** Segundos de una sesión en curso, para el cronómetro de la pantalla. */
export function elapsedSeconds(startedAt: string | null, now: number): number {
  if (startedAt === null) {
    return 0;
  }
  const inicio = Date.parse(startedAt);
  if (Number.isNaN(inicio)) {
    return 0;
  }
  return Math.max(0, Math.floor((now - inicio) / 1000));
}

/** Cronómetro en `mm:ss` (o `h:mm:ss` si pasa de una hora). */
export function clock(seconds: number): string {
  const horas = Math.floor(seconds / 3600);
  const minutos = Math.floor((seconds % 3600) / 60);
  const segundos = seconds % 60;
  const dos = (valor: number): string => String(valor).padStart(2, '0');
  return horas > 0
    ? `${String(horas)}:${dos(minutos)}:${dos(segundos)}`
    : `${dos(minutos)}:${dos(segundos)}`;
}

/** Puntuación legible: la fracción exacta con su decimal (ADR-010). */
export function scoreText(score: Score): string {
  return formatScore(score);
}
