import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

import {
  ADMIN_NAV_ITEMS,
  ROUTE_REDIRECTS,
  STUDENT_NAV_ITEMS,
} from '../../src/app/navigation';
import { revisarPantalla } from '../palabrasProhibidas';

/**
 * E2E-00, después de F1 (6 de octubre de 2026): la aplicación tiene **dos zonas**.
 *
 * Lo que se comprueba aquí es lo que promete la fase: que el alumno tiene siete entradas y ninguna
 * de la trastienda, que el panel tiene su aviso de que no hay contraseña, que las pantallas que ya
 * existían se alcanzan por `/admin/...` y que **ninguna dirección antigua da 404** (redirige a su
 * sitio nuevo, sin perder lo que llevaba la consulta).
 *
 * La lista de rutas no se copia: se lee de `src/app/navigation.ts`, que es la misma que usa la
 * aplicación. Si una entrada del menú se queda sin pantalla, esta prueba lo dice.
 */

const VIEWPORTS = [
  { name: 'escritorio 1440x900', width: 1440, height: 900 },
  { name: 'portátil 1024x768', width: 1024, height: 768 },
  { name: 'móvil 390x844', width: 390, height: 844 },
];

/** La pantalla de cada sección del panel: su título de nivel 1. */
const PANTALLAS_DEL_PANEL: readonly { readonly path: string; readonly h1: string }[] = [
  { path: '/admin/importar', h1: 'Bandeja' },
  { path: '/admin/biblioteca', h1: 'Biblioteca' },
  { path: '/admin/revision', h1: 'Revisión' },
  { path: '/admin/cambios', h1: 'Cambios' },
  { path: '/admin/errores', h1: 'Errores' },
  { path: '/admin/preguntas', h1: 'Preguntas' },
  { path: '/admin/programa', h1: 'Programa' },
  { path: '/admin/estudiar', h1: 'Estudiar' },
  { path: '/admin/buscar', h1: 'Buscar y preguntar' },
  { path: '/admin/ajustes', h1: 'Ajustes' },
  { path: '/admin/ui', h1: 'Componentes' },
];

/** El título de la pantalla de esa dirección. Falla si el menú trae una sección sin pantalla. */
function tituloDe(path: string): string {
  const pantalla = PANTALLAS_DEL_PANEL.find((candidata) => candidata.path === path);
  if (pantalla === undefined) {
    throw new Error(`la sección ${path} no tiene pantalla declarada en esta prueba`);
  }
  return pantalla.h1;
}

test('E2E-00 primera ejecución: la zona del alumno arranca y dice qué toca', async ({ page }) => {
  await page.goto('/');

  await expect(page.getByRole('heading', { level: 1, name: 'Inicio' })).toBeVisible();

  // Las tres tarjetas de la zona de estudio, y ninguna más.
  await expect(page.getByRole('heading', { name: 'Continuar' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Repasar fallos' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Tu progreso' })).toBeVisible();

  // Los estados vacíos dicen la verdad y no simulan datos. La suite arranca con datos nuevos, pero se
  // admite también el caso de un directorio de datos conservado a propósito.
  await expect(
    page
      .getByText('Aún no has hecho ningún test.')
      .or(page.getByText('No tienes ningún test a medias.'))
      .or(page.getByText('Continuar el test')),
  ).toBeVisible();
  await expect(
    page.getByText('No tienes fallos pendientes de repaso.').or(page.getByText('Repasar mis fallos')),
  ).toBeVisible();

  // La barra del alumno: siete entradas, en orden, y ninguna de la trastienda.
  const nav = page.getByRole('navigation', { name: 'Secciones de la aplicación' });
  await expect(nav.getByRole('link')).toHaveText(STUDENT_NAV_ITEMS.map((item) => item.label));

  // Ni buscar en el material, ni selector de oposición, ni contadores: eso es del panel.
  await expect(page.getByLabel('Buscar en el corpus')).toHaveCount(0);
  await expect(page.getByLabel('Oposición')).toHaveCount(0);
  await expect(page.locator('.nav__count')).toHaveCount(0);
  await expect(page.getByText('Bandeja')).toHaveCount(0);
  await expect(page.getByText('Revisión')).toHaveCount(0);

  // Y una sola puerta al panel, en el pie.
  const administrar = page.getByRole('link', { name: 'Administrar' });
  await expect(administrar).toBeVisible();
  await administrar.click();
  await expect(page).toHaveURL(/\/admin\/importar$/);
});

