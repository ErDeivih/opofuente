import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

const API = 'http://127.0.0.1:8765/api/v1';
const GC_NAME = 'Escala de Cabos y Guardias de la Guardia Civil';
const TAI_NAME = 'Cuerpo de Técnicos Auxiliares de Informática de la Administración del Estado';

/** Los tres anchos de referencia de 07_UI-UX §14. */
const VIEWPORTS = [
  { name: 'escritorio 1440x900', width: 1440, height: 900 },
  { name: 'portátil 1024x768', width: 1024, height: 768 },
  { name: 'móvil 390x844', width: 390, height: 844 },
];

/**
 * Cambiar de oposición es una escritura y afecta a toda la aplicación, así que cada prueba deja
 * TAI activo al terminar. Sin esto, una prueba que falle a mitad dejaría el estado cambiado y
 * haría fallar a las siguientes por un motivo que no es el suyo.
 */
test.afterEach(async ({ request }) => {
  const response = await request.get(`${API}/oppositions`);
  const oppositions = (await response.json()) as { id: string; code: string }[];
  const tai = oppositions.find((item) => item.code === 'tai-age');
  if (tai !== undefined) {
    await request.post(`${API}/oppositions/${tai.id}/activate`);
  }
});

test('S01: el Programa muestra el temario oficial de TAI con su procedencia', async ({ page }) => {
  await page.goto('/programa');

  await expect(page.getByRole('heading', { level: 1, name: 'Programa' })).toBeVisible();
  // Cuatro bloques y treinta y tres temas, tal y como se siembran desde el BOE.
  await expect(page.getByText(/4 bloques/)).toBeVisible();
  await expect(page.getByText(/33 temas/)).toBeVisible();
  await expect(
    page.getByText('Organización del Estado y Administración electrónica'),
  ).toBeVisible();

  // Enlace oficial y fecha de publicación visibles.
  await expect(page.getByRole('link', { name: /BOE-A-2025-26262/ })).toBeVisible();
  await expect(page.getByText('2025-12-22')).toBeVisible();
});

test('S01: el Programa muestra las reglas del examen con su cita', async ({ page }) => {
  await page.goto('/programa');

  await expect(page.getByRole('heading', { name: 'Reglas del examen' })).toBeVisible();
  await expect(page.getByText('120 min')).toBeVisible();
  await expect(page.getByText('80 (+5 de reserva)')).toBeVisible();
  await expect(page.getByText('blank_answer_penalty')).toBeVisible();
  // Lo que la convocatoria no publica se declara: TAI no dice cuántas alternativas hay.
  await expect(page.getByText('No consta en la convocatoria')).toBeVisible();
});

test('S01: cambiar de oposición cambia el programa (25 temas de Guardia Civil)', async ({ page }) => {
  await page.goto('/programa');

  await page.getByLabel('Oposición').selectOption({ label: GC_NAME });

  await expect(page.getByRole('heading', { level: 1, name: 'Programa' })).toBeVisible();
  await expect(page.getByText(/25 temas/)).toBeVisible();
  // El botón del tema 1 incluye su código y su nivel en el nombre accesible.
  await expect(page.getByRole('button', { name: /DERECHOS HUMANOS/ })).toBeVisible();
  await expect(page.getByRole('link', { name: /BOE-A-2026-9982/ })).toBeVisible();

  // Y se puede volver.
  await page.getByLabel('Oposición').selectOption({ label: TAI_NAME });
  await expect(page.getByText(/33 temas/)).toBeVisible();
});

test('S01: abrir un tema muestra su ruta y su procedencia sin inventar cobertura', async ({
  page,
}) => {
  await page.goto('/programa');

  await expect(page.getByText(/33 temas/)).toBeVisible();
  await page.getByRole('button', { name: /La Constitución Española/ }).click();

  await expect(page.getByRole('heading', { name: 'Nodo seleccionado' })).toBeVisible();
  await expect(page.getByText('I.1', { exact: true })).toBeVisible();
  // Esta pantalla **no** inventa la cobertura: dice dónde se calcula en lugar de enseñar un cero que
  // parecería un dato. (Antes decía que no se calculaba todavía, y se calcula desde S04.)
  await expect(
    page.getByText(/Se calcula en Revisión, sobre las fuentes asignadas/),
  ).toBeVisible();
});

test('S01: accesibilidad del Programa sin violaciones automatizables', async ({ page }) => {
  await page.goto('/programa');
  await expect(page.getByRole('heading', { level: 1, name: 'Programa' })).toBeVisible();
  await expect(page.getByText(/33 temas/)).toBeVisible();

  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
    .analyze();

  expect(results.violations).toEqual([]);
});

/**
 * 07_UI-UX §14: los tres anchos de referencia, sin scroll horizontal.
 *
 * El árbol del programa es lo más ancho de la aplicación —rutas, títulos oficiales largos y las cifras
 * de cada nodo—, así que es donde un desbordamiento se ve primero. Faltaba: Programa solo tenía la
 * comprobación de accesibilidad.
 */
for (const viewport of VIEWPORTS) {
  test(`S01: responsive sin scroll horizontal (${viewport.name})`, async ({ page }) => {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await page.goto('/programa');
    await expect(page.getByRole('heading', { level: 1, name: 'Programa' })).toBeVisible();
    await expect(page.getByText(/33 temas/)).toBeVisible();

    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    expect(scrollWidth, `scroll horizontal en ${viewport.name}`).toBeLessThanOrEqual(
      viewport.width + 1,
    );
  });
}
