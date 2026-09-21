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

/** Escapa un literal de cadena PDF: paréntesis y barra invertida. */
function escapePdf(text: string): string {
  return text.replace(/\\/g, '\\\\').replace(/\(/g, '\\(').replace(/\)/g, '\\)');
}

/**
 * PDF mínimo **válido**, con su tabla `xref` y sus desplazamientos reales.
 *
 * Se construye a mano a propósito: un PDF de mentira (la cabecera y poco más) hace que la
 * extracción falle de verdad, y entonces la prueba estaría midiendo el fallo del andamio en lugar
 * del comportamiento de la aplicación.
 */
function buildPdf(pages: string[][]): Buffer {
  const pageIds = pages.map((_, index) => 3 + index);
  const contentIds = pages.map((_, index) => 3 + pages.length + index);
  const fontId = 3 + pages.length * 2;

  const objects: string[] = [
    '<< /Type /Catalog /Pages 2 0 R >>',
    `<< /Type /Pages /Kids [${pageIds.map((id) => `${id} 0 R`).join(' ')}] /Count ${pages.length} >>`,
  ];
  for (const id of contentIds) {
    objects.push(
      `<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents ${id} 0 R /Resources << /Font << /F1 ${fontId} 0 R >> >> >>`,
    );
  }
  for (const lines of pages) {
    const stream = [
      'BT /F1 12 Tf 60 780 Td 16 TL',
      ...lines.map((line) => `(${escapePdf(line)}) Tj T*`),
      'ET',
    ].join('\n');
    objects.push(
      `<< /Length ${Buffer.byteLength(stream, 'latin1')} >>\nstream\n${stream}\nendstream`,
    );
  }
  objects.push(
    '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>',
  );

  const parts: string[] = ['%PDF-1.4\n'];
  const offsets: number[] = [];
  let position = Buffer.byteLength(parts[0] ?? '', 'latin1');
  objects.forEach((body, index) => {
    offsets.push(position);
    const text = `${index + 1} 0 obj\n${body}\nendobj\n`;
    parts.push(text);
    position += Buffer.byteLength(text, 'latin1');
  });
  const entries = offsets.map((offset) => `${String(offset).padStart(10, '0')} 00000 n \n`).join('');
  parts.push(
    `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n${entries}` +
      `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${position}\n%%EOF\n`,
  );
  return Buffer.from(parts.join(''), 'latin1');
}

/** CRC-32 del formato ZIP (polinomio invertido 0xEDB88320), sin dependencias. */
function crc32(data: Buffer): number {
  let crc = 0xffffffff;
  for (const byte of data) {
    crc ^= byte;
    for (let bit = 0; bit < 8; bit += 1) {
      crc = (crc >>> 1) ^ (0xedb88320 & -(crc & 1));
    }
  }
  return (crc ^ 0xffffffff) >>> 0;
}

/** ZIP de entradas **sin comprimir**: lo justo para probar la expansión real desde la interfaz. */
function buildZip(entries: Record<string, string>): Buffer {
  const locals: Buffer[] = [];
  const central: Buffer[] = [];
  let offset = 0;

  for (const [name, content] of Object.entries(entries)) {
    const nameBytes = Buffer.from(name, 'utf8');
    const data = Buffer.from(content, 'utf8');
    const crc = crc32(data);

    const local = Buffer.alloc(30);
    local.writeUInt32LE(0x04034b50, 0);
    local.writeUInt16LE(20, 4);
    local.writeUInt16LE(0x0800, 6); // nombres en UTF-8
    local.writeUInt16LE(0, 8); // sin compresión
    local.writeUInt16LE(0, 10);
    local.writeUInt16LE(0x21, 12);
    local.writeUInt32LE(crc, 14);
    local.writeUInt32LE(data.length, 18);
    local.writeUInt32LE(data.length, 22);
    local.writeUInt16LE(nameBytes.length, 26);
    local.writeUInt16LE(0, 28);
    locals.push(local, nameBytes, data);

    const header = Buffer.alloc(46);
    header.writeUInt32LE(0x02014b50, 0);
    header.writeUInt16LE(20, 4);
    header.writeUInt16LE(20, 6);
    header.writeUInt16LE(0x0800, 8);
    header.writeUInt16LE(0, 10);
    header.writeUInt16LE(0, 12);
    header.writeUInt16LE(0x21, 14);
    header.writeUInt32LE(crc, 16);
    header.writeUInt32LE(data.length, 20);
    header.writeUInt32LE(data.length, 24);
    header.writeUInt16LE(nameBytes.length, 28);
    header.writeUInt16LE(0, 30);
    header.writeUInt16LE(0, 32);
    header.writeUInt16LE(0, 34);
    header.writeUInt16LE(0, 36);
    header.writeUInt32LE(0, 38);
    header.writeUInt32LE(offset, 42);
    central.push(header, nameBytes);

    offset += local.length + nameBytes.length + data.length;
  }

  const centralSize = central.reduce((total, part) => total + part.length, 0);
  const end = Buffer.alloc(22);
  end.writeUInt32LE(0x06054b50, 0);
  end.writeUInt16LE(0, 4);
  end.writeUInt16LE(0, 6);
  end.writeUInt16LE(Object.keys(entries).length, 8);
  end.writeUInt16LE(Object.keys(entries).length, 10);
  end.writeUInt32LE(centralSize, 12);
  end.writeUInt32LE(offset, 16);
  end.writeUInt16LE(0, 20);

  return Buffer.concat([...locals, ...central, end]);
}

