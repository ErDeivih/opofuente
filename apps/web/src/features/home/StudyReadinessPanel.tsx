import { Link } from 'react-router-dom';

import { useStudyReadiness } from '../../api/queries';
import { STEP_STATUS_LABEL, STEP_STATUS_TONE } from '../../api/readiness';
import { ErrorState } from '../../components/ErrorState';
import { LoadingState } from '../../components/LoadingState';
import { StatusBadge } from '../../components/StatusBadge';

function describeError(error: unknown): string {
  return error instanceof Error ? error.message : 'Error desconocido';
}

/**
 * «¿Puedo estudiar ya, o me falta algo?» (S12.6).
 *
 * La respuesta corta va en la insignia y las frases largas las escribe el **servidor**: la pantalla no
 * suma cifras ni decide qué falta, porque solo el servidor ve el corpus entero. Cada paso lleva el
 * enlace a la pantalla donde se resuelve, que es lo único que el propietario tiene que hacer él.
 */
export function StudyReadinessPanel({ oppositionId }: { oppositionId: string }) {
  const readiness = useStudyReadiness(oppositionId);

  return (
    <>
      <h3 id="listo-para-estudiar">¿Listo para estudiar?</h3>
      {readiness.isPending && <LoadingState label="Mirando qué falta…" />}
      {readiness.isError && (
        <ErrorState
          title="No se pudo mirar qué falta"
          message={describeError(readiness.error)}
          onRetry={() => {
            void readiness.refetch();
          }}
        />
      )}
      {readiness.isSuccess && (
        <>
          <p className="status-summary" aria-live="polite">
            {readiness.data.ready ? (
              <StatusBadge tone="ok">listo para estudiar</StatusBadge>
            ) : (
              <StatusBadge tone="warning">
                {readiness.data.missing.length === 1
                  ? 'falta una cosa'
                  : `faltan ${readiness.data.missing.length} cosas`}
              </StatusBadge>
            )}
            <span className="hint">
              {readiness.data.ready
                ? 'Los tres pasos están completos: puedes empezar una sesión.'
                : 'Lo que falta está dicho en su paso, con lo que hay que hacer para resolverlo.'}
            </span>
          </p>
          <ul className="check-list">
            {readiness.data.steps.map((step) => (
              <li key={step.key} className="check-list__item">
                <StatusBadge tone={STEP_STATUS_TONE[step.status]}>
                  {`${step.title}: ${STEP_STATUS_LABEL[step.status]}`}
                </StatusBadge>
                <span className="check-list__detail">{step.detail}</span>
                <Link to={step.action_href}>{step.action_label}</Link>
              </li>
            ))}
          </ul>
        </>
      )}
    </>
  );
}
