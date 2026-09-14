import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { defineConfig, devices } from '@playwright/test';

const here = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(here, '..', '..');
const e2eDataDir = process.env.OPOFUENTE_DATA_DIR ?? path.join(repoRoot, '.e2e-data');

/** Entorno del sistema sin variables sin definir, para pasarlo a los procesos hijos. */
const inheritedEnv: Record<string, string> = Object.fromEntries(
  Object.entries(process.env).filter((entry): entry is [string, string] => {
    return typeof entry[1] === 'string';
  }),
);

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false,
  workers: 1,
  timeout: 30_000,
  expect: { timeout: 10_000 },
  reporter: [['list']],
  use: {
    baseURL: 'http://127.0.0.1:4173',
    trace: 'retain-on-failure',
    locale: 'es-ES',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: [
    {
      // Migra el directorio de datos del E2E (nunca el real), siembra los perfiles oficiales
      // (la siembra es idempotente) y arranca la API en loopback.
      command:
        'uv run alembic upgrade head && uv run python -m opofuente.tools.seed_profiles && uv run python -m uvicorn opofuente.main:app --host 127.0.0.1 --port 8765',
      cwd: repoRoot,
      url: 'http://127.0.0.1:8765/api/v1/health/live',
      env: { ...inheritedEnv, OPOFUENTE_DATA_DIR: e2eDataDir, OPOFUENTE_LOG_LEVEL: 'WARNING' },
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
    {
      // Sirve el build de producción local (`npm run build` antes de las pruebas).
      command: 'npm run preview --workspace @opofuente/web -- --port 4173 --strictPort',
      cwd: repoRoot,
      url: 'http://127.0.0.1:4173',
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
  ],
});
