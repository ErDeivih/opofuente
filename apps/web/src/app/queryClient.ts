import { QueryClient } from '@tanstack/react-query';

/** Estado remoto gestionado por TanStack Query; sin Redux en el MVP (02_ARCHITECTURE §4). */
export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: 1,
        refetchOnWindowFocus: false,
        staleTime: 5_000,
      },
    },
  });
}
