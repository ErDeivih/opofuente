import path from 'node:path';

import AxeBuilder from '@axe-core/playwright';
import { expect, test, type APIRequestContext, type Page } from '@playwright/test';

const API = 'http://127.0.0.1:8765/api/v1';

/**
 * Dónde se guardan las capturas de esta prueba. Por defecto, en `test-results` (efímero). Para
 * dejar evidencia en el repositorio se pasa `OPOFUENTE_CAPTURAS_DIR=docs/capturas` al ejecutar la
 * suite; así las capturas de la revisión visual no se pierden con la limpieza de Playwright.
 */
const CAPTURAS = process.env.OPOFUENTE_CAPTURAS_DIR ?? path.join('test-results');

interface NodoApi {
  id: string;
  node_type: string;
  official_code: string;
  title: string;
  path: string;
  children?: NodoApi[];
}

interface ApareceApi {
  convocation_id: string;
  convocation_title: string;
  official_url: string;
  role: string;
  convocation_status: string;
}

async function temarioComun(request: APIRequestContext): Promise<{ code: string; nodes: NodoApi[] }> {
  const lista = (await (await request.get(`${API}/curricula`)).json()) as {
    code: string;
    kind: string;
    active_version: { code: string } | null;
  }[];
  const comun = lista.find((item) => item.kind === 'common' && item.active_version !== null);
  expect(comun, 'la prueba necesita un temario común activo').toBeDefined();
  const detalle = (await (
    await request.get(`${API}/curricula/${comun?.code ?? ''}`)
  ).json()) as { code: string; nodes: NodoApi[] };
  return { code: detalle.code, nodes: detalle.nodes };
}

function temasDe(nodes: NodoApi[]): NodoApi[] {
  const temas: NodoApi[] = [];
  const recorrer = (items: NodoApi[]) => {
    for (const nodo of items) {
      if (nodo.node_type === 'topic') {
        temas.push(nodo);
      }
      recorrer(nodo.children ?? []);
    }
  };
  recorrer(nodes);
  return temas;
}

async function sinDesborde(page: Page): Promise<void> {
  const desborde = await page.evaluate(() => {
    return document.documentElement.scrollWidth - window.innerWidth;
  });
  expect(desborde, 'la pantalla no debe tener scroll horizontal').toBeLessThanOrEqual(1);
}

test('S13: el temario común enseña sus cinco bloques y cuarenta temas', async ({ page }) => {
  await page.goto('/temario');
  await expect(page.getByRole('heading', { level: 1, name: 'Temario' })).toBeVisible();
  await expect(page.locator('.page__lead')).toContainText('5 bloques');
  await expect(page.locator('.page__lead')).toContainText('40 temas');
  await expect(page.getByRole('list', { name: 'Temario común' })).toBeVisible();

  // La búsqueda perdona tildes y dice cuántos temas quedan.
  await page.getByLabel('Buscar un tema').fill('redes');
  await expect(page.getByRole('status')).toContainText(/tema/);
  await expect(page.getByRole('link', { name: /redes/i }).first()).toBeVisible();

  // Revisión visual de referencia: móvil y escritorio, sin desbordes.
  for (const ancho of [1280, 390]) {
    await page.setViewportSize({ width: ancho, height: ancho === 390 ? 844 : 900 });
    await page.goto('/temario');
    await expect(page.getByRole('list', { name: 'Temario común' })).toBeVisible();
    await sinDesborde(page);
    await page.screenshot({
      path: path.join(CAPTURAS, `temario-indice-${String(ancho)}.png`),
      fullPage: true,
    });
  }
});

test('S13: la ficha del tema enlaza las convocatorias C1 que lo estudian', async ({
  page,
  request,
}) => {
  const { nodes } = await temarioComun(request);
  const primerTema = temasDe(nodes)[0];
  expect(primerTema, 'el temario común debe tener temas').toBeDefined();

  const detalle = (await (
    await request.get(`${API}/curriculum-nodes/${primerTema?.id ?? ''}`)
  ).json()) as { appears_in: ApareceApi[] };
  expect(detalle.appears_in.length, 'el tema debe aparecer en convocatorias').toBeGreaterThan(0);

  await page.goto(`/temario/${primerTema?.id ?? ''}`);
  await expect(
    page.getByRole('heading', { level: 1, name: primerTema?.title ?? '' }),
  ).toBeVisible();
  await expect(page.getByText(primerTema?.path ?? '', { exact: true }).first()).toBeVisible();
  // La cabecera lleva a las convocatorias sin bajar la ficha entera, con el número real.
  const enlaceConvocatorias = page
    .locator('.page__lead')
    .getByRole('link', { name: `${String(detalle.appears_in.length)} convocatorias` });
  await expect(enlaceConvocatorias).toHaveAttribute('href', '#aparece-en');

  const aparece = page.locator('section[aria-labelledby="aparece-en"]');
  await expect(aparece.getByRole('heading', { name: 'En qué convocatorias aparece' })).toBeVisible();
  // Todas las convocatorias que devuelve el servidor tienen su enlace oficial en la ficha.
  await expect(aparece.locator('a[href^="http"]')).toHaveCount(detalle.appears_in.length);
  // Y se distingue lo confirmado de lo que solo está en el listado.
  const porConfirmar = detalle.appears_in.filter(
    (aparicion) => aparicion.convocation_status === 'draft',
  ).length;
  if (porConfirmar > 0) {
    await expect(aparece.getByText(/convocatorias? por confirmar/)).toBeVisible();
  }

  // Revisión móvil y de escritorio de la ficha, con sus convocatorias y sin desbordes.
  for (const ancho of [1280, 390]) {
    await page.setViewportSize({ width: ancho, height: ancho === 390 ? 844 : 900 });
    await page.goto(`/temario/${primerTema?.id ?? ''}`);
    await expect(
      page.getByRole('heading', { level: 1, name: primerTema?.title ?? '' }),
    ).toBeVisible();
    await expect(
      page.locator('section[aria-labelledby="aparece-en"]'),
    ).toBeVisible();
    await sinDesborde(page);
    await page.screenshot({
      path: path.join(CAPTURAS, `temario-ficha-${String(ancho)}.png`),
      fullPage: true,
    });
  }

  // Sin lenguaje de desarrollo en la pantalla (DOCTRINA-CALIDAD §8).
  await expect(page.getByText(/se calcula|cobertura/i)).toHaveCount(0);
});

test('S13: el temario no tiene violaciones automatizables', async ({ page }) => {
  await page.goto('/temario');
  await expect(page.getByRole('list', { name: 'Temario común' })).toBeVisible();
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
    .analyze();
  expect(results.violations).toEqual([]);
});
