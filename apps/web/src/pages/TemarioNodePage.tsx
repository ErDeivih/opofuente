import { Link, useParams, useSearchParams } from 'react-router-dom';

import {
  useMarkTemarioStudied,
  useTemarioDetail,
  useTemarioNodeDetail,
  useTemarioNodeMaterials,
  useTemarioNodeQuestions,
  useUnmarkTemarioStudied,
} from '../api/queries';
import type { Adjustment, Appearance } from '../api/temario';
import { EmptyState } from '../components/EmptyState';
import { ErrorState } from '../components/ErrorState';
import { LoadingState } from '../components/LoadingState';
import { StatusBadge } from '../components/StatusBadge';
import {
  adjustmentDetail,
  adjustmentLabel,
  formatDate,
  materialTypeLabel,
  questionTypeLabel,
  roleLabel,
  temarioHref,
} from '../features/temario/labels';
import { flattenTopics } from '../features/temario/search';

interface AppearanceItemProps {
  appearance: Appearance;
  nodeId: string;
  selectedConvocationId: string | null;
}

function AppearanceItem({ appearance, nodeId, selectedConvocationId }: AppearanceItemProps) {
  const selected = appearance.convocation_id === selectedConvocationId;

  return (
    <li className="appearance">
      <div className="appearance__header">
        <span className="appearance__title">{appearance.convocation_title}</span>
        <span className="tag">{roleLabel(appearance.role)}</span>
        {appearance.convocation_status === 'draft' && (
          <StatusBadge tone="warning">Por confirmar</StatusBadge>
        )}
        {appearance.omitted && <StatusBadge tone="warning">No incluido</StatusBadge>}
      </div>
      {appearance.source_reference !== null && appearance.source_reference !== undefined && (
        <p className="quote">{appearance.source_reference}</p>
      )}
      {appearance.adjustments.length > 0 && (
        <p className="hint">
          {appearance.adjustments
            .map((adjustment) => adjustmentLabel(adjustment.kind))
            .join(' · ')}
        </p>
      )}
      <p className="appearance__action">
        {selected ? (
          <span className="hint">Convocatoria elegida</span>
        ) : (
          <Link to={temarioHref(nodeId, appearance.convocation_id)}>Ver particularidades</Link>
        )}
      </p>
    </li>
  );
}

function AdjustmentItem({ adjustment }: { adjustment: Adjustment }) {
  const detail = adjustmentDetail(adjustment);

  return (
    <li className="adjustment">
      <p className="adjustment__label">{adjustmentLabel(adjustment.kind)}</p>
      {detail !== null && (
        <p className="adjustment__detail">
          {adjustment.kind === 'renumbered'
            ? 'Número en esta convocatoria: '
            : 'Título en esta convocatoria: '}
          <strong>{detail}</strong>
        </p>
      )}
      <blockquote className="quote">{adjustment.evidence_quote}</blockquote>
    </li>
  );
}

/** Material de la biblioteca catalogado en este tema. Si no hay, no ocupa sitio. */
function ApuntesMateriales({ nodeId }: { nodeId: string }) {
  const materiales = useTemarioNodeMaterials(nodeId);

  if (materiales.isPending) {
    return <p className="hint">Cargando el material del tema…</p>;
  }
  if (materiales.isError) {
    return <p className="hint">No se pudo cargar el material del tema.</p>;
  }
  if (materiales.data.total === 0) {
    return null;
  }

  return (
    <>
      <h3>Material del tema</h3>
      <ul className="material-list">
        {materiales.data.materials.map((material) => (
          <li key={`${material.subject_type}-${material.subject_id}`} className="material">
            <div className="material__header">
              <span className="material__title">{material.title}</span>
              <span className="tag">{materialTypeLabel(material.subject_type)}</span>
            </div>
            {material.section_title !== null && material.section_title !== undefined && (
              <p className="material__section">{material.section_title}</p>
            )}
            {((material.page !== null && material.page !== undefined) ||
              (material.citation_label !== null && material.citation_label !== undefined)) && (
              <p className="hint">
                {material.page !== null && material.page !== undefined && (
                  <>Página {material.page}</>
                )}
                {material.citation_label !== null &&
                  material.citation_label !== undefined && <> {material.citation_label}</>}
              </p>
            )}
            {material.excerpt !== null && material.excerpt !== undefined && (
              <blockquote className="quote">{material.excerpt}</blockquote>
            )}
          </li>
        ))}
      </ul>
    </>
  );
}

