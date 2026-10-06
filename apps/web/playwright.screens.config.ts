import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { defineConfig, devices } from '@playwright/test';

import base from './playwright.config';

/**
 * La configuración de `npm run screens`: las capturas de todas las pantallas (F0 del rediseño).
 *
 * Es la misma aplicación, los mismos datos de prueba y los mismos dos servidores que la suite; lo
 * único que cambia es qué ficheros se ejecutan. Se hace así —y no con una etiqueta en la suite— para
 * que las capturas no entren en las puertas: `npm run e2e` sigue mirando solo `tests/e2e`.
 */
const here = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  ...base,
  testDir: path.join(here, 'tests', 'screens'),
  // La herramienta **fotografía también las pantallas lentas**: la de Revisión tarda hoy 30-35 s
  // (medido el 6 de octubre de 2026) y con el límite de la suite se quedaba sin retrato. Esto no es el
  // juez: el tiempo de cada pantalla queda en el informe, que es lo que sirve para arreglarla.
  timeout: 120_000,
  fullyParallel: false,
  workers: 1,
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
});
