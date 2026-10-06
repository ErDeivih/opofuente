import { existsSync, rmSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

/**
 * La suite arranca con **datos nuevos** (6 de octubre de 2026).
 *
 * El directorio `.e2e-data` se reutilizaba entre corridas y cada corrida deja dentro lo que importa:
 * después de un día de pasadas tenía **649 ficheros y 148 MB**. Con esa mochila, dos pruebas
 * (`library.spec.ts` y `questions.spec.ts`) empezaron a fallar —no encontraban una fila en la tabla, que
 * ya caía en otra página— y la suite pasó de **2,4 a 7,9 minutos**. El fallo parecía de la aplicación y
 * era de la suite: se comprobó borrando el directorio, y las dos volvieron a pasar.
 *
 * Si alguien quiere conservar los datos (para depurar a mano), pone `OPOFUENTE_E2E_DATA_DIR` y aquí no
 * se toca nada: la limpieza es solo del directorio por defecto.
 */
export default function globalSetup(): void {
  if (process.env.OPOFUENTE_E2E_DATA_DIR !== undefined) {
    return;
  }
  const here = path.dirname(fileURLToPath(import.meta.url));
  const repoRoot = path.resolve(here, '..', '..', '..');
  const datos = path.join(repoRoot, '.e2e-data');
  if (existsSync(datos)) {
    rmSync(datos, { recursive: true, force: true });
  }
}
