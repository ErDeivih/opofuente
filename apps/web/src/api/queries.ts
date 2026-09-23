import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { QueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';

import {
  confirmChangeSet,
  createSummary,
  discardChangeSet,
  fetchChangeSet,
  fetchChangeSets,
  fetchDerivedArtifacts,
  resolveDerivedArtifact,
  type CreateSummary,
} from './changes';
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
  addToCollection,
  assignVersionToNode,
  createCollection,
  fetchCollections,
  fetchDocument,
  fetchDocuments,
  fetchEvidence,
  fetchSections,
  fetchVersionDiff,
  fetchVersionMappings,
  fetchVersions,
  markSupersedes,
  removeFromCollection,
  removeMapping,
  type CoverageType,
  type SubjectType,
} from './library';
import {
  activateConvocation,
  activateOpposition,
  fetchConvocation,
  fetchConvocations,
  fetchCurriculum,
  fetchCurriculumNode,
  fetchOppositions,
} from './profiles';
import {
  askCorpus,
  fetchRagQuery,
  fetchRetrieval,
  searchCorpus,
  type AskRequest,
  type SearchRequest,
} from './search';
import {
  classifyError,
  completeReview,
  exportBank,
  fetchLearningError,
  fetchLearningErrors,
  fetchMastery,
  fetchReviewHistory,
  fetchReviewQueue,
  resolveError,
  snoozeReview,
  type ErrorCause,
  type ExportRequest,
} from './reviews';
import {
  answerQuestion,
  createSession,
  fetchCurrentQuestion,
  fetchDiagnosticReading,
  fetchSession,
  fetchSessionResult,
  fetchSessionReview,
  fetchSessions,
  finishSession,
  navigateSession,
  recalculateSession,
  startSession,
  type AnswerRequest,
  type CreateSession,
  type NavigateRequest,
} from './study';
import {
  activateAnswerKey,
  correctQuestion,
  createQuestionSet,
  fetchAnswerKeys,
  fetchConflictingQuestions,
  fetchExplanations,
  fetchOutdatedSessions,
  fetchQuestion,
  fetchQuestionEvidence,
  fetchQuestionSet,
  fetchQuestionSets,
  fetchSetQuestions,
  importQuestionsFromDocument,
  markKeySupersedes,
  parseIntoSet,
  patchQuestion,
  recalculateSetSessions,
  reportQuestionIssue,
  setExplanation,
  type CreateQuestionSet,
  type CsvMapping,
  type ImportKind,
  type IssueKind,
  type PatchQuestion,
} from './questions';
import { fetchCapabilities, fetchReadiness, fetchSettings } from './system';
import { fetchPendingActions, fetchStudyReadiness } from './readiness';
import {
  createBackup,
  executeRestore,
  fetchBackups,
  fetchDiagnostic,
  fetchDiagnosticText,
  fetchHousekeeping,
  fetchIndexHealth,
  purge,
  reindex,
  validateRestore,
  verifyBackup,
  type PurgeActionValue,
} from './maintenance';
export const queryKeys = {
  readiness: ['system', 'readiness'] as const,
  // `readiness` (arriba) es la salud del sistema; esta es la preparación para estudiar (S12.6).
  studyReadiness: (oppositionId: string) =>
    ['profiles', 'study-readiness', oppositionId] as const,
  pendingActions: ['profiles', 'pending-actions'] as const,
  conflictingQuestions: ['questions', 'conflicting'] as const,
  capabilities: ['system', 'capabilities'] as const,
  settings: ['system', 'settings'] as const,
  oppositions: ['profiles', 'oppositions'] as const,
  convocations: (oppositionId: string) => ['profiles', 'convocations', oppositionId] as const,
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
  proposals: (status: string, offset = 0) =>
    ['classification', 'proposals', status, offset] as const,
  reviewGroups: ['classification', 'review-groups'] as const,
  coverage: (nodeId: string) => ['classification', 'coverage', nodeId] as const,
  /* S05: biblioteca. Cuelgan de «library» por lo mismo: aceptar una versión cambia el listado (su
     versión activa y su estado) y la propia ficha, y las dos deben contar lo mismo. */
  libraryDocuments: (documentType: string, ownerScope: string, collectionId = '') =>
    ['library', 'documents', documentType, ownerScope, collectionId] as const,
  /* Las colecciones cuelgan de «library» porque añadir un documento a una colección cambia a la vez
     la lista de colecciones y los documentos que enseña el filtro. */
  libraryCollections: () => ['library', 'collections'] as const,
  libraryDocument: (documentId: string) => ['library', 'document', documentId] as const,
  libraryVersions: (documentId: string) =>
    ['library', 'document', documentId, 'versions'] as const,
  librarySections: (versionId: string) => ['library', 'version', versionId, 'sections'] as const,
  libraryEvidence: (versionId: string) => ['library', 'version', versionId, 'evidence'] as const,
  libraryMappings: (versionId: string) => ['library', 'version', versionId, 'mappings'] as const,
  libraryDiff: (documentId: string, fromVersionId: string, toVersionId: string) =>
    ['library', 'document', documentId, 'diff', fromVersionId, toVersionId] as const,
  /* S06: banco de preguntas. Cuelgan de «questions» para poder invalidarlas juntas: importar cambia
     las preguntas, sus claves, los conflictos y los recuentos del conjunto a la vez. */
  questionSets: (oppositionId: string) => ['questions', 'sets', oppositionId] as const,
  questionSet: (setId: string) => ['questions', 'set', setId] as const,
  setQuestions: (setId: string, filtros: string) =>
    ['questions', 'set', setId, 'list', filtros] as const,
  question: (questionId: string) => ['questions', 'question', questionId] as const,
  questionEvidence: (questionId: string) =>
    ['questions', 'question', questionId, 'evidence'] as const,
  /* S12.7: la explicación de la pregunta entera y la de cada opción. */
  questionExplanations: (questionId: string) =>
    ['questions', 'question', questionId, 'explanations'] as const,
  answerKeys: (setId: string) => ['questions', 'set', setId, 'keys'] as const,
  /* DEBT-013: qué sesiones del conjunto quedan sin corregir con su plantilla activa. */
  outdatedSessions: (setId: string) => ['questions', 'set', setId, 'outdated'] as const,
  /* S07: sesiones de estudio. Cuelgan de «study» porque responder cambia a la vez el progreso de la
     sesión, el intento y su corrección. */
  studySessions: (oppositionId: string) => ['study', 'sessions', oppositionId] as const,
  studySession: (sessionId: string) => ['study', 'session', sessionId] as const,
  studyCurrent: (sessionId: string) => ['study', 'session', sessionId, 'current'] as const,
  studyReview: (sessionId: string) => ['study', 'session', sessionId, 'review'] as const,
  studyResult: (sessionId: string) => ['study', 'session', sessionId, 'result'] as const,
  studyDiagnostic: (sessionId: string) => ['study', 'session', sessionId, 'diagnostic'] as const,
  /* S09: búsqueda y RAG. Cuelgan de «search» porque una consulta guarda su recuperación y su
     respuesta, y las tres cosas cambian juntas. */
  searchResults: (query: string, versionMode: string) =>
    ['search', 'results', query, versionMode] as const,
  ragQuery: (queryId: string) => ['search', 'rag', queryId] as const,
  retrieval: (queryId: string) => ['search', 'rag', queryId, 'retrieval'] as const,
  /* S10: errores y repaso. Cuelgan de «review» porque clasificar un fallo, repasar y aplazar cambian
     a la vez la cola, el concepto al que pertenece el error y su historial. */
  reviewQueue: (oppositionId: string) => ['review', 'queue', oppositionId] as const,
  learningErrors: (oppositionId: string) => ['review', 'errors', oppositionId] as const,
  learningError: (errorId: string) => ['review', 'error', errorId] as const,
  reviewHistory: (reviewId: string) => ['review', 'item', reviewId, 'history'] as const,
  mastery: (oppositionId: string) => ['review', 'mastery', oppositionId] as const,
  /* S11: cambios y derivados. Cuelgan de «change» porque confirmar un cambio afecta a la vez al
     documento, a sus versiones y a los derivados que dependían de él. */
  changeSets: () => ['change', 'sets'] as const,
  changeSet: (changeId: string) => ['change', 'set', changeId] as const,
  derivedArtifacts: (needsReview: string) => ['change', 'artifacts', needsReview] as const,
  /* S12: copias, almacén y diagnóstico. Cuelgan de «maintenance» porque una copia, una retirada o
     un reindexado cambian a la vez el uso de disco, la lista de copias y el estado del índice. */
  backups: () => ['maintenance', 'backups'] as const,
  housekeeping: () => ['maintenance', 'housekeeping'] as const,
  indexHealth: () => ['maintenance', 'index'] as const,
  diagnostic: () => ['maintenance', 'diagnostic'] as const,
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

export function useConvocations(oppositionId: string | null) {
  return useQuery({
    queryKey: queryKeys.convocations(oppositionId ?? 'ninguna'),
    queryFn: () => fetchConvocations(oppositionId as string),
    enabled: oppositionId !== null,
    staleTime: 30_000,
  });
}

/**
 * Cambia la convocatoria vigente. Se invalida todo `['profiles']` porque la convocatoria elegida
 * aparece en más de una respuesta (la oposición activa, el programa, el resumen de preparación) y
 * dejar una de ellas con la anterior daría dos versiones de lo mismo en pantalla.
 */
export function useActivateConvocation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: activateConvocation,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['profiles'] });
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
export function useProposals(status: ProposalStatus, offset = 0) {
  return useQuery({
    queryKey: queryKeys.proposals(status, offset),
    queryFn: () => fetchProposals(status, offset),
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
  return useMutation({
    mutationFn: runClassification,
    // No se invalida nada aquí: encolar no clasifica todavía. Lo que se sigue es el **trabajo**
    // (DEBT-024), y cuando termina es cuando la pantalla recarga las propuestas.
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
export function useDocuments(
  documentType: string,
  ownerScope: string,
  collectionId: string | null = null,
) {
  return useQuery({
    queryKey: queryKeys.libraryDocuments(documentType, ownerScope, collectionId ?? ''),
    queryFn: () =>
      fetchDocuments({
        documentType: documentType === '' ? null : documentType,
        ownerScope: ownerScope === '' ? null : ownerScope,
        collectionId,
      }),
    staleTime: 5_000,
  });
}

export function useCollections() {
  return useQuery({ queryKey: queryKeys.libraryCollections(), queryFn: fetchCollections });
}

export function useCreateCollection() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: { name: string; description: string | null }) => createCollection(input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['library'] });
    },
  });
}

