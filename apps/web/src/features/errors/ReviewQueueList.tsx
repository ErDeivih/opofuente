import type { DueItem, ErrorCause } from '../../api/reviews';
import { StatusBadge } from '../../components/StatusBadge';

export interface ReviewQueueListProps {
  items: readonly DueItem[];
  busy: boolean;
  error: string | null;
  conflict: string | null;
  onComplete: (input: {
    reviewId: string;
    outcome: 'correct' | 'wrong';
    confidence: 'low' | 'medium' | 'high' | null;
    cause: ErrorCause | null;
    note: string | null;
  }) => void;
  onSnooze: (input: { reviewId: string; days: number }) => void;
  onStudyQueue: () => void;
}

/**
 * La vista `Hoy` (07_UI-UX §9): la cola ordenada, con el motivo de cada elemento.
 *
 * Dos formas de repasar, y las dos dicen lo que son:
 *
 * 1. **contestar aquí mismo** no es posible sin clave: la aplicación no enseña la solución antes del
 *    intento, así que repasar de verdad se hace en una sesión de repaso, que se compone con lo
 *    vencido. El botón la crea y lleva a Estudiar;
 * 2. **declarar el resultado** es para lo que se repasa fuera (en voz alta, en papel): la persona dice
 *    qué tal le fue, y la pantalla deja claro que ese desenlace es declarado, no medido.
 */
export function ReviewQueueList({
  items,
  busy,
  error,
  conflict,
  onComplete,
  onSnooze,
  onStudyQueue,
}: ReviewQueueListProps) {
  if (items.length === 0) {
    return (
      <p className="hint">
        No hay nada vencido. La cola se llena sola cuando fallas una pregunta en una sesión; si
        quieres repasar antes de que toque, puedes declarar el resultado de un repaso hecho fuera.
      </p>
    );
  }

  return (
    <>
      <div className="form__row">
        <button className="button" type="button" disabled={busy} onClick={onStudyQueue}>
          Repasar en una sesión ({items.length})
        </button>
        <span className="hint">
          La sesión se compone con lo vencido y no enseña la solución antes de contestar.
        </span>
      </div>

      {conflict !== null && (
        <p className="hint" role="alert">
          {conflict}
        </p>
      )}
      {error !== null && (
        <p className="hint" role="alert">
          {error}
        </p>
      )}

      <ol className="results">
        {items.map((item) => (
          <ReviewRow
            key={item.review.id}
            item={item}
            busy={busy}
            onComplete={onComplete}
            onSnooze={onSnooze}
          />
        ))}
      </ol>
    </>
  );
}

function ReviewRow({
  item,
  busy,
  onComplete,
  onSnooze,
}: {
  item: DueItem;
  busy: boolean;
  onComplete: ReviewQueueListProps['onComplete'];
  onSnooze: ReviewQueueListProps['onSnooze'];
}) {
  const review = item.review;
  return (
    <li>
      <p>
        <strong>{item.stem}</strong>{' '}
        <StatusBadge tone={item.overdue_days > 0 ? 'warning' : 'info'}>
          {item.overdue_days > 0
            ? `vencido hace ${String(item.overdue_days)} día(s)`
            : 'toca hoy'}
        </StatusBadge>{' '}
        <span className="hint">
          {review.interval_days === 0
            ? 'primer repaso'
            : `intervalo de ${String(review.interval_days)} día(s)`}{' '}
          · {review.lapses} fallo(s) · {item.origin_type}
          {item.is_reserve ? ' · reserva' : ''}
        </span>
      </p>
      <p className="hint">{item.explanation}</p>
      <ul className="evidence">
        {item.options.map((opcion) => (
          <li key={opcion.stable_key}>
            <span className="sample__path">{opcion.stable_key.toUpperCase()})</span> {opcion.text}
          </li>
        ))}
      </ul>
      <div className="form__row">
        <button
          className="button"
          type="button"
          aria-label={`Declarar que acerté el repaso de «${item.stem}»`}
          disabled={busy}
          onClick={() => {
            onComplete({
              reviewId: review.id,
              outcome: 'correct',
              confidence: 'high',
              cause: null,
              note: null,
            });
          }}
        >
          Repasado y sabido
        </button>
        <button
          className="button"
          type="button"
          aria-label={`Declarar que fallé el repaso de «${item.stem}»`}
          disabled={busy}
          onClick={() => {
            onComplete({
              reviewId: review.id,
              outcome: 'wrong',
              confidence: 'low',
              cause: null,
              note: null,
            });
          }}
        >
          Repasado y fallado
        </button>
        <button
          className="button"
          type="button"
          aria-label={`Aplazar el repaso de «${item.stem}» tres días`}
          disabled={busy}
          onClick={() => {
            onSnooze({ reviewId: review.id, days: 3 });
          }}
        >
          Aplazar 3 días
        </button>
      </div>
      <p className="hint">
        Declarar el resultado es para lo que repases fuera de aquí: el desenlace lo dices tú, no lo
        mide la aplicación.
        {review.last_reason !== null && review.last_reason !== undefined
          ? ` Último cambio: ${review.last_reason}.`
          : ''}
      </p>
    </li>
  );
}
