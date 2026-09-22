import AxeBuilder from '@axe-core/playwright';
import { expect, test, type APIRequestContext } from '@playwright/test';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

/**
 * E2E-05 «Preguntas» (10_TEST-PLAN §5): importar un CSV parcialmente inválido, corregir el mapeo de
 * columnas, comprobar que las aceptadas quedan utilizables y ver las rechazadas con su causa.
 *
 * El material es **sintético** y se escribe en la propia pantalla: nada del usuario. El recorrido es
 * el de una persona que acaba de recibir un CSV de un tercero y no sabe cómo se llaman sus columnas.
 *
 * Tres precisiones sobre el guion, para no dar por hecho lo que no hay:
 *
 * 1. «Practicar las aceptadas» se comprueba **hasta donde llega S06**: las aceptadas entran en el
 *    banco con su clave, se abren en su ficha y su plantilla se puede activar (que es lo que las hace
 *    utilizables para corregir un examen). Contestarlas en una sesión con puntuación es S07, y el
 *    recorrido de sesión es E2E-06: aquí no se simula.
 * 2. El conjunto se crea en cada ejecución con un título único: los directorios de datos del E2E se
 *    reutilizan entre ejecuciones y la importación es idempotente por huella, así que reutilizar un
 *    conjunto convertiría las aceptadas en «ya estaban» y la prueba dejaría de medir lo que dice.
 * 3. El primer intento de importación lleva el mapeo **sin corregir** a propósito: es el paso que
 *    demuestra que el error de columnas se explica antes de tocar la base.
 */

const CSV_SIN_CORREGIR = [
  'enunciado;op1;op2;clave',
  'La Constitucion espanola se aprobo en;1976;1978;b',
].join('\n');

const API_BASE = process.env.OPOFUENTE_API_URL ?? 'http://127.0.0.1:8765';

/**
 * El material del que salen las preguntas: un texto con dos preguntas numeradas, cada una con sus
 * opciones. Se escribe en el directorio temporal del sistema y entra por la Bandeja, que es el camino
 * real: la copia, la extracción y la promoción no se simulan.
 */
const TEXTO_DEL_DOCUMENTO = [
  'Temario de prueba para preguntas importadas de un documento.',
  '',
  '1. La Constitucion Espanola se aprobo en:',
  'a) 1976',
  'b) 1978',
  'c) 1980',
  '',
  '2. El plazo de alegaciones del procedimiento es de:',
  'a) Diez dias habiles',
  'b) Veinte dias habiles',
  'c) Un mes',
  '',
].join('\n');

interface LoteConEntradas {
  id: string;
  status: string;
  entries: { original_name: string }[];
}

interface Representacion {
  artifact_id: string;
}

interface Promocion {
  document_id: string;
  version_id: string;
}

const CSV = [
  'enunciado;op1;op2;clave',
  'La Constitucion espanola se aprobo en;1976;1978;b',
  'El plazo de alegaciones es de diez dias habiles;Verdadero;Falso;a',
  'Fila a la que le falta una de las dos opciones;unica;;b',
  'Fila cuya clave no existe entre las opciones;uno;dos;z',
].join('\n');

/**
 * Crea un conjunto con un título irrepetible y devuelve ese título.
 *
 * Los directorios de datos del E2E se reutilizan entre ejecuciones y la importación es idempotente
 * por huella: reutilizar un conjunto convertiría las aceptadas en «ya estaban» y la prueba dejaría de
 * medir lo que dice.
 */
async function crearConjunto(page: import('@playwright/test').Page): Promise<string> {
  const titulo = `Importacion E2E ${String(Date.now())}-${String(Math.random()).slice(2, 8)}`;

  await page.goto('/preguntas');
  await expect(page.getByRole('heading', { level: 1, name: 'Preguntas' })).toBeVisible();

  await page.locator('summary').filter({ hasText: 'Crear un conjunto' }).click();
  await page.getByLabel('Título', { exact: true }).fill(titulo);
  await page.getByRole('button', { name: 'Crear el conjunto de preguntas' }).click();

  await expect(page.getByText(`Conjunto «${titulo}» creado.`)).toBeVisible();
  return titulo;
}

async function escribirCsv(page: import('@playwright/test').Page, csv: string) {
  await page.getByLabel('Contenido del CSV (con su cabecera)').fill(csv);
}

