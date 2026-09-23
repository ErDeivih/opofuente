import type { components } from '@opofuente/contracts';

import type { FicheroParaSubir } from '../features/ingestion/carpetas';
import { apiFetch } from './client';

export type Entry = components['schemas']['EntrySchema'];
export type Issue = components['schemas']['IssueSchema'];
export type Batch = components['schemas']['BatchSchema'];
export type Inventory = components['schemas']['InventorySchema'];
export type BatchDetail = components['schemas']['BatchDetailSchema'];
export type ImportReport = components['schemas']['ImportReportSchema'];
export type Job = components['schemas']['JobSchema'];
export type EntryPage = components['schemas']['EntryPageSchema'];
export type IssuePage = components['schemas']['IssuePageSchema'];
export type Representation = components['schemas']['RepresentationSchema'];
export type RepresentationText = components['schemas']['RepresentationTextSchema'];

/**
 * Estados en los que el lote sigue trabajando: la interfaz refresca mientras dure.
 *
 * `paused` **no** está aquí a propósito: un lote en pausa no avanza, así que refrescarlo cada
 * segundo sería preguntar por algo que no cambia. Vuelve a refrescarse en cuanto se reanuda.
 */
export const ACTIVE_BATCH_STATUSES: ReadonlySet<string> = new Set([
  'queued',
  'running',
  'cancel_requested',
]);

export function isPaused(batch: Batch | undefined): boolean {
  return batch?.status === 'paused';
}

/** Un lote en marcha o en cola se puede pausar; uno en pausa, reanudar. */
export function canPause(batch: Batch | undefined): boolean {
  return batch !== undefined && (batch.status === 'queued' || batch.status === 'running');
}

export function isActive(batch: Batch | undefined): boolean {
  return batch !== undefined && ACTIVE_BATCH_STATUSES.has(batch.status);
}

export function fetchBatches(): Promise<Batch[]> {
  return apiFetch<Batch[]>('/api/v1/ingestion-batches?limit=25');
}

export function fetchBatch(batchId: string): Promise<BatchDetail> {
  return apiFetch<BatchDetail>(`/api/v1/ingestion-batches/${batchId}`);
}

export function fetchBatchItems(batchId: string): Promise<EntryPage> {
  return apiFetch<EntryPage>(`/api/v1/ingestion-batches/${batchId}/items?limit=200`);
}

export function fetchBatchIssues(batchId: string): Promise<IssuePage> {
  return apiFetch<IssuePage>(`/api/v1/ingestion-batches/${batchId}/issues?limit=200`);
}

export function fetchJob(jobId: string): Promise<Job> {
  return apiFetch<Job>(`/api/v1/jobs/${jobId}`);
}

export function fetchRepresentations(batchId: string): Promise<Representation[]> {
  return apiFetch<Representation[]>(`/api/v1/ingestion-batches/${batchId}/representations`);
}

export function fetchRepresentationText(
  representationId: string,
  offset: number,
  limit: number,
): Promise<RepresentationText> {
  const params = new URLSearchParams({ offset: String(offset), limit: String(limit) });
  return apiFetch<RepresentationText>(
    `/api/v1/representations/${representationId}/text?${params.toString()}`,
  );
}

/* --- Entradas directas de S03 ------------------------------------------------------------- */

/**
 * Sube ficheros. No se fija `Content-Type`: lo pone el navegador con su separador.
 *
 * El nombre que viaja **no** es siempre el del fichero: al soltar una carpeta entera se manda su
 * ruta relativa («Tema 3/apuntes.pdf»), porque si no, treinta ficheros de tres carpetas llegan
 * como treinta entradas sin ninguna relación entre ellas.
 */
export function ingestFiles(files: FicheroParaSubir[]): Promise<Batch> {
  const form = new FormData();
  for (const { file, name } of files) {
    form.append('files', file, name);
  }
  return apiFetch<Batch>('/api/v1/ingestion-batches/files', { method: 'POST', body: form });
}

export function ingestPaste(text: string, title: string): Promise<Batch> {
  return apiFetch<Batch>('/api/v1/ingestion-batches/paste', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(title.trim() ? { text, title: title.trim() } : { text }),
  });
}

export function ingestUrl(url: string): Promise<Batch> {
  return apiFetch<Batch>('/api/v1/ingestion-batches/url', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  });
}

export function createInventory(sourcePath: string): Promise<Inventory> {
  return apiFetch<Inventory>('/api/v1/inventories', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ source_path: sourcePath }),
  });
}

export function confirmImport(inventoryId: string): Promise<Batch> {
  return apiFetch<Batch>(`/api/v1/inventories/${inventoryId}/confirm-import`, { method: 'POST' });
}

export function cancelBatch(batchId: string): Promise<Batch> {
  return apiFetch<Batch>(`/api/v1/ingestion-batches/${batchId}/cancel`, { method: 'POST' });
}

/** Pausa el lote: deja de avanzar donde está y lo copiado sigue copiado (DEBT-027 §4). */
export function pauseBatch(batchId: string): Promise<Batch> {
  return apiFetch<Batch>(`/api/v1/ingestion-batches/${batchId}/pause`, { method: 'POST' });
}

export function resumeBatch(batchId: string): Promise<Batch> {
  return apiFetch<Batch>(`/api/v1/ingestion-batches/${batchId}/resume`, { method: 'POST' });
}

export function retryBatch(batchId: string): Promise<Batch> {
  return apiFetch<Batch>(`/api/v1/ingestion-batches/${batchId}/retry`, { method: 'POST' });
}
