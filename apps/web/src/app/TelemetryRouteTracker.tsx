import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

import { trackPageView } from '../telemetry';

/**
 * Envía un `page_view` cada vez que cambia la ruta, con el nombre estable de la pantalla.
 *
 * Va dentro del router (lo monta `App`) porque necesita `useLocation`; el módulo de telemetría
 * decide si el envío está activo y, si no lo está, esto no hace nada.
 */
export function TelemetryRouteTracker() {
  const { pathname } = useLocation();

  useEffect(() => {
    trackPageView(pathname);
  }, [pathname]);

  return null;
}
