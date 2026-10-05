import { useQueryClient } from '@tanstack/react-query';

import { API_UNAVAILABLE_HELP } from '../api/client';
import { clearApiUnavailable, useApiUnavailable } from '../app/apiAvailability';

/**
 * Un solo aviso cuando la API no responde.
 *
 * Antes, con la API parada, cada tarjeta de cada pantalla decía «Failed to fetch» con su botón de
 * reintentar: ocho avisos iguales, en inglés, sin decir qué hacer (5 de octubre de 2026). Este aviso
 * aparece **una vez**, arriba, y explica cómo arrancar la aplicación.
 */
export function ApiUnavailableNotice() {
  const sinApi = useApiUnavailable();
  const cliente = useQueryClient();

  if (!sinApi) {
    return null;
  }

  return (
    <div className="notice notice--blocked" role="alert" data-testid="aviso-api-caida">
      <p>
        <strong>La aplicación no responde.</strong> {API_UNAVAILABLE_HELP}
      </p>
      <button
        className="button"
        type="button"
        onClick={() => {
          clearApiUnavailable();
          void cliente.invalidateQueries();
        }}
      >
        Reintentar
      </button>
    </div>
  );
}
