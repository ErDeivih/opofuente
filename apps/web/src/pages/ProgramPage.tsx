import { useState } from 'react';

import type { CurriculumNode } from '../api/profiles';
import { useConvocation, useCurriculum, useCurriculumNode, useMastery, useOppositions } from '../api/queries';
import { EmptyState } from '../components/EmptyState';
import { ErrorState } from '../components/ErrorState';
import { LoadingState } from '../components/LoadingState';
import { ConvocationSource } from '../features/profiles/ConvocationSource';
import { CurriculumTree } from '../features/profiles/CurriculumTree';
import { ExamSummary } from '../features/profiles/ExamSummary';

/**
 * Programa (07_UI-UX §5): árbol oficial del temario de la convocatoria activa.
 *
 * Se muestra la estructura y las reglas tal y como las publica la convocatoria. La cobertura documental
 * y las preguntas **no** se muestran como ceros; el **dominio** sí, desde S10, con la regla honesta:
 * sin intentos «sin datos» y con pocos, «evidencia insuficiente» (nunca un porcentaje).
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

  if (oppositions.isPending) {
    return <LoadingState label="Cargando oposiciones…" />;
  }

  if (oppositions.isError) {
    return (
      <ErrorState
        title="No se pudieron cargar las oposiciones"
        message="Inténtalo de nuevo."
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
            title="No hay ninguna oposición activa"
            description="Elige una oposición en el selector de la cabecera."
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

      <section className="card" aria-labelledby="arbol-programa">
        <h2 id="arbol-programa">Temario oficial</h2>
        {curriculum.isPending && <LoadingState label="Cargando el programa…" />}
        {curriculum.isError && (
          <ErrorState
            title="No se pudo cargar el programa"
            message="Inténtalo de nuevo."
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
      </section>

      {selectedId !== null && (
        <section className="card" aria-labelledby="detalle-nodo">
          <h2 id="detalle-nodo">Nodo seleccionado</h2>
          {node.isPending && <LoadingState label="Cargando el nodo…" />}
          {node.isError && (
            <ErrorState
              title="No se pudo cargar el nodo"
              message="El nodo ya no está disponible."
              onRetry={() => {
                void node.refetch();
              }}
            />
          )}
          {node.isSuccess && (
            <>
              <p className="node__path">{node.data.node.path}</p>
              <p className="node__title">{node.data.node.title}</p>
              {(node.data.ancestors ?? []).length > 0 && (
                <p className="hint">
                  {(node.data.ancestors ?? [])
                    .map((ancestor) => ancestor.title)
                    .join(' › ')}
                </p>
              )}
              <dl className="facts">
                <dt>Procedencia</dt>
                <dd>
                  {node.data.convocation === null || node.data.convocation === undefined ? (
                    <span className="hint">Sin convocatoria asociada</span>
                  ) : (
                    <a
                      href={node.data.convocation.official_url}
                      target="_blank"
                      rel="noreferrer noopener"
                    >
                      {node.data.convocation.source_reference ?? node.data.convocation.code}
                    </a>
                  )}
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
