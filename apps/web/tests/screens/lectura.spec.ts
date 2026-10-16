/**
 * La lectura de los apuntes: capturas y **cifras** del arreglo (F35, §3.1 y §3 del encargo).
 *
 * Es la herramienta con la que se demuestra, sobre los datos reales, lo que el propietario pidió de la
 * pantalla con la que estudia:
 *
 * 1. **un capítulo por pantalla** (un epígrafe oficial cada vez): la altura de la página del tema baja
 *    de los 110.427 px de IV.7 y los 314.402 px de I.1 —medidos antes de este cambio— a la altura del
 *    epígrafe que se sirve;
 * 2. **el índice siempre accesible**: no pasa del alto de la ventana y tiene su propio scroll, así que
 *    sus últimos apartados se pueden pulsar (antes medía 1.415 px en una ventana de 800 y su mitad de
 *    abajo no se alcanzaba ni desplazándose);
 * 3. **el enlace llega al párrafo**: `/temario/IV.7#apartado-puertos` abre el capítulo que contiene ese
 *    apartado y baja a él. Antes medía `scrollY = 0` con el párrafo a 87.623 px;
 * 4. **el texto ocupa un ancho de lectura**: la columna pasa de 370 px a su medida de 68 caracteres;
 * 5. **las tablas no parten palabras**: su ancho es el suyo y, si no cabe, **se desplaza ella**;
 * 6. **ningún párrafo explicativo visible por defecto**: el recuento de la nota al margen está plegado.
 *
 * Y comprueba lo que el propietario exige de una captura: **cero violaciones de axe** y **cero errores
 * de consola**, medido por la prueba y no mirando el PNG.
 *
 * Se lanza con `npm run screens -- --datos <dir> --grep lectura`, que es lo que pasa la copia de la
 * base real por `OPOFUENTE_E2E_DATA_DIR` (y no la borra). Las cifras quedan en
 * `artifacts/lectura/medidas.json` y los PNG en `artifacts/lectura/despues/`.
 *
 * **Estas capturas son de los datos reales y no de la siembra**, y por eso se saltan cuando no se ha
 * pasado `--datos`: con la siembra, IV.7 no tiene 25 apartados ni I.1 21, así que las cifras que se
 * comparan aquí no serían las del propietario. Un cero medido sobre otros datos no demuestra nada.
 */

import { mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';

import AxeBuilder from '@axe-core/playwright';
import { expect, test, type Page } from '@playwright/test';

import { datosEnElTexto, lenguajeInternoEnElTexto } from '../palabrasProhibidas';
import { guardarFila, nombreDeFichero } from './informe';

test.skip(
  process.env.OPOFUENTE_E2E_DATA_DIR === undefined,
  'la lectura por capítulos se mide sobre la copia de los datos reales: npm run screens -- --datos <dir>',
);

const SALIDA = process.env.OPOFUENTE_LECTURA_SALIDA
  ? path.resolve(process.env.OPOFUENTE_LECTURA_SALIDA)
  : path.resolve(process.cwd(), '..', '..', 'artifacts', 'lectura', 'despues');

const ANCHOS: readonly { ancho: number; alto: number; etiqueta: string }[] = [
  { ancho: 1280, alto: 800, etiqueta: 'escritorio' },
  { ancho: 390, alto: 844, etiqueta: 'movil' },
];

/** Lo medido en esta corrida: es el fichero que se publica con el entregable. */
const MEDIDAS: Record<string, unknown>[] = [];

test.afterAll(() => {
  mkdirSync(SALIDA, { recursive: true });
  writeFileSync(
    path.join(SALIDA, '..', 'medidas.json'),
    JSON.stringify(MEDIDAS, null, 2),
    'utf-8',
  );
});

/** Visita una ruta, la retrata y devuelve lo que hay que exigirle. */
async function retratar(
  page: Page,
  ruta: string,
  fichero: string,
  ancho: number,
  alto: number,
  etiqueta: string,
): Promise<string[]> {
  const errores: string[] = [];
  page.on('console', (mensaje) => {
    if (mensaje.type() === 'error') {
      errores.push(mensaje.text());
    }
  });
  page.on('pageerror', (error) => errores.push(String(error)));

  await page.setViewportSize({ width: ancho, height: alto });
  const inicio = Date.now();
  await page.goto(ruta, { waitUntil: 'networkidle' });
  const ms = Date.now() - inicio;
  await expect(page.locator('main')).toBeVisible();
  mkdirSync(SALIDA, { recursive: true });
  const nombreFichero = nombreDeFichero(fichero, etiqueta);
  await page.screenshot({ path: path.join(SALIDA, `${nombreFichero}.png`), fullPage: false });

  const analisis = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
    .analyze();

  // Y la fila del informe, como las demás capturas del proyecto: el tiempo, la consola, axe y las
  // **palabras prohibidas** medidas con el detector de la casa, para que la revisión de la pantalla
  // quede en el mismo sitio que la de las otras.
  const textos = await page.evaluate(() => {
    const copia = document.body.cloneNode(true) as HTMLElement;
    for (const nodo of Array.from(copia.querySelectorAll('[data-contenido]'))) {
      nodo.remove();
    }
    return {
      interfaz: copia.innerText || copia.textContent || '',
      todo: document.body.innerText,
    };
  });
  guardarFila({
    ruta,
    ancho: `${ancho}×${alto}`,
    ms,
    errores,
    violaciones: analisis.violations.map((violacion) => violacion.id),
    prohibidas: [
      ...datosEnElTexto(textos.todo),
      ...lenguajeInternoEnElTexto(textos.interfaz),
    ],
    fichero: nombreFichero,
  });

  expect(errores, `consola en ${ruta}: ${errores.join(' | ')}`).toEqual([]);
  return analisis.violations.map((violacion) => violacion.id);
}

/** La geometría que se publica: altura de la página, ancho de la columna y del índice. */
async function medir(page: Page): Promise<Record<string, number | string | null>> {
  return page.evaluate(() => {
    const redondo = (valor: number): number => Math.round(valor);
    const columna = document.querySelector('.apartado__cuerpo');
    const indice = document.querySelector('.apuntes__indice');
    const marco = document.querySelector('.apuntes__indice-lista-marco');
    const marcos = [...document.querySelectorAll('.apuntes__tabla-marco')];
    return {
      altoDocumento: document.documentElement.scrollHeight,
      anchoDocumento: document.documentElement.scrollWidth,
      anchoVentana: window.innerWidth,
      columnaTexto: columna === null ? null : redondo(columna.getBoundingClientRect().width),
      capituloAbierto: document.querySelector('.apuntes__capitulo-codigo')?.textContent ?? null,
      apartadosServidos: document.querySelectorAll('.apartado').length,
      capitulosEnIndice: document.querySelectorAll('.apuntes__indice-capitulo').length,
      indiceAlto: indice === null ? null : redondo(indice.getBoundingClientRect().height),
      indicePosicion: indice === null ? null : getComputedStyle(indice).position,
      indiceScrollPropio: marco === null ? 0 : redondo(marco.scrollHeight - marco.clientHeight),
      tablas: marcos.length,
      tablasQueSeDesplazan: marcos.filter((fila) => fila.scrollWidth > fila.clientWidth).length,
    };
  });
}

for (const { ancho, alto, etiqueta } of ANCHOS) {
  test(`lectura: IV.7 por capítulos a ${ancho} px`, async ({ page }) => {
    const violaciones = await retratar(page, '/temario/IV.7', 'tema-IV-7', ancho, alto, etiqueta);
    const medidas = await medir(page);
    MEDIDAS.push({ ruta: '/temario/IV.7', ancho, ...medidas });

    // §3.1: se sirve **un capítulo**, no el tema entero. El de IV.7 tiene 6 apartados; el tema son 25.
    expect(medidas.apartadosServidos).toBe(6);
    expect(medidas.capitulosEnIndice).toBe(2);
    expect(medidas.capituloAbierto).toBe('IV.7.1');
    expect(Number(medidas.altoDocumento)).toBeLessThan(110_427);

    // §3.2: el índice no pasa del alto de la ventana y tiene su propio scroll cuando le hace falta.
    expect(medidas.indicePosicion).toBe(ancho === 1280 ? 'sticky' : 'static');
    expect(Number(medidas.indiceAlto)).toBeLessThanOrEqual(alto);
    expect(Number(medidas.indiceScrollPropio)).toBeGreaterThanOrEqual(0);

    // §3.4: el texto ocupa un ancho de lectura. Antes medía 370 px en una pantalla de 1280.
    if (ancho === 1280) {
      expect(Number(medidas.columnaTexto)).toBeGreaterThanOrEqual(600);
    }

    // §3.5: las tablas tienen su propio ancho; las que no caben se desplazan, no parten las palabras.
    expect(medidas.tablas).toBeGreaterThan(0);
    const sinPartir = await page.evaluate(() => {
      const celda = document.querySelector('.apuntes__tabla td, .apuntes__tabla th');
      if (celda === null) return null;
      const estilo = getComputedStyle(celda);
      return { wrap: estilo.overflowWrap, break: estilo.wordBreak };
    });
    expect(sinPartir?.wrap).toBe('normal');
    expect(sinPartir?.break ?? 'normal').toBe('normal');
    if (ancho === 1280) {
      expect(Number(medidas.tablasQueSeDesplazan)).toBeGreaterThan(0);
    }

    // §3.6: la frase que explica el recuento está plegada; el rótulo se ve.
    const primerApartado = page.locator('.apartado').first();
    const rotulo = primerApartado.getByRole('button', { name: /esto se pregunta/i });
    await expect(rotulo).toBeVisible();
    await expect(rotulo).toHaveAttribute('aria-expanded', 'false');
    await expect(
      primerApartado.getByText(/preguntas? de este tema se contestan? en este apartado/i),
    ).toBeHidden();
    await rotulo.click();
    await expect(
      primerApartado.getByText(/preguntas? de este tema se contestan? en este apartado/i),
    ).toBeVisible();

    if (ancho === 390) {
      expect(Number(medidas.anchoDocumento)).toBeLessThanOrEqual(390);
    }
    expect(violaciones, `axe en IV.7 a ${ancho}: ${violaciones.join(', ')}`).toEqual([]);
  });

  test(`lectura: I.1 por capítulos a ${ancho} px`, async ({ page }) => {
    const violaciones = await retratar(page, '/temario/I.1', 'tema-I-1', ancho, alto, etiqueta);
    const medidas = await medir(page);
    MEDIDAS.push({ ruta: '/temario/I.1', ancho, ...medidas });

    // El tema más largo del programa son 21 apartados: aquí se sirve su primer epígrafe, con 12.
    expect(medidas.apartadosServidos).toBe(12);
    expect(medidas.capitulosEnIndice).toBe(4);
    expect(Number(medidas.altoDocumento)).toBeLessThan(314_402);
    expect(Number(medidas.indiceAlto)).toBeLessThanOrEqual(alto);
    expect(violaciones, `axe en I.1 a ${ancho}: ${violaciones.join(', ')}`).toEqual([]);
  });

  test(`lectura: el enlace de un apartado abre su capítulo y baja al párrafo a ${ancho} px`, async ({
    page,
  }) => {
    // `puertos` vive en `IV.7.2`, que **no** es el capítulo que la página abre por defecto: es el
    // caso que antes dejaba al alumno arriba (`scrollY = 0` con el párrafo a 87.623 px).
    await page.setViewportSize({ width: ancho, height: alto });
    await page.goto('/temario/IV.7#apartado-puertos', { waitUntil: 'networkidle' });
    await expect(page).toHaveURL(/capitulo=IV\.7\.2/);
    await expect(page.locator('#apartado-puertos')).toBeInViewport();

    const medidas = await page.evaluate(() => ({
      scrollY: Math.round(window.scrollY),
      capituloAbierto: document.querySelector('.apuntes__capitulo-codigo')?.textContent ?? null,
      apartadoALaVista: (() => {
        const apartado = document.getElementById('apartado-puertos');
        if (apartado === null) return false;
        const rect = apartado.getBoundingClientRect();
        return rect.top >= -8 && rect.top < window.innerHeight;
      })(),
    }));
    MEDIDAS.push({ ruta: '/temario/IV.7#apartado-puertos', ancho, ...medidas });
    expect(medidas.capituloAbierto).toBe('IV.7.2');
    expect(medidas.scrollY, 'la vista tiene que haber bajado al párrafo').toBeGreaterThan(1000);
    expect(medidas.apartadoALaVista).toBe(true);

    mkdirSync(SALIDA, { recursive: true });
    await page.screenshot({
      path: path.join(SALIDA, `ancla-puertos-${etiqueta}.png`),
      fullPage: false,
    });
  });
}

/**
 * La medida de lectura **también en una pantalla ancha** (F35-bis).
 *
 * La nota al margen no vuelve a su columna a ninguna anchura, y eso es una decisión **medida**: el
 * lienzo del alumno está limitado a 1080 px por el diseño, y dentro de él caben el índice, el hueco,
 * el relleno de la tarjeta y **o** el texto con sus 68 caracteres **o** la columna de la nota.
 * Medido a 1600 px con las tres columnas: el texto se quedaba en **582 px** (61 caracteres) en vez
 * de 647. Como lo que el propietario pidió es que el texto tenga un ancho de lectura cómodo, manda el
 * texto y la nota cae debajo de su párrafo.
 *
 * Esta prueba existe porque es una decisión de maquetación: sin ella, la siguiente pantalla que toque
 * la rejilla se lleva por delante la medida sin que nadie se entere.
 */
test('lectura: a 1600 px el texto conserva su medida y la nota sigue debajo', async ({ page }) => {
  await page.setViewportSize({ width: 1600, height: 900 });
  await page.goto('/temario/IV.7', { waitUntil: 'networkidle' });
  await expect(page.locator('main')).toBeVisible();
  // El `ch` de la medida se resuelve con la fuente de los apuntes: hasta que no está cargada, la
  // columna mide otra cosa. `document.fonts.ready` es la espera que lo garantiza.
  await page.evaluate(() => document.fonts.ready);

  const medidas = await page.evaluate(() => {
    const apartado = document.querySelector('.apartado');
    const cuerpo = apartado?.querySelector('.apartado__cuerpo');
    const lateral = apartado?.querySelector('.apartado__lateral');
    if (!cuerpo || !lateral) return null;
    const c = cuerpo.getBoundingClientRect();
    const l = lateral.getBoundingClientRect();
    return {
      anchoTexto: Math.round(c.width),
      izquierdaDelTexto: Math.round(c.left),
      izquierdaDeLaNota: Math.round(l.left),
      arribaDeLaNota: Math.round(l.top),
      abajoDelTexto: Math.round(c.bottom),
      notaEnLaColumnaDelTexto: Math.abs(Math.round(l.left) - Math.round(c.left)) <= 2,
      notaDebajoDelTexto: Math.round(l.top) >= Math.round(c.bottom) - 2,
    };
  });

  MEDIDAS.push({ ruta: '/temario/IV.7#pantalla-ancha', ancho: 1600, ...medidas });
  expect(medidas, 'el apartado tiene que estar pintado').not.toBeNull();
  expect(medidas?.anchoTexto, 'el texto conserva su medida de lectura').toBeGreaterThanOrEqual(600);
  expect(medidas?.notaEnLaColumnaDelTexto, 'la nota va en la columna del texto').toBe(true);
  expect(medidas?.notaDebajoDelTexto, 'y debajo de él, no al lado').toBe(true);

  mkdirSync(SALIDA, { recursive: true });
  await page.screenshot({ path: path.join(SALIDA, 'pantalla-ancha-1600.png'), fullPage: false });
});
