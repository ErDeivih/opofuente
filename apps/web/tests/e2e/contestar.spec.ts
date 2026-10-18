import AxeBuilder from '@axe-core/playwright';
import { expect, test, type Page } from '@playwright/test';

import {
  quedaAlgoDeLaPrueba,
  retirarLoDeLaPrueba,
  sembrarCuestionario,
  sesionDeLaDireccion,
  TEMA,
} from '../cuestionarioDeContestar';

/**
 * El ciclo de contestar: **contestar, volver, cambiar y terminar**, de una tirada y por la pantalla.
 *
 * Es la prueba que el §3.2 del encargo F36 pide por su nombre, y existe porque los defectos 5, 6 y 8
 * del recorrido del 16-oct-2026 (no poder volver a una pregunta contestada, un 409 al cambiar la
 * respuesta y un 500 al contestar dos veces deprisa) eran **uno solo**: el ciclo de contestar no
 * estaba escrito como una máquina de estados. Aquí se mide el recorrido entero y, además, se **miden
 * las tres cifras** que el encargo pide con número y no con adjetivo:
 *
 * 1. cuántos `POST /start` se mandan al abrir un test (el recorrido midió 4, 4, 4, 6 y hasta 12; una
 *    basta);
 * 2. qué código devuelve contestar dos veces seguidas (era 200 la tranquila y **500** la rápida, con
 *    `UNIQUE constraint failed: attempts.session_question_id`);
 * 3. qué código devuelve **cambiar** una respuesta (era **409**).
 *
 * El material es sintético y se siembra por la API real —conjunto, preguntas, clave activa y
 * catalogación en el tema—, porque la zona del alumno no monta un test de la nada: lo compone con las
 * preguntas catalogadas que tengan clave. **El ciclo se recorre pulsando lo que hay en pantalla.**
 *
 * Y **se retira al terminar**, como `bandeja-por-conjunto.spec.ts`: cuatro preguntas catalogadas en
 * `IV.1` son un tema más y cuatro preguntas más para el diagnóstico de `study.spec.ts`, que corre
 * **después** por orden alfabético. Medido: su muestra pasa de «6 en 3» a «8 en 4» y su aserción de
 * «0 de 6 respondidas» cae. Una prueba que deja datos no es una prueba, es una fuga que aparece tres
 * ficheros más allá.
 */


/** Dos anchos de referencia (07_UI-UX §14): el de escritorio y el del móvil. */
const ANCHOS = [
  { ancho: 1280, alto: 800, etiqueta: 'escritorio' },
  { ancho: 390, alto: 844, etiqueta: 'movil' },
];
/**
 * Abre un test del tema y devuelve cuántos `POST /start` se han mandado y la sesión que se abrió.
 *
 * El contador se engancha **antes** de navegar: engancharlo después dejaría fuera justo la petición
 * que se quiere medir, que sale al montar la pantalla. Y el identificador de la sesión se lee de la
 * dirección (`/test/<uuid>`), que es lo que después permite retirarla: sin él, la prueba dejaría un
 * test abierto en los datos de la suite.
 */
async function abrirTest(page: Page): Promise<{ arranques: number; sesion: string | null }> {
  const arranques: string[] = [];
  page.on('request', (peticion) => {
    if (peticion.method() === 'POST' && peticion.url().includes('/start')) {
      arranques.push(peticion.url());
    }
  });

  await page.goto(`/tests?tema=${TEMA}&count=4`, { waitUntil: 'networkidle' });
  await expect(page.getByRole('heading', { level: 1, name: 'Tests' })).toBeVisible();
  await page.getByRole('button', { name: 'Empezar el test' }).click();

  // El test en curso se reconoce por su cabecera: «Pregunta 1 de 4».
  await expect(page.getByText(/^Pregunta 1 de \d+$/)).toBeVisible({ timeout: 20_000 });
  // Y un respiro para que ninguna petición rezagada se quede fuera del recuento.
  await page.waitForTimeout(300);
  return { arranques: arranques.length, sesion: sesionDeLaDireccion(page.url()) };
}