/**
 * Añade un sujeto a una colección.
 *
 * Invalida la biblioteca entera y no solo la colección: si el filtro por colección está activo, los
 * documentos que se están viendo cambian con esta operación.
 */
export function useAddToCollection() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: { collectionId: string; subjectType: SubjectType; subjectId: string }) =>
      addToCollection(input.collectionId, {
        subjectType: input.subjectType,
        subjectId: input.subjectId,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['library'] });
    },
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
 * Se leen con la ruta del contrato §7 (`GET /document-versions/{id}/mappings`), que es la que
 * relaciona una **versión** con un nodo del programa.
 */
export function useDocumentMappings(versionId: string | null) {
  return useQuery({
    queryKey: queryKeys.libraryMappings(versionId ?? 'ninguna'),
    queryFn: () => fetchVersionMappings(versionId as string),
    enabled: versionId !== null,
  });
}

/**
 * Comparación de dos versiones del mismo documento.
 *
 * Solo se pide con las dos versiones elegidas: sin par no hay nada que comparar, y el servidor
 * responde 404 si alguna versión no es de ese documento.
 */
export function useVersionDiff(
  documentId: string | null,
  fromVersionId: string | null,
  toVersionId: string | null,
) {
  return useQuery({
    queryKey: queryKeys.libraryDiff(
      documentId ?? 'ninguno',
      fromVersionId ?? 'ninguna',
      toVersionId ?? 'ninguna',
    ),
    queryFn: () => fetchVersionDiff(documentId as string, fromVersionId as string, toVersionId as string),
    enabled: documentId !== null && fromVersionId !== null && toVersionId !== null,
  });
}

