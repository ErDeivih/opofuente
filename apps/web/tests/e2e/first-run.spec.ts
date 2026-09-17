import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

const VIEWPORTS = [
  { name: 'escritorio 1440x900', width: 1440, height: 900 },
  { name: 'portátil 1024x768', width: 1024, height: 768 },
  { name: 'móvil 390x844', width: 390, height: 844 },
];

test('E2E-00 primera ejecución: la aplicación arranca y declara su estado real', async ({ page }) => {
  await page.goto('/');

  await expect(page.getByRole('heading', { level: 1, name: 'Inicio' })).toBeVisible();
  // La sonda comprueba la base de datos de verdad, no un texto fijo.
  await expect(page.getByText('listo para trabajar')).toBeVisible();
  await expect(page.getByText('sqlite ok')).toBeVisible();
  await expect(page.getByText('directorio de datos escribible')).toBeVisible();
  // Desde S01, el estado del programa es real: hay oposición activa con su convocatoria.
  await expect(page.getByText('Oposición activa')).toBeVisible();
  await expect(page.getByText('tai-age-2025')).toBeVisible();
  // Los estados vacíos que siguen existiendo explican qué falta y cuándo llega.
  await expect(page.getByText('No hay material importado')).toBeVisible();
  await expect(page.getByText('Sin sesiones de estudio')).toBeVisible();
});

test('E2E-00 navegación: las secciones construidas llevan a su pantalla y el resto anuncia su slice', async ({
  page,
}) => {
  await page.goto('/');

  // La Biblioteca se entregó en S05: su ruta lleva a la pantalla, no a un aviso de pendiente.
  await page.getByRole('link', { name: /^Biblioteca/ }).click();
  await expect(page.getByRole('heading', { level: 1, name: 'Biblioteca' })).toBeVisible();
  await expect(page.getByText('Esta sección todavía no está construida')).toHaveCount(0);

  // Preguntas se entregó en S06.
  await page.getByRole('link', { name: /^Preguntas/ }).click();
  await expect(page.getByRole('heading', { level: 1, name: 'Preguntas' })).toBeVisible();
  await expect(page.getByText('Esta sección todavía no está construida')).toHaveCount(0);

  // Las secciones que siguen sin construirse declaran su slice en lugar de quedarse en blanco.
  await page.getByRole('link', { name: /^Estudiar/ }).click();
  await expect(page.getByRole('heading', { level: 1, name: 'Estudiar' })).toBeVisible();
  await expect(page.getByText('Esta sección todavía no está construida')).toBeVisible();
  await expect(page.getByText(/slice S07/)).toBeVisible();

  await page.getByRole('link', { name: /^Inicio/ }).click();
  await expect(page.getByRole('heading', { level: 1, name: 'Inicio' })).toBeVisible();
});

for (const viewport of VIEWPORTS) {
  test(`E2E-00 responsive sin scroll horizontal (${viewport.name})`, async ({ page }) => {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await page.goto('/');
    await expect(page.getByRole('heading', { level: 1, name: 'Inicio' })).toBeVisible();

    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    expect(scrollWidth, `scroll horizontal en ${viewport.name}`).toBeLessThanOrEqual(
      viewport.width + 1,
    );
  });
}

test('E2E-00 accesibilidad: sin violaciones automatizables en Inicio', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByText('listo para trabajar')).toBeVisible();

  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
    .analyze();

  expect(results.violations).toEqual([]);
});
