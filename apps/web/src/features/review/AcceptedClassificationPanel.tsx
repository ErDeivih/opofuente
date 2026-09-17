import { useQuery } from '@tanstack/react-query';

import {
  fetchAcceptedClassification,
  type AcceptedValue,
  type SubjectType,
} from '../../api/classification';
import { StatusBadge } from '../../components/StatusBadge';
import { axisLabel, statusLabel } from './labels';

/** Los cinco ejes, en el orden en el que se revisan: el que no viene, está sin clasificar. */
const EJES = ['document_type', 'opposition', 'topic', 'authority', 'rights'] as const;

export interface AcceptedClassificationPanelProps {
  subjectType: SubjectType;
  subjectId: string;
  /** Etiqueta visible del material, para que se sepa de qué se está hablando. */
  subjectLabel?: string | null | undefined;
}

function valorDe(valores: AcceptedValue[], eje: string): AcceptedValue | undefined {
  return valores.find((valor) => valor.axis === eje);
}

/**
 * Clasificación vigente de un material (07_UI-UX §4).
 *
 * Enseña **los cinco ejes** aunque solo haya valor en algunos: un eje vacío se dice («sin clasificar»)
 * en lugar de desaparecer, porque el hueco también es información. Y distingue lo que el usuario
 * aceptó de lo que el motor aplicó por su cuenta, que sigue siendo revisable (04 §8).
 */
export function AcceptedClassificationPanel({
  subjectType,
  subjectId,
  subjectLabel,
}: AcceptedClassificationPanelProps) {
  const consulta = useQuery({
    queryKey: ['classification', subjectType, subjectId],
    queryFn: () => fetchAcceptedClassification(subjectType, subjectId),
  });

  return (
    <section className="panel" aria-label="Clasificación de este material">
      <h2>Clasificación de este material</h2>
      <p className="hint">
        {subjectLabel ?? subjectId}
        {subjectType === 'representation' ? ' (texto del documento)' : ' (material)'}
      </p>

      {consulta.isPending && <p className="hint">Cargando la clasificación…</p>}
      {consulta.isError && (
        <p className="hint" role="alert">
          No se ha podido leer la clasificación de este material.
        </p>
      )}

      {consulta.data !== undefined && (
        <>
          {consulta.data.pending_review && (
            <p className="hint">
              Hay etiquetas aplicadas provisionalmente: son revisables y puedes confirmarlas o
              rechazarlas en la cola.
            </p>
          )}
          <table className="table">
            <caption>Lo que consta de este material, eje por eje</caption>
            <thead>
              <tr>
                <th scope="col">Eje</th>
                <th scope="col">Valor</th>
                <th scope="col">Origen de la etiqueta</th>
              </tr>
            </thead>
            <tbody>
              {EJES.map((eje) => {
                const valor = valorDe(consulta.data.values ?? [], eje);
                return (
                  <tr key={eje}>
                    <th scope="row">{axisLabel(eje)}</th>
                    <td>
                      {valor === undefined ? (
                        <span className="hint">sin clasificar</span>
                      ) : (
                        (valor.value_label ?? valor.value)
                      )}
                    </td>
                    <td>
                      {valor === undefined ? (
                        <span className="hint">—</span>
                      ) : valor.status === 'accepted' ? (
                        <StatusBadge tone="ok">{statusLabel(valor.status)}</StatusBadge>
                      ) : (
                        <StatusBadge tone="warning">{statusLabel(valor.status)}</StatusBadge>
                      )}
                      {valor?.is_critical === true && (
                        <span className="hint"> requiere tu confirmación</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </>
      )}
    </section>
  );
}
