import { createHash } from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

import AxeBuilder from '@axe-core/playwright';
import { expect, test, type Locator, type Page } from '@playwright/test';

/**
 * E2E-02: bandeja completa contra la API real.
 *
 * La bandeja de origen es **sintética** y se crea en el directorio temporal del sistema: nunca se
 * apunta a ficheros reales del usuario. Se crea fuera del directorio de datos (`OPOFUENTE_DATA_DIR`)
 * a propósito: el inventario rechaza la propia carpeta de datos para no importarse a sí misma.
 */

interface Snapshot {
  [name: string]: { sha256: string; mtimeMs: number; size: number };
}

const VIEWPORTS = [
  { name: 'escritorio 1440x900', width: 1440, height: 900 },
  { name: 'portátil 1024x768', width: 1024, height: 768 },
  { name: 'móvil 390x844', width: 390, height: 844 },
];

let base = '';
let inbox = '';
let outside = '';

test.beforeAll(() => {
  base = fs.mkdtempSync(path.join(os.tmpdir(), 'opofuente-e2e-'));
  inbox = path.join(base, 'material-sintetico');
  outside = path.join(base, 'fuera');
  fs.mkdirSync(inbox);
  fs.mkdirSync(outside);

  const pdf = Buffer.from(`%PDF-1.4\n${'OpoFuente E2E, contenido sintético.\n'.repeat(120)}`);
  fs.writeFileSync(path.join(inbox, 'tema-01.pdf'), pdf);
  // Copia byte a byte: debe producir **un** artefacto con dos orígenes.
  fs.writeFileSync(path.join(inbox, 'tema-01-copia.pdf'), pdf);
  fs.writeFileSync(path.join(inbox, 'notas.txt'), 'Apuntes sintéticos.\n', 'utf-8');
  // Material que la política omite y que el informe debe declarar.
  fs.writeFileSync(path.join(inbox, '.oculto.txt'), 'no debe copiarse\n', 'utf-8');
  fs.writeFileSync(path.join(inbox, '~$temporal.docx'), 'no debe copiarse\n', 'utf-8');
  fs.writeFileSync(path.join(inbox, 'programa.exe'), 'no debe copiarse\n', 'utf-8');
  fs.mkdirSync(path.join(inbox, 'node_modules'));
  fs.writeFileSync(path.join(inbox, 'node_modules', 'basura.js'), 'no debe copiarse\n', 'utf-8');
  fs.writeFileSync(path.join(outside, 'secreto.txt'), 'no debe copiarse\n', 'utf-8');
  // Junction fuera de la carpeta: no se sigue.
  fs.symlinkSync(outside, path.join(inbox, 'enlace-fuera'), 'junction');
});

test.afterAll(() => {
  fs.rmSync(base, { recursive: true, force: true });
});

function snapshot(root: string): Snapshot {
  const result: Snapshot = {};
  for (const name of fs.readdirSync(root)) {
    const full = path.join(root, name);
    const stat = fs.statSync(full);
    if (!stat.isFile()) {
      continue;
    }
    result[name] = {
      sha256: createHash('sha256').update(fs.readFileSync(full)).digest('hex'),
      mtimeMs: stat.mtimeMs,
      size: stat.size,
    };
  }
  return result;
}

async function inventariar(page: Page, carpeta: string) {
  await page.goto('/bandeja');
  await page.getByLabel(/Carpeta a inventariar/).fill(carpeta);
  await page.getByRole('button', { name: 'Inventariar (solo lectura)' }).click();
  await expect(page.getByRole('heading', { name: 'Vista previa del inventario' })).toBeVisible();
}

async function confirmarImportacion(page: Page) {
  await page.getByRole('button', { name: 'Importar una copia' }).click();
  const importacion = page.getByRole('region', { name: 'Importación' });
  await expect(importacion).toBeVisible();
  // El trabajo lo ejecuta el worker real del servidor: se espera a que termine de verdad.
  await expect(importacion.getByText('succeeded', { exact: true }).first()).toBeVisible({
    timeout: 60_000,
  });
  return importacion;
}

/** Valor de un término de la lista de datos (`<dt>Etiqueta</dt><dd>Valor</dd>`). */
function fact(scope: Locator, label: string) {
  return scope.locator(`dt:text-is("${label}") + dd`);
}