export interface AssignMappingInput {
  versionId: string;
  curriculumNodeId: string;
  coverageType: CoverageType;
}

/** Asigna una versión a un nodo del programa. El recuento de asignaciones del documento cambia. */
export function useAssignMapping() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: AssignMappingInput) =>
      assignVersionToNode(input.versionId, {
        curriculumNodeId: input.curriculumNodeId,
        coverageType: input.coverageType,
      }),
    onSuccess: () => {
      invalidateLibrary(queryClient);
    },
  });
}

export interface RemoveMappingInput {
  mappingId: string;
}

/** Retira una asignación de programa. No borra material: solo deja de estar asignada. */
export function useRemoveMapping() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: RemoveMappingInput) => removeMapping(input.mappingId),
    onSuccess: () => {
      invalidateLibrary(queryClient);
    },
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

/* ------------------------------------------------------------------ S06: banco de preguntas */

/** Invalida todo lo del banco: importar o decidir cambia preguntas, claves, conflictos y recuentos. */
function invalidateQuestions(queryClient: QueryClient): void {
  void queryClient.invalidateQueries({ queryKey: ['questions'] });
}

export function useQuestionSets(oppositionId: string | null) {
  return useQuery({
    queryKey: queryKeys.questionSets(oppositionId ?? 'todas'),
    queryFn: () => fetchQuestionSets(oppositionId),
  });
}

