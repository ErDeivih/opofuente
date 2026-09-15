import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';

import type { Batch } from './ingestion';
import {
  cancelBatch,
  confirmImport,
  createInventory,
  fetchBatch,
  fetchBatchIssues,
  fetchBatches,
  fetchBatchItems,
  fetchJob,
  fetchRepresentationText,
  fetchRepresentations,
  ingestFiles,
  ingestPaste,
  ingestUrl,
  isActive,
  retryBatch,
} from './ingestion';
import {
  activateOpposition,
  fetchConvocation,
  fetchCurriculum,
  fetchCurriculumNode,
  fetchOppositions,
} from './profiles';
import { fetchCapabilities, fetchReadiness, fetchSettings } from './system';

export const queryKeys = {
  readiness: ['system', 'readiness'] as const,
  capabilities: ['system', 'capabilities'] as const,
  settings: ['system', 'settings'] as const,
  oppositions: ['profiles', 'oppositions'] as const,
  convocation: (id: string) => ['profiles', 'convocation', id] as const,
  curriculum: (id: string) => ['profiles', 'curriculum', id] as const,
  curriculumNode: (id: string) => ['profiles', 'curriculum-node', id] as const,
  batches: ['ingestion', 'batches'] as const,
  batch: (id: string) => ['ingestion', 'batch', id] as const,
  batchItems: (id: string) => ['ingestion', 'batch', id, 'items'] as const,
  batchIssues: (id: string) => ['ingestion', 'batch', id, 'issues'] as const,
  job: (id: string) => ['ingestion', 'job', id] as const,
  representations: (id: string) => ['ingestion', 'batch', id, 'representations'] as const,
  representationText: (id: string, offset: number, limit: number) =>
    ['ingestion', 'representation', id, 'text', offset, limit] as const,
};

export function useReadiness() {
  return useQuery({
    queryKey: queryKeys.readiness,
    queryFn: fetchReadiness,
    refetchInterval: 15_000,
  });
}

export function useCapabilities() {
  return useQuery({
    queryKey: queryKeys.capabilities,
    queryFn: fetchCapabilities,
    staleTime: 60_000,
  });
}

export function useSettings() {
  return useQuery({
    queryKey: queryKeys.settings,
    queryFn: fetchSettings,
    staleTime: 60_000,
  });
}

export function useOppositions() {
  return useQuery({
    queryKey: queryKeys.oppositions,
    queryFn: fetchOppositions,
    staleTime: 30_000,
  });
}

export function useConvocation(convocationId: string | null) {
  return useQuery({
    queryKey: queryKeys.convocation(convocationId ?? 'ninguna'),
    queryFn: () => fetchConvocation(convocationId as string),
    enabled: convocationId !== null,
    staleTime: 60_000,
  });
}

export function useCurriculum(convocationId: string | null) {
  return useQuery({
    queryKey: queryKeys.curriculum(convocationId ?? 'ninguna'),
    queryFn: () => fetchCurriculum(convocationId as string),
    enabled: convocationId !== null,
    staleTime: 60_000,
  });
}

export function useCurriculumNode(nodeId: string | null) {
  return useQuery({
    queryKey: queryKeys.curriculumNode(nodeId ?? 'ninguno'),
    queryFn: () => fetchCurriculumNode(nodeId as string),
    enabled: nodeId !== null,
    staleTime: 60_000,
  });
}

export function useActivateOpposition() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: activateOpposition,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.oppositions });
    },
  });
}

/* ---------------------------------------------------------------- S02: bandeja */

export function useBatches() {
  return useQuery({
    queryKey: queryKeys.batches,
    queryFn: fetchBatches,
    staleTime: 5_000,
  });
}

export function useBatch(batchId: string | null) {
  return useQuery({
    queryKey: queryKeys.batch(batchId ?? 'ninguno'),
    queryFn: () => fetchBatch(batchId as string),
    enabled: batchId !== null,
    // Mientras el lote trabaja se refresca solo; al terminar deja de consultar.
    refetchInterval: (query) => (isActive(query.state.data?.batch) ? 1_000 : false),
  });
}

