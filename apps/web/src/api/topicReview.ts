import type { components } from '@opofuente/contracts';

import { apiFetch } from './client';

/**
 * La cola de revisión de la clasificación (F5): las propuestas de tema sin confirmar y las
 * decisiones que las despachan.
 *
 * Todo lo que se lee aquí viene del contrato generado: la pantalla no declara ni un campo por su
 * cuenta. Y todo se **escribe** por la misma ruta por lotes que usa la clasificación automática
 * (`POST /questions/topics/bulk`), que es la que deja el mapeo y su evento de auditoría: no hay un
 * segundo camino para decidir desde la interfaz.
 */
export type TopicProposalPage = components['schemas']['QuestionTopicProposalPageSchema'];
export type TopicProposalCard = components['schemas']['QuestionTopicProposalsSchema'];
export type TopicProposal = components['schemas']['QuestionTopicProposalSchema'];
export type ProgrammeNodeRef = components['schemas']['ProgrammeNodeRefSchema'];
export type TopicAssignmentReport = components['schemas']['BulkTopicAssignmentReportSchema'];
export type TopicAssignmentResult = components['schemas']['BulkTopicAssignmentResultSchema'];
export type TopicAssignmentRow = components['schemas']['BulkTopicAssignmentSchema'];
export type ExclusionPage = components['schemas']['QuestionExclusionPageSchema'];
export type Exclusion = components['schemas']['QuestionExclusionSchema'];
export type ConflictPage = components['schemas']['QuestionTopicConflictPageSchema'];
export type ConflictCard = components['schemas']['QuestionTopicConflictSchema'];
export type ConflictingTopic = components['schemas']['ConflictingTopicSchema'];

/** El vocabulario del fuera de temario, tal y como lo publica el servidor. */
export type ExclusionReason = Exclusion['reason'];

/** Cuántas tarjetas se piden de la cola de una vez. */
export const PROPOSALS_LIMIT = 50;

/** Cuántas marcas de fuera de temario se leen de una vez. */
export const EXCLUSIONS_LIMIT = 100;

/** Cuántas preguntas en dos temas se leen de una vez. */
export const CONFLICTS_LIMIT = 100;

/**
 * El motivo de un fuera de temario en palabras, para poder marcarlo sin abrir nada.
 *
 * Los dos motivos no son lo mismo y se revisan distinto: uno es material bueno que no cae en este
 * examen y el otro es un enunciado que hay que arreglar. La pantalla los ofrece separados por eso.
 */
export const EXCLUSION_LABELS: Record<ExclusionReason, string> = {
  otra_administracion: 'De otra administración',
  enunciado_roto: 'Enunciado roto',
};

/** Por qué un fuera de temario se retira: asignar un tema levanta la marca. */
export const REASON_PROMOTED = 'aceptada en la revisión de la clasificación';
export const REASON_CHANGED = 'cambiada a mano en la revisión de la clasificación';
export const REASON_EXCLUDED = 'marcada fuera de temario en la revisión de la clasificación';
export const REASON_RETIRED = 'ya tiene tema decidido: sobran las demás propuestas';

export function fetchTopicProposals(offset = 0, limit = PROPOSALS_LIMIT): Promise<TopicProposalPage> {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  return apiFetch<TopicProposalPage>(`/api/v1/question-topic-proposals?${params.toString()}`);
}

/**
 * Aplica un lote de decisiones: aceptar, cambiar de tema o declarar fuera de temario.
 *
 * Una sola llamada por lote y no una por pregunta: el propietario despacha cientos y la ruta está
 * hecha para eso. `retire_others` es lo que impide que una pregunta con dos propuestas acabe con dos
 * temas: al decidir una, las demás se retiran en la misma operación.
 */
export function applyTopicDecisions(rows: TopicAssignmentRow[]): Promise<TopicAssignmentReport> {
  return apiFetch<TopicAssignmentReport>('/api/v1/questions/topics/bulk', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ assignments: rows }),
  });
}

/** Los temas y epígrafes del programa vigente, para poder cambiar el destino a mano. */
export function fetchExclusions(offset = 0, limit = EXCLUSIONS_LIMIT): Promise<ExclusionPage> {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  return apiFetch<ExclusionPage>(`/api/v1/question-exclusions?${params.toString()}`);
}

/**
 * Las preguntas que cuentan en dos temas aceptados a la vez.
 *
 * Es la lectura de lo que quedó torcido antes de esta tanda (catalogación heredada, migraciones y
 * las dos corridas que se pisaron). Una pregunta en dos temas suma en los dos en todos los
 * recuentos, así que hay que poder dejarla con uno —eligiendo— y **no tocar nada** si nadie decide.
 */
export function fetchTopicConflicts(offset = 0, limit = CONFLICTS_LIMIT): Promise<ConflictPage> {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  return apiFetch<ConflictPage>(`/api/v1/question-topic-conflicts?${params.toString()}`);
}

/**
 * El actor de un mapeo, en palabras.
 *
 * Saber que un tema viene de una migración y no del modelo cambia cómo se mira, y es lo que permite
 * decidir cuál de los dos se queda: por eso la lista lo enseña en lugar de dar por hecho que todo
 * lo escribió la máquina.
 */
export function actorLabel(actor: string | null | undefined): string {
  if (actor === null || actor === undefined || actor === '') {
    return 'sin registro de quién lo escribió';
  }
  if (actor.startsWith('llm:')) {
    return `propuesto por el modelo (${actor.slice(4)})`;
  }
  if (actor === 'auto') {
    return 'heredado del documento (la aplicación sola)';
  }
  if (actor === 'local') {
    return 'a mano o heredado (una persona en esta máquina)';
  }
  return actor;
}

/** Un tema o epígrafe como destino: lo que se manda al escribir es su identificador. */
export function nodeLabel(node: ProgrammeNodeRef): string {
  return `${node.official_code} · ${node.title}`;
}

/** La propuesta que la pantalla enseña elegida: la de menos confianza si no se ha elegido otra. */
export function proposalOf(card: TopicProposalCard, index: number): TopicProposal | null {
  return card.proposals[index] ?? card.proposals[0] ?? null;
}