export function useQuestionSet(setId: string | null) {
  return useQuery({
    queryKey: queryKeys.questionSet(setId ?? 'ninguno'),
    queryFn: () => fetchQuestionSet(setId as string),
    enabled: setId !== null,
  });
}

export function useSetQuestions(
  setId: string | null,
  filtros: { status: string; originType: string; onlyReserves: boolean; offset?: number },
) {
  // El desplazamiento entra en la clave: dos páginas del mismo filtro son dos respuestas distintas.
  const clave = `${filtros.status}|${filtros.originType}|${String(filtros.onlyReserves)}|${String(filtros.offset ?? 0)}`;
  return useQuery({
    queryKey: queryKeys.setQuestions(setId ?? 'ninguno', clave),
    queryFn: () => fetchSetQuestions(setId as string, filtros),
    enabled: setId !== null,
  });
}

export function useQuestion(questionId: string | null) {
  return useQuery({
    queryKey: queryKeys.question(questionId ?? 'ninguna'),
    queryFn: () => fetchQuestion(questionId as string),
    enabled: questionId !== null,
  });
}

/** Evidencia que sostiene la pregunta. Vacío es una respuesta, no un error. */
export function useQuestionEvidence(questionId: string | null) {
  return useQuery({
    queryKey: queryKeys.questionEvidence(questionId ?? 'ninguna'),
    queryFn: () => fetchQuestionEvidence(questionId as string),
    enabled: questionId !== null,
  });
}

/** Explicaciones de la pregunta y de cada opción (S12.7). */
export function useQuestionExplanations(questionId: string | null) {
  return useQuery({
    queryKey: queryKeys.questionExplanations(questionId ?? 'ninguna'),
    queryFn: () => fetchExplanations(questionId as string),
    enabled: questionId !== null,
  });
}

/**
 * Escribe o sustituye la explicación de un hueco (la pregunta entera o una de sus opciones).
 *
 * Al guardar se recargan las explicaciones de esa pregunta: la identidad es `(pregunta, opción)`, así
 * que la respuesta del servidor sustituye a la que había y la ficha tiene que enseñar la nueva.
 */
export function useSetQuestionExplanation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: { questionId: string; text: string; optionStableKey: string | null }) =>
      setExplanation(input.questionId, {
        text: input.text,
        optionStableKey: input.optionStableKey,
      }),
    onSuccess: (_explicacion, input) => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.questionExplanations(input.questionId),
      });
    },
  });
}

export function useAnswerKeys(setId: string | null) {
  return useQuery({
    queryKey: queryKeys.answerKeys(setId ?? 'ninguno'),
    queryFn: () => fetchAnswerKeys(setId as string),
    enabled: setId !== null,
  });
}

export function useCreateQuestionSet() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: CreateQuestionSet) => createQuestionSet(input),
    onSuccess: () => {
      invalidateQuestions(queryClient);
    },
  });
}

export interface ParseIntoSetInput {
  setId: string;
  kind: ImportKind;
  text: string;
  mapping?: CsvMapping | null;
}

/**
 * Importa las preguntas de una versión de documento (DEBT-010).
 *
 * Va aparte de `useParseIntoSet` porque no manda texto: manda la versión, y lo que entra lo decide el
 * servidor leyendo el documento. Mezclarlas obligaría a que el asistente de texto aceptara un cuerpo
 * sin texto, que es justo lo que no es.
 */
export function useImportQuestionsFromDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: { setId: string; documentVersionId: string }) =>
      importQuestionsFromDocument(input.setId, input.documentVersionId),
    onSuccess: () => {
      invalidateQuestions(queryClient);
    },
  });
}

export function useParseIntoSet() {
  const queryClient = useQueryClient();
  return useMutation({
    // El mapeo solo se manda cuando existe: con `exactOptionalPropertyTypes`, pasar un `undefined`
    // explícito no es lo mismo que no pasar la propiedad, y el contrato distingue las dos cosas.
    mutationFn: (input: ParseIntoSetInput) =>
      input.mapping === undefined || input.mapping === null
        ? parseIntoSet(input.setId, { kind: input.kind, text: input.text })
        : parseIntoSet(input.setId, {
            kind: input.kind,
            text: input.text,
            mapping: input.mapping,
          }),
    onSuccess: () => {
      invalidateQuestions(queryClient);
    },
  });
}

