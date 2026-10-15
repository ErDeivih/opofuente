import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';

import { PolicyProvider } from './policy';
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
 *
 * Desde S28 (§8 a §11 del objetivo vivo) aquí se pregunta además **qué está encendido en esta
 * instalación** (`PolicyProvider`): con cuentas o sin ellas, con páginas legales o sin ellas. Va
 * dentro del cliente de consultas y fuera del enrutador porque lo necesitan las dos zonas, y por
 * encima del enrutador porque la primera petición —la de la política— no depende de la dirección.
 */
export function App({ queryClient }: AppProps = {}) {
  return (
    <QueryClientProvider client={queryClient ?? defaultQueryClient}>
      <PolicyProvider>
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
      </PolicyProvider>
    </QueryClientProvider>
  );
}
