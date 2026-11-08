import { Link, useParams } from 'react-router-dom';

import { useTemarioBlockQuestions, useTemarioNodeDetail } from '../api/queries';
import { EmptyState } from '../components/EmptyState';
import { ErrorState } from '../components/ErrorState';
import { LoadingState } from '../components/LoadingState';
import { questionTypeLabel } from '../features/temario/labels';

/**
 * Práctica libre de un bloque (B-017, alcance de vista del banco).
 *
 * Junta las preguntas **aceptadas** catalogadas en los temas del bloque y enlaza cada una con su
 * ficha del banco. No crea una sesión, no cronometra y no puntúa: eso sería otro modo de estudio
 * (S07) y se decide aparte. Aquí se puede repasar el bloque entero sin montar un examen.
 */
export function TemarioBlockPracticePage() {
  const { nodeId } = useParams<{ nodeId: string }>();
  const detalle = useTemarioNodeDetail(nodeId ?? null, null);
  const preguntas = useTemarioBlockQuestions(nodeId ?? null);
  const volver = (
    <p className="hint">
      <Link to="/temario">Volver al temario</Link>
    </p>
  );

  if (nodeId === undefined) {
    return (
      <section className="card">
        <ErrorState title="No se pudo cargar la práctica" message="Vuelve al temario y elige un bloque." />
        {volver}
      </section>
    );
  }

  if (detalle.isPending) {
    return (
      <section className="card">
        <LoadingState label="Cargando el bloque…" />
        {volver}
      </section>
    );
  }
  if (detalle.isError) {
    return (
      <section className="card">
        <ErrorState
          title="No se pudo cargar la práctica"
          message="El bloque no existe o no está disponible."
          onRetry={() => {
            void detalle.refetch();
          }}
        />
        {volver}
      </section>
    );
  }

  const nodo = detalle.data.node;

  return (
    <>
      <header className="page__header">
        <nav className="breadcrumb" aria-label="Ruta de la práctica">
          <Link to="/temario">Temario</Link>
          <span aria-hidden="true">›</span> {nodo.title}
        </nav>
        <h1>Práctica libre del bloque</h1>
        <p className="page__lead">
          <span className="node__path">{nodo.path}</span> · {nodo.title}
        </p>
      </header>

      <section className="card" aria-labelledby="practica-libre">
        <h2 id="practica-libre">Preguntas del bloque</h2>
        <p className="hint">
          Preguntas aceptadas del banco catalogadas en los temas de este bloque. Se abren en su
          ficha para repasarlas; no es una sesión ni tiene nota.
        </p>

        {preguntas.isPending && <LoadingState label="Cargando las preguntas del bloque…" />}
        {preguntas.isError && (
          <ErrorState
            title="No se pudieron cargar las preguntas"
            message="Inténtalo de nuevo."
            onRetry={() => {
              void preguntas.refetch();
            }}
          />
        )}
        {preguntas.isSuccess &&
          (preguntas.data.total === 0 ? (
            <EmptyState
              title="Este bloque aún no tiene preguntas"
              description="Cuando el banco tenga preguntas aceptadas de sus temas aparecerán aquí."
            />
          ) : (
            <>
              <p className="hint">
                {preguntas.data.total === 1
                  ? '1 pregunta'
                  : `${String(preguntas.data.total)} preguntas`}
              </p>
              <ul className="question-list">
                {preguntas.data.questions.map((pregunta) => (
                  <li key={pregunta.id} className="question">
                    <div className="question__header">
                      <span className="tag">{questionTypeLabel(pregunta.question_type)}</span>
                    </div>
                    <p className="question__stem">{pregunta.stem}</p>
                    <p className="question__action">
                      <Link
                        to={`/preguntas?conjunto=${encodeURIComponent(
                          pregunta.question_set_id,
                        )}&pregunta=${encodeURIComponent(pregunta.id)}`}
                      >
                        Repasar en el banco
                      </Link>
                    </p>
                  </li>
                ))}
              </ul>
            </>
          ))}
      </section>

      {volver}
    </>
  );
}