export interface PatchQuestionInput {
  questionId: string;
  changes: PatchQuestion;
}

export function usePatchQuestion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: PatchQuestionInput) => patchQuestion(input.questionId, input.changes),
    onSuccess: () => {
      invalidateQuestions(queryClient);
    },
  });
}

export interface CorrectQuestionInput {
  questionId: string;
  note: string;
  stem?: string | null;
  options?: string[] | null;
}

export function useCorrectQuestion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: CorrectQuestionInput) =>
      correctQuestion(input.questionId, {
        note: input.note,
        stem: input.stem ?? null,
        options: input.options ?? null,
      }),
    onSuccess: () => {
      invalidateQuestions(queryClient);
    },
  });
}

export interface ReportIssueInput {
  questionId: string;
  kind: IssueKind;
  detail: string;
}

export function useReportIssue() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: ReportIssueInput) =>
      reportQuestionIssue(input.questionId, { kind: input.kind, detail: input.detail }),
    onSuccess: () => {
      invalidateQuestions(queryClient);
    },
  });
}

export interface ActivateKeyInput {
  setId: string;
  keyId: string;
}

export function useActivateAnswerKey() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: ActivateKeyInput) => activateAnswerKey(input.setId, input.keyId),
    onSuccess: () => {
      // Activar una plantilla cambia la corrección de las sesiones ya terminadas, así que se relee
      // también la cuenta de desactualizadas, que cuelga de «questions» (DEBT-013).
      invalidateQuestions(queryClient);
    },
  });
}

/**
 * Las sesiones terminadas del conjunto sin corregir con su plantilla activa (DEBT-013).
 *
 * Se lee por conjunto y no se deduce en el navegador: quién está al día depende de la evaluación
 * **vigente** de cada intento, y eso solo lo sabe el servidor.
 */
export function useOutdatedSessions(setId: string | null) {
  return useQuery({
    queryKey: queryKeys.outdatedSessions(setId ?? 'ninguno'),
    queryFn: () => fetchOutdatedSessions(setId as string),
    enabled: setId !== null,
  });
}

/** Recalcula en bloque las sesiones del conjunto. El informe dice qué cambió en cada una. */
export function useRecalculateSetSessions() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (setId: string) => recalculateSetSessions(setId),
    onSuccess: () => {
      // Recalcular mueve la puntuación de sesiones que quizá se estén mirando en otra pantalla, así
      // que se invalida todo lo que cuelga de las sesiones, además del banco (que lleva la cuenta de
      // desactualizadas).
      void queryClient.invalidateQueries({ queryKey: ['study'] });
      invalidateQuestions(queryClient);
    },
  });
}

export interface MarkKeySupersedesInput {
  keyId: string;
  supersededId: string;
}

export function useMarkKeySupersedes() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: MarkKeySupersedesInput) =>
      markKeySupersedes(input.keyId, input.supersededId),
    onSuccess: () => {
      invalidateQuestions(queryClient);
    },
  });
}

/* ------------------------------------------------------------------ S07: sesiones de estudio */

/** Invalida todo lo de estudio: crear, responder o terminar cambia sesión, progreso y resultado. */
function invalidateStudy(queryClient: QueryClient, sessionId: string): void {
  void queryClient.invalidateQueries({ queryKey: ['study'] });
  void queryClient.invalidateQueries({ queryKey: queryKeys.studySession(sessionId) });
}

export function useStudySessions(oppositionId: string | null) {
  return useQuery({
    queryKey: queryKeys.studySessions(oppositionId ?? 'todas'),
    queryFn: () => fetchSessions(oppositionId),
  });
}

export function useStudySession(sessionId: string | null) {
  return useQuery({
    queryKey: queryKeys.studySession(sessionId ?? 'ninguna'),
    queryFn: () => fetchSession(sessionId as string),
    enabled: sessionId !== null,
  });
}

export function useCurrentQuestion(sessionId: string | null) {
  return useQuery({
    queryKey: queryKeys.studyCurrent(sessionId ?? 'ninguna'),
    queryFn: () => fetchCurrentQuestion(sessionId as string),
    enabled: sessionId !== null,
  });
}

export function useStudyReview(sessionId: string | null, enabled = true) {
  return useQuery({
    queryKey: queryKeys.studyReview(sessionId ?? 'ninguna'),
    queryFn: () => fetchSessionReview(sessionId as string),
    enabled: sessionId !== null && enabled,
  });
}

