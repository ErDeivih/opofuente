/**
 * Convierte `artifacts/recorrido/filas.json` en la tabla de tiempos del informe.
 *
 * Los números se **leen del JSON que escribió el recorrido**, no se copian a mano: una cifra que no
 * está medida no entra en un documento.
 */

import { readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const AQUI = path.dirname(fileURLToPath(import.meta.url));
const SALIDA = path.resolve(AQUI, '..');
const filas = JSON.parse(readFileSync(path.join(SALIDA, 'filas.json'), 'utf8'));

const lineas = [
  '| # | paso | URL | carga (ms) | desborde a 390 px | errores de consola |',
  '|---|---|---|---|---|---|',
];
for (const fila of filas) {
  const url = fila.evidencia?.url ?? '—';
  const anchoMovil = fila.evidenciaMovil?.anchoDocumento ?? null;
  const desborde =
    anchoMovil === null || anchoMovil <= 390 ? 'no' : `sí (${String(anchoMovil)} px)`;
  const desbordesDetalle = (fila.evidenciaMovil?.desbordes ?? []).slice(0, 2).join('; ');
  lineas.push(
    `| ${fila.id.split('-')[0]} | ${fila.etiqueta} | \`${url}\` | ${fila.ms === null ? '—' : String(fila.ms)} | ` +
      `${desborde}${desbordesDetalle === '' ? '' : ` · ${desbordesDetalle}`} | ` +
      `${(fila.erroresConsola ?? []).length === 0 ? '0' : String((fila.erroresConsola ?? []).length)} |`,
  );
}

const totales = filas.filter((f) => typeof f.ms === 'number');
const suma = totales.reduce((t, f) => t + f.ms, 0);
lineas.push('', `Pasos con tiempo medido: ${String(totales.length)} · suma: ${String(suma)} ms`);

const lentos = [...totales].sort((a, b) => b.ms - a.ms).slice(0, 8);
lineas.push('', '## Los ocho pasos más lentos', '');
for (const fila of lentos) {
  lineas.push(`- **${String(fila.ms)} ms** · ${fila.etiqueta} (\`${fila.evidencia?.url ?? '—'}\`)`);
}

const conConsola = filas.filter((f) => (f.erroresConsola ?? []).length > 0);
lineas.push('', `## Errores de consola (${String(conConsola.length)} pasos)`, '');
for (const fila of conConsola) {
  lineas.push(`### ${fila.etiqueta}`, '');
  for (const error of fila.erroresConsola) lineas.push(`- ${error}`);
  lineas.push('');
}

writeFileSync(path.join(SALIDA, 'TIEMPOS.md'), `${lineas.join('\n')}\n`, 'utf8');
console.log(lineas.join('\n'));
