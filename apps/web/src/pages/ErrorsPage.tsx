import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { isApiError } from '../api/client';
import { queueSummary } from '../api/reviews';
import type { ExportResult } from '../api/reviews';
import {
  useCompleteReview,
  useExportBank,
  useLearningError,
  useLearningErrors,
  useOppositions,
  useResolveError,
  useReviewQueue,
  useSnoozeReview,
  useCreateStudySession,
} from '../api/queries';
import { ErrorState } from '../components/ErrorState';
import { LoadingState } from '../components/LoadingState';
import { ConceptList } from '../features/errors/ConceptList';
import { ExportPanel } from '../features/errors/ExportPanel';
import { ReviewQueueList } from '../features/errors/ReviewQueueList';

type TabId = 'hoy' | 'conceptos';

const TABS: readonly { id: TabId; label: string }[] = [
  { id: 'hoy', label: 'Hoy' },
  { id: 'conceptos', label: 'Conceptos' },
];

function describeError(error: unknown): string {
  return error instanceof Error ? error.message : 'Error desconocido';
}

/**
 * Errores y repaso (07_UI-UX §9 y 06_QUESTIONS §8).
 *
 * Tres cosas que la pantalla hace porque son la razón de ser del slice:
 *
 * 1. **la cola explica por qué está ahí**: cada elemento dice qué toca, cuánto lleva vencido y con qué
 *    motivo se reprogramó, en lugar de ser una lista de fechas;
 * 2. **repasar es contestar**: el repaso de verdad se hace en una sesión compuesta con lo vencido (no
 *    se enseña la solución antes del intento), y declarar el resultado queda para lo que se repasa
 *    fuera, dicho como lo que es;
 * 3. **el error lo declara quien estudia**: la causa, el concepto y la nota son suyos, y la ficha
 *    enseña el historial del repaso con sus dos fechas y su motivo.
 */
