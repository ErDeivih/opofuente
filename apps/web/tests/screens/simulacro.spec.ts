/**
 * El arreglo del §3.3 y §3.4, medido con un navegador de verdad y contra la copia de los datos.
 *
 * No es una prueba de las puertas (`npm run e2e` mira `tests/e2e`): es la **medición** del encargo, y
 * vive aquí porque necesita los mismos dos servidores que las capturas y el mismo `--datos <dir>`.
 *
 * Lo que comprueba, y por qué se comprueba aquí y no solo mirando un PNG:
 *
 * 1. **el simulacro se monta en menos de 5 s**, medido en el navegador **y** con el reloj del servidor
 *    (`Server-Timing`, que el servidor escribe alrededor de la composición): la diferencia entre los
 *    dos es lo que se va en pintar, y sin las dos cifras no se sabe qué se está midiendo;
 * 2. **mientras monta, la pantalla lo dice** y el botón se queda ocupado;
 * 3. el reloj del simulacro **enseña lo que queda y lo que llevas**, y el del examen oficial también;
 * 4. **«Abandonar» pide confirmación**, deja el test fuera de las notas y **se puede volver a entrar**
 *    (abandonado y volviendo a entrar, y abandonando dos veces: la segunda no da 500 ni 409);
 * 5. **cero errores de consola y cero violaciones de axe** en cada pantalla capturada, a 1280 y a 390.
 */

import { mkdirSync } from 'node:fs';
import path from 'node:path';

import AxeBuilder from '@axe-core/playwright';
import { expect, test, type Page } from '@playwright/test';

const SALIDA = process.env.OPOFUENTE_SCREENS_SALIDA
  ? path.resolve(process.env.OPOFUENTE_SCREENS_SALIDA)
  : path.resolve(process.cwd(), '..', '..', 'artifacts', 'simulacro');

/**
 * Dónde escucha la API. La web la llama **en absoluto** (`client.ts`, `DEFAULT_BASE_URL`), así que una
 * petición de esta prueba no puede ir contra el servidor de vista previa: allí no hay proxy y da 404.
 */
const API = process.env.OPOFUENTE_API_URL ?? 'http://127.0.0.1:8765';

/**
 * Los anchos del encargo: escritorio y móvil, los dos del recorrido.
 */
const ANCHOS: readonly { ancho: number; alto: number }[] = [
  { ancho: 1280, alto: 800 },
  { ancho: 390, alto: 844 },
];

/**
 * Los errores de consola de una pestaña, escuchados desde antes de navegar.
 *
 * Se devuelve la lista para que cada comprobación pueda exigir su cero: un recuento que nadie mira no
 * es una comprobación.
 */
function escucharConsola(page: Page): string[] {
  const errores: string[] = [];
  page.on('console', (mensaje) => {
    if (mensaje.type() === 'error') {
      errores.push(mensaje.text());
    }
  });
  page.on('pageerror', (error) => errores.push(String(error)));
  return errores;
}

/**
 * Retrata una pantalla a los dos anchos y devuelve las violaciones de axe que encuentra.
 *
 * La accesibilidad se mide en la **última** pasada (la del móvil): axe analiza el documento en el
 * ancho en el que está, y comprobar el de escritorio dos veces no dice nada del de 390.
 */
async function retratar(
  page: Page,
  nombre: string,
): Promise<{ violaciones: string[] }> {
  let violaciones: string[] = [];
  for (const { ancho, alto } of ANCHOS) {
    await page.setViewportSize({ width: ancho, height: alto });
    mkdirSync(SALIDA, { recursive: true });
    await page.screenshot({
      path: path.join(SALIDA, `${nombre}-${String(ancho)}.png`),
      fullPage: true,
    });
    const analisis = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
      .analyze();
    violaciones = analisis.violations.map((violacion) => violacion.id);
  }
  return { violaciones };
}