test('E2E-02 bandeja: el inventario no toca los originales y la copia conserva hash y fecha', async ({
  page,
}) => {
  const antes = snapshot(inbox);
  const antesFuera = snapshot(outside);

  await inventariar(page, inbox);

  // La vista previa describe sin copiar: recuento real de la carpeta sintética.
  const previa = page.getByRole('region', { name: 'Vista previa del inventario' });
  await expect(fact(previa, 'Ficheros a copiar')).toHaveText('3');
  await expect(previa.getByText('tema-01.pdf')).toBeVisible();
  await expect(
    previa.getByText(
      'OpoFuente ha leído la carpeta sin modificarla. No se ha copiado ni movido nada todavía.',
    ),
  ).toBeVisible();

  // La política de omisión se declara entera, incluido el enlace que sale de la carpeta.
  await expect(previa.getByText('omitted_hidden')).toBeVisible();
  await expect(previa.getByText('omitted_temporary')).toBeVisible();
  await expect(previa.getByText('omitted_executable')).toBeVisible();
  await expect(previa.getByText('omitted_directory')).toBeVisible();
  await expect(previa.getByText('link_escapes_root')).toBeVisible();
  await expect(previa.getByText('enlace-fuera')).toBeVisible();

  // Inventariar es estrictamente de lectura.
  expect(snapshot(inbox)).toEqual(antes);
  expect(snapshot(outside)).toEqual(antesFuera);

  const importacion = await confirmarImportacion(page);

  await expect(fact(importacion, 'Copiados')).toHaveText('3 de 3');
  // Dos ficheros idénticos comparten artefacto: 3 copias, 2 artefactos.
  await expect(fact(importacion, 'Artefactos')).toHaveText('2');
  await expect(fact(importacion, 'Informe cuadra')).toHaveText('sí');

  // Las entradas copiadas se listan con su estado real.
  const entradas = page.getByRole('table', { name: /entradas/ });
  await expect(entradas.getByText('tema-01.pdf')).toBeVisible();
  await expect(entradas.getByText('notas.txt')).toBeVisible();

  // El material omitido sigue en su sitio y sin cambios, y no aparece entre las entradas.
  await expect(entradas.getByText('.oculto.txt')).toHaveCount(0);
  await expect(entradas.getByText('secreto.txt')).toHaveCount(0);
  expect(snapshot(inbox)).toEqual(antes);
  expect(snapshot(outside)).toEqual(antesFuera);
});

test('E2E-02 bandeja: una carpeta inexistente se explica en lugar de fallar en silencio', async ({
  page,
}) => {
  await page.goto('/bandeja');
  await page.getByLabel(/Carpeta a inventariar/).fill(path.join(base, 'no-existe-esta-carpeta'));
  await page.getByRole('button', { name: 'Inventariar (solo lectura)' }).click();

  const error = page.getByRole('alert');
  await expect(error).toBeVisible();
  await expect(error).toContainText('No se pudo inventariar esa carpeta');
  await expect(page.getByRole('heading', { name: 'Vista previa del inventario' })).toHaveCount(0);
});

test('E2E-02 bandeja: el historial abre un lote anterior sin volver a copiar', async ({ page }) => {
  await inventariar(page, inbox);
  await confirmarImportacion(page);

  const historial = page.getByRole('region', { name: 'Lotes recientes' });
  await expect(historial.getByRole('button', { name: /import/ }).first()).toBeVisible();
  await historial.getByRole('button', { name: /import/ }).first().click();

  await expect(page.getByRole('heading', { name: 'Entradas del lote' })).toBeVisible();
  await expect(page.getByText('succeeded', { exact: true }).first()).toBeVisible();
});

for (const viewport of VIEWPORTS) {
  test(`E2E-02 bandeja responsive sin scroll horizontal (${viewport.name})`, async ({ page }) => {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await inventariar(page, inbox);
    await confirmarImportacion(page);

    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    expect(scrollWidth, `scroll horizontal en ${viewport.name}`).toBeLessThanOrEqual(
      viewport.width + 1,
    );
  });
}

test('E2E-02 bandeja accesibilidad: sin violaciones automatizables', async ({ page }) => {
  await inventariar(page, inbox);
  await confirmarImportacion(page);

  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
    .analyze();

  expect(results.violations).toEqual([]);
});
