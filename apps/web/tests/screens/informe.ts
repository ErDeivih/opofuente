/**
 * El informe de las capturas (F0 del rediseño).
 *
 * Cada pantalla deja su fila en un JSON suelto, y esto lo junta en `report.md`. Se hace así y no en
 * memoria a propósito: **Playwright reinicia el proceso al fallar una prueba**, y con el informe en
 * memoria se perdían todas las filas anteriores al fallo (medido: 9 de 22 el 6 de octubre de 2026, y
 * justo faltaba el informe de las pantallas rápidas, que son la mayoría).
 */

import { mkdirSync, readdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import path from 'node:path';

import type { Encontrado } from '../palabrasProhibidas';

export interface FilaDeCaptura {
  ruta: string;
  ancho: string;
  ms: number;
  errores: string[];
  violaciones: string[];
  prohibidas: Encontrado[];
  alto?: number;
  /**
   * El nombre del PNG, sin extensión. Se guarda **calculado** y no se deduce de la ruta al escribir
   * el informe: una ruta con identificador dentro (`/test/<uuid>`) daría un fichero distinto en cada
   * corrida y el enlace del informe apuntaría a un PNG que no existe.
   */
  fichero?: string;
}

const SALIDA = path.resolve(process.cwd(), '..', '..', 'artifacts', 'screens');
const FILAS = path.join(SALIDA, 'filas');

/** Deja la fila de una pantalla en disco, sin fiarse de la memoria del proceso. */
export function guardarFila(fila: FilaDeCaptura): void {
  mkdirSync(FILAS, { recursive: true });
  const nombre = `${fila.ruta.replace(/[^a-zA-Z0-9]/g, '_')}-${fila.ancho}.json`.replace(
    /×/g,
    'x',
  );
  writeFileSync(path.join(FILAS, nombre), JSON.stringify(fila, null, 2), 'utf8');
}

/** Junta todas las filas en el informe y limpia los JSON sueltos. */
export function escribirInforme(): void {
  mkdirSync(SALIDA, { recursive: true });
  const filas: FilaDeCaptura[] = [];
  if (existsSync(FILAS)) {
    for (const nombre of readdirSync(FILAS)) {
      filas.push(JSON.parse(readFileSync(path.join(FILAS, nombre), 'utf8')) as FilaDeCaptura);
    }
  }
  filas.sort((izquierda, derecha) =>
    `${izquierda.ruta}${izquierda.ancho}`.localeCompare(`${derecha.ruta}${derecha.ancho}`),
  );

  const lineas = [
    '# Capturas de las pantallas',
    '',
    'Generado por `npm run screens` (F0 del rediseño). Las palabras prohibidas se **informan**:',
    'todavía no bloquean nada.',
    '',
    '| ruta | ancho | carga | errores de consola | violaciones axe | palabras prohibidas |',
    '| --- | --- | --- | --- | --- | --- |',
  ];
  for (const fila of filas) {
    lineas.push(
      `| \`${fila.ruta}\` | ${fila.ancho} | ${fila.ms} ms | ${fila.errores.length} | ` +
        `${fila.violaciones.length} | ${fila.prohibidas.map((p) => p.palabra).join(', ') || '—'} |`,
    );
  }

  const conProhibidas = filas.filter((fila) => fila.prohibidas.length > 0);
  lineas.push(
    '',
    `## Palabras prohibidas encontradas (${conProhibidas.length} de ${filas.length} capturas)`,
    '',
  );
  if (conProhibidas.length === 0) {
    lineas.push('Ninguna: la zona del alumno no enseña nada del material ni de la cocina interna.');
  }
  for (const fila of conProhibidas) {
    lineas.push(`### ${fila.ruta} · ${fila.ancho}`, '');
    for (const encontrada of fila.prohibidas) {
      lineas.push(`- «${encontrada.palabra}»: …${encontrada.contexto}…`);
    }
    lineas.push('');
  }

  lineas.push('', '## PNG', '');
  for (const fila of filas) {
    const fichero = fila.fichero ?? nombreDeFichero(fila.ruta, fila.ancho);
    lineas.push(`- [${fila.ruta} · ${fila.ancho}](${fichero}.png)`);
  }

  // Los errores de consola, con su texto: una pantalla que carga con un error en la consola está
  // avisando de algo, y el recuento a secas no dice de qué.
  const conErrores = filas.filter((fila) => fila.errores.length > 0);
  lineas.push('', `## Errores de consola (${conErrores.length} capturas)`, '');
  for (const fila of conErrores) {
    lineas.push(`### ${fila.ruta} · ${fila.ancho}`, '');
    for (const error of fila.errores) {
      lineas.push(`- ${error.slice(0, 300)}`);
    }
    lineas.push('');
  }
  writeFileSync(path.join(SALIDA, 'report.md'), `${lineas.join('\n')}\n`, 'utf8');
  rmSync(FILAS, { recursive: true, force: true });
}

/** El nombre del PNG de una captura: `inicio-escritorio.png`, `temario-I-1-movil.png`. */
export function nombreDeFichero(ruta: string, ancho: string): string {
  const limpio = ruta.replace(/^\//, '').replace(/[/?=.]/g, '-') || 'inicio';
  return `${limpio}-${ancho}`;
}

function existsSync(ruta: string): boolean {
  try {
    readdirSync(ruta);
    return true;
  } catch {
    return false;
  }
}
