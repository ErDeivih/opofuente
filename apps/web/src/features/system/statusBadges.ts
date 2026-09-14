import type { CapabilityStatus } from '../../api/system';
import type { StatusTone } from '../../components/StatusBadge';

/** Traducción de los estados de capacidad de la API a la interfaz. */
export const CAPABILITY_TONE: Record<CapabilityStatus, StatusTone> = {
  enabled: 'ok',
  disabled: 'info',
  unavailable: 'blocked',
  configured_unverified: 'warning',
  planned: 'info',
};

export const CAPABILITY_LABEL: Record<CapabilityStatus, string> = {
  enabled: 'operativo',
  disabled: 'desactivado',
  unavailable: 'no disponible',
  configured_unverified: 'configurado sin verificar',
  planned: 'pendiente',
};
