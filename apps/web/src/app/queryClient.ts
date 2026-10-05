import { QueryClient, QueryCache, MutationCache } from '@tanstack/react-query';

import { noteApiError } from './apiAvailability';

/** Estado remoto gestionado por TanStack Query; sin Redux en el MVP (02_ARCHITECTURE §4). */
export function createQueryClient(): QueryClient {
  return new QueryClient({
    // El aviso de «la API no responde» se enciende aquí, en un solo sitio, y no en cada pantalla:
    // cuando el fallo es de red no tiene sentido que cada tarjeta cuente su propia versión.
    queryCache: new QueryCache({
      onError: (error) => {
        noteApiError(error);
      },
    }),
    mutationCache: new MutationCache({
      onError: (error) => {
        noteApiError(error);
      },
    }),
    defaultOptions: {
      queries: {
        retry: 1,
        refetchOnWindowFocus: false,
        staleTime: 5_000,
      },
    },
  });
}
