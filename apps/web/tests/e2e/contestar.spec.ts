import AxeBuilder from '@axe-core/playwright';
import { expect, test, type APIRequestContext, type Page } from '@playwright/test';

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
 */

const API_BASE = process.env.OPOFUENTE_API_URL ?? 'http://127.0.0.1:8765';
const API = `${API_BASE}/api/v1`;
const ORIGEN = 'http://127.0.0.1:4173';
const TEMA = 'IV.1';

/** Dos anchos de referencia (07_UI-UX §14): el de escritorio y el del móvil. */
const ANCHOS = [
  { ancho: 1280, alto: 800, etiqueta: 'escritorio' },
  { ancho: 390, alto: 844, etiqueta: 'movil' },
];

interface NodoPrograma {
  id: string;
  node_type: string;
  path: string;
  children?: NodoPrograma[];
}

function aplanar(nodos: readonly NodoPrograma[]): NodoPrograma[] {
  return nodos.flatMap((nodo) => [nodo, ...aplanar(nodo.children ?? [])]);
}

async function nodoDelTema(request: APIRequestContext): Promise<NodoPrograma> {
  const oposiciones = (await (await request.get(`${API}/oppositions`)).json()) as {
    active: boolean;
    active_convocation: { id: string } | null;
  }[];
  const activa = oposiciones.find((oposicion) => oposicion.active);
  if (activa?.active_convocation == null) {
    throw new Error('no hay oposición activa con convocatoria');
  }
  const programa = (await (
    await request.get(`${API}/convocations/${activa.active_convocation.id}/curriculum`)
  ).json()) as { nodes: NodoPrograma[] };
  const tema = aplanar(programa.nodes).find(
    (nodo) => nodo.node_type === 'topic' && nodo.path === TEMA,
  );
  if (tema === undefined) {
    throw new Error(`el programa no tiene el tema ${TEMA}`);
  }
  return tema;
}

/**
 * Un banco de cuatro preguntas con su clave **activa**, catalogadas en el tema.
 *
 * La clave se activa por la ruta de verdad: una plantilla en borrador no corrige, y sin corrección no
 * hay ciclo que medir. Las cuatro preguntas se contestan con la misma letra a propósito (la A es la
 * correcta), así que la prueba sabe de antemano cuál es el acierto y cuál el fallo.
 */
async function sembrarCuestionario(request: APIRequestContext): Promise<void> {
  const tema = await nodoDelTema(request);
  const oposiciones = (await (await request.get(`${API}/oppositions`)).json()) as {
    id: string;
    active: boolean;
    active_convocation: { id: string } | null;
  }[];
  const activa = oposiciones.find((oposicion) => oposicion.active);
  const cabeceras = { Origin: ORIGEN, 'Content-Type': 'application/json' };

  const conjunto = (await (
    await request.post(`${API}/question-sets`, {
      headers: cabeceras,
      data: {
        title: `Ciclo de contestar ${String(Date.now())}`,
        opposition_id: activa?.id,
        set_type: 'private_bank',
        convocation_version_id: activa?.active_convocation?.id,
      },
    })
  ).json()) as { id: string };

  // Cuatro enunciados **distintos**: el importador quita los duplicados por la firma de la pregunta
  // —«la misma pregunta» no puede caer dos veces en un test— y cuatro textos que solo se diferencian
  // en el número se quedan en uno (medido: `created=1, existing=3`).
  const enunciados = [
    'El plazo del procedimiento del caso A es de diez días hábiles.',
    'El plazo del procedimiento del caso B es de veinte días hábiles.',
    'El plazo del procedimiento del caso C es de treinta días hábiles.',
    'El plazo del procedimiento del caso D es de cuarenta días hábiles.',
  ];
  const lineas: string[] = [];
  enunciados.forEach((enunciado, indice) => {
    lineas.push(`${String(indice + 1)}. ${enunciado}`);
    lineas.push('a) Verdadero');
    lineas.push('b) Falso');
    lineas.push('Respuesta correcta: a');
    lineas.push('');
  });
  await request.post(`${API}/question-sets/${conjunto.id}/parse`, {
    headers: cabeceras,
    data: { kind: 'questions', text: lineas.join('\n') },
  });

  const claves = (await (
    await request.get(`${API}/question-sets/${conjunto.id}/answer-keys`)
  ).json()) as { id: string }[];
  expect(claves[0], 'el conjunto tiene que traer su plantilla').toBeDefined();
  await request.post(
    `${API}/question-sets/${conjunto.id}/answer-keys/${claves[0]?.id ?? ''}/activate`,
    { headers: cabeceras },
  );

  const preguntas = (await (
    await request.get(`${API}/questions?set_id=${conjunto.id}`)
  ).json()) as { questions: { id: string }[] };
  expect(preguntas.questions).toHaveLength(4);
  for (const pregunta of preguntas.questions) {
    await request.post(`${API}/questions/${pregunta.id}/topics`, {
      headers: cabeceras,
      data: { curriculum_node_id: tema.id },
    });
  }
}

/**
 * Abre un test del tema y devuelve cuántos `POST /start` se han mandado por el camino.
 *
 * El contador se engancha **antes** de navegar: engancharlo después dejaría fuera justo la petición
 * que se quiere medir, que sale al montar la pantalla.
 */
async function abrirTest(page: Page): Promise<number> {
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
  return arranques.length;
}

test('E2E-F36 el ciclo entero: contestar, volver, cambiar y terminar', async ({
  page,
  request,
}) => {
  await sembrarCuestionario(request);

  const errores: string[] = [];
  page.on('console', (mensaje) => {
    if (mensaje.type() === 'error') {
      errores.push(mensaje.text());
    }
  });
  page.on('pageerror', (error) => errores.push(String(error)));

  // --- 1. abrir el test: **un** `POST /start`, medido -------------------------------------------------
  const arranques = await abrirTest(page);
  expect(arranques, 'un test abierto arranca una vez, no de cuatro a doce').toBe(1);

  // --- 2. contestar, y medir el código de la **segunda** respuesta seguida ---------------------------
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

  // --- 3. **cambiarla** ------------------------------------------------------------------------------
  await page.getByRole('button', { name: /Verdadero/ }).click();
  await expect(page.locator('.test-opcion--correcta')).toHaveCount(1, { timeout: 20_000 });
  await expect.poll(() => respuestas.length).toBeGreaterThanOrEqual(3);
  expect(respuestas[2], 'cambiar una respuesta mientras el test corre se admite').toBe(200);

  // --- 4. terminar -----------------------------------------------------------------------------------
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
    await sembrarCuestionario(request);
    await page.setViewportSize({ width: ancho, height: alto });
    await abrirTest(page);

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
  });
}
