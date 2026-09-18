import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

import AxeBuilder from '@axe-core/playwright';
import { expect, test, type APIRequestContext, type Locator, type Page } from '@playwright/test';

/**
 * E2E-08 «RAG» (10_TEST-PLAN §5): una pregunta respaldada enseña citas que se pueden abrir, una
 * pregunta fuera del corpus se declara insuficiente y una versión sustituida no entra.
 *
 * El material es **sintético** y se escribe en el directorio temporal del sistema: nunca se usa nada
 * del usuario. Es un `.txt` —el caso más probable de quien estudia y el que ADR-008 convirtió en
 * material citable— así que además se comprueba que un texto sin sintaxis produce fragmentos con su
 * cita.
 *
 * Los dos caminos que se recorren son los que promete el producto:
 *
 * 1. **buscar no responde**: la búsqueda devuelve fragmentos con su cita y la respuesta se pide a
 *    propósito, así que la prueba hace las dos cosas por separado;
 * 2. **lo que no entra se dice**: la versión sustituida aparece en «Fuera del corpus» con su motivo,
 *    en lugar de desaparecer sin explicación (05_RAG §2).
 *
 * Cada documento lleva el sufijo de la ejecución en su título y en su texto, y las comprobaciones se
 * hacen **sobre su fila**: el directorio de datos del E2E se conserva entre ejecuciones, así que
 * «el primer resultado» no es una afirmación estable.
 *
 * Lo que **no** se prueba aquí, y por qué: el índice vectorial no existe (sin proveedor de
 * embeddings, DEBT-014), así que la búsqueda es literal y su degradación se declara en pantalla; el
 * conjunto patrón de 50+30+20 consultas de 05_RAG §9 es material de evaluación con datos reales y no
 * se simula con dos apuntes.
 */

const API_BASE = process.env.OPOFUENTE_API_URL ?? 'http://127.0.0.1:8765';

interface FilaDeLote {
  id: string;
  status: string;
}

interface Entrada {
  original_name: string;
}

interface Representacion {
  artifact_id: string;
  quality: string;
}

interface Promocion {
  document_id: string;
  version_id: string;
  created_document: boolean;
  created_version: boolean;
  applied: boolean;
}

async function json<T>(request: APIRequestContext, ruta: string): Promise<T> {
  const respuesta = await request.get(`${API_BASE}/api/v1${ruta}`);
  expect(respuesta.ok(), `GET ${ruta}: ${respuesta.status()} ${await respuesta.text()}`).toBe(true);
  return (await respuesta.json()) as T;
}

async function enviar<T>(
  request: APIRequestContext,
  ruta: string,
  cuerpo: unknown,
): Promise<T> {
  const respuesta = await request.post(`${API_BASE}/api/v1${ruta}`, { data: cuerpo });
  const detalle = `${respuesta.status()} ${await respuesta.text()}`;
  expect(respuesta.ok(), `POST ${ruta}: ${detalle}`).toBe(true);
  return (await respuesta.json()) as T;
}

function primero<T>(items: T[], mensaje: string): T {
  const first = items[0];
  if (first === undefined) {
    throw new Error(mensaje);
  }
  return first;
}

/** El lote que trae ese fichero: otros guiones comparten servidor y base. */
async function loteCon(request: APIRequestContext, nombre: string): Promise<FilaDeLote> {
  const lotes = await json<FilaDeLote[]>(request, '/ingestion-batches?limit=25');
  for (const candidato of lotes) {
    const detalle = await json<{ entries: Entrada[] }>(
      request,
      `/ingestion-batches/${candidato.id}`,
    );
    if (detalle.entries.some((entrada) => entrada.original_name === nombre)) {
      return candidato;
    }
  }
  throw new Error(`ningún lote trae ${nombre}`);
}

/** Ingresa un fichero por la bandeja (el camino real: se copia, se extrae y se clasifica). */
async function ingerir(page: Page, archivo: string): Promise<void> {
  await page.goto('/bandeja');
  await page.getByLabel(/Suelta aquí o elige ficheros/).setInputFiles([archivo]);
  await expect(
    page.getByRole('region', { name: 'Importación' }).getByText('succeeded', { exact: true }).first(),
  ).toBeVisible({ timeout: 60_000 });
}

