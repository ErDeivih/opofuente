import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';

import { AppShell } from './AppShell';
import { createQueryClient } from './queryClient';
import { AppRoutes } from './routes';

const defaultQueryClient = createQueryClient();

export interface AppProps {
  /** Permite a las pruebas usar un cliente propio y aislado. */
  queryClient?: QueryClient;
}

export function App({ queryClient }: AppProps = {}) {
  return (
    <QueryClientProvider client={queryClient ?? defaultQueryClient}>
      <BrowserRouter>
        <AppShell>
          <AppRoutes />
        </AppShell>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
