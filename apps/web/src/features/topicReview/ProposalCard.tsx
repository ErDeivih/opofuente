import type { TopicProposalCard } from '../../api/topicReview';
import { StatusBadge } from '../../components/StatusBadge';
import { TopicPicker } from './TopicPicker';
import type { TopicOption } from './programme';

/**
 * Una tarjeta de la cola: **una pregunta**, con sus propuestas y la decisión a mano.
 *
 * Se enseña el enunciado con sus opciones porque la propuesta no se puede juzgar sin él: la
 * confianza dice cuánto dudó el modelo, no si acertó, y el motivo solo se entiende con el texto
 * delante. Cuando hay más de una propuesta se listan todas, numeradas: son las teclas `1`, `2`… con
 * las que se elige, y verlas juntas es lo que evita decidir dos veces sobre la misma pregunta.
 *
 * La tarjeta no decide nada: avisa de lo que se ha pulsado y quién lo aplica es la página, en lote.
 */
export function ProposalCard({
  card,
  current,
  chosen,
  skipped,
  queued,
  changeOpen,
  topics,
  changeTopicId,
  changeEpigraphId,
  busy,
  onChoose,
  onChangeTopic,
  onChangeEpigraph,
  onCancelChange,
  onApplyChange,
}: {
  card: TopicProposalCard;
  /** ¿Es la tarjeta donde está el cursor? La que recibe las teclas. */
  current: boolean;
  /** Qué propuesta de esta tarjeta está elegida (0 si no se ha elegido otra). */
  chosen: number;
  skipped: boolean;
  /** Ya está en la bandeja de decisiones sin guardar. */
  queued: boolean;
  changeOpen: boolean;
  topics: readonly TopicOption[];
  changeTopicId: string;
  changeEpigraphId: string;
  busy: boolean;
  onChoose: (index: number) => void;
  onChangeTopic: (id: string) => void;
  onChangeEpigraph: (id: string) => void;
  onCancelChange: () => void;
  onApplyChange: () => void;
}) {
  const decidida = card.accepted !== null;
  return (
    <li
      className={`topic-card${current ? ' topic-card--current' : ''}${
        queued ? ' topic-card--queued' : ''
      }`}
      aria-current={current ? 'true' : undefined}
      aria-label={`Pregunta: ${card.stem}`}
    >
      <div className="topic-card__head">
        <span className="hint">{card.set_title}</span>
        {current && <span className="badge badge--info">aquí</span>}
        {queued && <StatusBadge tone="ok">decidida, sin guardar</StatusBadge>}
        {skipped && <StatusBadge tone="warning">saltada en esta pasada</StatusBadge>}
      </div>

      <p className="topic-card__stem" data-contenido>
        {card.stem}
      </p>
      {card.options.length > 0 && (
        <ol className="topic-card__options" data-contenido>
          {card.options.map((opcion) => (
            <li key={opcion.stable_key}>
              <strong>{opcion.label ?? opcion.stable_key})</strong> {opcion.text}
            </li>
          ))}
        </ol>
      )}

      {decidida ? (
        <div className="notice notice--inline">
          <p>
            <strong>Ya tiene tema decidido:</strong> {card.accepted?.path} ·{' '}
            {card.accepted?.title}. Las propuestas que queden sobran: se retiran sin elegir ninguna.
          </p>
          <p className="hint">
            Pulsa <kbd>R</kbd> para retirarlas (no se borran: quedan marcadas y dejan de aparecer).
          </p>
        </div>
      ) : (
        <ul className="topic-card__proposals">
          {card.proposals.map((propuesta, indice) => (
            <li
              key={propuesta.mapping_id}
              className={indice === chosen ? 'topic-card__proposal topic-card__proposal--chosen' : 'topic-card__proposal'}
            >
              <div className="topic-card__proposal-head">
                <span className="topic-card__number">[{indice + 1}]</span>{' '}
                <strong>{propuesta.topic.path}</strong> · {propuesta.topic.title}
                <span className="hint"> · {Math.round(propuesta.confidence * 100)} % de confianza</span>
              </div>
              {propuesta.epigraphs.length > 0 && (
                <p className="hint">
                  Epígrafes propuestos:{' '}
                  {propuesta.epigraphs.map((epigrafe) => `${epigrafe.path} · ${epigrafe.title}`).join(' | ')}
                </p>
              )}
              {propuesta.reason !== null && propuesta.reason !== undefined && (
                <p className="hint" data-contenido>
                  Motivo del modelo: {propuesta.reason}
                </p>
              )}
              <div className="form__row">
                <button
                  className="button button--link"
                  type="button"
                  onClick={() => {
                    onChoose(indice);
                  }}
                >
                  Elegir esta propuesta ({indice + 1})
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      {changeOpen && (
        <TopicPicker
          topics={topics}
          topicId={changeTopicId}
          epigraphId={changeEpigraphId}
          busy={busy}
          onTopicChange={onChangeTopic}
          onEpigraphChange={onChangeEpigraph}
          onCancel={onCancelChange}
          onApply={onApplyChange}
        />
      )}
    </li>
  );
}
