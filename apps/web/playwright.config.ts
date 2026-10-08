import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { defineConfig, devices } from '@playwright/test';

const here = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(here, '..', '..');

/**
 * El directorio de datos de la suite es **suyo y solo suyo**: `.e2e-data` dentro del repositorio.
 *
 * **No** se toma de `OPOFUENTE_DATA_DIR` a propósito (DEBT-026): esa es la variable con la que se
 * apunta la aplicación a los datos de verdad —el propietario la tiene puesta en su máquina, a veces
 * señalando una copia de su corpus—, y una suite que la hereda escribe sus pruebas **dentro de esos
 * datos**. Pasó el 22 de septiembre de 2026: dos ficheros sintéticos, su clasificación y sus sesiones
 * entraron en una copia del corpus del propietario por correr Playwright a mano con esa variable
 * puesta. Las puertas no lo veían porque `gates.ps1` borra la variable antes de la puerta 18; el
 * camino manual, que es el que se usa para depurar, sí.
 *
 * Para apuntar la suite a otro sitio hay una variable propia y explícita, que nadie pone sin querer.
 */
const e2eDataDir = process.env.OPOFUENTE_E2E_DATA_DIR ?? path.join(repoRoot, '.e2e-data');

/**
 * Datos nuevos en cada corrida: sin esto `.e2e-data` se llena con lo que van dejando las pasadas
 * (649 ficheros y 148 MB en un día de trabajo; 230 propuestas pendientes en la cola de revisión el
 * 8 de octubre de 2026) y la suite empieza a fallar por sus propios restos: la prueba de
 * accesibilidad de `review.spec.ts` pasó de 1,5 s a 39 s analizando el DOM acumulado y se quedó sin
 * tiempo por la mochila de las pasadas anteriores.
 *
 * La limpieza va **en el primer servidor** y no en un `globalSetup` a propósito: Playwright arranca
 * los `webServer` antes de `globalSetup` —comprobado midiéndolo—, así que para entonces la API ya
 * tiene abierto `opofuente.sqlite3` y borrar el directorio falla con `EPERM`. Aquí ocurre antes de
 * migrar nada, que es cuando de verdad está vacío. Con un directorio propio
 * (`OPOFUENTE_E2E_DATA_DIR`) no se borra nada: quien lo pone quiere conservar lo que haya.
 */
const limpiezaDatos =
  process.env.OPOFUENTE_E2E_DATA_DIR === undefined
    ? 'node -e "require(\'node:fs\').rmSync(process.env.OPOFUENTE_DATA_DIR, ' +
      '{ recursive: true, force: true, maxRetries: 5, retryDelay: 200 })" && '
    : '';

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
      // Borra el directorio de datos del E2E de la pasada anterior, migra el de esta (nunca el real),
      // siembra los perfiles oficiales (la siembra es idempotente) y arranca la API en loopback.
      command:
        limpiezaDatos +
        'uv run alembic upgrade head && uv run python -m opofuente.tools.seed_profiles && uv run python -m uvicorn opofuente.main:app --host 127.0.0.1 --port 8765',
      cwd: repoRoot,
      url: 'http://127.0.0.1:8765/api/v1/health/live',
      env: { ...inheritedEnv, OPOFUENTE_DATA_DIR: e2eDataDir, OPOFUENTE_LOG_LEVEL: 'WARNING' },
      // **No se reutiliza** un servidor que ya esté escuchando (DEBT-021). Reutilizarlo corría la
      // suite contra la base de datos de otro proceso —incluso contra una copia del material real—
      // y le dejaba escritas sus pruebas dentro. Peor: el puerto ocupado no avisaba de nada, así que
      // los fallos parecían defectos del código. Si el puerto está ocupado, la suite tiene que
      // fallar y decirlo.
      reuseExistingServer: false,
      timeout: 120_000,
    },
    {
      // Sirve el build de producción local (`npm run build` antes de las pruebas).
      command: 'npm run preview --workspace @opofuente/web -- --port 4173 --strictPort',
      cwd: repoRoot,
      url: 'http://127.0.0.1:4173',
      // Tampoco se reutiliza: un servidor de vista previa viejo sirve un paquete viejo, y entonces
      // la suite prueba una interfaz que ya no existe (pasó al renombrar una etiqueta).
      reuseExistingServer: false,
      timeout: 120_000,
    },
  ],
});