export function useStudyResult(sessionId: string | null, enabled = true) {
  return useQuery({
    queryKey: queryKeys.studyResult(sessionId ?? 'ninguna'),
    queryFn: () => fetchSessionResult(sessionId as string),
    enabled: sessionId !== null && enabled,
  });
}

/**
 * La lectura por temas de un diagnóstico (DEBT-012).
 *
 * Se pide **solo** cuando la sesión es un diagnóstico: en otro modo el servidor responde 409, y pedirla
 * para que falle sería ruido en la pantalla y en los registros.
 */
export function useDiagnosticReading(sessionId: string | null, enabled = true) {
  return useQuery({
    queryKey: queryKeys.studyDiagnostic(sessionId ?? 'ninguna'),
    queryFn: () => fetchDiagnosticReading(sessionId as string),
    enabled: sessionId !== null && enabled,
  });
}

export function useCreateStudySession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: CreateSession) => createSession(input),
    onSuccess: (session) => {
      invalidateStudy(queryClient, session.id);
    },
  });
}

export function useStartStudySession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (sessionId: string) => startSession(sessionId),
    onSuccess: (session) => {
      invalidateStudy(queryClient, session.id);
    },
  });
}

export interface NavigateStudyInput {
  sessionId: string;
  navigation: NavigateRequest;
}

export function useNavigateStudy() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: NavigateStudyInput) => navigateSession(input.sessionId, input.navigation),
    onSuccess: (_datos, input) => {
      invalidateStudy(queryClient, input.sessionId);
    },
  });
}

export interface AnswerStudyInput {
  sessionId: string;
  answer: AnswerRequest;
}

export function useAnswerQuestion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: AnswerStudyInput) => answerQuestion(input.sessionId, input.answer),
    onSuccess: (_datos, input) => {
      invalidateStudy(queryClient, input.sessionId);
    },
  });
}

export function useFinishStudySession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (sessionId: string) => finishSession(sessionId),
    onSuccess: (resultado) => {
      invalidateStudy(queryClient, resultado.session_id);
    },
  });
}

export function useRecalculateStudySession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (sessionId: string) => recalculateSession(sessionId),
    onSuccess: (resultado) => {
      invalidateStudy(queryClient, resultado.session_id);
    },
  });
}

/* ------------------------------------------------------------------ S09: búsqueda y RAG */

export function useSearchResults(input: SearchRequest | null) {
  return useQuery({
    queryKey: queryKeys.searchResults(input?.query ?? '', input?.version_mode ?? 'current'),
    queryFn: () => searchCorpus(input as SearchRequest),
    enabled: input !== null && input.query.trim() !== '',
  });
}

export function useAskCorpus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: AskRequest) => askCorpus(input),
    onSuccess: (consulta) => {
      queryClient.setQueryData(queryKeys.ragQuery(consulta.id), consulta);
    },
  });
}

export function useRagQuery(queryId: string | null) {
  return useQuery({
    queryKey: queryKeys.ragQuery(queryId ?? 'ninguna'),
    queryFn: () => fetchRagQuery(queryId as string),
    enabled: queryId !== null,
  });
}

export function useRetrieval(queryId: string | null) {
  return useQuery({
    queryKey: queryKeys.retrieval(queryId ?? 'ninguna'),
    queryFn: () => fetchRetrieval(queryId as string),
    enabled: queryId !== null,
  });
}

/* ------------------------------------------------------------------ S10: errores y repaso */

/** Invalida todo lo que cambia al repasar o al clasificar un fallo: cola, conceptos e historial. */
function invalidateReview(queryClient: QueryClient, oppositionId: string | null): void {
  void queryClient.invalidateQueries({
    queryKey: queryKeys.reviewQueue(oppositionId ?? 'todas'),
  });
  void queryClient.invalidateQueries({
    queryKey: queryKeys.learningErrors(oppositionId ?? 'todas'),
  });
  void queryClient.invalidateQueries({ queryKey: ['review', 'error'] });
  void queryClient.invalidateQueries({ queryKey: ['review', 'item'] });
  void queryClient.invalidateQueries({ queryKey: queryKeys.mastery(oppositionId ?? 'todas') });
}

export function useReviewQueue(oppositionId: string | null) {
  return useQuery({
    queryKey: queryKeys.reviewQueue(oppositionId ?? 'todas'),
    queryFn: () => fetchReviewQueue(oppositionId),
  });
}

