/**
 * El ciclo de contestar: **capturas** a 1280 y a 390, y las **cifras medidas** del arreglo (F36, §3.2).
 *
 * Es la herramienta con la que se demuestra, sobre la aplicación de verdad y desde el navegador, las
 * tres cifras que el encargo pide con número y no con adjetivo:
 *
 * 1. **cuántos `POST /start` por test abierto**: el recorrido del 16-oct-2026 midió 4, 4, 4, 6 y hasta
 *    12; la prueba exige **uno**;
 * 2. **el código de la segunda respuesta seguida**: era un **500** con
 *    `UNIQUE constraint failed: attempts.session_question_id` que el navegador leía como error de
 *    CORS; tiene que ser idempotente;
 * 3. **el código de cambiar una respuesta**: era **409**; mientras el test no ha terminado se admite.
 *
 * Y comprueba lo que el propietario exige de una captura: **cero violaciones de axe** y **cero errores
 * de consola**, medido por la prueba y no mirando el PNG. Las cifras quedan en
 * `artifacts/contestar/medidas.json` y los PNG en `artifacts/contestar/`.
 *
 * Se captura contra los datos de la suite (`.e2e-data`): el material se siembra por las rutas de la
 * API —conjunto, preguntas, clave activa y catalogación— y el ciclo se recorre **pulsando lo que hay
 * en pantalla**, que es lo que se retrata. Corre en la batería de siempre, sin `--datos`: la pantalla
 * que se juzga es la misma con los datos del propietario.
 */

import { mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';

import AxeBuilder from '@axe-core/playwright';
import { expect, test, type Page } from '@playwright/test';

import { datosEnElTexto, lenguajeInternoEnElTexto } from '../palabrasProhibidas';
import {
  quedaAlgoDeLaPrueba,
  retirarLoDeLaPrueba,
  sembrarCuestionario,
  sesionDeLaDireccion,
  TEMA,
} from '../cuestionarioDeContestar';
import { guardarFila, nombreDeFichero } from './informe';

const SALIDA = process.env.OPOFUENTE_CONTESTAR_SALIDA
  ? path.resolve(process.env.OPOFUENTE_CONTESTAR_SALIDA)
  : path.resolve(process.cwd(), '..', '..', 'artifacts', 'contestar');

const ANCHOS: readonly { ancho: number; alto: number; etiqueta: string }[] = [
  { ancho: 1280, alto: 800, etiqueta: 'escritorio' },
  { ancho: 390, alto: 844, etiqueta: 'movil' },
];

/** Lo medido en esta corrida: es el fichero que se publica con el entregable. */
const MEDIDAS: Record<string, unknown>[] = [];

test.afterAll(() => {
  mkdirSync(SALIDA, { recursive: true });
  writeFileSync(path.join(SALIDA, 'medidas.json'), JSON.stringify(MEDIDAS, null, 2), 'utf-8');
});

async function abrirLaHoja(page: Page): Promise<void> {
  const hoja = page.getByRole('complementary', { name: 'Hoja de respuestas' });
  if (!(await hoja.isVisible())) {
    await page.getByRole('button', { name: 'Hoja' }).click();
  }
  await expect(hoja).toBeVisible();
}

/** Lo que hay que exigirle a una captura: axe en cero, consola en cero y ni un dato del propietario. */
interface Captura {
  violaciones: string[];
  /** Los **datos prohibidos** encontrados (rutas, bancos, otras oposiciones, UUID visible). */
  datos: string[];
}

/** Retrata la pantalla, guarda la fila del informe y devuelve lo que hay que exigirle. */
async function retratar(
  page: Page,
  ruta: string,
  fichero: string,
  ancho: number,
  alto: number,
  etiqueta: string,
  errores: readonly string[],
): Promise<Captura> {
  await page.setViewportSize({ width: ancho, height: alto });
  mkdirSync(SALIDA, { recursive: true });
  const nombre = nombreDeFichero(fichero, etiqueta);
  await page.screenshot({ path: path.join(SALIDA, `${nombre}.png`), fullPage: true });

  const analisis = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
    .analyze();

  // La fila del informe de la casa: el mismo sitio donde quedan las demás capturas, y con las
  // **palabras prohibidas** medidas con su detector, que es la regla del proyecto.
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
  // Los datos del propietario y las otras oposiciones se buscan en **toda** la pantalla, contenido
  // incluido: si salen, es una fuga venga de donde venga. La jerga interna solo fuera del contenido,
  // que es la regla de la casa (el temario habla de «clave primaria» sin que eso sea una fuga).
  const datos = datosEnElTexto(textos.todo);
  guardarFila({
    ruta,
    ancho: `${ancho}×${alto}`,
    ms: 0,
    errores: [...errores],
    violaciones: analisis.violations.map((violacion) => violacion.id),
    prohibidas: [...datos, ...lenguajeInternoEnElTexto(textos.interfaz)],
    fichero: nombre,
  });

  return {
    violaciones: analisis.violations.map((violacion) => violacion.id),
    datos: datos.map((encontrado) => encontrado.palabra),
  };
}

for (const { ancho, alto, etiqueta } of ANCHOS) {
  test(`contestar: el ciclo entero a ${String(ancho)} px, con sus cifras`, async ({
    page,
    request,
  }) => {
    // Lo que la captura deja en la base, para poder retirarlo **aunque falle a mitad**: el `try`
    // envuelve también la siembra, que es el patrón de `bandeja-por-conjunto.spec.ts`. Aquí importa el
    // doble: con `--datos` esta herramienta escribe en una **copia de la base del propietario**, y
    // dejar la siembra ahí no es una fuga de una corrida, es escribir en sus datos.
    const creados: string[] = [];
    const sesiones: string[] = [];

    try {
      await sembrarCuestionario(request, creados);

      const errores: string[] = [];
      page.on('console', (mensaje) => {
        if (mensaje.type() === 'error') {
          errores.push(mensaje.text());
        }
      });
      page.on('pageerror', (error) => errores.push(String(error)));

      // --- la cifra 1: cuántos `POST /start` por test abierto -------------------------------------
      const arranques: string[] = [];
      page.on('request', (peticion) => {
        if (peticion.method() === 'POST' && peticion.url().includes('/start')) {
          arranques.push(peticion.url());
        }
      });
      const respuestas: number[] = [];
      page.on('response', (respuesta) => {
        if (respuesta.request().method() === 'POST' && respuesta.url().includes('/answers')) {
          respuestas.push(respuesta.status());
        }
      });

      await page.setViewportSize({ width: ancho, height: alto });
      await page.goto(`/tests?tema=${TEMA}&count=4`, { waitUntil: 'networkidle' });
      await page.getByRole('button', { name: 'Empezar el test' }).click();
      await expect(page.getByText(/^Pregunta 1 de \d+$/)).toBeVisible({ timeout: 20_000 });
      await page.waitForTimeout(300);
      const sesion = sesionDeLaDireccion(page.url());
      if (sesion !== null) {
        sesiones.push(sesion);
      }

      const enCurso = await retratar(
        page,
        `/test (en curso) a ${String(ancho)}`,
        'test-en-curso',
        ancho,
        alto,
        etiqueta,
        errores,
      );

      // --- contestar, volver y cambiar -------------------------------------------------------------
      await page.getByRole('button', { name: /Falso/ }).click();
      await expect(page.getByText(/^Pregunta 2 de \d+$/)).toBeVisible({ timeout: 20_000 });
      await abrirLaHoja(page);
      // **`exact: true`, y no es un adorno**: `getByRole` compara el nombre **por subcadena** cuando
      // se le da un texto, así que «Ir a la pregunta 1» casaba también con la 10, la 11 y la 12 —con
      // la siembra de pruebas había menos de diez preguntas y nunca se vio—. Aquí se quiere la 1.
      await page.getByRole('button', { name: 'Ir a la pregunta 1', exact: true }).click();
      await expect(page.getByText(/^Pregunta 1 de \d+$/)).toBeVisible({ timeout: 20_000 });
      // La vuelta a una pregunta contestada **es** la captura del arreglo: antes no se podía.
      const vuelta = await retratar(
        page,
        `/test (vuelta a la pregunta 1) a ${String(ancho)}`,
        'test-vuelta',
        ancho,
        alto,
        etiqueta,
        errores,
      );

      await page.getByRole('button', { name: /Falso/ }).click();
      await expect.poll(() => respuestas.length).toBeGreaterThanOrEqual(2);

      await page.getByRole('button', { name: /Verdadero/ }).click();
      await expect(page.locator('.test-opcion--correcta')).toHaveCount(1, { timeout: 20_000 });
      await expect.poll(() => respuestas.length).toBeGreaterThanOrEqual(3);

      await page.getByRole('button', { name: 'Terminar' }).click();
      await expect(page).toHaveURL(/\/resultado\//, { timeout: 20_000 });
      await expect(page.getByRole('heading', { level: 1, name: /Resultado/ })).toBeVisible({
        timeout: 20_000,
      });
      const resultado = await retratar(
        page,
        `/resultado a ${String(ancho)}`,
        'resultado-ciclo',
        ancho,
        alto,
        etiqueta,
        errores,
      );

      const capturas = [enCurso, vuelta, resultado];

      // --- las tres cifras, medidas --------------------------------------------------------------
      const cifras = {
        ancho,
        postStartPorTestAbierto: arranques.length,
        segundaRespuestaSeguida: respuestas[1] ?? null,
        cambioDeRespuesta: respuestas[2] ?? null,
        respuestasObservadas: respuestas.length,
        erroresDeConsola: errores.length,
        violacionesAxe: capturas.flatMap((captura) => captura.violaciones),
        datosProhibidos: capturas.flatMap((captura) => captura.datos),
      };
      MEDIDAS.push(cifras);

      expect(cifras.postStartPorTestAbierto, 'un test abierto arranca una vez').toBe(1);
      expect(cifras.segundaRespuestaSeguida, 'la segunda respuesta seguida es idempotente').toBe(
        200,
      );
      expect(
        cifras.cambioDeRespuesta,
        'cambiar la respuesta se admite mientras el test corre',
      ).toBe(200);
      expect(errores, `consola: ${errores.join(' | ')}`).toEqual([]);
      expect(cifras.violacionesAxe, 'axe en el ciclo entero').toEqual([]);
      // La zona del alumno no enseña las otras oposiciones, ni bancos ajenos, ni rutas del propietario.
      expect(cifras.datosProhibidos, 'datos prohibidos en la zona del alumno').toEqual([]);
    } finally {
      retirarLoDeLaPrueba(creados, sesiones);
      // Y se comprueba que la retirada ha corrido de verdad, en vez de suponerlo: con `--datos` esto
      // es la diferencia entre dejar la copia del propietario como estaba y escribir en sus datos.
      expect(quedaAlgoDeLaPrueba(creados, sesiones), 'la captura ha dejado datos').toEqual({
        conjuntos: 0,
        sesiones: 0,
        preguntas: 0,
        catalogaciones: 0,
      });
    }
  });
}
