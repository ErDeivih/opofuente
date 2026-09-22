import { useEffect, useMemo, useState } from 'react';

import type {
  BulkDecisionResponse,
  Decision,
  DecisionOutcome,
  Proposal,
} from '../api/classification';
import { isApiError } from '../api/client';
import type { CurriculumNode } from '../api/profiles';
import {
  useBulkDecision,
  useCoverage,
  useCurriculum,
  useDecideProposal,
  useJob,
  useOppositions,
  useProposals,
  useReviewGroups,
  useRunClassification,
  useUndoDecision,
} from '../api/queries';
import { useQueryClient } from '@tanstack/react-query';
import { ErrorState } from '../components/ErrorState';
import { LoadingState } from '../components/LoadingState';
import { CoveragePanel } from '../features/review/CoveragePanel';
import type { SessionDecision } from '../features/review/DecisionHistory';
import { DecisionHistory } from '../features/review/DecisionHistory';
import { AcceptedClassificationPanel } from '../features/review/AcceptedClassificationPanel';
import { ProposalList } from '../features/review/ProposalList';
import { ReviewGroups } from '../features/review/ReviewGroups';
import { subjectLabel, valueLabel } from '../features/review/labels';

function describeError(error: unknown): string {
  return error instanceof Error ? error.message : 'Error desconocido';
}

/** Estados en los que un trabajo sigue trabajando: mientras dure, la pantalla lo sigue. */
const ACTIVE_JOB_STATUSES = new Set(['queued', 'leased', 'running', 'cancel_requested']);

/**
 * El avance de un trabajo, en palabras (DEBT-024).
 *
 * Un trabajo recién encolado informa 0 y ya terminado informa 1: en esos dos extremos el porcentaje
 * no dice nada que no diga el estado, así que solo se enseña mientras hay avance de verdad.
 */
function describeAvance(progress: number | undefined): string {
  if (typeof progress !== 'number' || progress <= 0 || progress >= 1) {
    return '';
  }
  return ` · ${String(Math.round(progress * 100))} %`;
}

/** Identificador con el que se deshace una decisión: su traza de auditoría, o la propuesta. */
function decisionId(outcome: DecisionOutcome): string {
  return outcome.audit_event_id ?? outcome.proposal_id;
}

/**
 * Revisión de la clasificación (07_UI-UX §4 «Revisión», 04 §8).
 *
 * Todo lo que se ve aquí es una **propuesta**: nada se aplica de forma definitiva sin que alguien lo
 * confirme, y lo que el motor aplicó solo por su banda de confianza se muestra como provisional y
 * reversible, no como un hecho. Las propuestas de autoridad y derechos —los ejes críticos— se marcan
 * como «requiere tu confirmación» porque el servidor no las aplica nunca solo, ni con confianza alta.
 *
 * La pantalla no decide ninguna regla: la banda, la criticidad, el valor legible y la cobertura
 * vienen del servidor. Aquí solo se decide cómo se cuentan y cómo se deja deshacer.
 */