export function useLearningErrors(oppositionId: string | null) {
  return useQuery({
    queryKey: queryKeys.learningErrors(oppositionId ?? 'todas'),
    queryFn: () => fetchLearningErrors(oppositionId),
  });
}

export function useLearningError(errorId: string | null) {
  return useQuery({
    queryKey: queryKeys.learningError(errorId ?? 'ninguno'),
    queryFn: () => fetchLearningError(errorId as string),
    enabled: errorId !== null,
  });
}

export function useReviewHistory(reviewId: string | null) {
  return useQuery({
    queryKey: queryKeys.reviewHistory(reviewId ?? 'ninguno'),
    queryFn: () => fetchReviewHistory(reviewId as string),
    enabled: reviewId !== null,
  });
}

export function useMastery(oppositionId: string | null) {
  return useQuery({
    queryKey: queryKeys.mastery(oppositionId ?? 'todas'),
    queryFn: () => fetchMastery(oppositionId),
  });
}

export function useClassifyError(oppositionId: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: {
      attemptId: string;
      cause: ErrorCause;
      conceptLabel: string | null;
      curriculumNodeId: string | null;
      note: string | null;
    }) =>
      classifyError(input.attemptId, {
        cause: input.cause,
        concept_label: input.conceptLabel,
        curriculum_node_id: input.curriculumNodeId,
        note: input.note,
      }),
    onSuccess: () => {
      invalidateReview(queryClient, oppositionId);
    },
  });
}

export function useCompleteReview(oppositionId: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: {
      reviewId: string;
      outcome: 'correct' | 'wrong';
      confidence: 'low' | 'medium' | 'high' | null;
      cause: ErrorCause | null;
      note: string | null;
    }) =>
      completeReview(input.reviewId, {
        outcome: input.outcome,
        confidence: input.confidence,
        cause: input.cause,
        note: input.note,
      }),
    onSuccess: () => {
      invalidateReview(queryClient, oppositionId);
    },
  });
}

export function useSnoozeReview(oppositionId: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: { reviewId: string; days: number }) =>
      snoozeReview(input.reviewId, input.days),
    onSuccess: () => {
      invalidateReview(queryClient, oppositionId);
    },
  });
}

export function useResolveError(oppositionId: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: { errorId: string; resolved: boolean; note: string | null }) =>
      resolveError(input.errorId, { resolved: input.resolved, note: input.note }),
    onSuccess: () => {
      invalidateReview(queryClient, oppositionId);
    },
  });
}

export function useExportBank() {
  return useMutation({
    mutationFn: (input: { format: 'anki-csv' | 'markdown'; request: ExportRequest }) =>
      exportBank(input.format, input.request),
  });
}

/* ------------------------------------------------------------------ S11: cambios y derivados */

/** Invalida lo que cambia al confirmar un cambio: los conjuntos, los derivados y la biblioteca. */
function invalidateChanges(queryClient: QueryClient): void {
  void queryClient.invalidateQueries({ queryKey: ['change'] });
  void queryClient.invalidateQueries({ queryKey: ['library'] });
}

export function useChangeSets() {
  return useQuery({ queryKey: queryKeys.changeSets(), queryFn: fetchChangeSets });
}

export function useChangeSet(changeId: string | null) {
  return useQuery({
    queryKey: queryKeys.changeSet(changeId ?? 'ninguno'),
    queryFn: () => fetchChangeSet(changeId as string),
    enabled: changeId !== null,
  });
}

export function useDerivedArtifacts(needsReview?: boolean) {
  return useQuery({
    queryKey: queryKeys.derivedArtifacts(needsReview === undefined ? 'todos' : String(needsReview)),
    queryFn: () => fetchDerivedArtifacts(needsReview),
  });
}

export function useConfirmChangeSet() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (changeId: string) => confirmChangeSet(changeId),
    onSuccess: () => {
      invalidateChanges(queryClient);
    },
  });
}

export function useDiscardChangeSet() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (changeId: string) => discardChangeSet(changeId),
    onSuccess: () => {
      invalidateChanges(queryClient);
    },
  });
}

export function useCreateSummary() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: CreateSummary) => createSummary(input),
    onSuccess: () => {
      queryClient.setQueryData(queryKeys.derivedArtifacts('todos'), undefined);
      invalidateChanges(queryClient);
    },
  });
}

export function useResolveDerivedArtifact() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: { artifactId: string; resolution: 'reviewed' | 'discarded' }) =>
      resolveDerivedArtifact(input.artifactId, input.resolution),
    onSuccess: () => {
      invalidateChanges(queryClient);
    },
  });
}