/** El lote que trae ese fichero: otros guiones comparten servidor y base, así que «el último» no vale. */
async function loteCon(request: APIRequestContext, nombre: string): Promise<LoteConEntradas> {
  const lotes = (await (
    await request.get(`${API_BASE}/api/v1/ingestion-batches?limit=25`)
  ).json()) as { id: string; status: string }[];
  for (const candidato of lotes) {
    const detalle = (await (
      await request.get(`${API_BASE}/api/v1/ingestion-batches/${candidato.id}`)
    ).json()) as { entries: { original_name: string }[] };
    if (detalle.entries.some((entrada) => entrada.original_name === nombre)) {
      return { id: candidato.id, status: candidato.status, entries: detalle.entries };
    }
  }
  throw new Error(`ningún lote trae ${nombre}`);
}

test('E2E-05 importación: las preguntas de un documento entran con su cita y se abre el original', async ({
  page,
  request,
}) => {
  // El guion hace dos ingestas (subir el texto y esperar al worker) y promociona el documento: con el
  // presupuesto por defecto se queda al límite por reloj, no por producto.
  test.slow();

  // --- 1. El material entra por la Bandeja, que es el camino real ------------
  const temporal = fs.mkdtempSync(path.join(os.tmpdir(), 'opofuente-e2e-05-'));
  const sufijo = Date.now().toString(36);
  const fichero = path.join(temporal, `temario-${sufijo}.txt`);
  fs.writeFileSync(fichero, TEXTO_DEL_DOCUMENTO, 'utf8');

  await page.goto('/bandeja');
  await page.getByLabel(/Suelta aquí ficheros o carpetas/).setInputFiles(fichero);
  const importacion = page.getByRole('region', { name: 'Importación' });
  await expect(importacion.getByText('succeeded', { exact: true }).first()).toBeVisible({
    timeout: 60_000,
  });

  // --- 2. Se promociona a documento y se acepta su versión -------------------
  // Por la API, como en E2E-04: la aceptación tiene su propio recorrido en la Biblioteca, y lo que
  // aquí se mide es la importación de preguntas desde un documento.
  const lote = await loteCon(request, path.basename(fichero));
  const representaciones = (await (
    await request.get(`${API_BASE}/api/v1/ingestion-batches/${lote.id}/representations`)
  ).json()) as Representacion[];
  const artifactId = representaciones[0]?.artifact_id ?? '';
  const titulo = `Temario E2E preguntas ${sufijo}`;
  const promocion = (await (
    await request.post(`${API_BASE}/api/v1/documents`, {
      data: { artifact_id: artifactId, title: titulo, document_type: 'curriculum' },
    })
  ).json()) as Promocion;
  const aceptada = await request.post(
    `${API_BASE}/api/v1/documents/${promocion.document_id}/versions/${promocion.version_id}/accept`,
    { data: {} },
  );
  expect(aceptada.ok(), `aceptar la versión: ${String(aceptada.status())}`).toBe(true);

  // --- 3. Se importan las preguntas desde ese documento ----------------------
  await crearConjunto(page);
  await page.getByRole('tab', { name: 'Importar' }).click();
  await page.getByLabel('Qué se importa').selectOption('document');
  await page
    .getByLabel('Documento del que salen las preguntas')
    .selectOption({ label: titulo });

  // El aviso dice de dónde salen: de la versión **aceptada**, que es la buena.
  await expect(page.getByText(/Se importa la versión aceptada de/)).toBeVisible();
  await page.getByRole('button', { name: 'Importar las preguntas del documento' }).click();

  // El informe dice las citas creadas: la pregunta queda enlazada con su fragmento.
  const informe = page.locator('section[aria-labelledby="informe-importacion"]');
  await expect(informe.getByText(/citas creadas/)).toBeVisible({ timeout: 30_000 });

  // --- 4. La pregunta está en el banco y su ficha enseña la cita -------------
  await page.getByRole('tab', { name: 'Preguntas' }).click();
  const banco = page.getByRole('table', { name: /preguntas del conjunto/ });
  await expect(banco.getByText('La Constitucion Espanola se aprobo en:')).toBeVisible();

  await page.getByRole('button', { name: 'Abrir la pregunta 1' }).click();
  const ficha = page.locator('div.card', { has: page.getByRole('heading', { name: 'Pregunta 1' }) });
  await expect(ficha.getByRole('heading', { name: 'Evidencia que la sostiene' })).toBeVisible();
  await expect(ficha.getByText('stem')).toBeVisible();
  await expect(ficha.getByText(/La Constitucion Espanola se aprobo en/).last()).toBeVisible();

  // Y la cita se puede abrir en el original: es el enlace que faltaba (DEBT-010).
  const enlace = ficha.getByRole('link', { name: /abrir el original de la cita/ });
  await expect(enlace).toBeVisible();
  await expect(enlace).toHaveAttribute(
    'href',
    new RegExp(`/api/v1/document-versions/${promocion.version_id}/original`),
  );
});

