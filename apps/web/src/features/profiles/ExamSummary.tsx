import type { ExamPart, ExamRule } from '../../api/profiles';
import { StatusBadge } from '../../components/StatusBadge';

export interface ExamSummaryProps {
  parts: ExamPart[];
  rules: ExamRule[];
}

/** Etiquetas legibles para los enumerados del contrato. */
const FORMAT_LABEL: Record<string, string> = {
  single_choice: 'elección única',
  multi_mark_error: 'marcar errores',
  psychotechnical: 'psicotécnica',
};

function formatLabel(format: ExamPart['format']): string {
  if (format === null || format === undefined) {
    return '—';
  }
  return FORMAT_LABEL[format] ?? format;
}

/** Un dato que la convocatoria no publica se declara: no se rellena con una suposición. */
function value(amount: number | null | undefined): string {
  return amount === null || amount === undefined ? 'no consta' : String(amount);
}

/** Las pruebas de una parte se pintan igual cuelguen de una agrupación o no. */
function TestsTable({ tests }: { tests: ExamPart[] }) {
  return (
    <table className="table">
      <caption className="table__caption">Pruebas de esta parte</caption>
      <thead>
        <tr>
          <th scope="col">Prueba</th>
          <th scope="col">Formato</th>
          <th scope="col">Preguntas</th>
          <th scope="col">Puntuación</th>
          <th scope="col">Condición</th>
        </tr>
      </thead>
      <tbody>
        {tests.map((test) => (
          <tr key={test.code}>
            <th scope="row">{test.name}</th>
            <td>{formatLabel(test.format)}</td>
            <td>
              {value(test.ordinary_items)}
              {test.reserve_items !== null && test.reserve_items !== undefined
                ? ` (+${test.reserve_items} de reserva)`
                : ''}
            </td>
            <td>
              {test.score_max === null || test.score_max === undefined
                ? 'apto / no apto'
                : `${value(test.score_min)}–${value(test.score_max)}, mínimo ${value(test.pass_score)}`}
            </td>
            <td>
              {test.fail_if_errors_gte !== null && test.fail_if_errors_gte !== undefined
                ? `no apto con ${test.fail_if_errors_gte} o más errores`
                : '—'}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

/**
 * Reglas de examen de la convocatoria, cada una con la cita literal de la fuente.
 *
 * Si un dato no lo publica la convocatoria, se muestra «no consta» en lugar de un valor supuesto
 * (por ejemplo, TAI no dice cuántas alternativas tiene cada pregunta).
 *
 * No todas las convocatorias agrupan sus pruebas: Celador publica un ejercicio único que no cuelga
 * de ninguna agrupación. Esas pruebas se enseñan igual, sin inventarles un grupo para que encajen.
 */
export function ExamSummary({ parts, rules }: ExamSummaryProps) {
  const groups = parts.filter((part) => part.kind === 'group');
  const tests = parts.filter((part) => part.kind === 'test');
  const sinGrupo = tests.filter(
    (test) =>
      test.parent_code === null ||
      test.parent_code === undefined ||
      !groups.some((group) => group.code === test.parent_code),
  );

  return (
    <section className="card" aria-labelledby="reglas-examen">
      <h2 id="reglas-examen">Reglas del examen</h2>
      <p className="hint">
        Cada parte y cada regla incluye la cita literal de la convocatoria de la que procede. Esta
        pantalla solo muestra lo que publica la convocatoria: la puntuación de una sesión se calcula
        en Estudio, con estas reglas.
      </p>

      {groups.map((group) => (
        <div key={group.code} className="exam-group">
          <h3>
            {group.name}
            {group.time_minutes !== null && group.time_minutes !== undefined && (
              <span className="tag">{group.time_minutes} min</span>
            )}
          </h3>
          <p className="hint">{group.structure_note}</p>
          <TestsTable tests={tests.filter((test) => test.parent_code === group.code)} />
          {group.evidence_quote !== '' && (
            <blockquote className="quote">{group.evidence_quote}</blockquote>
          )}
        </div>
      ))}

      {sinGrupo.map((test) => (
        <div key={test.code} className="exam-group">
          <h3>
            {test.name}
            {test.time_minutes !== null && test.time_minutes !== undefined && (
              <span className="tag">{test.time_minutes} min</span>
            )}
          </h3>
          <p className="hint">{test.structure_note}</p>
          <TestsTable tests={[test]} />
          {test.evidence_quote !== '' && (
            <blockquote className="quote">{test.evidence_quote}</blockquote>
          )}
        </div>
      ))}

      <h3>Reglas transversales</h3>
      <ul className="rules">
        {rules.map((rule) => (
          <li key={rule.code} className="rules__item">
            <div className="rules__header">
              <StatusBadge tone="info">{rule.code}</StatusBadge>
              <span className="rules__value">{rule.value_text}</span>
            </div>
            <p className="rules__description">{rule.description}</p>
            <blockquote className="quote">{rule.evidence_quote}</blockquote>
          </li>
        ))}
      </ul>
    </section>
  );
}