/** Preguntas del banco catalogadas en el tema. Sin clave: la ficha no examina. */
function PreguntasDelTema({ nodeId }: { nodeId: string }) {
  const preguntas = useTemarioNodeQuestions(nodeId);

  return (
    <section className="card" aria-labelledby="tema-preguntas">
      <h2 id="tema-preguntas">Preguntas</h2>
      {preguntas.isPending && <p className="hint">Cargando las preguntas del tema…</p>}
      {preguntas.isError && <p className="hint">No se pudieron cargar las preguntas del tema.</p>}
      {preguntas.isSuccess &&
        (preguntas.data.total === 0 ? (
          <EmptyState
            title="Este tema aún no tiene preguntas"
            description="Cuando el banco tenga preguntas de este tema aparecerán aquí."
          />
        ) : (
          <>
            <p className="hint">
              {preguntas.data.total === 1
                ? '1 pregunta'
                : `${String(preguntas.data.total)} preguntas`}{' '}
              en el banco
            </p>
            <ul className="question-list">
              {preguntas.data.questions.map((pregunta) => (
                <li key={pregunta.id} className="question">
                  <div className="question__header">
                    <span className="tag">{questionTypeLabel(pregunta.question_type)}</span>
                    {pregunta.is_reserve && <StatusBadge tone="info">Reserva</StatusBadge>}
                  </div>
                  <p className="question__stem">{pregunta.stem}</p>
                </li>
              ))}
            </ul>
          </>
        ))}
    </section>
  );
}

/**
 * Ficha de tema (ESPECIFICACION §9, pantalla 2).
 *
 * Enseña el título, la ruta, los apuntes (o dice que no los hay), en qué convocatorias aparece y,
 * cuando se llega con `?convocatoria=<id>`, las particularidades de esa convocatoria sin copiar el
 * temario. La marca de estudiado se guarda en el servidor y su fecha queda a la vista.
 */
