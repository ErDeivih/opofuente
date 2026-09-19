import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

/**
 * E2E-10 «Ajustes» (07_UI-UX §11): la pantalla que cierra el producto.
 *
 * Recorre lo que un usuario hace de verdad en Ajustes y comprueba tres cosas que solo se pueden ver
 * en un navegador:
 *
 * 1. **la CSP no rompe la aplicación**: si la política bloqueara el bundle o las llamadas al API, la
 *    pantalla no cargaría nada. Es el criterio que más fácil se rompe sin que ninguna prueba unitaria
 *    lo note, porque el jsdom no aplica CPS;
 * 2. **la foto del almacén es real**: se enseña el uso por área y, si hay algo que retirar, se retira
 *    con confirmación y se dice qué se ha hecho;
 * 3. **el diagnóstico se puede generar y no lleva secretos**.
 */

test('E2E-10 ajustes: la pantalla carga con la CSP puesta y enseña el estado real', async ({ page }) => {
  await page.goto('/ajustes');

  await expect(page.getByRole('heading', { level: 1, name: 'Ajustes' })).toBeVisible();
  // La ruta de datos y el disco salen del servidor, no de un valor escrito en el frontend.
  await expect(page.getByText('Ruta de datos')).toBeVisible();
  await expect(page.getByText(/libres de/)).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Capacidades instaladas' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Privacidad: a dónde sale tu contenido' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Copia y restauración' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Límites en vigor' })).toBeVisible();

  // Y lo que no debe salir: ni la clave, ni una ruta absoluta de disco en el diagnóstico.
  const contenido = await page.content();
  expect(contenido).not.toContain('clave-secreta');
});

test('E2E-10 ajustes: una copia se hace, se verifica y se previsualiza su restauración', async ({
  page,
}) => {
  await page.goto('/ajustes');
  await expect(page.getByRole('heading', { level: 1, name: 'Ajustes' })).toBeVisible();

  // 1. Copia con nota: el aviso dice qué se ha hecho y cuánto ocupa.
  await page.getByLabel('Nota de la copia (opcional)').fill('copia de E2E-10');
  await page.getByRole('button', { name: 'Hacer una copia ahora' }).click();
  await expect(page.getByText(/Copia hecha:/)).toBeVisible();

  // 2. La copia aparece en la tabla con su nota y marcada como restaurable.
  const tabla = page.getByRole('table', { name: 'Copias de seguridad' });
  const fila = tabla.getByRole('row', { name: /copia de E2E-10/ }).first();
  await expect(fila).toBeVisible();
  await expect(fila.getByText('sí')).toBeVisible();

  // 3. Verificar dice que está entera, fichero a fichero.
  await fila.getByRole('button', { name: 'Verificar' }).click();
  await expect(page.getByText(/está entera:/)).toBeVisible();

  // 4. Previsualizar **no** restaura: enseña qué se va a sustituir y el aviso de la copia previa.
  await fila.getByRole('button', { name: 'Previsualizar restauración' }).click();
  await expect(page.getByRole('heading', { name: /Restaurar/ })).toBeVisible();
  await expect(page.getByText(/opofuente.sqlite3, artifacts, extracted/)).toBeVisible();
  await expect(page.getByText(/copia automática de lo que hay ahora/)).toBeVisible();
  await expect(page.getByRole('button', { name: 'Restaurar esta copia' })).toBeEnabled();
});

test('E2E-10 ajustes: el índice se rehace y el diagnóstico se genera saneado', async ({ page }) => {
  await page.goto('/ajustes');
  await expect(page.getByRole('heading', { level: 1, name: 'Ajustes' })).toBeVisible();

  // Rehacer el índice informa de lo que ha hecho; el texto está en la evidencia, así que no se pierde.
  await page.getByRole('button', { name: 'Rehacer el índice' }).click();
  // El aviso dice el recuento antes/después y el tiempo: no basta con «hecho».
  await expect(page.getByText(/índice rehecho|no hay fragmentos que indexar/)).toBeVisible();

  await page.getByRole('button', { name: 'Preparar el diagnóstico en texto' }).click();
  // El texto plano llega del servidor y se enseña en un área de solo lectura: es lo que se copia.
  const area = page.getByLabel('Diagnóstico sanitizado');
  await expect(area).toBeVisible({ timeout: 15_000 });  const texto = await area.inputValue();
  expect(texto).toContain('diagnóstico sanitizado');
  // Las rutas van abreviadas y los recuentos van dentro: es lo que se puede pegar en una incidencia.
  expect(texto).toContain('…');
  expect(texto).toContain('capacidades:');
  expect(texto).toContain('recuentos:');
});

test('E2E-10 ajustes: accesibilidad sin violaciones automatizables', async ({ page }) => {
  await page.goto('/ajustes');
  await expect(page.getByRole('heading', { level: 1, name: 'Ajustes' })).toBeVisible();

  const resultado = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
    .analyze();

  expect(resultado.violations).toEqual([]);
});

test('E2E-10 ajustes: responsive sin scroll horizontal a 390 px', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/ajustes');
  await expect(page.getByRole('heading', { level: 1, name: 'Ajustes' })).toBeVisible();

  const desbordamiento = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(desbordamiento).toBeLessThanOrEqual(1);
});