/* --- S12: copias, almacén y diagnóstico ------------------------------------------------------- */

/**
 * Invalida todo lo que cambia cuando se toca el almacén.
 *
 * Una copia, una restauración, una retirada o un reindexado cambian a la vez el uso de disco, la
 * lista de copias, el estado del índice y los recuentos del diagnóstico: invalidar solo una parte
 * dejaría la pantalla enseñando cifras de antes del cambio.
 */
function invalidateMaintenance(queryClient: QueryClient): void {
  void queryClient.invalidateQueries({ queryKey: ['maintenance'] });
}

export function useBackups() {
  return useQuery({ queryKey: queryKeys.backups(), queryFn: fetchBackups });
}

export function useHousekeeping() {
  return useQuery({ queryKey: queryKeys.housekeeping(), queryFn: fetchHousekeeping });
}

export function useIndexHealth() {
  return useQuery({ queryKey: queryKeys.indexHealth(), queryFn: fetchIndexHealth });
}

export function useDiagnostic() {
  return useQuery({ queryKey: queryKeys.diagnostic(), queryFn: fetchDiagnostic });
}

export function useCreateBackup() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (note: string | null) => createBackup(note),
    onSuccess: () => {
      invalidateMaintenance(queryClient);
    },
  });
}

export function useVerifyBackup() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (backupId: string) => verifyBackup(backupId),
    onSuccess: () => {
      invalidateMaintenance(queryClient);
    },
  });
}

export function useValidateRestore() {
  return useMutation({ mutationFn: (backupId: string) => validateRestore(backupId) });
}

export function useExecuteRestore() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (backupId: string) => executeRestore(backupId),
    onSuccess: () => {
      invalidateMaintenance(queryClient);
    },
  });
}

export function usePurge() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: { action: PurgeActionValue; references: string[] | null }) =>
      purge(input.action, input.references),
    onSuccess: () => {
      invalidateMaintenance(queryClient);
      // Retirar material cambia lo que la biblioteca y la bandeja pueden contar.
      void queryClient.invalidateQueries({ queryKey: ['library'] });
      void queryClient.invalidateQueries({ queryKey: ['tray'] });
    },
  });
}

export function useReindex() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: reindex,
    onSuccess: () => {
      invalidateMaintenance(queryClient);
      void queryClient.invalidateQueries({ queryKey: ['search'] });
    },
  });
}

/**
 * Quita un miembro de una colección.
 *
 * Invalida la biblioteca entera como el alta: si el filtro por colección está activo, los documentos
 * que se están viendo cambian con esta operación.
 */
export function useRemoveFromCollection() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: { collectionId: string; subjectId: string }) =>
      removeFromCollection(input.collectionId, input.subjectId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['library'] });
    },
  });
}

export function useDiagnosticText() {
  return useMutation({ mutationFn: fetchDiagnosticText });
}

/* --------------------------------------------------- S12.6: ¿está listo para estudiar? */

/**
 * El resumen de preparación de una oposición: material por papel, preguntas por tema y claves activas.
 *
 * Se refresca a los 30 segundos como los perfiles: lo que cuenta cambia cuando el propietario acepta
 * material o activa una clave, y volver a Inicio tiene que enseñar el estado de ahora, no el de la
 * primera carga.
 */
export function useStudyReadiness(oppositionId: string | null) {
  return useQuery({
    queryKey: queryKeys.studyReadiness(oppositionId ?? 'ninguna'),
    queryFn: () => fetchStudyReadiness(oppositionId as string),
    enabled: oppositionId !== null,
    staleTime: 30_000,
  });
}

/**
 * Lo que sigue esperando una decisión de una persona.
 *
 * No se refresca sola con la misma prisa: es una lista de tareas, no un dato vivo. Se recarga al
 * volver a la pantalla y cuando una acción de la propia interfaz invalida `['profiles']`.
 */
export function usePendingActions() {
  return useQuery({
    queryKey: queryKeys.pendingActions,
    queryFn: fetchPendingActions,
    staleTime: 30_000,
  });
}

/**
 * Cuántas preguntas están en conflicto (07_UI-UX §2: el contador de la navegación).
 *
 * Es una consulta de una fila: se pide el total, no el banco.
 */
export function useConflictingQuestions() {
  return useQuery({
    queryKey: queryKeys.conflictingQuestions,
    queryFn: fetchConflictingQuestions,
    staleTime: 30_000,
  });
}