export function useBatchItems(batchId: string | null) {
  const batch = useBatch(batchId);
  const active = isActive(batch.data?.batch);
  const query = useQuery({
    queryKey: queryKeys.batchItems(batchId ?? 'ninguno'),
    queryFn: () => fetchBatchItems(batchId as string),
    enabled: batchId !== null,
    refetchInterval: active ? 2_000 : false,
  });
  useFinalRefetch(batchId !== null && batch.data !== undefined && !active, query.refetch);
  return query;
}

export function useBatchIssues(batchId: string | null) {
  const batch = useBatch(batchId);
  const active = isActive(batch.data?.batch);
  const query = useQuery({
    queryKey: queryKeys.batchIssues(batchId ?? 'ninguno'),
    queryFn: () => fetchBatchIssues(batchId as string),
    enabled: batchId !== null,
    refetchInterval: active ? 2_000 : false,
  });
  useFinalRefetch(batchId !== null && batch.data !== undefined && !active, query.refetch);
  return query;
}

/**
 * Última consulta de las entradas e incidencias al cerrarse un lote.
 *
 * Mientras el lote trabaja, sus hijos se consultan en bucle; al terminar, el bucle se detiene y la
 * última vuelta pudo pillar la copia a medias. Esta consulta final hace que el informe y la tabla
 * correspondan al lote terminado, no a una foto intermedia.
 */
function useFinalRefetch(isSettled: boolean, refetch: () => Promise<unknown>) {
  useEffect(() => {
    if (isSettled) {
      void refetch();
    }
  }, [isSettled, refetch]);
}

export function useJob(jobId: string | null | undefined) {
  return useQuery({
    queryKey: queryKeys.job(jobId ?? 'ninguno'),
    queryFn: () => fetchJob(jobId as string),
    enabled: Boolean(jobId),
    refetchInterval: (query) =>
      query.state.data !== undefined &&
      ['queued', 'leased', 'running', 'cancel_requested'].includes(query.state.data.status)
        ? 1_000
        : false,
  });
}

export function useCreateInventory() {
  return useMutation({ mutationFn: createInventory });
}

export function useConfirmImport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: confirmImport,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.batches });
    },
  });
}

export function useCancelBatch() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: cancelBatch,
    onSuccess: (batch) => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.batch(batch.id) });
      void queryClient.invalidateQueries({ queryKey: queryKeys.batches });
    },
  });
}

export function useRetryBatch() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: retryBatch,
    onSuccess: (batch) => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.batch(batch.id) });
      void queryClient.invalidateQueries({ queryKey: queryKeys.batches });
    },
  });
}

export function useRepresentations(batchId: string | null) {
  const batch = useBatch(batchId);
  const active = isActive(batch.data?.batch);
  const query = useQuery({
    queryKey: queryKeys.representations(batchId ?? 'ninguno'),
    queryFn: () => fetchRepresentations(batchId as string),
    enabled: batchId !== null,
    // Mientras el lote trabaja, el texto extraído va apareciendo: se refresca con él.
    refetchInterval: active ? 2_000 : false,
  });
  useFinalRefetch(batchId !== null && batch.data !== undefined && !active, query.refetch);
  return query;
}

export function useRepresentationText(
  representationId: string | null,
  offset: number,
  limit: number,
) {
  return useQuery({
    queryKey: queryKeys.representationText(representationId ?? 'ninguna', offset, limit),
    queryFn: () => fetchRepresentationText(representationId as string, offset, limit),
    enabled: representationId !== null,
  });
}

/** Las tres entradas directas comparten el refresco: al crear lote, se recarga el historial. */
function useIntakeMutation<TVariables>(mutationFn: (variables: TVariables) => Promise<Batch>) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.batches });
    },
  });
}

export function useIngestFiles() {
  return useIntakeMutation(ingestFiles);
}

export function useIngestPaste() {
  return useIntakeMutation((input: { text: string; title: string }) =>
    ingestPaste(input.text, input.title),
  );
}

export function useIngestUrl() {
  return useIntakeMutation(ingestUrl);
}
