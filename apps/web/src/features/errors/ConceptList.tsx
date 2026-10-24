import { useState } from 'react';

import type { Concept, LearningErrorDetail } from '../../api/reviews';
import { CAUSE_LABEL } from '../../api/reviews';
import { ErrorState } from '../../components/ErrorState';
import { LoadingState } from '../../components/LoadingState';
import { StatusBadge } from '../../components/StatusBadge';

export interface ConceptListProps {
  concepts: readonly Concept[];
  selectedId: string | null;
  detail: LearningErrorDetail | undefined;
  detailIsPending: boolean;
  detailIsError: boolean;
  busy: boolean;
  onSelect: (errorId: string | null) => void;
  onResolve: (input: { errorId: string; resolved: boolean; note: string | null }) => void;
  onRetryDetail: () => void;
}

/**
 * La vista `Conceptos` (07_UI-UX §9): los fallos agrupados por tema, con su causa y su historial.
 *
 * La causa la declara quien estudia, y por eso la ficha del error no la inventa: sin causa declarada
 * el fallo aparece como lo que es (un fallo sin explicar) y la ficha ofrece decirla. La nota propia y
 * el historial del repaso están a la vista para poder reconstruir qué pasó y cuándo.
 */
export function ConceptList({
  concepts,
  selectedId,
  detail,
  detailIsPending,
  detailIsError,
  busy,
  onSelect,
  onResolve,
  onRetryDetail,
}: ConceptListProps) {
  if (concepts.length === 0) {
    return (
      <p className="hint">
        Todavía no hay ningún error declarado. Un fallo entra en el repaso solo, pero el error —con su
        causa y su nota— lo declaras tú desde el resultado de una sesión o desde la ficha de la
        pregunta.
      </p>
    );
  }

  return (
    <div className="reader-split">
      <ul className="evidence" aria-label="Conceptos con fallos">
        {concepts.map((concepto) => (
          <li key={concepto.key}>
            <p>
              <strong>{concepto.label}</strong>{' '}
              <StatusBadge tone={concepto.open_count > 0 ? 'warning' : 'ok'}>
                {concepto.open_count > 0
                  ? `${String(concepto.open_count)} sin resolver`
                  : 'resueltos'}
              </StatusBadge>{' '}
              <span className="hint">
                {concepto.occurrences} fallo(s) · {concepto.errors.length} pregunta(s)
              </span>
            </p>
            <ul className="evidence">
              {concepto.errors.map((error) => (
                <li key={error.id}>
                  <button
                    className={error.id === selectedId ? 'button button--active' : 'button'}
                    type="button"
                    // **El nombre empieza por el texto que se ve** —el enunciado y la causa—, que es lo que
                    // exige `label-content-name-mismatch`: el texto visible tiene que estar dentro
                    // del nombre como trozo contiguo.
                    aria-label={`${error.stem ?? '(pregunta no disponible)'} ${CAUSE_LABEL[error.cause]}: abrir el error`}
                    onClick={() => {
                      onSelect(error.id === selectedId ? null : error.id);
                    }}
                  >
                    {error.stem ?? '(pregunta no disponible)'}{' '}
                    <span className="sample__path">{CAUSE_LABEL[error.cause]}</span>
                  </button>
                </li>
              ))}
            </ul>
          </li>
        ))}
      </ul>

      <div>
        {selectedId === null && <p className="hint">Elige un error para ver su historial.</p>}
        {selectedId !== null && detailIsPending && <LoadingState label="Cargando el error…" />}
        {selectedId !== null && detailIsError && (
          <ErrorState
            title="No se pudo cargar el error"
            message="El servidor no ha devuelto la ficha de este error."
            onRetry={onRetryDetail}
          />
        )}
        {detail !== undefined && <ErrorCard detail={detail} busy={busy} onResolve={onResolve} />}
      </div>
    </div>
  );
}

function ErrorCard({
  detail,
  busy,
  onResolve,
}: {
  detail: LearningErrorDetail;
  busy: boolean;
  onResolve: ConceptListProps['onResolve'];
}) {
  const [nota, setNota] = useState(detail.error.user_note ?? '');
  const error = detail.error;
  return (
    <section className="card" aria-labelledby="ficha-error">
      <h3 id="ficha-error">Error declarado</h3>
      <p>
        <StatusBadge tone={error.status === 'open' ? 'warning' : 'ok'}>
          {error.status === 'open' ? 'sin resolver' : 'resuelto'}
        </StatusBadge>{' '}
        <span className="hint">
          {CAUSE_LABEL[error.cause]} · {error.occurrences} vez/veces · {error.part_code ?? 'sin parte'}
        </span>
      </p>
      <dl className="facts">
        <dt>Pregunta</dt>
        <dd>{error.stem ?? 'no disponible'}</dd>
        <dt>Concepto</dt>
        <dd>{error.node_title ?? error.concept_label ?? 'sin concepto declarado'}</dd>
        <dt>Lo que marcaste</dt>
        <dd>{detail.chosen_option_keys.join(', ').toUpperCase() || 'en blanco'}</dd>
        <dt>Confianza al responder</dt>
        <dd>{detail.confidence ?? 'no la declaraste'}</dd>
        <dt>Repaso</dt>
        <dd>
          {detail.review === null || detail.review === undefined
            ? 'este fallo no tiene repaso (un blanco no lo crea)'
            : `toca el ${detail.review.due_at.slice(0, 10)} · cada ${String(detail.review.interval_days)} día(s) · ${String(detail.review.lapses)} fallo(s)`}
        </dd>
      </dl>

      <div className="form__row">
        <label className="form__label" htmlFor="nota-error">
          Nota propia
        </label>
        <input
          id="nota-error"
          className="selector__select"
          value={nota}
          onChange={(event) => {
            setNota(event.target.value);
          }}
        />
        <button
          className="button"
          type="button"
          disabled={busy}
          onClick={() => {
            onResolve({
              errorId: error.id,
              resolved: error.status === 'open',
              note: nota.trim() === '' ? null : nota,
            });
          }}
        >
          {error.status === 'open' ? 'Marcar resuelto' : 'Volver a abrirlo'}
        </button>
        <span className="hint">
          Resolver un error no detiene su repaso: seguir repasándolo es lo que hace que se quede.
        </span>
      </div>

      <h4>Historial del repaso</h4>
      {detail.events.length === 0 ? (
        <p className="hint">Este fallo no tiene repaso, así que no hay historial que enseñar.</p>
      ) : (
        <ul className="evidence">
          {detail.events.map((evento) => (
            <li key={evento.id}>
              <span className="sample__path">{evento.occurred_at.slice(0, 16).replace('T', ' ')}</span>{' '}
              {evento.outcome === null ? evento.kind : `${evento.kind}: ${evento.outcome}`} ·{' '}
              {evento.previous_interval_days ?? 0} → {evento.interval_days} día(s)
              <span className="hint"> · {evento.reason}</span>
            </li>
          ))}
        </ul>
      )}
      <p className="hint">
        La causa y la nota las declaras tú desde el resultado de una sesión: aquí solo se lee lo que
        ya está declarado, sin deducir por qué fallaste.
      </p>
    </section>
  );
}