/** Promociona el material copiado a documento y acepta la versión (la ruta que usa la ficha). */
async function promoverYAceptar(
  request: APIRequestContext,
  archivo: string,
  titulo: string,
  documentId?: string,
): Promise<Promocion> {
  const lote = await loteCon(request, path.basename(archivo));
  expect(lote.status).toBe('succeeded');
  const representaciones = await json<Representacion[]>(
    request,
    `/ingestion-batches/${lote.id}/representations`,
  );
  const representacion = primero(representaciones, 'la extracción no dejó representación');
  expect(representacion.quality).not.toBe('failed');

  const promocion = await enviar<Promocion>(request, '/documents', {
    artifact_id: representacion.artifact_id,
    title: titulo,
    document_type: 'personal_notes',
    ...(documentId === undefined ? {} : { document_id: documentId }),
  });
  expect(promocion.applied).toBe(true);
  await enviar(
    request,
    `/documents/${promocion.document_id}/versions/${promocion.version_id}/accept`,
    undefined,
  );
  return promocion;
}

/** La sección de resultados de una búsqueda. */
async function buscar(page: Page, termino: string): Promise<Locator> {
  await page.goto('/buscar');
  await page.getByLabel('Qué buscas').fill(termino);
  await page.getByRole('button', { name: 'Buscar' }).click();
  const resultados = page.getByRole('region', { name: 'Resultados' });
  await expect(resultados).toBeVisible();
  return resultados;
}

/** La fila de **este** documento en los resultados (el resto son ejecuciones anteriores). */
function filaDe(resultados: Locator, titulo: string): Locator {
  return resultados.locator('ol.results > li').filter({ hasText: titulo }).first();
}

/** Pregunta desde la pantalla y devuelve la tarjeta de la respuesta. */
async function preguntar(page: Page, pregunta: string): Promise<Locator> {
  await page.goto('/buscar');
  await page.getByLabel('Qué buscas').fill(pregunta);
  await page.getByRole('button', { name: 'Preguntar al corpus' }).click();
  const respuesta = page.getByRole('region', { name: 'Respuesta' });
  await expect(respuesta).toBeVisible({ timeout: 20_000 });
  return respuesta;
}

let temporal = '';

test.beforeAll(() => {
  temporal = fs.mkdtempSync(path.join(os.tmpdir(), 'opofuente-e2e-08-'));
});

test.afterAll(() => {
  fs.rmSync(temporal, { recursive: true, force: true });
});