export function TemarioNodePage() {
  const { nodeId } = useParams<{ nodeId: string }>();
  const [searchParams] = useSearchParams();
  const convocatoriaId = searchParams.get('convocatoria');

  const detalle = useTemarioNodeDetail(nodeId ?? null, convocatoriaId);
  const codigoTemario = detalle.data?.curriculum.code ?? null;
  const temario = useTemarioDetail(codigoTemario);
  const marcar = useMarkTemarioStudied();
  const retirar = useUnmarkTemarioStudied();

  const volver = (
    <p className="hint">
      <Link to="/temario">Volver al temario</Link>
    </p>
  );

  if (nodeId === undefined) {
    return (
      <>
        <header className="page__header">
          <h1>Tema</h1>
        </header>
        <section className="card">
          <ErrorState title="No se pudo cargar el tema" message="Vuelve al temario y elige un tema." />
          {volver}
        </section>
      </>
    );
  }

  if (detalle.isPending) {
    return (
      <>
        <header className="page__header">
          <h1>Tema</h1>
        </header>
        <section className="card">
          <LoadingState label="Cargando el tema…" />
          {volver}
        </section>
      </>
    );
  }

  if (detalle.isError) {
    return (
      <>
        <header className="page__header">
          <h1>Tema</h1>
        </header>
        <section className="card">
          <ErrorState
            title="No se pudo cargar el tema"
            message="El tema no existe o no está disponible."
            onRetry={() => {
              void detalle.refetch();
            }}
          />
          {volver}
        </section>
      </>
    );
  }

  const nodo = detalle.data.node;
  const curriculum = detalle.data.curriculum;
  const aparece = detalle.data.appears_in ?? [];
  const particularidades = detalle.data.particularities ?? [];
  const ancestros = detalle.data.ancestors ?? [];
  const estudiadoEn = detalle.data.studied_at ?? nodo.studied_at ?? null;
  const seleccionada =
    convocatoriaId === null
      ? undefined
      : aparece.find((appearance) => appearance.convocation_id === convocatoriaId);
  const esTema = nodo.node_type === 'topic';
  const errorMarca = marcar.error ?? retirar.error;
  const guardando = marcar.isPending || retirar.isPending;

  // Navegación anterior/siguiente dentro del mismo temario: se recorre el árbol en orden oficial.
  const temas = temario.data === undefined ? [] : flattenTopics(temario.data.nodes);
  const indice = temas.findIndex((tema) => tema.id === nodo.id);
  const anterior = indice > 0 ? temas[indice - 1] : undefined;
  const siguiente = indice >= 0 && indice < temas.length - 1 ? temas[indice + 1] : undefined;

  return (
    <>
      <header className="page__header">
        <nav className="breadcrumb" aria-label="Ruta del tema">
          <Link to="/temario">Temario</Link>
          {ancestros.map((ancestro) => (
            <span key={ancestro.id}>
              <span aria-hidden="true">›</span> {ancestro.title}
            </span>
          ))}
        </nav>
        <h1>{nodo.title}</h1>
        <p className="page__lead">
          <span className="node__path">{nodo.path}</span>
          {' · '}
          {curriculum.name}
        </p>
      </header>

      <section className="card" aria-labelledby="tema-apuntes">
        <h2 id="tema-apuntes">Apuntes</h2>
        {nodo.description !== null &&
        nodo.description !== undefined &&
        nodo.description.trim() !== '' ? (
          <div className="temario__notes">{nodo.description}</div>
        ) : (
          <EmptyState
            title="Este tema aún no tiene apuntes"
            description="Cuando haya texto para este tema aparecerá aquí."
          />
        )}

        <ApuntesMateriales nodeId={nodo.id} />

        {esTema && (
          <div className="study-mark">
            {estudiadoEn !== null && estudiadoEn !== undefined ? (
              <>
                <StatusBadge tone="ok">
                  Estudiado el <time dateTime={estudiadoEn}>{formatDate(estudiadoEn)}</time>
                </StatusBadge>
                <button
                  type="button"
                  className="button"
                  disabled={guardando}
                  onClick={() => {
                    retirar.mutate({ nodeId, convocationId: convocatoriaId });
                  }}
                >
                  {retirar.isPending ? 'Quitando…' : 'Retirar la marca'}
                </button>
              </>
            ) : (
              <button
                type="button"
                className="button"
                disabled={guardando}
                onClick={() => {
                  marcar.mutate({ nodeId, convocationId: convocatoriaId });
                }}
              >
                {marcar.isPending ? 'Guardando…' : 'Marcar como estudiado'}
              </button>
            )}
          </div>
        )}
        {errorMarca !== null && errorMarca !== undefined && (
          <ErrorState title="No se pudo actualizar la marca" message="Inténtalo de nuevo." />
        )}
      </section>

      <PreguntasDelTema nodeId={nodo.id} />

      <section className="card" aria-labelledby="aparece-en">
        <h2 id="aparece-en">En qué convocatorias aparece</h2>
        {curriculum.kind === 'published' ? (
          <>
            <p className="hint">Este tema pertenece al programa publicado de una convocatoria.</p>
            {detalle.data.convocation !== null && detalle.data.convocation !== undefined && (
              <dl className="facts">
                <dt>Publicación</dt>
                <dd>
                  <time dateTime={detalle.data.convocation.published_at}>
                    {formatDate(detalle.data.convocation.published_at)}
                  </time>
                </dd>
                <dt>Fuente</dt>
                <dd>
                  <a
                    href={detalle.data.convocation.official_url}
                    target="_blank"
                    rel="noreferrer noopener"
                  >
                    {detalle.data.convocation.source_reference ??
                      detalle.data.convocation.code}
                  </a>
                </dd>
              </dl>
            )}
          </>
        ) : aparece.length === 0 ? (
          <p className="hint">Este tema no aparece en ninguna convocatoria.</p>
        ) : (
          <ul className="appearances">
            {aparece.map((appearance) => (
              <AppearanceItem
                key={appearance.convocation_id}
                appearance={appearance}
                nodeId={nodo.id}
                selectedConvocationId={convocatoriaId}
              />
            ))}
          </ul>
        )}
      </section>

      {convocatoriaId !== null && curriculum.kind === 'common' && (
        <section className="card" aria-labelledby="particularidades">
          <h2 id="particularidades">En esta convocatoria</h2>
          {seleccionada === undefined ? (
            <p className="hint">Esta convocatoria no estudia este temario.</p>
          ) : (
            <>
              {seleccionada.omitted && (
                <p className="temario__notice">Esta convocatoria no incluye este tema.</p>
              )}
              {particularidades.length === 0 ? (
                !seleccionada.omitted && (
                  <p className="hint">
                    Sin particularidades: el tema se estudia tal y como está en el temario común.
                  </p>
                )
              ) : (
                <ul className="adjustments">
                  {particularidades.map((adjustment, index) => (
                    <AdjustmentItem
                      key={`${adjustment.kind}-${String(index)}`}
                      adjustment={adjustment}
                    />
                  ))}
                </ul>
              )}
            </>
          )}
        </section>
      )}

      <nav className="temario-nav" aria-label="Temas anterior y siguiente">
        {anterior !== undefined ? (
          <Link className="temario-nav__link" to={temarioHref(anterior.id, convocatoriaId)}>
            <span className="hint">Anterior</span>
            <span>
              {anterior.official_code} · {anterior.title}
            </span>
          </Link>
        ) : (
          <span className="temario-nav__link temario-nav__link--empty" aria-hidden="true" />
        )}
        {siguiente !== undefined ? (
          <Link className="temario-nav__link" to={temarioHref(siguiente.id, convocatoriaId)}>
            <span className="hint">Siguiente</span>
            <span>
              {siguiente.official_code} · {siguiente.title}
            </span>
          </Link>
        ) : (
          <span className="temario-nav__link temario-nav__link--empty" aria-hidden="true" />
        )}
      </nav>
    </>
  );
}
