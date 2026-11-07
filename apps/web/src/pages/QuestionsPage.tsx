import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import { isApiError } from '../api/client';
import type { CsvMapping, ImportKind, IssueKind, QuestionImportReport } from '../api/questions';
import { PAGE_LIMIT, SET_TYPES } from '../api/questions';
import {
  useActivateAnswerKey,
  useAnswerKeys,
  useCorrectQuestion,
  useCreateQuestionSet,
  useDocuments,
  useImportQuestionsFromDocument,
  useMarkKeySupersedes,
  useOppositions,
  useOutdatedSessions,
  useParseIntoSet,
  usePatchQuestion,
  useQuestion,
  useQuestionEvidence,
  useQuestionSets,
  useRecalculateSetSessions,
  useReportIssue,
  useSetQuestions,
} from '../api/queries';
import { ErrorState } from '../components/ErrorState';
import { LoadingState } from '../components/LoadingState';
import { StatusBadge } from '../components/StatusBadge';
import { AnswerKeysPanel } from '../features/questions/AnswerKeysPanel';
import { ImportPanel } from '../features/questions/ImportPanel';
import { QuestionDetail } from '../features/questions/QuestionDetail';
import { QuestionTable } from '../features/questions/QuestionTable';
import { setStatusLabel, setTypeLabel } from '../features/questions/labels';

type TabId = 'preguntas' | 'importar' | 'claves';

const TABS: readonly { id: TabId; label: string }[] = [
  { id: 'preguntas', label: 'Preguntas' },
  { id: 'importar', label: 'Importar' },
  { id: 'claves', label: 'Plantillas' },
];

function describeError(error: unknown): string {
  return error instanceof Error ? error.message : 'Error desconocido';
}

/** «1 pregunta» / «2 preguntas»: el resumen del conjunto se lee, no se descuenta. */
function plural(cantidad: number, singular: string, plurales: string): string {
  return `${String(cantidad)} ${cantidad === 1 ? singular : plurales}`;
}

/**
 * Pantalla del banco de preguntas (07_UI-UX §7 y contrato §9).
 *
 * Tres cosas que la pantalla hace porque son la razón de ser del slice:
 *
 * 1. **los badges de origen son obligatorios** (OFICIAL / PRIVADA / GENERADA) y no se suavizan;
 * 2. **los conflictos van arriba**, no escondidos en un filtro: una clave que contradice a otra es lo
 *    primero que hay que mirar antes de estudiar con este banco;
 * 3. **lo que no entró se ve**: el informe de importación trae las filas rechazadas con su causa y se
 *    pueden descargar para arreglarlas, en lugar de desaparecer en silencio.
 */