test('E2E-08 RAG: respuesta con citas abribles, negativa insuficiente y versión sustituida fuera', async ({
  page,
  request,
}) => {
  // Dos ingestas que pasan por el worker de verdad, dos promociones, la aceptación y la sustitución.
  test.slow();

  const sufijo = Date.now().toString(36);
  const titulo = `Apuntes sinteticos E2E-08 ${sufijo}`;
  const viejo = `expediente${sufijo}`;
  const nuevo = `registro${sufijo}`;
  const v1 = path.join(temporal, `e2e-08-${sufijo}-v1.txt`);
  const v2 = path.join(temporal, `e2e-08-${sufijo}-v2.txt`);

  // Tres bloques separados por línea en blanco: tres fragmentos citables (ADR-008).
  fs.writeFileSync(
    v1,
    [
      titulo,
      '',
      `El plazo del procedimiento del ${viejo} es de diez dias habiles.`,
      '',
      'La solicitud se presenta en el registro electronico comun.',
      '',
    ].join('\n'),
  );
  // La segunda edición renombra el expediente: el término de la primera deja de existir.
  fs.writeFileSync(
    v2,
    [
      titulo,
      '',
      `El plazo del procedimiento del ${nuevo} es de diez dias habiles.`,
      '',
      'La solicitud se presenta en el registro electronico comun.',
      '',
    ].join('\n'),
  );

  // --- 1. El material entra por la bandeja y se promociona -------------------
  await ingerir(page, v1);
  const promocion = await promoverYAceptar(request, v1, titulo);
  expect(promocion.created_document).toBe(true);
  expect(promocion.created_version).toBe(true);

  // --- 2. Buscar devuelve el fragmento con su cita; y no responde ------------
  const resultados = await buscar(page, viejo);

  const fila = filaDe(resultados, titulo);
  await expect(fila).toBeVisible();
  await expect(
    fila.getByText(`El plazo del procedimiento del ${viejo} es de diez dias habiles.`),
  ).toBeVisible();
  // La búsqueda declara lo que no puede hacer: hoy no hay índice vectorial (DEBT-014).
  await expect(resultados.getByText('Lo que esta búsqueda no puede hacer')).toBeVisible();
  await expect(resultados.getByText(/la búsqueda ha sido solo léxica \(FTS5\)/)).toBeVisible();
  // Y buscar no contesta: no hay respuesta hasta que se pide.
  await expect(page.getByRole('heading', { name: 'Respuesta' })).toHaveCount(0);

  // --- 3. La cita se abre: lleva a la ficha del documento --------------------
  const enlace = fila.getByRole('link', { name: /Abrir en la Biblioteca: / });
  await expect(enlace).toHaveAttribute('href', /\/biblioteca\?documento=/);
  await enlace.click();
  await expect(page.getByRole('heading', { level: 1, name: 'Biblioteca' })).toBeVisible();
  await expect(page.getByText(titulo).first()).toBeVisible();

  // --- 4. Preguntar: respuesta respaldada, con cada afirmación citada --------
  const pregunta = `El plazo del procedimiento del ${viejo} es de diez dias habiles`;
  const respuesta = await preguntar(page, pregunta);
  await expect(respuesta.getByText('respaldada por el corpus')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Afirmaciones y de dónde salen' })).toBeVisible();
  await expect(respuesta.getByText('literal del corpus').first()).toBeVisible();
  // Cada afirmación trae su fragmento y su enlace: la respuesta no es una cita global.
  await expect(
    respuesta.getByText(`El plazo del procedimiento del ${viejo} es de diez dias habiles.`).first(),
  ).toBeVisible();
  await expect(respuesta.getByRole('link', { name: /Abrir en la Biblioteca: / }).first()).toBeVisible();
  // La respuesta dice quién la redactó: texto del corpus, sin modelo.
  await expect(respuesta.getByText('extractive', { exact: true })).toBeVisible();
  // Y se puede ver todo lo que se recuperó, se usara o no (05_RAG §5, paso 9).
  await page.getByText('Ver todo lo que se recuperó, se usara o no').click();
  await expect(respuesta.getByText(/fragmentos recuperados/)).toBeVisible();

  // La pantalla se puede usar: sin violaciones de accesibilidad en la búsqueda con resultados y en
  // la respuesta con sus citas (07_UI-UX §1).
  const sinViolaciones = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
    .analyze();
  expect(sinViolaciones.violations).toEqual([]);

  // --- 5. Pregunta fuera del corpus: insuficiente, no una respuesta inventada -
  const negativa = await preguntar(page, 'Cual es la capital de Mongolia');
  await expect(negativa.getByText('evidencia insuficiente')).toBeVisible();
  await expect(
    negativa.getByText('No hay evidencia en el corpus para responder a esto.'),
  ).toBeVisible();
  // Los términos que faltan se dicen, término a término.
  await expect(negativa.getByText(/no se ha recuperado nada del corpus sobre: capital, mongolia/)).toBeVisible();
  await expect(negativa.getByText('Afirmaciones y de dónde salen')).toHaveCount(0);
  await expect(page.getByRole('heading', { name: 'Lo que no se ha podido sostener' })).toBeVisible();

  // --- 6. Segunda edición del mismo documento y sustitución de la primera ----
  await ingerir(page, v2);
  const promocionV2 = await promoverYAceptar(request, v2, titulo, promocion.document_id);
  expect(promocionV2.created_document).toBe(false);
  expect(promocionV2.created_version).toBe(true);
  await enviar(
    request,
    `/documents/${promocion.document_id}/versions/${promocionV2.version_id}/mark-supersedes`,
    { superseded_id: promocion.version_id },
  );

  // --- 7. Lo sustituido no entra, y se dice por qué --------------------------
  const sustituido = await buscar(page, viejo);
  await expect(sustituido.locator('ol.results > li')).toHaveCount(0);
  await expect(sustituido.getByText(/Ningún fragmento publicado responde a esa búsqueda/)).toBeVisible();
  await expect(sustituido.getByText('Fuera del corpus')).toBeVisible();
  await expect(sustituido.getByText(/la versión está en estado «superseded»/)).toBeVisible();

  // Y lo que sustituye a lo sustituido sí se recupera: la exclusión es por vigencia, no por texto.
  const vigente = await buscar(page, nuevo);
  await expect(
    filaDe(vigente, titulo).getByText(`El plazo del procedimiento del ${nuevo} es de diez dias habiles.`),
  ).toBeVisible();
});
