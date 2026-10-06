/**
 * Capturas de todas las pantallas, con su informe (F0 del rediseño).
 *
 * Para qué sirve: quien construye la interfaz tiene que **verla**. Este guion recorre cada ruta de la
 * aplicación a dos anchos (escritorio 1280×800 y móvil 390×844), guarda el PNG en
 * `artifacts/screens/` y escribe `artifacts/screens/report.md` con lo que ha visto en cada una: lo que
 * tarda en quedar lista, los errores de consola, las violaciones de accesibilidad que detecta axe y las
 * **palabras prohibidas** de la zona del alumno (`tests/palabrasProhibidas.ts`).
 *
 * No es una prueba de las puertas: es una herramienta. Las puertas corren `npm run e2e`, que solo mira
 * `tests/e2e`; esto vive en `tests/screens` y se lanza a mano con `npm run screens` (o se pide desde el
 * informe de una entrega).
 *
 * En F0 las palabras prohibidas se **informan**, no bloquean: primero hay que ver cuántas salen.
 */

import { mkdirSync } from 'node:fs';
import path from 'node:path';

import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

import { palabrasEnElTexto } from '../palabrasProhibidas';
import { escribirInforme, guardarFila, nombreDeFichero } from './informe';

const SALIDA = path.resolve(process.cwd(), '..', '..', 'artifacts', 'screens');

// El informe se escribe **después** de la última captura de este proceso. Si una captura se pasa de
// tiempo, Playwright reinicia el proceso y este `afterAll` vuelve a correr: cada fila ya está en
// disco, así que el informe sale completo igualmente.
test.afterAll(() => {
  escribirInforme();
});

/** Las rutas que se visitan, con el nombre con el que se guarda cada captura. */
const RUTAS: readonly { ruta: string; nombre: string }[] = [
  { ruta: '/', nombre: 'inicio' },
  { ruta: '/programa', nombre: 'programa' },
  { ruta: '/estudiar', nombre: 'estudiar' },
  { ruta: '/preguntas', nombre: 'preguntas' },
  { ruta: '/biblioteca', nombre: 'biblioteca' },
  { ruta: '/bandeja', nombre: 'bandeja' },
  { ruta: '/revision', nombre: 'revision' },
  { ruta: '/cambios', nombre: 'cambios' },
  { ruta: '/errores', nombre: 'errores' },
  { ruta: '/buscar?q=constitucion', nombre: 'buscar' },
  { ruta: '/ajustes', nombre: 'ajustes' },
];

const ANCHOS: readonly { ancho: number; alto: number; etiqueta: string }[] = [
  { ancho: 1280, alto: 800, etiqueta: 'escritorio' },
  { ancho: 390, alto: 844, etiqueta: 'movil' },
];

for (const { ruta, nombre } of RUTAS) {
  for (const { ancho, alto, etiqueta } of ANCHOS) {
    test(`${nombre} a ${ancho} px`, async ({ page }) => {
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
      await page.screenshot({
        path: path.join(SALIDA, `${nombreDeFichero(ruta, etiqueta)}.png`),
        fullPage: true,
      });

      const analisis = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
        .analyze();
      const contenido = await page.locator('body').innerText();

      guardarFila({
        ruta,
        ancho: `${ancho}×${alto}`,
        ms,
        errores,
        violaciones: analisis.violations.map((violacion) => violacion.id),
        prohibidas: palabrasEnElTexto(contenido),
      });
    });
  }
}
