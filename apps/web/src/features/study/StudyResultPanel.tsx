import type { PartScore, Score, SessionResult, StudySession } from '../../api/study';
import { formatScore } from '../../api/study';
import { StatusBadge } from '../../components/StatusBadge';
import { LoadingState } from '../../components/LoadingState';
import { ErrorState } from '../../components/ErrorState';
import type { SessionReview } from '../../api/study';
import { feedbackLabel, outcomeLabel, outcomeTone, scoreText } from './labels';

export interface StudyResultPanelProps {
  session: StudySession;
  result: SessionResult | null;
  review: SessionReview | null;
  isPending: boolean;
  isError: boolean;
  onRetry: () => void;
}

/** Recuentos de una parte: es lo que el resultado tiene que separar (criterio de aceptación). */
function Counts({ part }: { part: PartScore }) {
  return (
    <span className="hint">
      {part.correct} aciertos · {part.wrong} fallos · {part.blank} en blanco
      {part.annulled > 0 && ` · ${String(part.annulled)} anuladas`}
      {part.excluded > 0 && ` · ${String(part.excluded)} sin corregir`}
      {part.conflicting > 0 && ` · ${String(part.conflicting)} en conflicto`}
      {part.reserves_used > 0 && ` · ${String(part.reserves_used)} reservas usadas`}
      {part.unused_reserves > 0 && ` · ${String(part.unused_reserves)} reservas sin usar`}
    </span>
  );
}

function PartRow({ part }: { part: PartScore }) {
  return (
    <tr>
      <th scope="row">{part.part_name ?? 'total'}</th>
      <td>
        {scoreText(part.score)} <Counts part={part} />
      </td>
      <td className="hint">
        {part.score_max === null ? 'sin máximo publicado' : `${String(part.score_max)} máx.`}
        {part.pass_score === null
          ? ''
          : ` · mínimo oficial ${String(part.pass_score)}, que no se aplica a la puntuación directa`}
      </td>
    </tr>
  );
}

/**
 * Resultado de la sesión (07_UI-UX §8).
 *
 * La puntuación que se enseña es la **directa** (`A − E/3`), con su fracción exacta: la aplicación no
 * calcula la calificación oficial 0-50 ni dice «apto», porque eso depende de unos baremos que la
 * convocatoria no publica (ADR-010). El resultado lo dice con sus palabras en lugar de dejar el hueco.
 */
export function StudyResultPanel({
  session,
  result,
  review,
  isPending,
  isError,
  onRetry,
}: StudyResultPanelProps) {
  if (isPending) {
    return <LoadingState label="Cargando el resultado…" />;
  }
  if (isError || result === null) {
    return (
      <ErrorState
        title="No se pudo cargar el resultado"
        message="El servidor no responde o la sesión no tiene resultado guardado."
        onRetry={onRetry}
      />
    );
  }

  return (
    <>
      <section className="card" aria-labelledby="resultado-sesion">
        <h2 id="resultado-sesion">Resultado</h2>
        <p>
          Puntuación directa:{' '}
          <strong>
            <ScoreLine score={result.total.score} />
          </strong>{' '}
          <StatusBadge tone="info">calificación oficial no disponible</StatusBadge>
        </p>
        {result.official_note !== null && result.official_note !== undefined && (
          <p className="hint">{result.official_note}</p>
        )}
        <table className="table">
          <caption className="table__caption">Puntuación directa por parte</caption>
          <thead>
            <tr>
              <th scope="col">Parte</th>
              <th scope="col">Puntuación y recuentos</th>
              <th scope="col">Umbrales de la convocatoria</th>
            </tr>
          </thead>
          <tbody>
            {result.parts.map((parte) => (
              <PartRow key={parte.part_code ?? 'sin-parte'} part={parte} />
            ))}
            <PartRow part={result.total} />
          </tbody>
        </table>

        <dl className="facts">
          <dt>Clave con la que se corrigió</dt>
          <dd>{result.key_label ?? session.key_label ?? 'sin clave'}</dd>
          <dt>Corrección</dt>
          <dd>{feedbackLabel(session.feedback)}</dd>
          <dt>Sin responder</dt>
          <dd>
            {result.unfinished}
            {result.unfinished > 0 && ' (no puntúan, ni a favor ni en contra)'}
          </dd>
          {result.calculated_at !== null && result.calculated_at !== undefined && (
            <>
              <dt>Calculado</dt>
              <dd>
                <time dateTime={result.calculated_at}>{result.calculated_at}</time>
              </dd>
            </>
          )}
        </dl>

        {result.substitutions.length > 0 && (
          <>
            <h3>Reservas que entraron</h3>
            <p className="hint">
              {result.substitutions.length === 1
                ? 'Una pregunta anulada se sustituyó por la primera reserva no usada.'
                : `${String(result.substitutions.length)} preguntas anuladas se sustituyeron por reservas.`}
            </p>
          </>
        )}
      </section>

      <section className="card" aria-labelledby="revision-sesion">
        <h3 id="revision-sesion">Revisión, pregunta a pregunta</h3>
        {review === null ? (
          <LoadingState label="Cargando la revisión…" />
        ) : (
          <>
            {review.note !== null && review.note !== undefined && (
              <p className="hint">{review.note}</p>
            )}
            <ol className="review">
              {review.entries.map((entrada) => (
                <li key={entrada.session_question_id}>
                  <p>
                    <strong>{entrada.position}.</strong> {entrada.stem}{' '}
                    {entrada.is_reserve && <StatusBadge tone="info">reserva</StatusBadge>}
                  </p>
                  <p className="hint">
                    {entrada.answered ? (
                      <>
                        Marcaste:{' '}
                        <span className="sample__path">
                          {entrada.chosen_option_keys.join(', ').toUpperCase() || 'en blanco'}
                        </span>
                      </>
                    ) : (
                      'Sin responder'
                    )}
                    {entrada.correction !== null && entrada.correction !== undefined && (
                      <>
                        {' · '}
                        <StatusBadge tone={outcomeTone(entrada.correction.outcome)}>
                          {outcomeLabel(entrada.correction.outcome)}
                        </StatusBadge>{' '}
                        {entrada.correction.correct_option_keys.length > 0 && (
                          <>
                            correcta:{' '}
                            <span className="sample__path">
                              {entrada.correction.correct_option_keys.join(', ').toUpperCase()}
                            </span>
                          </>
                        )}
                      </>
                    )}
                  </p>
                </li>
              ))}
            </ol>
          </>
        )}
      </section>
    </>
  );
}

/** La puntuación con su fracción exacta delante: `1.6667 (5/3)`. */
function ScoreLine({ score }: { score: Score }) {
  return <span>{formatScore(score)} puntos</span>;
}
