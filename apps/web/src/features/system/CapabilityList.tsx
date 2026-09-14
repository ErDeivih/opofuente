import type { Capability } from '../../api/system';
import { StatusBadge } from '../../components/StatusBadge';
import { CAPABILITY_LABEL, CAPABILITY_TONE } from './statusBadges';

export interface CapabilityListProps {
  capabilities: Capability[];
}

export function CapabilityList({ capabilities }: CapabilityListProps) {
  return (
    <table className="table">
      <caption className="table__caption">Capacidades de esta instalación</caption>
      <thead>
        <tr>
          <th scope="col">Capacidad</th>
          <th scope="col">Estado</th>
          <th scope="col">Qué significa</th>
        </tr>
      </thead>
      <tbody>
        {capabilities.map((capability) => (
          <tr key={capability.id}>
            <th scope="row">
              {capability.label}
              {capability.planned_slice !== null && capability.planned_slice !== undefined && (
                <span className="tag">{capability.planned_slice}</span>
              )}
            </th>
            <td>
              <StatusBadge tone={CAPABILITY_TONE[capability.status]}>
                {CAPABILITY_LABEL[capability.status]}
              </StatusBadge>
            </td>
            <td>{capability.detail}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
