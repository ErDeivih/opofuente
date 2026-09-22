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
  // Desde S07 la tarjeta de estudio lee las sesiones de verdad: o dice que no hay ninguna, o enseña
  // la última (una sesión a medias se retoma y una terminada se puede reabrir). El directorio de datos
  // del E2E se reutiliza entre ejecuciones, así que la prueba acepta los dos estados reales.
  await expect(
    page
      .getByText('Sin sesiones de estudio')
      .or(page.getByText('Última sesión'))
      .or(page.getByText('Sesión en marcha')),
  ).toBeVisible();

  // Desde S12.6 las dos tarjetas que antes no leían nada leen de verdad. El estado del programa dice
  // si se puede estudiar, con los tres pasos del servidor y su frase...
  await expect(page.getByRole('heading', { name: '¿Listo para estudiar?' })).toBeVisible();
  await expect(page.getByText(/Material por papel: /)).toBeVisible();
  await expect(page.getByText(/Preguntas por tema: /)).toBeVisible();
  await expect(page.getByText(/Claves activas: /)).toBeVisible();
  await expect(page.getByText(/listo para estudiar|falta/).first()).toBeVisible();
  // ...y las acciones necesarias o dicen qué espera una decisión, o dicen que no hay nada.
  await expect(
    page.getByText(/Nada esperando tu decisión|pendiente\(s\)/).first(),
  ).toBeVisible();
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

  // Estudiar se entregó en S07.
  await page.getByRole('link', { name: /^Estudiar/ }).click();
  await expect(page.getByRole('heading', { level: 1, name: 'Estudiar' })).toBeVisible();
  await expect(page.getByText('Esta sección todavía no está construida')).toHaveCount(0);

  // Errores se entregó en S10 y Cambios en S11.
  await page.getByRole('link', { name: /^Errores/ }).click();
  await expect(page.getByRole('heading', { level: 1, name: 'Errores' })).toBeVisible();
  await expect(page.getByText('Esta sección todavía no está construida')).toHaveCount(0);

  await page.getByRole('link', { name: /^Cambios/ }).click();
  await expect(page.getByRole('heading', { level: 1, name: 'Cambios' })).toBeVisible();
  await expect(page.getByText('Esta sección todavía no está construida')).toHaveCount(0);

  // Ajustes se entregó en S12: es la última sección del MVP y ya no hay ninguna pendiente.
  await page.getByRole('link', { name: /^Ajustes/ }).click();
  await expect(page.getByRole('heading', { level: 1, name: 'Ajustes' })).toBeVisible();
  await expect(page.getByText('Esta sección todavía no está construida')).toHaveCount(0);
  await expect(page.getByText(/slice S\d/)).toHaveCount(0);

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