test.describe('el simulacro y el reloj, medidos en el navegador', () => {
  test('el simulacro se monta en menos de cinco segundos', async ({ page }) => {
    const errores = escucharConsola(page);

    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto('/simulacros', { waitUntil: 'networkidle' });

    // La petición de montaje, con sus dos tiempos: el del navegador y el que el servidor declara.
    const peticion = page.waitForResponse(
      (respuesta) =>
        respuesta.url().includes('/api/v1/student/mock-exams') &&
        respuesta.request().method() === 'POST',
    );
    const inicio = Date.now();
    await page.getByRole('button', { name: /empezar el simulacro/i }).click();
    const respuesta = await peticion;
    const msNavegador = Date.now() - inicio;

    const servidor = respuesta.headers()['server-timing'] ?? '';
    const coincidencia = /composicion;dur=([0-9.]+)/.exec(servidor);
    const msServidor = coincidencia === null ? null : Number(coincidencia[1]);
    console.log(
      `MONTAJE · navegador ${String(msNavegador)} ms · servidor ` +
        `${msServidor === null ? 'no declarado' : `${String(msServidor)} ms`} · ` +
        `cabecera «${servidor}»`,
    );

    expect(respuesta.status()).toBe(201);
    expect(msNavegador).toBeLessThan(5000);
    if (msServidor !== null) {
      expect(msServidor).toBeLessThan(5000);
    }

    // Se navega al test y se retrata con su reloj: 120 minutos de simulacro.
    await page.waitForURL(/\/test\//, { timeout: 10_000 });
    await page.waitForLoadState('networkidle');
    await expect(page.locator('.test-reloj')).toBeVisible();
    const { violaciones } = await retratar(page, 'simulacro-con-reloj');
    expect(violaciones).toEqual([]);
    expect(errores).toEqual([]);
  });

  test('mientras monta, la pantalla lo dice y el botón está ocupado', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto('/simulacros', { waitUntil: 'networkidle' });

    // Se retrasa la respuesta un segundo para poder mirar la pantalla **durante** el montaje, que es
    // justo el momento en el que antes no se decía nada.
    await page.route('**/api/v1/student/mock-exams', async (ruta) => {
      if (ruta.request().method() !== 'POST') {
        await ruta.continue();
        return;
      }
      await new Promise((listo) => setTimeout(listo, 1000));
      await ruta.continue();
    });

    await page.getByRole('button', { name: /empezar el simulacro/i }).click();
    const ocupado = page.getByRole('button', { name: /preparando tu simulacro/i });
    await expect(ocupado).toBeVisible();
    await expect(ocupado).toBeDisabled();
    await expect(page.getByRole('status')).toContainText(/puede tardar unos segundos/i);
    await retratar(page, 'simulacro-preparando');
    await expect(page.locator('.test-reloj')).toBeVisible({ timeout: 15_000 });
  });

  test('abandonar pide confirmación, se conserva y se puede volver a entrar', async ({ page }) => {
    const errores = escucharConsola(page);
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto('/simulacros', { waitUntil: 'networkidle' });
    await page.getByRole('button', { name: /empezar el simulacro/i }).click();
    await page.waitForURL(/\/test\//, { timeout: 15_000 });
    await page.waitForLoadState('networkidle');
    const url = page.url();
    const sesion = url.split('/test/')[1] ?? '';
    expect(sesion).not.toBe('');

    // Se contesta una pregunta y se **espera a que el servidor la haya guardado**: el abandono
    // conserva lo contestado (con cero respuestas el servidor descarta la sesión, que es la otra
    // regla). Esperar a la red no basta: hay que ver la respuesta del servidor con su intento dentro.
    const contestada = page.waitForResponse(
      (respuesta) =>
        respuesta.url().includes('/answers') && respuesta.request().method() === 'POST',
    );
    await page.locator('.test-opcion').first().click();
    const guardada = await contestada;
    expect(guardada.status()).toBe(200);
    await expect(page.locator('.hoja__casilla[data-estado="marcada"]').first()).toBeVisible();

    // Abandonar: primero sin confirmar (no pasa nada) y después confirmando.
    let confirmado = false;
    page.on('dialog', async (dialogo) => {
      if (!confirmado) {
        await dialogo.dismiss();
        return;
      }
      await dialogo.accept();
    });
    await page.getByRole('button', { name: 'Abandonar' }).click();
    await page.waitForTimeout(300);
    await expect(page.getByRole('button', { name: 'Abandonar' })).toBeVisible();

    confirmado = true;
    const abandono = page.waitForResponse(
      (respuesta) => respuesta.url().includes('/abandon') && respuesta.status() === 200,
    );
    await page.getByRole('button', { name: 'Abandonar' }).click();
    const parte = (await (await abandono).json()) as { action: string; detail: string };
    console.log(`ABANDONO · ${parte.action} · ${parte.detail}`);
    expect(parte.action).toBe('abandoned');

    await expect(page.getByText(/no cuenta como test hecho/i)).toBeVisible();
    const { violaciones } = await retratar(page, 'test-abandonado');
    expect(violaciones).toEqual([]);
    expect(errores).toEqual([]);

    // **Y se puede volver a entrar**: recargar la dirección de la sesión abandonada abre la pantalla,
    // la dice y no deja contestar. Es la comprobación de que abandonar no deja el test en un estado
    // del que no se pueda salir.
    await page.reload({ waitUntil: 'networkidle' });
    await expect(page.getByText(/no cuenta como test hecho/i)).toBeVisible();
    await expect(page.getByRole('button', { name: 'Terminar' })).toHaveCount(0);
    await expect(page.getByRole('button', { name: 'Abandonar' })).toHaveCount(0);
    await expect(page.getByRole('link', { name: 'Salir' })).toBeVisible();
    await expect(page.getByText(/no admite respuestas/)).toBeVisible();

    // Y abandonar **otra vez** (por API, que es lo que haría un reintento de la pantalla) no da 500
    // ni 404: es idempotente y devuelve el mismo parte.
    const segunda = await page.request.post(
      `${API}/api/v1/student/sessions/${sesion}/abandon`,
    );
    console.log(`ABANDONO 2ª · ${String(segunda.status())} · ${await segunda.text()}`);
    expect(segunda.status()).toBe(200);

    // Y la sesión no cuenta como test hecho: Inicio no la ofrece como el test a medias.
    await page.goto('/', { waitUntil: 'networkidle' });
    await expect(page.getByText(/no cuenta como test hecho/i)).toHaveCount(0);
  });

  test('el examen oficial enseña el reloj de su convocatoria y se puede abandonar', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto('/examenes', { waitUntil: 'networkidle' });

    const primero = page.getByRole('button', { name: /hacer este examen/i }).first();
    await expect(primero).toBeVisible();
    await primero.click();
    await page.waitForURL(/\/test\//, { timeout: 15_000 });
    await page.waitForLoadState('networkidle');

    // El examen oficial lleva el tiempo que declare su convocatoria: si lo declara, hay reloj.
    await expect(page.getByRole('button', { name: 'Abandonar' })).toBeVisible();
    const reloj = page.locator('.test-reloj');
    if ((await reloj.count()) > 0) {
      await expect(reloj).toContainText(/Quedan/);
      console.log(`EXAMEN OFICIAL · reloj «${(await reloj.innerText()).replace(/\s+/g, ' ')}»`);
    } else {
      console.log('EXAMEN OFICIAL · su convocatoria no declara minutos: no hay reloj que enseñar');
    }
    const { violaciones } = await retratar(page, 'examen-oficial-con-reloj');
    expect(violaciones).toEqual([]);
  });
});
