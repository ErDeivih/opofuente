import { useCapabilities } from '../../api/queries';
import { StatusBadge } from '../../components/StatusBadge';
import { CAPABILITY_LABEL, CAPABILITY_TONE } from './statusBadges';

/**
 * Indicadores de cabecera: estado del worker y política de IA.
 *
 * Si la API no responde, se dice; no se inventa un estado correcto (07_UI-UX §12).
 */
export function SystemIndicators() {
  const capabilities = useCapabilities();

  if (capabilities.isPending) {
    return (
      <p className="indicators indicators--unknown" role="status">
        Consultando capacidades…
      </p>
    );
  }

  if (capabilities.isError) {
    return (
      <p className="indicators indicators--unknown" role="status">
        API no disponible: no se puede confirmar el estado del sistema.
      </p>
    );
  }

  const worker = capabilities.data.capabilities.find((item) => item.id === 'worker');
  const llm = capabilities.data.capabilities.find((item) => item.id === 'llm');

  return (
    <ul className="indicators" aria-label="Estado de capacidades clave">
      <li>
        <span className="indicators__label">Worker</span>
        {worker === undefined ? (
          <StatusBadge tone="warning">sin datos</StatusBadge>
        ) : (
          <StatusBadge tone={CAPABILITY_TONE[worker.status]}>
            {CAPABILITY_LABEL[worker.status]}
          </StatusBadge>
        )}
      </li>
      <li>
        <span className="indicators__label">IA</span>
        {llm === undefined ? (
          <StatusBadge tone="warning">sin datos</StatusBadge>
        ) : (
          <StatusBadge tone={CAPABILITY_TONE[llm.status]}>
            {CAPABILITY_LABEL[llm.status]}
          </StatusBadge>
        )}
      </li>
    </ul>
  );
}
