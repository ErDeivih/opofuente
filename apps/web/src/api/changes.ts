import type { components } from '@opofuente/contracts';

import { apiFetch } from './client';

/**
 * Cambios, dependencias y derivados (S11), leídos del contrato generado (§11).
 *
 * Nada de lo que se ve aquí lo decide la pantalla: el diff por sección, los derivados afectados, el
 * motivo de cada uno y el aviso de lo que la aplicación **no** interpreta vienen del servidor.
 */
export type ChangeSet = components['schemas']['ChangeSetSchema'];
export type ChangeOutcome = components['schemas']['ChangeOutcomeSchema'];
export type SectionChange = components['schemas']['SectionChangeSchema'];
export type Affected = components['schemas']['AffectedSchema'];
export type DerivedArtifact = components['schemas']['DerivedArtifactSchema'];
export type CreateSummary = components['schemas']['CreateSummarySchema'];

export type ChangeStatus = ChangeSet['status'];
export type SectionChangeKind = SectionChange['kind'];

export const CHANGE_STATUS_LABEL: Record<ChangeStatus, string> = {
  proposed: 'propuesto, sin aplicar',
  confirmed: 'confirmado',
  discarded: 'descartado',
};

export const SECTION_KIND_LABEL: Record<SectionChangeKind, string> = {
  added: 'nueva',
  removed: 'quitada',
  changed: 'con el texto cambiado',
  unchanged: 'sin cambios',
};

export function fetchChangeSets(): Promise<ChangeSet[]> {
  return apiFetch<ChangeSet[]>('/api/v1/change-sets?limit=100');
}

export function fetchChangeSet(changeId: string): Promise<ChangeSet> {
  return apiFetch<ChangeSet>(`/api/v1/change-sets/${encodeURIComponent(changeId)}`);
}

export function fetchChangeSetAffected(changeId: string): Promise<ChangeSet> {
  return apiFetch<ChangeSet>(`/api/v1/change-sets/${encodeURIComponent(changeId)}/affected`);
}

export function confirmChangeSet(changeId: string): Promise<ChangeOutcome> {
  return apiFetch<ChangeOutcome>(`/api/v1/change-sets/${encodeURIComponent(changeId)}/confirm`, {
    method: 'POST',
  });
}

export function discardChangeSet(changeId: string): Promise<ChangeOutcome> {
  return apiFetch<ChangeOutcome>(`/api/v1/change-sets/${encodeURIComponent(changeId)}/discard`, {
    method: 'POST',
  });
}

export function fetchDerivedArtifacts(needsReview?: boolean): Promise<DerivedArtifact[]> {
  const consulta = needsReview === undefined ? '' : `?needs_review=${String(needsReview)}`;
  return apiFetch<DerivedArtifact[]>(`/api/v1/derived-artifacts${consulta}`);
}

export function fetchDerivedArtifact(artifactId: string): Promise<DerivedArtifact> {
  return apiFetch<DerivedArtifact>(`/api/v1/derived-artifacts/${encodeURIComponent(artifactId)}`);
}

export function createSummary(input: CreateSummary): Promise<DerivedArtifact> {
  return apiFetch<DerivedArtifact>('/api/v1/derived-artifacts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  });
}

export function resolveDerivedArtifact(
  artifactId: string,
  resolution: 'reviewed' | 'discarded',
): Promise<DerivedArtifact> {
  return apiFetch<DerivedArtifact>(
    `/api/v1/derived-artifacts/${encodeURIComponent(artifactId)}/resolution`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ resolution }),
    },
  );
}

/** Una frase con lo que un cambio hace, para la lista (sin adornos y sin interpretar nada). */
export function changeSummary(change: ChangeSet): string {
  const partes = [
    `${change.sections_changed} cambiada(s)`,
    `${change.sections_added} nueva(s)`,
    `${change.sections_removed} quitada(s)`,
    `${change.sections_unchanged} sin cambios`,
  ];
  const afectados = change.affected.length;
  const revisables = change.affected.filter((item) => item.reviewable).length;
  return `${partes.join(' · ')} · ${afectados} derivado(s) afectado(s), ${revisables} por revisar`;
}
