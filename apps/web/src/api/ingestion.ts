import type { components } from '@opofuente/contracts';

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

/** Estados en los que el lote sigue trabajando: la interfaz refresca mientras dure. */
export const ACTIVE_BATCH_STATUSES: ReadonlySet<string> = new Set([
  'queued',
  'running',
  'cancel_requested',
]);

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

export function retryBatch(batchId: string): Promise<Batch> {
  return apiFetch<Batch>(`/api/v1/ingestion-batches/${batchId}/retry`, { method: 'POST' });
}
