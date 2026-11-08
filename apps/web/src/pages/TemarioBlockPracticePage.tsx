import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import { useCreateStudySession, useOppositions, useTemarioBlockQuestions, useTemarioNodeDetail } from '../api/queries';
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
  const crear = useCreateStudySession();
  const oposiciones = useOppositions();
  const navigate = useNavigate();
  const [cantidad, setCantidad] = useState('todas');
  const [tiempo, setTiempo] = useState('sin');
  const activa = oposiciones.data?.find((oposicion) => oposicion.active) ?? null;
  const puedeEmpezar =
    activa !== null &&
    preguntas.data !== undefined &&
    preguntas.data.total > 0 &&
    !crear.isPending;
  const empezar = () => {
    if (activa === null || nodeId === undefined) {
      return;
    }
    crear.mutate(
      {
        opposition_id: activa.id,
        mode: 'block_practice',
        sources: [],
        block_node_id: nodeId,
        block_limit: cantidad === 'todas' ? null : Number(cantidad),
        time_limit_minutes: tiempo === 'sin' ? null : Number(tiempo),
        feedback: 'immediate',
        shuffle: false,
      },
      {
        onSuccess: () => {
          void navigate('/estudiar');
        },
      },
    );
  };
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
          Preguntas aceptadas del banco catalogadas en los temas de este bloque. Puedes abrirlas en
          su ficha o empezar una práctica del bloque: sin reservas ni tiempo y con la corrección de
          la convocatoria.
        </p>

        {puedeEmpezar && (
          <div className="form__row">
            <label className="form__label" htmlFor="practica-cantidad">
              Cuántas preguntas
            </label>
            <select
              id="practica-cantidad"
              className="form__input"
              value={cantidad}
              onChange={(event) => {
                setCantidad(event.target.value);
              }}
            >
              <option value="10">10</option>
              <option value="20">20</option>
              <option value="50">50</option>
              <option value="todas">Todas</option>
            </select>
            <label className="form__label" htmlFor="practica-tiempo">
              Tiempo máximo
            </label>
            <select
              id="practica-tiempo"
              className="form__input"
              value={tiempo}
              onChange={(event) => {
                setTiempo(event.target.value);
              }}
            >
              <option value="sin">Sin tiempo</option>
              <option value="15">15 minutos</option>
              <option value="30">30 minutos</option>
              <option value="60">60 minutos</option>
            </select>
            <button type="button" className="button" onClick={empezar} disabled={crear.isPending}>
              {crear.isPending ? 'Preparando…' : 'Empezar la práctica del bloque'}
            </button>
          </div>
        )}
        {crear.isError && (
          <ErrorState
            title="No se pudo empezar la práctica"
            message="El bloque no tiene preguntas con clave activa o no hay una oposición activa."
          />
        )}

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
