import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';

import { createQueryClient } from './queryClient';
import { AppRoutes } from './routes';

const defaultQueryClient = createQueryClient();

export interface AppProps {
  /** Permite a las pruebas usar un cliente propio y aislado. */
  queryClient?: QueryClient;
}

/**
 * La raíz de la aplicación (F1 del rediseño, 6 de octubre de 2026).
 *
 * Aquí ya **no** se elige el marco: cada zona trae el suyo desde sus rutas (`StudentZone` y
 * `AdminZone`), porque el marco es una consecuencia de la dirección y no una decisión de la raíz.
 */
export function App({ queryClient }: AppProps = {}) {
  return (
    <QueryClientProvider client={queryClient ?? defaultQueryClient}>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </QueryClientProvider>
  );
}
