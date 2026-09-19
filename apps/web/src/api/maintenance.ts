import type { components } from '@opofuente/contracts';

import { apiBaseUrl, apiFetch } from './client';

/**
 * Copia, restauración, higiene del almacén y diagnóstico (08_API-CONTRACT §11 y 07_UI-UX §11).
 *
 * Los tipos se leen del contrato generado: si el servidor cambia un campo, esto no compila y la
 * pantalla no puede quedarse enseñando un dato que ya no existe.
 */
export type Backup = components['schemas']['BackupSchema'];
export type BackupList = components['schemas']['BackupListSchema'];
export type Verification = components['schemas']['VerificationSchema'];
export type RestorePreview = components['schemas']['RestorePreviewSchema'];
export type RestoreResult = components['schemas']['RestoreResultSchema'];

export type HousekeepingReport = components['schemas']['HousekeepingReportSchema'];
export type HousekeepingCandidate = components['schemas']['HousekeepingCandidateSchema'];
export type AreaUsage = components['schemas']['AreaUsageSchema'];
export type PurgeResult = components['schemas']['PurgeResultSchema'];
export type IndexHealth = components['schemas']['IndexHealthSchema'];
export type ReindexResult = components['schemas']['ReindexSchema'];

export type Diagnostic = components['schemas']['DiagnosticSchema'];

/**
 * Acciones de retirada, indexadas por el **valor que usa el servidor** (`stale_temp`, no `temps`).
 *
 * La clave es lo que viaja en `candidate.action` y en `PurgeResult.action`, y `path` es el segmento de
 * la ruta. La primera versión de esto tenía las claves de la ruta como si fueran los valores del
 * servidor: la pantalla no encontraba ni un candidato y enseñaba una lista vacía sin error, que es el
 * peor fallo posible —el que parece que no hay nada que limpiar—. Lo encontró la prueba de componente.
 */
export const PURGE_ACTIONS = {
  stale_temp: {
    path: 'temps',
    label: 'Temporales de operaciones interrumpidas',
    why: 'restos de una copia o una restauración que no terminó',
  },
  orphan_artifact: {
    path: 'orphan-artifacts',
    label: 'Artefactos sin origen ni documento',
    why: 'contenido copiado que ya no sostiene ninguna cita ni cobertura',
  },
  old_job: {
    path: 'old-jobs',
    label: 'Trabajos terminados y antiguos',
    why: 'historial de la cola que ya no se va a volver a mirar',
  },
} as const;

/** Valor de acción tal como lo devuelve y lo acepta el servidor. */
export type PurgeActionValue = keyof typeof PURGE_ACTIONS;

export function fetchBackups(): Promise<BackupList> {
  return apiFetch<BackupList>('/api/v1/backups');
}

export function createBackup(note: string | null): Promise<Backup> {
  return apiFetch<Backup>('/api/v1/backups', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ note }),
  });
}

export function verifyBackup(backupId: string): Promise<Verification> {
  return apiFetch<Verification>(`/api/v1/backups/${encodeURIComponent(backupId)}/verify`, {
    method: 'POST',
  });
}

export function validateRestore(backupId: string): Promise<RestorePreview> {
  return apiFetch<RestorePreview>('/api/v1/restore/validate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ backup_id: backupId, keep_rollback: false }),
  });
}

export function executeRestore(backupId: string): Promise<RestoreResult> {
  return apiFetch<RestoreResult>('/api/v1/restore/execute', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ backup_id: backupId, keep_rollback: false }),
  });
}

export function fetchHousekeeping(): Promise<HousekeepingReport> {
  return apiFetch<HousekeepingReport>('/api/v1/housekeeping');
}

/**
 * Retira lo que se le pide. `references` vacío significa «todo lo que la foto propone para esa
 * acción», que nunca es más de lo que la foto ha enseñado antes.
 */
export function purge(action: PurgeActionValue, references: string[] | null): Promise<PurgeResult> {
  return apiFetch<PurgeResult>(`/api/v1/housekeeping/${PURGE_ACTIONS[action].path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    // `confirm: true` es obligatorio en el servidor: retirar material no ocurre por accidente.
    body: JSON.stringify({ references, confirm: true }),
  });
}

export function fetchIndexHealth(): Promise<IndexHealth> {
  return apiFetch<IndexHealth>('/api/v1/search/index');
}

export function reindex(): Promise<ReindexResult> {
  return apiFetch<ReindexResult>('/api/v1/search/reindex', { method: 'POST' });
}

export function fetchDiagnostic(): Promise<Diagnostic> {
  return apiFetch<Diagnostic>('/api/v1/diagnostics');
}

/**
 * El diagnóstico en texto plano, tal como se pega en una incidencia.
 *
 * Pasa por `apiBaseUrl()` y **no** por `apiFetch`: ese cliente interpreta siempre JSON, y esto es
 * texto. La primera versión pedía `/api/v1/diagnostics/text` a secas, así que en el navegador iba
 * contra el servidor del frontend (que no tiene esa ruta) y el área nunca aparecía. Lo encontró el
 * E2E: la prueba de componente no lo veía porque ahí `fetch` está simulado.
 */
export async function fetchDiagnosticText(): Promise<string> {
  const respuesta = await fetch(`${apiBaseUrl()}/api/v1/diagnostics/text`, {
    headers: { Accept: 'text/plain' },
  });
  if (!respuesta.ok) {
    throw new Error(`el diagnóstico no se pudo leer (HTTP ${String(respuesta.status)})`);
  }
  return respuesta.text();
}
