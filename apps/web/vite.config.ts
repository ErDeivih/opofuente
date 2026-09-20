/// <reference types="vitest/config" />

import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [react()],
  server: {
    host: '127.0.0.1',
    port: 5173,
    strictPort: true,
  },
  preview: {
    host: '127.0.0.1',
    port: 4173,
    strictPort: true,
  },
  test: {
    environment: 'jsdom',
    include: ['tests/unit/**/*.test.{ts,tsx}'],
    setupFiles: ['./tests/setup.ts'],
    // Las pruebas E2E viven en tests/e2e y las ejecuta Playwright, no Vitest.
    exclude: ['tests/e2e/**', 'node_modules/**', 'dist/**'],
    restoreMocks: true,
    // El tiempo límite por prueba sube a 15 s **por lentitud medida, no para tapar fallos**: la
    // suite crea un jsdom por fichero (15 veces) y, con todos los workers en marcha, una prueba que
    // espera a que la pantalla pinte puede pasarse de los 5 s por defecto sin que nada esté mal. Una
    // prueba que de verdad falla sigue fallando: lo que cambia es cuánto se le da para llegar.
    testTimeout: 15_000,
  },
});