test('E2E-F36 el ciclo entero: contestar, volver, cambiar y terminar', async ({
  page,
  request,
}) => {
  // Lo que la prueba va creando, para poder retirarlo **aunque se caiga a mitad**: el `try` envuelve
  // también la siembra. Es el patrón de `bandeja-por-conjunto.spec.ts`, y su motivo está medido.
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

    // --- 1. abrir el test: **un** `POST /start`, medido -----------------------------------------------
    const abierto = await abrirTest(page);
    if (abierto.sesion !== null) {
      sesiones.push(abierto.sesion);
    }
    expect(abierto.arranques, 'un test abierto arranca una vez, no de cuatro a doce').toBe(1);

    // --- 2. contestar, y medir el código de la **segunda** respuesta seguida -------------------------
    //
    // El test avanza solo al contestar (es lo que hace de siempre), así que después de responder se
    // vuelve a la fila 1 desde la hoja: eso es justo la mitad del ciclo —«volver»— y es lo que antes no
    // se podía hacer, porque los números de la hoja no tenían manejador.
    const respuestas: number[] = [];
    page.on('response', (respuesta) => {
      if (respuesta.request().method() === 'POST' && respuesta.url().includes('/answers')) {
        respuestas.push(respuesta.status());
      }
    });

    await page.getByRole('button', { name: /Falso/ }).click();
    await expect(page.getByText(/^Pregunta 2 de \d+$/)).toBeVisible({ timeout: 20_000 });

    await page.getByRole('button', { name: 'Ir a la pregunta 1' }).click();
    await expect(page.getByText(/^Pregunta 1 de \d+$/)).toBeVisible({ timeout: 20_000 });
    // La respuesta quedó guardada y la corrección inmediata la enseña: la marcada es la fallada.
    await expect(page.getByText('Tu respuesta')).toBeVisible();
    await expect(page.locator('.test-opcion--fallada')).toHaveCount(1);
    expect(respuestas[0], 'la primera respuesta se guarda').toBe(200);

    // La misma respuesta otra vez: es idempotente, y **nunca** un 500 con su `UNIQUE constraint`.
    await page.getByRole('button', { name: /Falso/ }).click();
    await expect(page.getByText('Tu respuesta')).toBeVisible();
    await expect(page.locator('.test-opcion--fallada')).toHaveCount(1);
    await expect
      .poll(() => respuestas.length, { message: 'se han mandado las dos respuestas' })
      .toBeGreaterThanOrEqual(2);
    expect(respuestas[1], 'la segunda respuesta seguida no puede ser un 500').toBe(200);

    // --- 3. **cambiarla** ----------------------------------------------------------------------------
    await page.getByRole('button', { name: /Verdadero/ }).click();
    await expect(page.locator('.test-opcion--correcta')).toHaveCount(1, { timeout: 20_000 });
    await expect.poll(() => respuestas.length).toBeGreaterThanOrEqual(3);
    expect(respuestas[2], 'cambiar una respuesta mientras el test corre se admite').toBe(200);

    // --- 4. terminar ----------------------------------------------------------------------------------
    await page.getByRole('button', { name: 'Terminar' }).click();
    await expect(page).toHaveURL(/\/resultado\//, { timeout: 20_000 });
    await expect(page.getByRole('heading', { level: 1, name: /Resultado/ })).toBeVisible({
      timeout: 20_000,
    });
    // Y el resultado enseña la hoja con lo que se dejó: la cambiada quedó en verde.
    await expect(page.locator('.hoja__casilla--correcta').first()).toBeVisible();

    // Y sin un solo error de consola en todo el ciclo: es lo que el 500 con mentira de CORS rompía
    // (el navegador lo contaba como «blocked by CORS policy»).
    expect(errores, `consola durante el ciclo: ${errores.join(' | ')}`).toEqual([]);
  } finally {
    retirarLoDeLaPrueba(creados, sesiones);
  }
});

/**
 * Las dos pantallas del ciclo, a 1280 y a 390, con **cero violaciones de axe**: el propietario juzga
 * una pantalla por cómo se ve, y el párrafo de ayuda que ahora dice la verdad (las flechas existen)
 * tiene que caber sin desbordar a 390.
 */
