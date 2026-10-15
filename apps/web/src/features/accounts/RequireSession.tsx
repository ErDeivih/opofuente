import { useQuery } from '@tanstack/react-query';
import { Navigate, useLocation } from 'react-router-dom';
import type { ReactNode } from 'react';

import { getMe } from '../../api/platform';
import { isApiError } from '../../api/client';
import { LoadingState } from '../../components/LoadingState';
import { usePolicy } from '../../app/policyContext';

/**
 * La guarda de rutas de la cuenta (§8 del objetivo vivo).
 *
 * **La guarda de la pantalla no es la que protege nada**: quien protege es el servidor, que contesta
 * 401 a `GET /accounts/me` sin sesión. Esto solo decide **qué se enseña** para que nadie rellene un
 * formulario que no va a poder enviar.
 *
 * Y solo guarda lo que de verdad necesita sesión —«mi cuenta»—, no la zona de estudio: cerrar el
 * temario con una guarda sería romper la regla que manda en todo el bloque, que es que quien
 * estudiaba sin cuenta siga estudiando igual.
 */
export function RequireSession({ children }: { children: ReactNode }) {
  const politica = usePolicy();
  const ubicacion = useLocation();

  const consulta = useQuery({
    queryKey: ['account-me'],
    queryFn: getMe,
    retry: 0,
    // Sin cuentas activadas no hay nada que preguntar.
    enabled: politica?.accounts.enabled === true,
  });

  if (politica === null || !politica.accounts.enabled) {
    // Esta instalación no tiene cuentas: no hay ninguna sesión que exigir.
    return <>{children}</>;
  }
  if (consulta.isPending) {
    return <LoadingState label="Comprobando tu sesión…" />;
  }
  if (consulta.isError && isApiError(consulta.error, 401)) {
    return <Navigate to={`/acceso?volver=${encodeURIComponent(ubicacion.pathname)}`} replace />;
  }
  return <>{children}</>;
}
