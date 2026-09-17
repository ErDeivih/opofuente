import type { DuplicateGroup, Question, QuestionOrigin } from '../../api/questions';
import { isConflicting, QUESTION_ORIGINS, QUESTION_STATUSES } from '../../api/questions';
import { ErrorState } from '../../components/ErrorState';
import { LoadingState } from '../../components/LoadingState';
import { StatusBadge } from '../../components/StatusBadge';
import {
  kindLabel,
  originLabel,
  originTone,
  questionStatusLabel,
  questionStatusTone,
  shortStem,
} from './labels';

export interface QuestionTableProps {
  questions: Question[];
  total: number;
  filters: { status: string; originType: string; onlyReserves: boolean };
  onFiltersChange: (filters: {
    status: string;
    originType: string;
    onlyReserves: boolean;
  }) => void;
  selectedId: string | null;
  onSelect: (questionId: string) => void;
  duplicates: DuplicateGroup[];
  isPending: boolean;
  isError: boolean;
  onRetry: () => void;
}

/**
 * Tabla de preguntas del conjunto, con sus filtros y —**arriba, no escondidos**— los conflictos.
 *
 * 07_UI-UX §7 lo dice así: «conflictos arriba, no escondidos en filtros». Un conflicto de claves es
 * justo lo que hay que mirar antes de estudiar con este banco, así que no puede depender de que
 * alguien se acuerde de filtrar por «en conflicto».
 */
export function QuestionTable({
  questions,
  total,
  filters,
  onFiltersChange,
  selectedId,
  onSelect,
  duplicates,
  isPending,
  isError,
  onRetry,
}: QuestionTableProps) {
  const conflictivas = questions.filter(isConflicting);
  const gruposEnConflicto = duplicates.filter((grupo) => grupo.conflicting_keys);
  const gruposReordenados = duplicates.filter((grupo) => grupo.kind === 'reordered_options');
  const hayConflictos = conflictivas.length > 0 || gruposEnConflicto.length > 0;

  if (isPending) {
    return <LoadingState label="Cargando las preguntas…" />;
  }

  if (isError) {
    return (
      <ErrorState
        title="No se pudieron cargar las preguntas"
        message="El conjunto no está disponible o el servidor no responde."
        onRetry={onRetry}
      />
    );
  }

  return (
    <>
      {hayConflictos && (
        <section className="card notice" aria-labelledby="aviso-conflictos">
          <h3 id="aviso-conflictos">Claves en conflicto: no se fusionan solas</h3>
          <p>
            {conflictivas.length > 0 && (
              <>
                <strong>{conflictivas.length}</strong>{' '}
                {conflictivas.length === 1 ? 'pregunta llega' : 'preguntas llegan'} con dos claves que
                se contradicen.{' '}
              </>
            )}
            {gruposEnConflicto.length > 0 && (
              <>
                Los duplicados detectados incluyen <strong>{gruposEnConflicto.length}</strong>{' '}
                {gruposEnConflicto.length === 1 ? 'grupo' : 'grupos'} con claves distintas.{' '}
              </>
            )}
            Dos respuestas que se contradicen no se pueden juntar sin decidir cuál es la buena, y eso
            lo decide una persona: la aplicación marca la contradicción y no elige.
          </p>
        </section>
      )}

      <div className="form__row">
        <label className="form__label" htmlFor="filtro-estado">
          Estado
        </label>
        <select
          id="filtro-estado"
          className="selector__select"
          value={filters.status}
          onChange={(event) => {
            onFiltersChange({ ...filters, status: event.target.value });
          }}
        >
          <option value="">todos</option>
          {QUESTION_STATUSES.map((estado) => (
            <option key={estado} value={estado}>
              {questionStatusLabel(estado)}
            </option>
          ))}
        </select>

        <label className="form__label" htmlFor="filtro-origen">
          Origen
        </label>
        <select
          id="filtro-origen"
          className="selector__select"
          value={filters.originType}
          onChange={(event) => {
            onFiltersChange({ ...filters, originType: event.target.value });
          }}
        >
          <option value="">todos</option>
          {QUESTION_ORIGINS.map((origen: QuestionOrigin) => (
            <option key={origen} value={origen}>
              {originLabel(origen)}
            </option>
          ))}
        </select>

        <label className="form__label" htmlFor="filtro-reservas">
          <input
            id="filtro-reservas"
            type="checkbox"
            checked={filters.onlyReserves}
            onChange={(event) => {
              onFiltersChange({ ...filters, onlyReserves: event.target.checked });
            }}
          />{' '}
          solo reservas
        </label>
      </div>

      {questions.length === 0 ? (
        <p className="hint">
          Este conjunto no tiene preguntas todavía. Se importan desde la pestaña «Importar»: pegando
          texto, un CSV con sus columnas mapeadas o una plantilla suelta.
        </p>
      ) : (
        <table className="table">
          <caption className="table__caption">
            {questions.length} de {total} preguntas del conjunto
          </caption>
          <thead>
            <tr>
              <th scope="col">Nº</th>
              <th scope="col">Enunciado</th>
              <th scope="col">Origen</th>
              <th scope="col">Tipo</th>
              <th scope="col">Clave</th>
              <th scope="col">Estado</th>
            </tr>
          </thead>
          <tbody>
            {questions.map((question) => (
              <tr key={question.id} aria-selected={question.id === selectedId}>
                <th scope="row">
                  {question.position}
                  {question.is_reserve && (
                    <>
                      {' '}
                      <StatusBadge tone="info">
                        reserva{question.reserve_order !== null && ` ${question.reserve_order}`}
                      </StatusBadge>
                    </>
                  )}
                </th>
                <td>
                  <button
                    className="button"
                    type="button"
                    aria-label={`Abrir la pregunta ${question.position}`}
                    onClick={() => {
                      onSelect(question.id);
                    }}
                  >
                    {shortStem(question.stem)}
                  </button>
                  {question.version_no > 1 && (
                    <span className="hint"> · versión {question.version_no}</span>
                  )}
                  {question.note !== null && question.note !== undefined && (
                    <p className="hint">corregida: {question.note}</p>
                  )}
                </td>
                <td>
                  <StatusBadge tone={originTone(question.origin_type)}>
                    {originLabel(question.origin_type)}
                  </StatusBadge>
                </td>
                <td className="hint">{kindLabel(question.question_type)}</td>
                <td>
                  <StatusBadge tone={question.key_outcome === 'keyed' ? 'ok' : 'warning'}>
                    {question.key_outcome === 'keyed'
                      ? `clave: ${question.correct_option_keys.join(', ') || 'sin opción'}`
                      : 'sin clave'}
                  </StatusBadge>
                </td>
                <td>
                  <StatusBadge tone={questionStatusTone(question.status)}>
                    {questionStatusLabel(question.status)}
                  </StatusBadge>
                  {question.explanation_count > 0 && (
                    <span className="hint"> · {question.explanation_count} explicación(es)</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {gruposReordenados.length > 0 && (
        <p className="hint">
          {gruposReordenados.length}{' '}
          {gruposReordenados.length === 1 ? 'grupo' : 'grupos'} con las{' '}
          <strong>mismas opciones en otro orden</strong>: es el modelo A/B de la misma pregunta, y se
          informa para poder relacionarlos a mano.
        </p>
      )}
    </>
  );
}
