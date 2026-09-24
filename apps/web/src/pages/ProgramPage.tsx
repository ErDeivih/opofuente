import { useState } from 'react';

import type { CurriculumNode } from '../api/profiles';
import type { NodeMastery } from '../api/reviews';
import { useConvocation, useCurriculum, useCurriculumNode, useMastery, useOppositions } from '../api/queries';
import { EmptyState } from '../components/EmptyState';
import { ErrorState } from '../components/ErrorState';
import { LoadingState } from '../components/LoadingState';
import { ConvocationSelector } from '../features/profiles/ConvocationSelector';
import { ConvocationSource } from '../features/profiles/ConvocationSource';
import { CurriculumTree } from '../features/profiles/CurriculumTree';
import { ExamSummary } from '../features/profiles/ExamSummary';
import { TopicPanel } from '../features/dossier/TopicPanel';
import { originLabel, questionStatusLabel } from '../features/questions/labels';

/**
 * La próxima revisión de un tema, con las mismas tres salidas que en el árbol del programa.
 *
 * Se escribe aquí y no en el árbol porque el árbol recibe otra forma (la ficha completa) y duplicar
 * el texto llevaría a que las dos dijeran cosas distintas del mismo dato.
 */
function textoRepasoDelNodo(estado: NodeMastery | undefined): string {
  if (estado === undefined) {
    return 'Se calcula con los repasos de las preguntas asignadas a este tema.';
  }
  if (estado.study_state.reviews_due > 0) {
    return `${String(estado.study_state.reviews_due)} repaso(s) vencido(s): tocan ahora.`;
  }
  if (estado.study_state.next_review_at !== null && estado.study_state.next_review_at !== undefined) {
    return `Próximo repaso programado: ${estado.study_state.next_review_at.slice(0, 10)}.`;
  }
  return 'Sin repaso programado: no hay ninguna pregunta de este tema fallada o vencida.';
}

/**
 * Programa (07_UI-UX §5): árbol oficial del temario de la convocatoria vigente.
 *
 * Se muestra la estructura y las reglas tal y como las publica la convocatoria, más las cuatro
 * columnas que pide la especificación por nodo: fuentes (en la ficha del nodo), preguntas por origen
 * y estado, dominio y próxima revisión. La cobertura documental y las preguntas **no** se muestran
 * como ceros; el **dominio** sí, desde S10, con la regla honesta: sin intentos «sin datos» y con
 * pocos, «evidencia insuficiente» (nunca un porcentaje).
 *
 * Cuando la oposición tiene más de una convocatoria publicada (Celador: acceso libre de 2022 y
 * estabilización), el selector de convocatoria de S12.2 elige con cuál se trabaja; sin él, el
 * programa de la otra quedaría sembrado pero invisible.
 */
