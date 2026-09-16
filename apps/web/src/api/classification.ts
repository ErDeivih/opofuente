import type { components } from '@opofuente/contracts';

import { apiFetch } from './client';

export type Proposal = components['schemas']['ProposalSchema'];
export type ProposalPage = components['schemas']['ProposalPageSchema'];
export type ReviewGroup = components['schemas']['ReviewGroupSchema'];
export type Coverage = components['schemas']['CoverageSchema'];
export type CoverageNode = components['schemas']['CoverageNodeSchema'];
export type DecisionOutcome = components['schemas']['DecisionOutcomeSchema'];
export type BulkDecisionResponse = components['schemas']['BulkDecisionResponseSchema'];
export type DecisionRequest = components['schemas']['DecisionRequestSchema'];
export type BulkDecisionRequest = components['schemas']['BulkDecisionRequestSchema'];
export type ClassificationReport = components['schemas']['ClassificationReportSchema'];

export type ProposalAxis = Proposal['axis'];
export type ProposalBand = Proposal['band'];
export type ProposalStatus = Proposal['status'];
export type SubjectType = Proposal['subject_type'];
export type Decision = 'accepted' | 'rejected';
export type CoverageType = DecisionRequest['coverage_type'];

/** Cuántas propuestas se piden de una vez. La cola de revisión se lee entera para poder decidirla. */
const PROPOSAL_LIMIT = 200;

/**
 * Estados que **siguen esperando a una persona**: pendientes y aplicadas provisionalmente.
 *
 * Lo autoaplicado no se esconde ni se presenta como definitivo: el motor lo aplicó por su banda de
 * confianza, sigue siendo provisional y se puede confirmar, rechazar o deshacer (04 §8).
 */
export const OPEN_PROPOSAL_STATUSES: readonly ProposalStatus[] = [
  'pending',
  'auto_applied_provisional',
];

/**
 * Alcance con el que se registra un mapeo de tema al aceptar.
 *
 * Se envía explícito porque el tipo del contrato lo exige, con el valor que el propio contrato marca
 * por defecto («parcial»). Qué significa cubrir un tema lo decide el dominio, no esta pantalla.
 */
const DEFAULT_COVERAGE_TYPE: CoverageType = 'partial';

export function fetchProposals(status: ProposalStatus): Promise<ProposalPage> {
  const params = new URLSearchParams({ status, limit: String(PROPOSAL_LIMIT) });
  return apiFetch<ProposalPage>(`/api/v1/classification-proposals?${params.toString()}`);
}

export function fetchReviewGroups(): Promise<ReviewGroup[]> {
  return apiFetch<ReviewGroup[]>('/api/v1/review-groups');
}

export function fetchCoverage(nodeId: string): Promise<Coverage> {
  return apiFetch<Coverage>(`/api/v1/curriculum-nodes/${nodeId}/coverage`);
}

/** Ejecuta una pasada de clasificación ahora. Es idempotente y no aplica nada definitivo. */
export function runClassification(): Promise<ClassificationReport> {
  return apiFetch<ClassificationReport>('/api/v1/classification-runs', { method: 'POST' });
}

export interface DecideInput {
  proposalId: string;
  decision: Decision;
  /** Motivo de la decisión. Viaja a la auditoría del servidor. */
  note?: string;
  /** Valor corregido por la persona. Solo se admite en los ejes que el servidor valida así. */
  overrideValue?: string;
}

export function decideProposal(input: DecideInput): Promise<DecisionOutcome> {
  const body: DecisionRequest = { coverage_type: DEFAULT_COVERAGE_TYPE };
  if (input.note !== undefined && input.note !== '') {
    body.note = input.note;
  }
  if (input.overrideValue !== undefined && input.overrideValue !== '') {
    body.override_value = input.overrideValue;
  }
  const action = input.decision === 'accepted' ? 'accept' : 'reject';
  return apiFetch<DecisionOutcome>(
    `/api/v1/classification-proposals/${input.proposalId}/${action}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    },
  );
}

export interface BulkDecisionInput {
  proposalIds: string[];
  decision: Decision;
  note?: string;
  /** Correcciones por propuesta, cuando las hay. */
  overrides?: Record<string, string>;
  /** Excepciones: propuestas del lote que **no** se tocan y se informan aparte. */
  excluded?: string[];
}

export function bulkDecision(input: BulkDecisionInput): Promise<BulkDecisionResponse> {
  const body: BulkDecisionRequest = {
    proposal_ids: input.proposalIds,
    decision: input.decision,
  };
  if (input.note !== undefined && input.note !== '') {
    body.note = input.note;
  }
  if (input.overrides !== undefined && Object.keys(input.overrides).length > 0) {
    body.overrides = input.overrides;
  }
  if (input.excluded !== undefined && input.excluded.length > 0) {
    body.excluded = input.excluded;
  }
  return apiFetch<BulkDecisionResponse>('/api/v1/classification-proposals/bulk-decision', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

/**
 * Deshace una decisión y devuelve la propuesta a la cola.
 *
 * `decisionId` es el evento de auditoría que devolvió la decisión, o el identificador de la
 * propuesta: el contrato admite los dos para no obligar a la interfaz a recordar la traza.
 */
export function undoDecision(decisionId: string): Promise<DecisionOutcome> {
  return apiFetch<DecisionOutcome>(
    `/api/v1/classification-decisions/${decisionId}/undo`,
    { method: 'POST' },
  );
}