test.beforeAll(() => {
  base = fs.mkdtempSync(path.join(os.tmpdir(), 'opofuente-e2e-'));
  inbox = path.join(base, 'material-sintetico');
  outside = path.join(base, 'fuera');
  fs.mkdirSync(inbox);
  fs.mkdirSync(outside);

  const pdf = buildPdf([
    [
      'OpoFuente E2E: contenido sintetico del tema 1.',
      'La Ley 39/2015 regula el procedimiento administrativo comun.',
    ],
    [
      'OpoFuente E2E: contenido sintetico del tema 2.',
      'El acto administrativo y su eficacia frente a terceros.',
    ],
  ]);
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

  // S03: la copia no termina en copiar. El texto de los ficheros está ahí, con su procedencia.
  const texto = page.getByRole('region', { name: 'Texto extraído' });
  await expect(texto.getByText('texto del documento').first()).toBeVisible();
  // Dos ficheros idénticos comparten representación: el lector declara sus dos rutas.
  const fila = texto.locator('li').filter({ hasText: 'tema-01-copia.pdf' });
  await expect(fila).toBeVisible();
  await fila.getByRole('button').click();
  await expect(texto.getByLabel('Texto extraído', { exact: true })).toContainText('Ley 39/2015');
});

test('E2E-03 bandeja: el texto pegado se copia, se extrae y se lee sin salir de la bandeja', async ({
  page,
}) => {
  await page.goto('/bandeja');

  await page
    .getByLabel('Texto', { exact: true })
    .fill('Tema 1. La Ley 39/2015 regula el procedimiento administrativo común.');
  await page.getByLabel(/Título/).fill('Apuntes del tema 1');
  await page.getByRole('button', { name: 'Guardar el texto' }).click();

  const importacion = page.getByRole('region', { name: 'Importación' });
  await expect(importacion.getByText('succeeded', { exact: true }).first()).toBeVisible({
    timeout: 60_000,
  });

  const texto = page.getByRole('region', { name: 'Texto extraído' });
  // El texto pegado no se disfraza de documento: se declara como tal, y su procedencia también.
  await expect(texto.getByRole('button', { name: 'texto pegado' })).toBeVisible();
  await expect(texto.getByText('origen: texto pegado')).toBeVisible();
  await expect(texto.getByLabel('Texto extraído', { exact: true })).toContainText('Ley 39/2015');
});

test('E2E-03 bandeja: un ZIP subido se expande en entradas propias y se extrae', async ({
  page,
}) => {
  const zip = path.join(base, 'paquete.zip');
  fs.writeFileSync(
    zip,
    buildZip({
      'temas/tema-01.txt': 'La Ley 39/2015 regula el procedimiento administrativo común.\n',
      'temas/tema-02.txt': 'El acto administrativo y su eficacia frente a terceros.\n',
    }),
  );

  await page.goto('/bandeja');
  await page.getByLabel(/Suelta aquí o elige ficheros/).setInputFiles(zip);

  const importacion = page.getByRole('region', { name: 'Importación' });
  await expect(importacion.getByText('succeeded', { exact: true }).first()).toBeVisible({
    timeout: 60_000,
  });

  // Los miembros del contenedor son entradas del lote, no un fichero opaco. Y el estado se lee: la
  // tabla no enseña el código crudo del enum (DEBT-019).
  const entradas = page.getByRole('table', { name: /entradas/ });
  await expect(entradas.getByText('paquete.zip/temas/tema-01.txt')).toBeVisible();
  await expect(entradas.getByText('paquete.zip/temas/tema-02.txt')).toBeVisible();
  await expect(entradas.getByText('contenedor expandido', { exact: true })).toBeVisible();
  await expect(entradas.getByText('expanded', { exact: true })).toHaveCount(0);
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