export function ErrorsPage() {
  const navigate = useNavigate();
  const [tab, setTab] = useState<TabId>('hoy');
  const [errorId, setErrorId] = useState<string | null>(null);
  const [exportResult, setExportResult] = useState<ExportResult | undefined>(undefined);

  const oppositions = useOppositions();
  const activa = oppositions.data?.find((oposicion) => oposicion.active) ?? null;
  const oppositionId = activa?.id ?? null;

  const cola = useReviewQueue(oppositionId);
  const conceptos = useLearningErrors(oppositionId);
  const detalle = useLearningError(errorId);

  const completar = useCompleteReview(oppositionId);
  const aplazar = useSnoozeReview(oppositionId);
  const resolver = useResolveError(oppositionId);
  const exportar = useExportBank();
  const crearSesion = useCreateStudySession();

  const busy =
    completar.isPending ||
    aplazar.isPending ||
    resolver.isPending ||
    exportar.isPending ||
    crearSesion.isPending;

  const conflicto =
    [completar.error, aplazar.error, resolver.error].find((fallo) => isApiError(fallo, 409)) ?? null;
  const otroError =
    [completar.error, aplazar.error, resolver.error].find(
      (fallo) => fallo !== null && !isApiError(fallo, 409),
    ) ?? null;
  const conflictoExport =
    exportar.error !== null && isApiError(exportar.error, 409) ? describeError(exportar.error) : null;
  const errorExport =
    exportar.error === null || conflictoExport !== null ? null : describeError(exportar.error);

  return (
    <>
      <header className="page__header">
        <h1>Errores</h1>
        <p className="page__lead">
          Lo que fallaste y cuándo toca repasarlo. Un fallo entra solo en la cola; la causa, el
          concepto y la nota los pones tú, y el repaso va subiendo el intervalo hasta un mes.
        </p>
      </header>

      {oppositions.isPending && <LoadingState label="Cargando oposiciones…" />}
      {oppositions.isError && (
        <ErrorState
          title="No se pudieron cargar las oposiciones"
          message="Comprueba que la API está en marcha y que los perfiles se han sembrado."
          onRetry={() => {
            void oppositions.refetch();
          }}
        />
      )}
      {oppositions.isSuccess && activa === null && (
        <p className="hint">
          Sin una oposición activa no hay repaso que enseñar: la cola cuelga de la oposición.
        </p>
      )}

      {oppositions.isSuccess && activa !== null && (
        <section className="card" aria-labelledby="cola-repaso">
          <h2 id="cola-repaso">Repaso</h2>
          {cola.isPending && <LoadingState label="Leyendo la cola de repaso…" />}
          {cola.isError && (
            <ErrorState
              title="No se pudo leer la cola de repaso"
              message="El servidor no ha devuelto lo que toca hoy."
              onRetry={() => {
                void cola.refetch();
              }}
            />
          )}
          {cola.data !== undefined && (
            <>
              <p className="hint">
                {queueSummary(cola.data)} · {cola.data.stats.lapses} fallo(s) acumulado(s)
              </p>
              {cola.data.notes.map((nota) => (
                <p className="hint" key={nota}>
                  {nota}
                </p>
              ))}
              <div className="tabs" role="tablist" aria-label="Partes del repaso">
                {TABS.map((item) => (
                  <button
                    key={item.id}
                    id={`pestana-errores-${item.id}`}
                    className={item.id === tab ? 'tabs__tab tabs__tab--active' : 'tabs__tab'}
                    type="button"
                    role="tab"
                    aria-selected={item.id === tab}
                    aria-controls={`panel-errores-${item.id}`}
                    onClick={() => {
                      setTab(item.id);
                    }}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
              <div
                id={`panel-errores-${tab}`}
                role="tabpanel"
                aria-labelledby={`pestana-errores-${tab}`}
                className="tabs__panel"
              >
                {tab === 'hoy' && (
                  <ReviewQueueList
                    items={cola.data.items}
                    busy={busy}
                    error={otroError === null ? null : describeError(otroError)}
                    conflict={conflicto === null ? null : describeError(conflicto)}
                    onComplete={(input) => {
                      completar.mutate(input);
                    }}
                    onSnooze={(input) => {
                      aplazar.mutate(input);
                    }}
                    onStudyQueue={() => {
                      crearSesion.mutate(
                        {
                          opposition_id: activa.id,
                          mode: 'error_review',
                          sources: [],
                          shuffle: false,
                        },
                        {
                          onSuccess: () => {
                            // La sesión de repaso es la más reciente, y Estudiar abre la más
                            // reciente: se navega sin inventar un parámetro que nadie lee.
                            void navigate('/estudiar');
                          },
                        },
                      );
                    }}
                  />
                )}
                {tab === 'conceptos' && (
                  <ConceptList
                    concepts={conceptos.data?.groups ?? []}
                    selectedId={errorId}
                    detail={detalle.data}
                    detailIsPending={detalle.isPending}
                    detailIsError={detalle.isError}
                    busy={busy}
                    onSelect={setErrorId}
                    onResolve={(input) => {
                      resolver.mutate(input);
                    }}
                    onRetryDetail={() => {
                      void detalle.refetch();
                    }}
                  />
                )}
              </div>
            </>
          )}
        </section>
      )}

      {oppositions.isSuccess && activa !== null && (
        <ExportPanel
          defaultTitle={`Banco de ${activa.code}`}
          busy={exportar.isPending}
          error={errorExport}
          conflict={conflictoExport}
          result={exportResult}
          onExport={(input) => {
            exportar.mutate(
              {
                format: input.format,
                request: {
                  opposition_id: activa.id,
                  include_restricted: input.includeRestricted,
                  title: input.title,
                },
              },
              {
                onSuccess: (resultado) => {
                  setExportResult(resultado);
                },
              },
            );
          }}
        />
      )}
    </>
  );
}