for (const { ancho, alto, etiqueta } of ANCHOS) {
  test(`E2E-F36 la pregunta y la hoja se pueden usar a ${String(ancho)} px`, async ({
    page,
    request,
  }) => {
    const creados: string[] = [];
    const sesiones: string[] = [];

    try {
      await sembrarCuestionario(request, creados);
      await page.setViewportSize({ width: ancho, height: alto });
      const abierto = await abrirTest(page);
      if (abierto.sesion !== null) {
        sesiones.push(abierto.sesion);
      }

      // La ayuda dice que las flechas recorren la hoja, y eso tiene que ser verdad: se comprueba aquí.
      await expect(page.getByText(/para recorrer la hoja/)).toBeVisible();

      const medidas = await page.evaluate(() => ({
        anchoDocumento: document.documentElement.scrollWidth,
        anchoVentana: window.innerWidth,
        hojaVisible: (() => {
          const hoja = document.querySelector('.test-hoja');
          return hoja !== null && getComputedStyle(hoja).display !== 'none';
        })(),
        filas: document.querySelectorAll('.hoja__fila').length,
        numerosQueNavegan: [...document.querySelectorAll('.hoja__numero')].filter(
          (boton) => boton.getAttribute('aria-label')?.startsWith('Ir a la pregunta') ?? false,
        ).length,
      }));
      expect(medidas.filas, 'la hoja tiene una fila por pregunta').toBe(4);
      expect(medidas.numerosQueNavegan, 'los números de la hoja son botones de verdad').toBe(4);

      // En el móvil la hoja nace plegada y se abre con su botón; una vez abierta, sus números navegan.
      // Sin esto, a 390 px la hoja sería un dibujo: se vería (o no) pero no se podría usar.
      if (medidas.hojaVisible) {
        expect(ancho, 'la hoja no debería nacer abierta en el móvil').toBe(1280);
      } else {
        await page.getByRole('button', { name: 'Hoja' }).click();
        await expect(page.getByRole('complementary', { name: 'Hoja de respuestas' })).toBeVisible();
        await page.getByRole('button', { name: 'Ir a la pregunta 2' }).click();
        await expect(page.getByText(/^Pregunta 2 de \d+$/)).toBeVisible({ timeout: 20_000 });
      }

      expect(
        medidas.anchoDocumento,
        `la pantalla se desborda en horizontal a ${String(ancho)} px (${etiqueta})`,
      ).toBeLessThanOrEqual(medidas.anchoVentana + 1);

      const analisis = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
        .analyze();
      expect(
        analisis.violations.map((violacion) => violacion.id),
        `axe a ${String(ancho)} px: ${analisis.violations.map((violacion) => violacion.id).join(', ')}`,
      ).toEqual([]);
    } finally {
      retirarLoDeLaPrueba(creados, sesiones);
    }
  });
}

/**
 * La prueba **no deja nada**: se mide, no se supone.
 *
 * El §3.2 se cerraba con una fuga y no con un defecto del código: esta spec sembraba un banco
 * catalogado en `IV.1` y no lo retiraba, y el diagnóstico de `study.spec.ts` —que corre después por
 * orden alfabético— pasaba de «6 en 3» a «8 en 4». La retirada de arriba lo arregla; esta prueba
 * comprueba que la retirada **ha corrido de verdad** en vez de confiar en que sí, y que la base queda
 * como estaba antes de sembrar.
 *
 * Corre al final y siembra/retira su propio banco a propósito: un `SELECT` sobre identificadores de
 * pruebas anteriores no demostraría nada (siempre daría cero) y este sí pasa por la siembra y la
 * retirada de verdad.
 */
test('E2E-F36 la prueba retira lo que siembra y no deja datos en la base de la suite', async ({
  request,
}) => {
  const creados: string[] = [];
  await sembrarCuestionario(request, creados);
  expect(creados).toHaveLength(1);
  expect(
    quedaAlgoDeLaPrueba(creados, []).preguntas,
    'acabamos de sembrar: tiene que haber preguntas que retirar',
  ).toBe(4);

  retirarLoDeLaPrueba(creados, []);

  expect(quedaAlgoDeLaPrueba(creados, []), 'la siembra no se ha retirado entera').toEqual({
    conjuntos: 0,
    sesiones: 0,
    preguntas: 0,
    catalogaciones: 0,
  });
});