export function QuestionsPage() {
  const [searchParams] = useSearchParams();
  // La ficha del tema enlaza aquí con `?conjunto=…&pregunta=…`: abrir el banco donde está la
  // pregunta evita que el alumno tenga que buscarla. Es un estado **inicial**, no una atadura: en
  // cuanto elige otra cosa, manda la pantalla.
  const conjuntoEnlazado = searchParams.get('conjunto');
  const preguntaEnlazada = searchParams.get('pregunta');
  const [tab, setTab] = useState<TabId>('preguntas');
  const [setIdElegido, setSetIdElegido] = useState<string | null>(conjuntoEnlazado);
  const [questionId, setQuestionId] = useState<string | null>(preguntaEnlazada);
  const [filters, setFilters] = useState({
    status: '',
    originType: '',
    onlyReserves: false,
    offset: 0,
  });
  const [report, setReport] = useState<QuestionImportReport | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [nuevo, setNuevo] = useState({
    title: '',
    setType: 'private_bank',
    modelCode: '',
  });

  const oppositions = useOppositions();
  const activa = oppositions.data?.find((oposicion) => oposicion.active) ?? null;
  const conjuntos = useQuestionSets(activa?.id ?? null);
  // El conjunto abierto se **deriva**: el elegido y, mientras nadie elija, el primero que haya. Sin
  // efecto que sincronice estado con la carga: obligar a un clic extra cuando hay un solo banco no
  // aporta nada.
  const setId = setIdElegido ?? conjuntos.data?.sets[0]?.id ?? null;
  const conjunto = conjuntos.data?.sets.find((candidato) => candidato.id === setId) ?? null;

  const preguntas = useSetQuestions(setId, filters);
  const detalle = useQuestion(questionId);
  const evidencia = useQuestionEvidence(questionId);
  const claves = useAnswerKeys(setId);
  // DEBT-013: activar una plantilla corregida no cambia sola las notas ya puestas, así que se cuenta
  // cuántas sesiones se quedan con la corrección vieja y se ofrece recalcularlas de una vez.
  const desactualizadas = useOutdatedSessions(setId);
  const recalcularConjunto = useRecalculateSetSessions();
  // DEBT-010: importar **desde un documento** necesita la biblioteca, para elegir de qué documento
  // salen las preguntas (y de qué versión: la activa, que es la aceptada).
  const biblioteca = useDocuments('', '');
  const importarDocumento = useImportQuestionsFromDocument();

  const crear = useCreateQuestionSet();
  const importar = useParseIntoSet();
  const editar = usePatchQuestion();
  const corregir = useCorrectQuestion();
  const reportar = useReportIssue();
  const activar = useActivateAnswerKey();
  const sustituir = useMarkKeySupersedes();

  // Cada zona muestra **sus** errores, y solo los suyos: si el mismo 409 se pintara en la página y
  // dentro del panel, la pantalla diría dos veces lo mismo.
  const falloCrear = crear.error ?? null;
  const falloImportar = importar.error ?? null;
  const falloFicha = editar.error ?? corregir.error ?? reportar.error ?? null;
  const falloClaves = activar.error ?? sustituir.error ?? null;
  const conflictoCrear = isApiError(falloCrear, 409) ? describeError(falloCrear) : null;
  const errorCrear =
    falloCrear === null || conflictoCrear !== null ? null : describeError(falloCrear);
  const conflictoImportar = isApiError(falloImportar, 409) ? describeError(falloImportar) : null;
  const errorImportar =
    falloImportar === null || conflictoImportar !== null ? null : describeError(falloImportar);
  const conflictoFicha = isApiError(falloFicha, 409) ? describeError(falloFicha) : null;
  const errorFicha =
    falloFicha === null || conflictoFicha !== null ? null : describeError(falloFicha);
  const conflictoClaves = isApiError(falloClaves, 409) ? describeError(falloClaves) : null;
  const errorClaves =
    falloClaves === null || conflictoClaves !== null ? null : describeError(falloClaves);
  const busy =
    crear.isPending ||
    importar.isPending ||
    editar.isPending ||
    corregir.isPending ||
    reportar.isPending ||
    activar.isPending ||
    sustituir.isPending;

  const duplicados = report?.duplicates ?? [];

  return (
    <>
      <header className="page__header">
        <h1>Preguntas</h1>
        <p className="hint">
          El banco de preguntas de una oposición: lo que se importa, lo que se revisa y la plantilla con
          la que se corrige. Importar no publica nada: una pregunta privada sigue siendo privada.
        </p>
      </header>

      {conjuntos.isPending && <LoadingState label="Cargando los conjuntos…" />}
      {conjuntos.isError && (
        <ErrorState
          title="No se pudieron cargar los conjuntos"
          message="El servidor no responde o la oposición no está disponible."
          onRetry={() => {
            void conjuntos.refetch();
          }}
        />
      )}

      <section className="card" aria-labelledby="conjuntos">
        <h2 id="conjuntos">Conjunto</h2>
        {conjuntos.data !== undefined && conjuntos.data.sets.length === 0 && (
          <p className="hint">
            Todavía no hay ningún conjunto de preguntas. Se crea aquí debajo: un examen oficial, un
            banco privado, práctica o un lote generado.
          </p>
        )}
        {conjuntos.data !== undefined && conjuntos.data.sets.length > 0 && (
          <div className="form__row">
            <label className="form__label" htmlFor="elegir-conjunto">
              Conjunto abierto
            </label>
            <select
              id="elegir-conjunto"
              className="selector__select"
              value={setId ?? ''}
              onChange={(event) => {
                setSetIdElegido(event.target.value);
                setQuestionId(null);
                setReport(null);
                setNotice(null);
              }}
            >
              {conjuntos.data.sets.map((candidato) => (
                <option key={candidato.id} value={candidato.id}>
                  {candidato.title} · {setTypeLabel(candidato.set_type)}
                  {candidato.model_code === null || candidato.model_code === undefined
                    ? ''
                    : ` · modelo ${candidato.model_code}`}
                </option>
              ))}
            </select>
            {conjunto !== null && (
              <span className="hint">
                {plural(conjunto.question_count, 'pregunta', 'preguntas')} (
                {plural(conjunto.incomplete_count, 'incompleta', 'incompletas')} ·{' '}
                {plural(conjunto.reserve_count, 'reserva', 'reservas')}) ·{' '}
                {plural(conjunto.key_count, 'plantilla', 'plantillas')}{' '}
                <StatusBadge tone={conjunto.status === 'confirmed' ? 'ok' : 'info'}>
                  {setStatusLabel(conjunto.status)}
                </StatusBadge>
                {conjunto.active_key_id === null || conjunto.active_key_id === undefined ? (
                  <>
                    {' '}
                    <StatusBadge tone="warning">sin clave activa</StatusBadge>
                  </>
                ) : (
                  <>
                    {' '}
                    <StatusBadge tone="ok">con clave activa</StatusBadge>
                  </>
                )}
              </span>
            )}
          </div>
        )}

        <details>
          <summary>Crear un conjunto</summary>
          <div className="form__row">
            <label className="form__label" htmlFor="nuevo-titulo">
              Título
            </label>
            <input
              id="nuevo-titulo"
              className="selector__select"
              value={nuevo.title}
              onChange={(event) => {
                setNuevo({ ...nuevo, title: event.target.value });
              }}
            />
            <label className="form__label" htmlFor="nuevo-tipo">
              Tipo
            </label>
            <select
              id="nuevo-tipo"
              className="selector__select"
              value={nuevo.setType}
              onChange={(event) => {
                setNuevo({ ...nuevo, setType: event.target.value });
              }}
            >
              {SET_TYPES.map((tipo) => (
                <option key={tipo} value={tipo}>
                  {setTypeLabel(tipo)}
                </option>
              ))}
            </select>
            <label className="form__label" htmlFor="nuevo-modelo">
              Modelo (A/B)
            </label>
            <input
              id="nuevo-modelo"
              className="selector__select"
              value={nuevo.modelCode}
              onChange={(event) => {
                setNuevo({ ...nuevo, modelCode: event.target.value });
              }}
            />
            <button
              className="button"
              type="button"
              disabled={busy || nuevo.title.trim() === '' || activa === null}
              aria-label="Crear el conjunto de preguntas"
              onClick={() => {
                if (activa === null) {
                  return;
                }
                crear.mutate(
                  {
                    title: nuevo.title.trim(),
                    opposition_id: activa.id,
                    set_type: nuevo.setType as (typeof SET_TYPES)[number],
                    model_code: nuevo.modelCode.trim() === '' ? null : nuevo.modelCode.trim(),
                    // La convocatoria de la oposición activa: sin ella el conjunto no cuelga de ningún
                    // programa, así que una columna `topic` no tendría contra qué resolverse (y la
                    // muestra por temas del diagnóstico se quedaría sin temas).
                    convocation_version_id: activa.active_convocation?.id ?? null,
                  },
                  {
                    onSuccess: (creado) => {
                      setSetIdElegido(creado.id);
                      setNuevo({ title: '', setType: 'private_bank', modelCode: '' });
                      setNotice(`Conjunto «${creado.title}» creado.`);
                    },
                  },
                );
              }}
            >
              Crear conjunto
            </button>
            {activa === null && (
              <p className="hint">
                Sin una oposición activa no se puede crear un conjunto: el banco cuelga de ella.
              </p>
            )}
          </div>
        </details>
      </section>

      {/* El error de crear un conjunto no tiene panel propio: se dice aquí. */}
      {conflictoCrear !== null && (
        <ErrorState title="El servidor rechazó la operación" message={conflictoCrear} />
      )}
      {errorCrear !== null && <ErrorState title="La operación no se aplicó" message={errorCrear} />}
      {notice !== null && <p className="hint">{notice}</p>}

      <section className="card" aria-labelledby="banco-preguntas">
        <h2 id="banco-preguntas">Banco</h2>
        <div className="tabs" role="tablist" aria-label="Partes del banco">
          {TABS.map((item) => (
            <button
              key={item.id}
              id={`pestana-preguntas-${item.id}`}
              className={item.id === tab ? 'tabs__tab tabs__tab--active' : 'tabs__tab'}
              type="button"
              role="tab"
              aria-selected={item.id === tab}
              aria-controls={`panel-preguntas-${item.id}`}
              onClick={() => {
                setTab(item.id);
              }}
            >
              {item.label}
            </button>
          ))}
        </div>

        <div
          id={`panel-preguntas-${tab}`}
          role="tabpanel"
          aria-labelledby={`pestana-preguntas-${tab}`}
          className="tabs__panel"
        >
          {setId === null ? (
            <p className="hint">Elige o crea un conjunto para trabajar con sus preguntas.</p>
          ) : (
            <>
              {tab === 'preguntas' && (
                <>
                  <QuestionTable
                    questions={preguntas.data?.questions ?? []}
                    total={preguntas.data?.total ?? 0}
                    filters={{ ...filters, limit: PAGE_LIMIT }}
                    onFiltersChange={setFilters}
                    selectedId={questionId}
                    onSelect={setQuestionId}
                    duplicates={duplicados}
                    isPending={preguntas.isPending}
                    isError={preguntas.isError}
                    onRetry={() => {
                      void preguntas.refetch();
                    }}
                  />
                  {detalle.isPending && questionId !== null && (
                    <LoadingState label="Cargando la pregunta…" />
                  )}
                  {detalle.data !== undefined && (
                    <QuestionDetail
                      // La ficha se remonta al cambiar de pregunta: sus formularios arrancan con
                      // el texto de la que se abre y no con el de la anterior.
                      key={detalle.data.id}
                      question={detalle.data}
                      evidence={evidencia.data ?? []}
                      evidenceIsPending={evidencia.isPending}
                      busy={busy}
                      conflict={conflictoFicha}
                      error={errorFicha}
                      onPatch={(changes) => {
                        editar.mutate(
                          { questionId: detalle.data.id, changes },
                          {
                            onSuccess: (guardada) => {
                              setNotice(
                                `Composición guardada: pregunta ${guardada.position}, ${guardada.question_type}.`,
                              );
                            },
                          },
                        );
                      }}
                      onCorrect={(input) => {
                        corregir.mutate(
                          { questionId: detalle.data.id, ...input },
                          {
                            onSuccess: (resultado) => {
                              setQuestionId(resultado.question.id);
                              setNotice(
                                `Corrección guardada como versión ${resultado.question.version_no}. El original no se ha tocado.`,
                              );
                            },
                          },
                        );
                      }}
                      onReportIssue={(input: { kind: IssueKind; detail: string }) => {
                        reportar.mutate(
                          {
                            questionId: detalle.data.id,
                            kind: input.kind,
                            detail: input.detail,
                          },
                          {
                            onSuccess: () => {
                              setNotice('Incidencia registrada: queda abierta para revisarla.');
                            },
                          },
                        );
                      }}
                    />
                  )}
                </>
              )}

              {tab === 'importar' && (
                <ImportPanel
                  onImport={(input: { kind: ImportKind; text: string; mapping: CsvMapping | null }) => {
                    importar.mutate(
                      { setId, kind: input.kind, text: input.text, mapping: input.mapping },
                      {
                        onSuccess: (informe) => {
                          setReport(informe);
                          setNotice(
                            `Importadas ${informe.created} preguntas nuevas y ${informe.key_entries} claves.`,
                          );
                        },
                      },
                    );
                  }}
                  onImportDocument={(documentVersionId) => {
                    importarDocumento.mutate(
                      { setId: setId, documentVersionId },
                      {
                        onSuccess: (informe) => {
                          setReport(informe);
                          setNotice(
                            `Importadas ${String(informe.created)} preguntas del documento, con ${String(informe.evidence_links)} cita(s).`,
                          );
                        },
                      },
                    );
                  }}
                  documents={biblioteca.data?.documents ?? []}
                  documentsIsPending={biblioteca.isPending}
                  documentsError={biblioteca.isError ? describeError(biblioteca.error) : null}
                  report={report}
                  isPending={importar.isPending || importarDocumento.isPending}
                  conflict={conflictoImportar}
                  error={errorImportar}
                />
              )}

              {tab === 'claves' && (
                <AnswerKeysPanel
                  keys={claves.data ?? []}
                  isPending={claves.isPending}
                  isError={claves.isError}
                  busy={busy}
                  conflict={conflictoClaves}
                  error={errorClaves}
                  onRetry={() => {
                    void claves.refetch();
                  }}
                  onActivate={(keyId) => {
                    activar.mutate(
                      { setId, keyId },
                      {
                        onSuccess: () => {
                          setNotice(
                            'Plantilla activada y aprobada con tu acción: queda registrado en la auditoría.',
                          );
                        },
                      },
                    );
                  }}
                  onSupersede={(keyId, supersededId) => {
                    sustituir.mutate(
                      { keyId, supersededId },
                      {
                        onSuccess: () => {
                          setNotice('Sustitución confirmada: la plantilla anterior se conserva.');
                        },
                      },
                    );
                  }}
                  outdated={desactualizadas.data ?? null}
                  outdatedPending={desactualizadas.isPending}
                  outdatedError={
                    desactualizadas.isError ? describeError(desactualizadas.error) : null
                  }
                  onRecalculate={() => {
                    if (setId === null) {
                      return;
                    }
                    recalcularConjunto.mutate(setId, {
                      onSuccess: (informe) => {
                        setNotice(
                          `Recalculadas ${String(informe.sessions.length)} sesión(es): ${String(informe.changed)} cambiaron.`,
                        );
                      },
                    });
                  }}
                  recalculating={recalcularConjunto.isPending}
                  recalculation={recalcularConjunto.data ?? null}
                  recalculateError={
                    recalcularConjunto.error === null
                      ? null
                      : describeError(recalcularConjunto.error)
                  }
                />
              )}
            </>
          )}
        </div>
      </section>
    </>
  );
}