test('E2E-05 importación: el CSV con columnas raras se importa tras corregir el mapeo', async ({
  page,
}) => {
  await crearConjunto(page);

  await page.getByRole('tab', { name: 'Importar' }).click();
  await page.getByLabel('Qué se importa').selectOption('csv');

  // 1. Primer intento con el mapeo por defecto (`stem`, `option_a`…), que este fichero no trae.
  await escribirCsv(page, CSV_SIN_CORREGIR);
  await page.getByRole('button', { name: 'Importar en el conjunto' }).click();

  await expect(page.getByText('La importación no se aplicó')).toBeVisible();
  await expect(page.getByText(/no trae la columna del enunciado «stem»/)).toBeVisible();

  // 2. Se corrige el mapeo con las columnas que el fichero sí tiene.
  await page.getByLabel('Columna del enunciado').fill('enunciado');
  await page.getByLabel('Columnas de opciones (separadas por comas)').fill('op1, op2');
  await page.getByLabel('Columna de la clave').fill('clave');
  await escribirCsv(page, CSV);
  await page.getByRole('button', { name: 'Importar en el conjunto' }).click();

  // El error del intento anterior no se queda pegado a la pantalla.
  await expect(page.getByText('La importación no se aplicó')).toHaveCount(0);
  await expect(page.getByText('Importadas 2 preguntas nuevas y 2 claves.')).toBeVisible();

  // 3. Las dos buenas entran; el informe dice qué se creó y qué se leyó sin guardar.
  const informe = page.locator('section[aria-labelledby="informe-importacion"]');
  await expect(informe).toBeVisible();
  await expect(informe.getByRole('heading', { name: 'Qué ha pasado con lo importado' })).toBeVisible();

  // 4. Las dos malas salen con su número de fila y su causa, en lugar de desaparecer. El número es
  // el del fichero: la cabecera es la 1, así que la tercera fila de datos es la 4.
  const rechazadas = informe.getByRole('table', { name: /filas rechazadas/ });
  await expect(rechazadas).toBeVisible();
  await expect(rechazadas.getByRole('rowheader', { name: '4' })).toBeVisible();
  await expect(rechazadas.getByRole('cell', { name: 'few_options' })).toBeVisible();
  await expect(rechazadas.getByRole('rowheader', { name: '5' })).toBeVisible();
  await expect(rechazadas.getByRole('cell', { name: 'key_without_option' })).toBeVisible();

  // Y se pueden descargar para arreglarlas y volver a importarlas: el CSV lleva la causa.
  const descarga = informe.getByRole('link', { name: 'Descargar las filas rechazadas (CSV)' });
  await expect(descarga).toHaveAttribute('download', 'filas-rechazadas.csv');
  const href = await descarga.getAttribute('href');
  const contenido = decodeURIComponent((href ?? '').replace('data:text/csv;charset=utf-8,', ''));
  expect(contenido).toContain('fila,causa,detalle');
  expect(contenido).toContain('4,few_options');
  expect(contenido).toContain('5,key_without_option');

  // 5. Lo aceptado es utilizable: está en el banco, con su clave y marcado como privado. El nombre
  // accesible de la fila lo pone el botón que la abre, así que el enunciado se comprueba en la celda.
  await page.getByRole('tab', { name: 'Preguntas' }).click();
  const banco = page.getByRole('table', { name: /preguntas del conjunto/ });
  const primera = banco.getByRole('row', { name: /Abrir la pregunta 1/ });
  await expect(primera).toContainText('La Constitucion espanola se aprobo en');
  await expect(primera).toContainText('PRIVADA');
  await expect(primera).toContainText('clave: b');
  await expect(primera).toContainText('completa');
  const segunda = banco.getByRole('row', { name: /Abrir la pregunta 2/ });
  await expect(segunda).toContainText('El plazo de alegaciones es de diez dias habiles');
  await expect(segunda).toContainText('clave: a');

  // 6. La ficha de una aceptada enseña sus opciones y cuál marca la clave.
  await page.getByRole('button', { name: 'Abrir la pregunta 1' }).click();
  const ficha = page.locator('div.card', { has: page.getByRole('heading', { name: 'Pregunta 1' }) });
  await expect(ficha.getByText('1978')).toBeVisible();
  await expect(ficha.getByRole('listitem').filter({ hasText: '1978' }).getByText('correcta')).toBeVisible();
  // Y no inventa una cita: no hay documento de origen, y lo dice.
  await expect(ficha.getByText(/no tiene documento de origen adjunto/)).toBeVisible();

  // 7. La plantilla que llegó con el CSV es un borrador: activarla es lo que la vuelve utilizable.
  await page.getByRole('tab', { name: 'Plantillas' }).click();
  const plantillas = page.getByRole('table', { name: /plantillas del conjunto/ });
  await expect(plantillas.getByRole('rowheader', { name: 'v1' })).toBeVisible();
  await expect(plantillas.getByText('borrador, sin activar')).toBeVisible();
  await expect(plantillas.getByText('2 preguntas con desenlace')).toBeVisible();
  await expect(plantillas.getByText('sin aprobar')).toBeVisible();

  await page.getByRole('button', { name: 'Activar la plantilla v1' }).click();
  await expect(page.getByText(/Activarla es aprobarla/)).toBeVisible();
  await page.getByRole('button', { name: 'Confirmar la activación de la plantilla v1' }).click();

  await expect(
    page.getByText('Plantilla activada y aprobada con tu acción: queda registrado en la auditoría.'),
  ).toBeVisible();
  await expect(plantillas.getByText('activa', { exact: true })).toBeVisible();
  await expect(plantillas.getByText('sin aprobar')).toHaveCount(0);

  // El banco lo dice con el estado real del conjunto, no con un texto fijo.
  await page.getByRole('tab', { name: 'Preguntas' }).click();
  await expect(page.getByText('con clave activa')).toBeVisible();
});

