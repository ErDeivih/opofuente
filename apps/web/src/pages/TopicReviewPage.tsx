import { useCallback, useEffect, useMemo, useState } from 'react';

import { isApiError } from '../api/client';
import type {
  ProgrammeNodeRef,
  TopicAssignmentReport,
  TopicAssignmentRow,
  TopicProposalCard,
} from '../api/topicReview';
import {
  EXCLUSION_LABELS,
  PROPOSALS_LIMIT,
  REASON_CHANGED,
  REASON_EXCLUDED,
  REASON_PROMOTED,
  REASON_RETIRED,
} from '../api/topicReview';
import {
  useApplyTopicDecisions,
  useCurriculum,
  useOppositions,
  useQuestionExclusions,
  useTopicProposals,
} from '../api/queries';
import { EmptyState } from '../components/EmptyState';
import { ErrorState } from '../components/ErrorState';
import { LoadingState } from '../components/LoadingState';
import { ExclusionList } from '../features/topicReview/ExclusionList';
import { ProposalCard } from '../features/topicReview/ProposalCard';
import { indexProgramme } from '../features/topicReview/programme';

/** El tope del lote que acepta el servidor: al llegar aquí, la bandeja se guarda sola. */
const MAX_LOTE = 200;

/** Una decisión sin guardar: la fila que se mandará y lo que se lee en la bandeja. */
interface QueuedDecision {
  row: TopicAssignmentRow;
  label: string;
}

function describeError(error: unknown): string {
  return error instanceof Error ? error.message : 'Error desconocido';
}

/**
 * El tema ya decidido de una tarjeta, o `null`.
 *
 * El contrato marca `accepted` como opcional con nulo, así que «no tiene tema decidido» llega de dos
 * maneras (`undefined` y `null`) y comprobarlo en cada sitio sería repetir la misma defensa cinco
 * veces. Se resuelve una vez, aquí.
 */
function aceptado(card: TopicProposalCard): ProgrammeNodeRef | null {
  return card.accepted ?? null;
}

/**
 * Los atajos, en pantalla y en un solo sitio.
 *
 * Van escritos y no escondidos en un `aria-keyshortcuts`: el propietario va a despachar cientos y lo
 * que necesita es tenerlos delante hasta que se le queden. La lista es también la documentación de
 * la pantalla, así que vive al lado del código que los implementa.
 */
const ATAJOS: readonly { teclas: string; que: string }[] = [
  { teclas: 'J / ↓', que: 'siguiente pregunta' },
  { teclas: 'K / ↑', que: 'pregunta anterior' },
  { teclas: '1…9', que: 'elegir la propuesta N de esta pregunta' },
  { teclas: 'A', que: 'aceptar la propuesta elegida' },
  { teclas: 'C', que: 'cambiar de tema o de epígrafe' },
  { teclas: 'F', que: 'fuera de temario: de otra administración' },
  { teclas: 'X', que: 'fuera de temario: enunciado roto' },
  { teclas: 'R', que: 'retirar las propuestas que sobran (ya tiene tema)' },
  { teclas: 'S', que: 'saltar' },
  { teclas: 'G', que: 'guardar lo decidido (una sola llamada)' },
];

/**
 * La cola de revisión de la clasificación (F5): las propuestas de tema que dejó el clasificador.
 *
 * La pantalla existe para **despachar cientos de preguntas con el teclado**, y todo lo que hay en
 * ella sale de esa decisión:
 *
 * - se lee **una tarjeta por pregunta**, con el enunciado y sus opciones, porque una propuesta no se
 *   puede juzgar sin el texto delante; si la pregunta trae dos propuestas (dos corridas que se
 *   pisaron), se ven juntas y al decidir una la otra se retira;
 * - las decisiones se acumulan en una **bandeja** y se guardan de una vez: la ruta por lotes está
 *   para eso, y una petición por pregunta convertiría 500 preguntas en 500 peticiones;
 * - el fuera de temario se marca con su motivo y se puede **deshacer** asignando un tema, que es
 *   como el servidor levanta la marca;
 * - lo que queda pendiente se cuenta con la cifra del servidor, y cuando no queda nada se dice.
 *
 * La pantalla no decide ninguna regla: los umbrales, qué es una propuesta y qué se escribe al
 * decidirla viven en el servidor. Aquí solo se decide cómo se despacha.
 */
