import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { QueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';

import type { ProposalStatus } from './classification';
import {
  bulkDecision,
  decideProposal,
  fetchCoverage,
  fetchProposals,
  fetchReviewGroups,
  runClassification,
  undoDecision,
} from './classification';
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
  acceptVersion,
  fetchDocument,
  fetchDocuments,
  fetchEvidence,
  fetchMappings,
  fetchSections,
  fetchVersions,
  markSupersedes,
} from './library';
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
  /* S04: revisión de clasificación. Todas cuelgan de «classification» para poder invalidarlas
     juntas: una decisión cambia la cola, los grupos y la cobertura a la vez. */
  proposals: (status: string) => ['classification', 'proposals', status] as const,
  reviewGroups: ['classification', 'review-groups'] as const,
  coverage: (nodeId: string) => ['classification', 'coverage', nodeId] as const,
  /* S05: biblioteca. Cuelgan de «library» por lo mismo: aceptar una versión cambia el listado (su
     versión activa y su estado) y la propia ficha, y las dos deben contar lo mismo. */
  libraryDocuments: (documentType: string, ownerScope: string) =>
    ['library', 'documents', documentType, ownerScope] as const,
  libraryDocument: (documentId: string) => ['library', 'document', documentId] as const,
  libraryVersions: (documentId: string) =>
    ['library', 'document', documentId, 'versions'] as const,
  librarySections: (versionId: string) => ['library', 'version', versionId, 'sections'] as const,
  libraryEvidence: (versionId: string) => ['library', 'version', versionId, 'evidence'] as const,
  libraryMappings: (versionId: string) => ['library', 'version', versionId, 'mappings'] as const,
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

/* ------------------------------------------------------- S04: revisión de clasificación */

/**
 * Todo lo que cambia al decidir cuelga de la misma clave raíz, así que se invalida de una vez.
 *
 * Decidir una propuesta cambia la cola (deja de estar pendiente), los grupos (puede desaparecer su
 * grupo) y la cobertura (si el eje era el tema). Refrescar solo una parte dejaría la pantalla
 * contando dos verdades distintas a la vez.
 */
function invalidateClassification(queryClient: QueryClient) {
  void queryClient.invalidateQueries({ queryKey: ['classification'] });
}

/** Propuestas de un estado concreto, tal y como las sirve el servidor. */
export function useProposals(status: ProposalStatus) {
  return useQuery({
    queryKey: queryKeys.proposals(status),
    queryFn: () => fetchProposals(status),
    staleTime: 5_000,
  });
}

export function useReviewGroups() {
  return useQuery({
    queryKey: queryKeys.reviewGroups,
    queryFn: fetchReviewGroups,
    staleTime: 5_000,
  });
}

/** Cobertura de un nodo del programa. Sin nodo elegido no se pide nada. */
export function useCoverage(nodeId: string | null) {
  return useQuery({
    queryKey: queryKeys.coverage(nodeId ?? 'ninguno'),
    queryFn: () => fetchCoverage(nodeId as string),
    enabled: nodeId !== null,
  });
}

export function useDecideProposal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: decideProposal,
    onSuccess: () => {
      invalidateClassification(queryClient);
    },
  });
}

export function useBulkDecision() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: bulkDecision,
    onSuccess: () => {
      invalidateClassification(queryClient);
    },
  });
}

export function useUndoDecision() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: undoDecision,
    onSuccess: () => {
      invalidateClassification(queryClient);
    },
  });
}

export function useRunClassification() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: runClassification,
    onSuccess: () => {
      invalidateClassification(queryClient);
    },
  });
}

/* ------------------------------------------------------------------- S05: biblioteca */

/**
 * Aceptar una versión o marcar una sustitución cambia **todo** lo que la biblioteca enseña: la
 * versión activa del listado, el estado de las versiones de la ficha y, con ellas, qué se puede
 * citar como aceptado. Por eso se invalida la biblioteca entera, no una consulta concreta.
 */
function invalidateLibrary(queryClient: QueryClient) {
  void queryClient.invalidateQueries({ queryKey: ['library'] });
}

/** Documentos de la biblioteca con los filtros que admite el servidor. */
export function useDocuments(documentType: string, ownerScope: string) {
  return useQuery({
    queryKey: queryKeys.libraryDocuments(documentType, ownerScope),
    queryFn: () =>
      fetchDocuments({
        documentType: documentType === '' ? null : documentType,
        ownerScope: ownerScope === '' ? null : ownerScope,
      }),
    staleTime: 5_000,
  });
}

export function useDocumentDetail(documentId: string | null) {
  return useQuery({
    queryKey: queryKeys.libraryDocument(documentId ?? 'ninguno'),
    queryFn: () => fetchDocument(documentId as string),
    enabled: documentId !== null,
  });
}

export function useVersions(documentId: string | null) {
  return useQuery({
    queryKey: queryKeys.libraryVersions(documentId ?? 'ninguno'),
    queryFn: () => fetchVersions(documentId as string),
    enabled: documentId !== null,
  });
}

/** Estructura de una versión. Sin versión (documento sin promover) no se pide nada. */
export function useSections(versionId: string | null) {
  return useQuery({
    queryKey: queryKeys.librarySections(versionId ?? 'ninguna'),
    queryFn: () => fetchSections(versionId as string),
    enabled: versionId !== null,
  });
}

export function useEvidence(versionId: string | null) {
  return useQuery({
    queryKey: queryKeys.libraryEvidence(versionId ?? 'ninguna'),
    queryFn: () => fetchEvidence(versionId as string),
    enabled: versionId !== null,
  });
}

/**
 * Asignaciones de programa de una versión de documento.
 *
 * Se leen por versión porque es lo que el servidor sabe relacionar con un nodo del programa
 * (`subject_type=document_version`).
 */
export function useDocumentMappings(versionId: string | null) {
  return useQuery({
    queryKey: queryKeys.libraryMappings(versionId ?? 'ninguna'),
    queryFn: () => fetchMappings('document_version', versionId as string),
    enabled: versionId !== null,
  });
}

export interface AcceptVersionInput {
  documentId: string;
  versionId: string;
}

export function useAcceptVersion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: AcceptVersionInput) => acceptVersion(input.documentId, input.versionId),
    onSuccess: () => {
      invalidateLibrary(queryClient);
    },
  });
}

export interface MarkSupersedesInput {
  documentId: string;
  versionId: string;
  supersededId: string;
}

export function useMarkSupersedes() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: MarkSupersedesInput) =>
      markSupersedes(input.documentId, input.versionId, input.supersededId),
    onSuccess: () => {
      invalidateLibrary(queryClient);
    },
  });
}