test('E2E-00 el panel: aviso de que no hay contraseña, menú propio y cada sección por su dirección', async ({
  page,
}) => {
  await page.goto('/admin');

  // `/admin` no se queda sin pantalla: entra en la primera sección del menú.
  await expect(page).toHaveURL(/\/admin\/importar$/);
  await expect(
    page.getByText('Modo administración · sin contraseña: solo en este ordenador'),
  ).toBeVisible();

  const nav = page.getByRole('navigation', { name: 'Secciones de administración' });
  await expect(nav.getByRole('link')).toHaveCount(ADMIN_NAV_ITEMS.length);
  // Las direcciones del menú, tal cual: la insignia de un contador no cambia a dónde lleva el enlace.
  expect(
    await nav.getByRole('link').evaluateAll((enlaces) =>
      enlaces.map((enlace) => enlace.getAttribute('href')),
    ),
  ).toEqual(ADMIN_NAV_ITEMS.map((item) => item.path));

  // Cada entrada del menú lleva a su pantalla, y el marco del panel sigue puesto. Las pantallas son
  // las de siempre: lo que cambia en F1 es dónde viven, no lo que hacen. Se pulsa por la **dirección**
  // del enlace, no por su nombre: el nombre accesible lleva el contador («Errores: 4 repasos
  // vencidos») y buscar por texto encontraría también el enlace de Importaciones.
  for (const item of ADMIN_NAV_ITEMS) {
    await nav.locator(`a[href="${item.path}"]`).click();
    await expect(page).toHaveURL(new RegExp(`${item.path.replace('/', '\\/')}$`));
    await expect(page.getByRole('heading', { level: 1, name: tituloDe(item.path) })).toBeVisible();
    await expect(page.getByText('Modo administración · sin contraseña: solo en este ordenador')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Página no encontrada' })).toHaveCount(0);
    await expect(page.getByText('Esta sección todavía no está construida')).toHaveCount(0);
  }
});

test('E2E-00 ninguna dirección antigua da 404: cada una acaba en su pantalla nueva', async ({ page }) => {
  for (const { from, to } of ROUTE_REDIRECTS) {
    await page.goto(from);
    await expect(page, `${from} debería acabar en ${to}`).toHaveURL(new RegExp(`${to.replace('/', '\\/')}$`));
    await expect(
      page.getByRole('heading', { level: 1, name: tituloDe(to) }),
      `${from} debería enseñar «${tituloDe(to)}»`,
    ).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Página no encontrada' })).toHaveCount(0);
  }

  // Y la consulta no se pierde por el camino: hay enlaces con estado dentro (`?documento=`, `?q=`).
  await page.goto('/biblioteca?documento=no-existe');
  await expect(page).toHaveURL(/\/admin\/biblioteca\?documento=no-existe$/);

  await page.goto('/buscar?q=estado');
  await expect(page).toHaveURL(/\/admin\/buscar\?q=estado$/);
  await expect(page.getByLabel('Qué buscas')).toHaveValue('estado');
});

test('E2E-00 la zona del alumno no enseña la cocina en ninguna de sus pantallas', async ({ page }) => {
  const rutas = STUDENT_NAV_ITEMS.map((item) => item.path);

  for (const ruta of rutas) {
    await page.goto(ruta);
    await expect(
      page.getByRole('heading', { level: 1 }),
      `${ruta} debería tener su título`,
    ).toBeVisible();

    // Dos textos, porque son dos comprobaciones: el de la **interfaz** (todo menos lo que va dentro de
    // un contenedor `data-contenido`) y el de **toda** la pantalla. La jerga se busca solo en el
    // primero; las rutas del propietario y los bancos privados, en los dos.
    const { interfaz, todo } = await page.evaluate(() => {
      const copia = document.body.cloneNode(true) as HTMLElement;
      for (const nodo of Array.from(copia.querySelectorAll('[data-contenido]'))) {
        nodo.remove();
      }
      return {
        interfaz: copia.innerText || copia.textContent || '',
        todo: document.body.innerText,
      };
    });

    expect(revisarPantalla(interfaz, todo), `palabras prohibidas en ${ruta}`).toEqual([]);
  }
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
  await expect(page.getByRole('heading', { level: 1, name: 'Inicio' })).toBeVisible();

  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
    .analyze();

  expect(results.violations).toEqual([]);
});

test('E2E-00 accesibilidad: sin violaciones automatizables en el panel', async ({ page }) => {
  await page.goto('/admin/importar');
  await expect(page.getByRole('heading', { level: 1, name: 'Bandeja' })).toBeVisible();

  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
    .analyze();

  expect(results.violations).toEqual([]);
});
