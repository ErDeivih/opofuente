import type { DiagnosticReading } from '../../api/study';
import { ErrorState } from '../../components/ErrorState';
import { LoadingState } from '../../components/LoadingState';

export interface DiagnosticPanelProps {
  reading: DiagnosticReading | null;
  isPending: boolean;
  isError: boolean;
  onRetry: () => void;
}

/**
 * La lectura de un diagnóstico (06_QUESTIONS §5): por tema, con su intervalo y su muestra delante.
 *
 * Tres cosas que este panel no hace:
 *
 * 1. **no enseña un porcentaje de dominio**: enseña el recuento de la muestra y su intervalo al 95 %,
 *    que es lo que la muestra sostiene. Un «80 % de dominio» con cuatro preguntas es lo que la spec
 *    prohíbe;
 * 2. **no esconde la muestra corta**: cada tema dice cuántas preguntas traía, y el aviso del servidor
 *    («no son una nota ni un dominio del tema») va arriba, no en letra pequeña al final;
 * 3. **no inventa temas**: lo que se contestó de una pregunta sin tema asignado se agrupa como tal.
 */
export function DiagnosticPanel({ reading, isPending, isError, onRetry }: DiagnosticPanelProps) {
  if (isPending) {
    return <LoadingState label="Leyendo la muestra por temas…" />;
  }
  if (isError || reading === null) {
    return (
      <ErrorState
        title="No se pudo leer la muestra"
        message="El servidor no responde o la sesión no es un diagnóstico."
        onRetry={onRetry}
      />
    );
  }

  return (
    <section className="card" aria-labelledby="diagnostico-sesion">
      <h2 id="diagnostico-sesion">Estimación por tema</h2>
      <p className="hint">
        {reading.detail}. Con {reading.sample_size} pregunta(s) en la muestra y {reading.answered}{' '}
        contestada(s), un intervalo estrecho no es posible: sirve para saber **por dónde** mirar, no para
        poner una nota.
      </p>

      <table className="table">
        <caption className="table__caption">
          Muestra por tema con su intervalo del 95 %
        </caption>
        <thead>
          <tr>
            <th scope="col">Tema</th>
            <th scope="col">Respuestas</th>
            <th scope="col">Intervalo</th>
            <th scope="col">Qué se puede decir</th>
          </tr>
        </thead>
        <tbody>
          {reading.topics.map((ficha) => (
            <tr key={ficha.node_id}>
              <th scope="row">{ficha.title}</th>
              <td>
                {ficha.correct} de {ficha.answered}
              </td>
              <td>
                {ficha.interval === null || ficha.interval === undefined
                  ? 'sin respuestas'
                  : `${ficha.interval.low.toFixed(2)} – ${ficha.interval.high.toFixed(2)}`}
              </td>
              <td className="hint">{ficha.note}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
