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
import { expect, test, type APIRequestContext, type Page } from '@playwright/test';

import { datosEnElTexto, lenguajeInternoEnElTexto } from '../palabrasProhibidas';
import { guardarFila, nombreDeFichero } from './informe';

const SALIDA = process.env.OPOFUENTE_CONTESTAR_SALIDA
  ? path.resolve(process.env.OPOFUENTE_CONTESTAR_SALIDA)
  : path.resolve(process.cwd(), '..', '..', 'artifacts', 'contestar');

const API_BASE = process.env.OPOFUENTE_API_URL ?? 'http://127.0.0.1:8765';
const API = `${API_BASE}/api/v1`;
const ORIGEN = 'http://127.0.0.1:4173';
const TEMA = 'IV.1';

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

interface NodoPrograma {
  id: string;
  node_type: string;
  path: string;
  children?: NodoPrograma[];
}

function aplanar(nodos: readonly NodoPrograma[]): NodoPrograma[] {
  return nodos.flatMap((nodo) => [nodo, ...aplanar(nodo.children ?? [])]);
}

/** El mismo material que siembra `tests/e2e/contestar.spec.ts`: cuatro preguntas de la A. */
async function sembrarCuestionario(request: APIRequestContext): Promise<void> {
  const respuestaOposiciones = await request.get(`${API}/oppositions`);
  expect(
    respuestaOposiciones.status(),
    `GET ${API}/oppositions: ${(await respuestaOposiciones.text()).slice(0, 200)}`,
  ).toBe(200);
  const oposiciones = (await respuestaOposiciones.json()) as {
    id: string;
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

  const cabeceras = { Origin: ORIGEN, 'Content-Type': 'application/json' };
  const conjunto = (await (
    await request.post(`${API}/question-sets`, {
      headers: cabeceras,
      data: {
        title: `Ciclo de contestar (capturas) ${String(Date.now())}`,
        opposition_id: activa.id,
        set_type: 'private_bank',
        convocation_version_id: activa.active_convocation.id,
      },
    })
  ).json()) as { id: string };

  // Cuatro enunciados **distintos**: el importador quita los duplicados por la firma de la pregunta.
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
  await request.post(
    `${API}/question-sets/${conjunto.id}/answer-keys/${claves[0]?.id ?? ''}/activate`,
    { headers: cabeceras },
  );

  const preguntas = (await (
    await request.get(`${API}/questions?set_id=${conjunto.id}`)
  ).json()) as { questions: { id: string }[] };
  expect(preguntas.questions, 'el banco de la captura tiene sus cuatro preguntas').toHaveLength(4);
  for (const pregunta of preguntas.questions) {
    await request.post(`${API}/questions/${pregunta.id}/topics`, {
      headers: cabeceras,
      data: { curriculum_node_id: tema.id },
    });
  }
}

/**
 * Deja la hoja de respuestas a la vista.
 *
 * En el móvil la hoja nace plegada (`display: none` hasta `test-hoja--abierta`) y se abre con el
 * botón «Hoja» de la cabecera: es el diseño, no un fallo. Sin abrirla, sus números no se pueden
 * pulsar —y la captura de móvil no enseñaría la hoja, que es justo lo que se quiere revisar—.
 */
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
    await sembrarCuestionario(request);

    const errores: string[] = [];
    page.on('console', (mensaje) => {
      if (mensaje.type() === 'error') {
        errores.push(mensaje.text());
      }
    });
    page.on('pageerror', (error) => errores.push(String(error)));

    // --- la cifra 1: cuántos `POST /start` por test abierto ---------------------------------------
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

    const enCurso = await retratar(
      page,
      `/test (en curso) a ${String(ancho)}`,
      'test-en-curso',
      ancho,
      alto,
      etiqueta,
      errores,
    );

    // --- contestar, volver y cambiar ---------------------------------------------------------------
    await page.getByRole('button', { name: /Falso/ }).click();
    await expect(page.getByText(/^Pregunta 2 de \d+$/)).toBeVisible({ timeout: 20_000 });
    await abrirLaHoja(page);
    await page.getByRole('button', { name: 'Ir a la pregunta 1' }).click();
    await expect(page.getByText(/^Pregunta 1 de \d+$/)).toBeVisible({ timeout: 20_000 });
    // La vuelta a una pregunta contestada **es** la captura del arreglo: antes esto no se podía hacer.
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
    expect(cifras.segundaRespuestaSeguida, 'la segunda respuesta seguida es idempotente').toBe(200);
    expect(cifras.cambioDeRespuesta, 'cambiar la respuesta se admite mientras el test corre').toBe(
      200,
    );
    expect(errores, `consola: ${errores.join(' | ')}`).toEqual([]);
    expect(cifras.violacionesAxe, 'axe en el ciclo entero').toEqual([]);
    // La zona del alumno no enseña las otras oposiciones, ni bancos ajenos, ni rutas del propietario.
    expect(cifras.datosProhibidos, 'datos prohibidos en la zona del alumno').toEqual([]);
  });
}