export function TopicReviewPage() {
  const [offset, setOffset] = useState(0);
  const proposals = useTopicProposals(offset);
  const exclusions = useQuestionExclusions(0);
  const oppositions = useOppositions();
  const active = oppositions.data?.find((opposition) => opposition.active) ?? null;
  const convocationId = active?.active_convocation?.id ?? null;
  const curriculum = useCurriculum(convocationId);
  const topics = useMemo(() => indexProgramme(curriculum.data?.nodes ?? []), [curriculum.data]);
  const apply = useApplyTopicDecisions();

  const cards = useMemo(() => proposals.data?.questions ?? [], [proposals.data]);
  const total = proposals.data?.total ?? 0;

  const [cursor, setCursor] = useState(0);
  const [chosen, setChosen] = useState<Record<string, number>>({});
  const [skipped, setSkipped] = useState<readonly string[]>([]);
  const [queued, setQueued] = useState<QueuedDecision[]>([]);
  const [changeFor, setChangeFor] = useState<string | null>(null);
  const [changeTopicId, setChangeTopicId] = useState('');
  const [changeEpigraphId, setChangeEpigraphId] = useState('');
  const [report, setReport] = useState<TopicAssignmentReport | null>(null);

  const decididas = useMemo(
    () => new Set(queued.map((decision) => decision.row.question_version_id)),
    [queued],
  );
  const visibles = useMemo(
    () => cards.filter((card) => !decididas.has(card.question_version_id)),
    [cards, decididas],
  );
  const actual = visibles[Math.min(cursor, Math.max(visibles.length - 1, 0))] ?? null;

  const guardar = useCallback(
    (decisiones: QueuedDecision[]) => {
      if (decisiones.length === 0) {
        return;
      }
      apply.mutate(
        decisiones.map((decision) => decision.row),
        {
          onSuccess: (resultado) => {
            setReport(resultado);
            setQueued((previo) => previo.filter((item) => !decisiones.includes(item)));
          },
        },
      );
    },
    [apply],
  );

  // Al llegar al tope del lote, se guarda solo: si no, la siguiente decisión haría que el servidor
  // rechazara la llamada entera (acepta 200 filas), y el propietario perdería la bandeja.
  useEffect(() => {
    if (queued.length >= MAX_LOTE && !apply.isPending) {
      guardar(queued);
    }
  }, [queued, apply.isPending, guardar]);

  const avanzar = useCallback(() => {
    if (cursor + 1 >= visibles.length && total > offset + cards.length) {
      setOffset(offset + PROPOSALS_LIMIT);
      setCursor(0);
      return;
    }
    setCursor((previo) => Math.min(previo + 1, Math.max(visibles.length - 1, 0)));
  }, [cursor, visibles.length, total, offset, cards.length]);

  /**
   * Encola una decisión y **deja el cursor donde está**.
   *
   * La tarjeta decidida desaparece de la lista, así que la siguiente ocupa su sitio: avanzar el
   * cursor además de quitarla se saltaría una pregunta, que es justo lo que no puede pasar cuando
   * se despachan cientos de corrido. Solo `saltar` mueve el cursor, porque ahí la tarjeta se queda.
   *
   * Si con esta decisión la página se queda sin tarjetas y quedan más por despachar, se pasa a la
   * siguiente: lo pendiente está en las páginas siguientes, no en una lista vacía.
   */
  const encolar = useCallback(
    (row: TopicAssignmentRow, label: string) => {
      setQueued((previo) => [...previo, { row, label }]);
      const restantes = visibles.filter(
        (card) => card.question_version_id !== row.question_version_id,
      );
      if (restantes.length === 0 && total > offset + cards.length) {
        setOffset(offset + PROPOSALS_LIMIT);
        setCursor(0);
        return;
      }
      setCursor((previo) => Math.min(previo, Math.max(restantes.length - 1, 0)));
    },
    [visibles, total, offset, cards.length],
  );

  const aceptar = useCallback(() => {
    if (actual === null || aceptado(actual) !== null) {
      return;
    }
    const propuesta = actual.proposals[chosen[actual.question_version_id] ?? 0] ?? actual.proposals[0];
    if (propuesta === undefined) {
      return;
    }
    encolar(
      {
        question_version_id: actual.question_version_id,
        curriculum_node_id: propuesta.topic.node_id,
        epigraph_node_id: propuesta.epigraphs[0]?.node_id ?? null,
        confidence: 1,
        reason: REASON_PROMOTED,
        status: 'accepted',
        retire_others: true,
      },
      `aceptada: ${propuesta.topic.path}`,
    );
  }, [actual, chosen, encolar]);

  const retirar = useCallback(() => {
    const yaDecidido = actual === null ? null : aceptado(actual);
    if (actual === null || yaDecidido === null) {
      return;
    }
    encolar(
      {
        question_version_id: actual.question_version_id,
        curriculum_node_id: yaDecidido.node_id,
        confidence: 1,
        reason: REASON_RETIRED,
        status: 'accepted',
        retire_others: true,
      },
      `retiradas las que sobraban de ${yaDecidido.path}`,
    );
  }, [actual, encolar]);

  const excluir = useCallback(
    (reason: 'otra_administracion' | 'enunciado_roto') => {
      if (actual === null) {
        return;
      }
      encolar(
        {
          question_version_id: actual.question_version_id,
          exclusion_reason: reason,
          confidence: 1,
          reason: REASON_EXCLUDED,
          retire_others: true,
        },
        `fuera de temario: ${EXCLUSION_LABELS[reason]}`,
      );
    },
    [actual, encolar],
  );

  const abrirCambio = useCallback(() => {
    if (actual === null || aceptado(actual) !== null) {
      return;
    }
    setChangeFor(actual.question_version_id);
    setChangeTopicId('');
    setChangeEpigraphId('');
  }, [actual]);

  const aplicarCambio = useCallback(() => {
    if (actual === null || changeTopicId === '') {
      return;
    }
    const tema = topics.find((item) => item.id === changeTopicId) ?? null;
    encolar(
      {
        question_version_id: actual.question_version_id,
        curriculum_node_id: changeTopicId,
        epigraph_node_id: changeEpigraphId === '' ? null : changeEpigraphId,
        confidence: 1,
        reason: REASON_CHANGED,
        status: 'accepted',
        retire_others: true,
      },
      `cambiada a ${tema?.path ?? changeTopicId}`,
    );
    setChangeFor(null);
  }, [actual, changeTopicId, changeEpigraphId, topics, encolar]);

  const saltar = useCallback(() => {
    if (actual !== null) {
      setSkipped((previo) =>
        previo.includes(actual.question_version_id)
          ? previo
          : [...previo, actual.question_version_id],
      );
    }
    avanzar();
  }, [actual, avanzar]);

  /** El teclado de la cola. Los campos del selector tienen el suyo y aquí no se tocan. */
  const alPulsar = useCallback(
    (event: KeyboardEvent) => {
      const objetivo = event.target;
      // Escribiendo en un campo (el selector de tema, un buscador) las teclas son suyas. La excepción
      // es Escape, que cierra el selector aunque el foco esté dentro.
      const enUnCampo =
        objetivo instanceof HTMLElement &&
        objetivo.closest('select, input, textarea, [contenteditable="true"]') !== null;
      if (enUnCampo && event.key !== 'Escape') {
        return;
      }
      const tecla = event.key.toLowerCase();
      if (/^[1-9]$/.test(tecla)) {
        event.preventDefault();
        if (actual !== null) {
          setChosen((previo) => ({ ...previo, [actual.question_version_id]: Number(tecla) - 1 }));
        }
        return;
      }
      const acciones: Record<string, () => void> = {
        j: avanzar,
        arrowdown: avanzar,
        k: () => {
          setCursor((previo) => Math.max(previo - 1, 0));
        },
        arrowup: () => {
          setCursor((previo) => Math.max(previo - 1, 0));
        },
        a: aceptar,
        c: abrirCambio,
        f: () => {
          excluir('otra_administracion');
        },
        x: () => {
          excluir('enunciado_roto');
        },
        r: retirar,
        s: saltar,
        g: () => {
          guardar(queued);
        },
        escape: () => {
          setChangeFor(null);
        },
      };
      const accion = acciones[tecla];
      if (accion !== undefined) {
        event.preventDefault();
        accion();
      }
    },
    [actual, avanzar, aceptar, abrirCambio, excluir, retirar, saltar, guardar, queued],
  );

  /*
   * El teclado se escucha en el documento y no en la cola, y es una decisión de producto: el
   * propietario va a despachar cientos de preguntas y no puede tener que *meterse* en la lista con
   * el tabulador antes de cada atajo. Se engancha al montar la pantalla y se suelta al salir de ella,
   * y mientras hay foco en un campo las teclas son del campo.
   */
  useEffect(() => {
    document.addEventListener('keydown', alPulsar);
    return () => {
      document.removeEventListener('keydown', alPulsar);
    };
  }, [alPulsar]);

  return (
    <>
      <header className="page__header">
        <h1>Clasificación</h1>
        <p className="page__lead">
          El clasificador propuso un tema para cada pregunta y dejó aparte las que no tenía claras.
          Aquí se despachan con el teclado: aceptar, cambiar el tema, marcar fuera de temario o
          saltar. Nada de esta pantalla cuenta para el alumno hasta que se decide.
        </p>
      </header>

      <section className="card" aria-labelledby="atajos">
        <h2 id="atajos">Atajos</h2>
        <ul className="shortcuts">
          {ATAJOS.map((atajo) => (
            <li key={atajo.teclas}>
              <kbd>{atajo.teclas}</kbd> {atajo.que}
            </li>
          ))}
        </ul>
        <p className="hint">
          Lo que se decide no se escribe hasta que se pulsa <kbd>G</kbd>: así se despachan cientos
          con una sola llamada en lugar de una por pregunta. Los campos de tema se manejan con las
          flechas y el Intro, como cualquier selector.
        </p>
      </section>

      <section className="card queue" aria-labelledby="cola-clasificacion">
        <h2 id="cola-clasificacion">
          Propuestas pendientes{' '}
          <span className="hint">
            {total === 0 ? '· ninguna' : `· quedan ${String(total)}`}
          </span>
        </h2>

        {proposals.isPending && <LoadingState label="Cargando las propuestas…" />}
        {proposals.isError && (
          <ErrorState
            title="No se pudieron cargar las propuestas"
            message={describeError(proposals.error)}
            onRetry={() => {
              void proposals.refetch();
            }}
          />
        )}

        {proposals.isSuccess && visibles.length === 0 && (
          <EmptyState
            title="No queda ninguna propuesta"
            description={
              total === 0
                ? 'La cola está despachada: no hay ninguna pregunta esperando un tema.'
                : 'Las de esta página ya están decididas: se escribirán al guardar.'
            }
          />
        )}

        {visibles.length > 0 && (
          <ol className="queue__list">
            {visibles.map((card, indice) => (
              <ProposalCard
                key={card.question_version_id}
                card={card}
                current={indice === cursor}
                chosen={chosen[card.question_version_id] ?? 0}
                skipped={skipped.includes(card.question_version_id)}
                queued={false}
                changeOpen={changeFor === card.question_version_id}
                topics={topics}
                changeTopicId={changeTopicId}
                changeEpigraphId={changeEpigraphId}
                busy={apply.isPending}
                onChoose={(elegida) => {
                  setCursor(indice);
                  setChosen((previo) => ({ ...previo, [card.question_version_id]: elegida }));
                }}
                onChangeTopic={(id) => {
                  setChangeTopicId(id);
                  setChangeEpigraphId('');
                }}
                onChangeEpigraph={setChangeEpigraphId}
                onCancelChange={() => {
                  setChangeFor(null);
                }}
                onApplyChange={aplicarCambio}
              />
            ))}
          </ol>
        )}

        {queued.length > 0 && (
          <div className="queue__tray" role="status">
            <p>
              <strong>{queued.length}</strong> decisión(es) sin guardar:{' '}
              {queued.map((decision) => decision.label).join(' · ')}
            </p>
            <button
              className="button"
              type="button"
              disabled={apply.isPending}
              onClick={() => {
                guardar(queued);
              }}
            >
              {apply.isPending ? 'Guardando…' : `Guardar ${String(queued.length)} decisiones`}
            </button>
            <span className="hint">
              Se manda en una sola llamada (<kbd>G</kbd>).
            </span>
          </div>
        )}

        {apply.isError && (
          <ErrorState
            title="El lote no se pudo guardar"
            message={describeError(apply.error)}
            onRetry={() => {
              guardar(queued);
            }}
          />
        )}

        {report !== null && !apply.isPending && (
          <p className="hint" role="status">
            Última llamada: {report.promoted} confirmada(s), {report.created} creada(s),{' '}
            {report.existing} que ya estaban, {report.excluded} fuera de temario,{' '}
            {report.already_excluded} que ya lo estaban, {report.errors} con error.
          </p>
        )}
        {report !== null && report.errors > 0 && (
          <ul className="issues">
            {report.results
              .filter((fila) => fila.outcome === 'error')
              .map((fila) => (
                <li key={fila.question_version_id} className="issues__item">
                  Una fila no se pudo aplicar: {fila.detail ?? 'sin motivo'}
                </li>
              ))}
          </ul>
        )}
      </section>

      <section className="card" aria-labelledby="fuera-de-temario">
        <h2 id="fuera-de-temario">Fuera de temario</h2>
        <p className="hint">
          Lo que no es materia de este programa, con el motivo por el que se declaró. Para deshacer
          una marca se le asigna un tema: la marca se levanta sola, porque una pregunta no puede ser
          de un tema y no ser del temario a la vez.
        </p>
        {exclusions.isPending && <LoadingState label="Cargando las marcas…" />}
        {exclusions.isError && (
          <ErrorState
            title="No se pudieron cargar las marcas"
            message={describeError(exclusions.error)}
            onRetry={() => {
              void exclusions.refetch();
            }}
          />
        )}
        {exclusions.isSuccess && (
          <>
            <p className="hint">
              {exclusions.data.total === 0
                ? 'Ninguna pregunta está fuera de temario.'
                : `${String(exclusions.data.total)} pregunta(s) fuera de temario.`}
              {isApiError(apply.error, 409) && ' La última decisión no encajó con el estado actual.'}
            </p>
            <ExclusionList
              exclusions={exclusions.data.exclusions}
              topics={topics}
              busy={apply.isPending}
              onAssign={({ questionVersionId, topicId, epigraphId }) => {
                apply.mutate(
                  [
                    {
                      question_version_id: questionVersionId,
                      curriculum_node_id: topicId,
                      epigraph_node_id: epigraphId === '' ? null : epigraphId,
                      confidence: 1,
                      reason: REASON_PROMOTED,
                      status: 'accepted',
                      // La marca de fuera de temario la levanta el propio servidor al asignar el
                      // tema; retirar aquí las demás propuestas es lo mismo que se hace al aceptar.
                      retire_others: true,
                    },
                  ],
                  { onSuccess: setReport },
                );
              }}
            />
          </>
        )}
      </section>
    </>
  );
}