test('E2E-05 accesibilidad: el banco y su informe sin violaciones automatizables', async ({
  page,
}) => {
  await crearConjunto(page);

  await page.getByRole('tab', { name: 'Importar' }).click();
  await page.getByLabel('Qué se importa').selectOption('csv');
  await page.getByLabel('Columna del enunciado').fill('enunciado');
  await page.getByLabel('Columnas de opciones (separadas por comas)').fill('op1, op2');
  await page.getByLabel('Columna de la clave').fill('clave');
  await escribirCsv(page, CSV);
  await page.getByRole('button', { name: 'Importar en el conjunto' }).click();
  await expect(page.getByText('Importadas 2 preguntas nuevas y 2 claves.')).toBeVisible();

  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
    .analyze();

  expect(results.violations).toEqual([]);
});

test('E2E-05 responsive: el banco no provoca scroll horizontal a 390 px', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await crearConjunto(page);

  await page.getByRole('tab', { name: 'Importar' }).click();
  await page.getByLabel('Qué se importa').selectOption('csv');
  await page.getByLabel('Columna del enunciado').fill('enunciado');
  await page.getByLabel('Columnas de opciones (separadas por comas)').fill('op1, op2');
  await page.getByLabel('Columna de la clave').fill('clave');
  await escribirCsv(page, CSV);
  await page.getByRole('button', { name: 'Importar en el conjunto' }).click();
  await expect(page.getByText('Importadas 2 preguntas nuevas y 2 claves.')).toBeVisible();

  await page.getByRole('tab', { name: 'Preguntas' }).click();
  await expect(page.getByRole('table', { name: /preguntas del conjunto/ })).toBeVisible();

  const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
  expect(scrollWidth, 'scroll horizontal a 390 px').toBeLessThanOrEqual(391);
});