export function ProgramPage() {
  const oppositions = useOppositions();
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const active = oppositions.data?.find((opposition) => opposition.active) ?? null;
  const convocationId = active?.active_convocation?.id ?? null;

  const convocation = useConvocation(convocationId);
  const curriculum = useCurriculum(convocationId);
  const node = useCurriculumNode(selectedId);
  const mastery = useMastery(active?.id ?? null);
  const dominioPorNodo = Object.fromEntries(
    (mastery.data?.nodes ?? []).map((ficha) => [ficha.curriculum_node_id, ficha]),
  );
  const estadoDelNodo = selectedId === null ? undefined : dominioPorNodo[selectedId];

  if (oppositions.isPending) {
    return <LoadingState label="Cargando oposiciones…" />;
  }

  if (oppositions.isError) {
    return (
      <ErrorState
        title="No se pudieron cargar las oposiciones"
        message="Comprueba que la API está en marcha y que los perfiles se han sembrado."
        onRetry={() => {
          void oppositions.refetch();
        }}
      />
    );
  }

  if (active === null || convocationId === null) {
    return (
      <>
        <header className="page__header">
          <h1>Programa</h1>
        </header>
        <section className="card">
          <EmptyState
            title="No hay ninguna oposición activa con convocatoria"
            description="Los perfiles oficiales se siembran desde los fixtures versionados."
            hint="Ejecuta scripts/seed.ps1 (o ./scripts/install.ps1 en una instalación nueva) para sembrar TAI 2025 y Guardia Civil 2026."
          />
        </section>
      </>
    );
  }

  return (
    <>
      <header className="page__header">
        <h1>Programa</h1>
        <p className="page__lead">
          {active.name}
          {convocation.data && (
            <>
              {' · '}
              <code>{convocation.data.code}</code>
            </>
          )}
          {curriculum.data && (
            <>
              {' · '}
              <strong>{curriculum.data.counts.block ?? 0}</strong> bloques,{' '}
              <strong>{curriculum.data.counts.topic ?? 0}</strong> temas
              {(curriculum.data.counts.epigraph ?? 0) > 0 && (
                <>
                  , <strong>{curriculum.data.counts.epigraph}</strong> epígrafes
                </>
              )}
            </>
          )}
        </p>
      </header>

      <ConvocationSelector oppositionId={active.id} />

      <section className="card" aria-labelledby="arbol-programa">
        <h2 id="arbol-programa">Temario oficial</h2>
        {curriculum.isPending && <LoadingState label="Cargando el programa…" />}
        {curriculum.isError && (
          <ErrorState
            title="No se pudo cargar el programa"
            message="La convocatoria activa no tiene programa sembrado."
            onRetry={() => {
              void curriculum.refetch();
            }}
          />
        )}
        {curriculum.isSuccess && (
          <CurriculumTree
            nodes={curriculum.data.nodes}
            selectedId={selectedId}
            mastery={dominioPorNodo}
            onSelect={(selected: CurriculumNode) => {
              setSelectedId(selected.id);
            }}
          />
        )}
        {mastery.data !== undefined && (
          <p className="hint">
            Estado por tema: {mastery.data.nodes_with_estimate} de {mastery.data.nodes_total} con
            dominio estimado · {mastery.data.nodes_insufficient} con evidencia insuficiente ·{' '}
            {mastery.data.nodes_without_data} sin datos. {mastery.data.note}
          </p>
        )}
      </section>

      {selectedId !== null && (
        <section className="card" aria-labelledby="detalle-nodo">
          <h2 id="detalle-nodo">El tema</h2>
          {node.isPending && <LoadingState label="Cargando el nodo…" />}
          {node.isError && (
            <ErrorState
              title="No se pudo cargar el nodo"
              message="El nodo ya no existe o la API no responde."
              onRetry={() => {
                void node.refetch();
              }}
            />
          )}
          {node.isSuccess && (
            <>
              <p className="node__path">{node.data.node.path}</p>
              <p className="node__title">{node.data.node.title}</p>
              {node.data.ancestors.length > 0 && (
                <p className="hint">
                  {node.data.ancestors.map((ancestor) => ancestor.title).join(' › ')}
                </p>
              )}
              {/* Lo que el corpus dice del tema: sus fuentes citadas, sus huecos y su historial
                  (S13). Sustituye al panel que solo decía dónde se calculaba la cobertura. */}
              <TopicPanel nodeId={node.data.node.id} />
              <dl className="facts">
                <dt>Preguntas</dt>
                <dd>
                  {/* El desglose completo del tema: es lo que en el árbol va en etiquetas. */}
                  {estadoDelNodo === undefined || estadoDelNodo.study_state.questions_total === 0 ? (
                    <span className="hint">
                      Sin preguntas asignadas a este tema: el dominio no se puede estimar hasta que
                      las haya.
                    </span>
                  ) : (
                    <span>
                      {estadoDelNodo.study_state.questions_total} en total ·{' '}
                      {estadoDelNodo.study_state.questions_by_origin
                        .map((fila) => `${String(fila.count)} ${originLabel(fila.status)}`)
                        .join(', ')}{' '}
                      ·{' '}
                      {estadoDelNodo.study_state.questions_by_status
                        .map((fila) => `${String(fila.count)} ${questionStatusLabel(fila.status)}`)
                        .join(', ')}
                    </span>
                  )}
                </dd>
                <dt>Próxima revisión</dt>
                <dd>{textoRepasoDelNodo(estadoDelNodo)}</dd>
                <dt>Procedencia</dt>
                <dd>
                  <a href={node.data.official_url} target="_blank" rel="noreferrer noopener">
                    {node.data.source_reference ?? node.data.convocation_code}
                  </a>
                </dd>
              </dl>
            </>
          )}
        </section>
      )}
      {convocation.isPending && <LoadingState label="Cargando la convocatoria…" />}
      {convocation.isError && (
        <ErrorState
          title="No se pudo cargar la convocatoria"
          message="La convocatoria activa no está disponible."
          onRetry={() => {
            void convocation.refetch();
          }}
        />
      )}
      {convocation.isSuccess && (
        <>
          <ExamSummary parts={convocation.data.parts} rules={convocation.data.rules} />
          <ConvocationSource convocation={convocation.data} />
        </>
      )}
    </>
  );
}
