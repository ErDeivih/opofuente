/**
 * Genera `src/openapi.d.ts` a partir de `openapi.json`.
 *
 * `openapi.json` lo escribe el backend:
 *   uv run python -m opofuente.tools.export_openapi
 *
 * Con `--check` no escribe nada y falla si el fichero commiteado está desincronizado,
 * de modo que un cambio de contrato no puede pasar desapercibido (ver ADR-002).
 */

import { readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const contractsDir = path.resolve(here, '..');
const schemaPath = path.join(contractsDir, 'openapi.json');
const targetPath = path.join(contractsDir, 'src', 'openapi.d.ts');
const checkOnly = process.argv.includes('--check');

const HEADER = `/**
 * GENERADO AUTOMÁTICAMENTE — no editar a mano.
 * Fuente: packages/contracts/openapi.json (esquema OpenAPI de FastAPI).
 * Regenerar: uv run python -m opofuente.tools.export_openapi && npm run contracts:generate
 */

`;

async function render() {
  const module = await import('openapi-typescript');
  const openapiTS = module.default ?? module.openapiTS;
  if (typeof openapiTS !== 'function') {
    throw new Error('openapi-typescript no expone una función de generación compatible');
  }
  // Se pasa el objeto ya parseado: una ruta de Windows con letra de unidad se interpreta
  // como URL remota si se pasa como cadena.
  const schema = JSON.parse(readFileSync(schemaPath, 'utf8'));
  const result = await openapiTS(schema);
  const text = typeof result === 'string' ? result : module.astToString(result);
  return HEADER + text;
}

const rendered = await render();

if (checkOnly) {
  let current = '';
  try {
    current = readFileSync(targetPath, 'utf8');
  } catch {
    console.error('Faltan los tipos derivados. Ejecuta: npm run contracts:generate');
    process.exit(1);
  }
  if (current !== rendered) {
    console.error(
      'packages/contracts/src/openapi.d.ts está desincronizado con openapi.json. ' +
        'Ejecuta: npm run contracts:generate',
    );
    process.exit(1);
  }
  console.log('Tipos derivados sincronizados: openapi.d.ts');
} else {
  writeFileSync(targetPath, rendered, 'utf8');
  console.log('Tipos derivados escritos: src/openapi.d.ts');
}