export function ReviewPage() {
  const oppositions = useOppositions();
  const active = oppositions.data?.find((opposition) => opposition.active) ?? null;
  const convocationId = active?.active_convocation?.id ?? null;
  const curriculum = useCurriculum(convocationId);

  const pending = useProposals('pending');
  const provisional = useProposals('auto_applied_provisional');
  const groups = useReviewGroups();

  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const coverage = useCoverage(selectedNodeId);

  const decide = useDecideProposal();
  const bulk = useBulkDecision();
  const undo = useUndoDecision();
  const classify = useRunClassification();
  const [history, setHistory] = useState<SessionDecision[]>([]);

  // La pasada de clasificación es un **trabajo** (DEBT-024): se encola, se sigue por su id y, al
  // terminar, se recargan las propuestas. Mientras corre se dice en qué va, en lugar de dejar el
  // botón bloqueado sin explicación.
  const [classificationJobId, setClassificationJobId] = useState<string | null>(null);
  const classificationJob = useJob(classificationJobId);
  const queryClient = useQueryClient();
  const jobStatus = classificationJob.data?.status ?? null;
  const clasificando =
    classificationJobId !== null && (jobStatus === null || ACTIVE_JOB_STATUSES.has(jobStatus));

  useEffect(() => {
    if (jobStatus !== 'succeeded') {
      return;
    }
    // Terminó: ahora sí, lo que hay que releer son las propuestas.
    void queryClient.invalidateQueries({ queryKey: ['classification'] });
  }, [jobStatus, queryClient]);

  const proposals = useMemo(
    () => [...(pending.data?.proposals ?? []), ...(provisional.data?.proposals ?? [])],
    [pending.data, provisional.data],
  );
  // El panel de clasificación vigente muestra el material de la primera propuesta abierta: es el
  // que el usuario tiene delante en la cola.
  const primerSujeto = proposals[0];
  const byId = useMemo(
    () => new Map(proposals.map((proposal) => [proposal.id, proposal])),
    [proposals],
  );
  const curriculumNodes: CurriculumNode[] = curriculum.data?.nodes ?? [];
  const busy = decide.isPending || bulk.isPending || undo.isPending;
  const conflict = isApiError(decide.error, 409);

  function entry(outcome: DecisionOutcome, proposal: Proposal | undefined): SessionDecision {
    return {
      id: decisionId(outcome),
      label: proposal === undefined ? outcome.proposal_id : subjectLabel(proposal),
      value: proposal === undefined ? '—' : valueLabel(proposal),
      // El mismo material aparece como artefacto y como representación: sin el tipo de sujeto, dos
      // decisiones distintas comparten nombre accesible y «Deshacer» se vuelve ambiguo.
      subjectType: proposal === undefined ? undefined : proposal.subject_type,
      outcome,
      undone: false,
    };
  }

  function remember(outcomes: DecisionOutcome[], source: Map<string, Proposal>) {
    setHistory((previous) => [
      ...outcomes.map((outcome) => entry(outcome, source.get(outcome.proposal_id))),
      ...previous,
    ]);
  }

  function markUndone(id: string) {
    setHistory((previous) =>
      previous.map((decision) =>
        decision.id === id ? { ...decision, undone: true } : decision,
      ),
    );
  }

  function decideOne(input: {
    proposalId: string;
    decision: Decision;
    overrideValue?: string;
  }) {
    decide.mutate(input, {
      onSuccess: (outcome) => {
        remember([outcome], byId);
      },
    });
  }

  function decideBatch(input: {
    proposalIds: string[];
    excluded: string[];
    decision: Decision;
    note: string;
  }) {
    bulk.mutate(input, {
      onSuccess: (response: BulkDecisionResponse) => {
        remember(response.outcomes, byId);
      },
    });
  }

  /**
   * Deshace un lote entero, una decisión detrás de otra.
   *
   * En serie y no en paralelo: cada deshacer es una escritura auditada y el servidor las registra en
   * orden. Si una falla, las demás siguen y el historial enseña cuál se quedó sin deshacer.
   */
  function undoTenBatch(outcomes: DecisionOutcome[]) {
    void (async () => {
      for (const outcome of outcomes.filter((item) => item.applied)) {
        try {
          await undo.mutateAsync(decisionId(outcome));
          markUndone(decisionId(outcome));
        } catch {
          // La entrada se queda como estaba: un deshacer fallido no se disfraza de deshecho.
        }
      }
    })();
  }

  function undoOne(decision: SessionDecision) {
    undo.mutate(decision.id, {
      onSuccess: () => {
        markUndone(decision.id);
      },
    });
  }

  return (
    <>
      <header className="page__header">
        <h1>Revisión</h1>
        <p className="page__lead">
          Revisa lo que la aplicación propone sobre tu material: qué eje, qué valor, con qué confianza
          y con qué evidencia. Decidir aquí es lo que convierte una propuesta en algo aceptado.
        </p>
      </header>

      <section className="card notice" aria-labelledby="aviso-propuestas">
        <h2 id="aviso-propuestas">Esto son propuestas, no hechos</h2>
        <p>
          Nada de esta pantalla se aplicó por su cuenta: cada propuesta espera tu decisión. Lo que
          aparece como <strong>aplicada provisionalmente</strong> lo propuso el motor por su banda de
          confianza, es reversible y lo puedes confirmar, rechazar o deshacer. Las propuestas de{' '}
          <strong>autoridad</strong> y <strong>derechos</strong> no se aplican solas nunca, ni con
          confianza alta: requieren tu confirmación.
        </p>
        <p className="hint">
          Aceptar no convierte el material en oficial: solo lo aprueba para tu corpus (07_UI-UX §12).
        </p>
      </section>

      <section className="card" aria-labelledby="cola-revision">
        <h2 id="cola-revision">Cola de revisión</h2>
        <div className="form__row">
          <button
            className="button"
            type="button"
            disabled={classify.isPending || clasificando}
            onClick={() => {
              classify.mutate(undefined, {
                onSuccess: (trabajo) => {
                  setClassificationJobId(trabajo.id);
                },
              });
            }}
          >
            {clasificando ? 'Clasificando…' : 'Buscar propuestas ahora'}
          </button>
          <span className="hint">
            Una pasada de clasificación no cambia nada por sí sola: solo propone.
          </span>
        </div>
        {clasificando && (
          <p className="hint" role="status">
            {classificationJob.data?.step ?? 'Encolada: clasificando el material…'}
            {describeAvance(classificationJob.data?.progress)}
          </p>
        )}
        {jobStatus === 'succeeded' && (
          <p className="hint" role="status">
            {classificationJob.data?.step ?? 'Clasificación terminada.'}
          </p>
        )}
        {jobStatus !== null && !ACTIVE_JOB_STATUSES.has(jobStatus) && jobStatus !== 'succeeded' && (
          <ErrorState
            title="La clasificación no terminó"
            message={
              classificationJob.data?.error_message ?? 'El trabajo de clasificación falló.'
            }
            onRetry={() => {
              void classificationJob.refetch();
            }}
          />
        )}
        {classify.isError && (
          <ErrorState
            title="No se pudo clasificar el material"
            message={describeError(classify.error)}
          />
        )}
        {groups.isPending && <LoadingState label="Cargando los grupos de revisión…" />}
        {groups.isError && (
          <ErrorState
            title="No se pudieron cargar los grupos de revisión"
            message={describeError(groups.error)}
            onRetry={() => {
              void groups.refetch();
            }}
          />
        )}
        {groups.isSuccess && (
          <ReviewGroups
            groups={groups.data}
            proposals={pending.data?.proposals ?? []}
            busy={busy}
            result={bulk.data ?? null}
            onBulk={decideBatch}
            onUndoBatch={undoTenBatch}
          />
        )}
        {bulk.isError && (
          <ErrorState title="El lote no se pudo aplicar" message={describeError(bulk.error)} />
        )}
      </section>

      {primerSujeto !== undefined && (
        <AcceptedClassificationPanel
          subjectType={primerSujeto.subject_type}
          subjectId={primerSujeto.subject_id}
          subjectLabel={primerSujeto.subject_label}
        />
      )}

      <section className="card" aria-labelledby="propuestas">
        <h2 id="propuestas">Propuestas</h2>
        {(pending.isPending || provisional.isPending) && (
          <LoadingState label="Cargando las propuestas…" />
        )}
        {pending.isError && (
          <ErrorState
            title="No se pudieron cargar las propuestas"
            message={describeError(pending.error)}
            onRetry={() => {
              void pending.refetch();
            }}
          />
        )}
        {(pending.isSuccess || provisional.isSuccess) && (
          <ProposalList
            proposals={proposals}
            curriculumNodes={curriculumNodes}
            busy={busy}
            onDecide={decideOne}
          />
        )}
        {decide.isError && (
          <>
            <ErrorState
              title={conflict ? 'La decisión no se aplicó' : 'No se pudo aplicar la decisión'}
              message={describeError(decide.error)}
            />
            {conflict && (
              <p className="hint">
                Un conflicto no cambia nada: la propuesta se queda como estaba para que puedas
                revisarla con el motivo delante.
              </p>
            )}
          </>
        )}
      </section>

      {history.length > 0 && (
        <section className="card" aria-labelledby="historial-decisiones">
          <h2 id="historial-decisiones">Decisiones de esta sesión</h2>
          {undo.isError && (
            <ErrorState
              title="No se pudo deshacer la decisión"
              message={describeError(undo.error)}
            />
          )}
          <DecisionHistory decisions={history} busy={busy} onUndo={undoOne} />
        </section>
      )}

      <section className="card" aria-labelledby="cobertura">
        <h2 id="cobertura">Cobertura del programa</h2>
        {curriculum.isPending && convocationId !== null && (
          <LoadingState label="Cargando el programa…" />
        )}
        {curriculum.isError && (
          <ErrorState
            title="No se pudo cargar el programa"
            message="La convocatoria activa no tiene programa sembrado."
            onRetry={() => {
              void curriculum.refetch();
            }}
          />
        )}
        <CoveragePanel
          nodes={curriculumNodes}
          selectedId={selectedNodeId}
          onSelect={(node) => {
            setSelectedNodeId(node.id);
          }}
          coverage={coverage.data}
          isPending={coverage.isPending}
          isError={coverage.isError}
          onRetry={() => {
            void coverage.refetch();
          }}
          oppositionName={active?.name ?? null}
        />
      </section>
    </>
  );
}
