/**
 * F38 (§3.5 del encargo): el Resultado del alumno, con las tres cosas que el propietario vio.
 *
 * Lo que esta prueba **mide**, no describe:
 *
 * 1. **los colores de la hoja de respuestas**, por su valor computado: el `background-color` y el
 *    `color` de cada casilla corregida (`[data-estado="correcta"]` y `[data-estado="fallada"]`), en el
 *    test en curso y en el resultado. Su queja era que **se ven distintas**, así que la prueba compara
 *    las dos pantallas y exige los mismos valores; y los compara con los del diseño (`tokens.css`:
 *    acierto `#15734a`, fallo `#b42318`, letra `--sobre-acento`), que es lo que impide que el color se
 *    «arregle» poniendo otro a mano;
 * 2. **lo que dice un test de práctica**: aciertos, fallos, porcentaje y netos con penalización, y
 *    **ninguna** banda del examen (`sobre 50`, `mínimo 25`) —esa es del simulacro y del examen oficial—;
 * 3. **que la puntuación directa no baja de 0,00 en pantalla** (0 aciertos y 1 fallo dan −0,33) y que
 *    la cifra exacta está en el pliegue;
 * 4. y lo que el encargo pide de cualquier captura: **0 violaciones de axe**, **0 errores de consola** y
 *    **ningún dato prohibido** en la pantalla (rutas del propietario, otras oposiciones, bancos).
 *
 * Las capturas —**las dos pantallas a 1280 y a 390**— se guardan en `artifacts/capturas-f38/` para que
 * el propietario las compare: son el mismo caso que él miró. Los PNG no se rastrean (se rehacen en cada
 * corrida); lo que se rastrea es esta prueba, que es la que mide.
 *
 * Los datos se siembran por las rutas de la API sobre la base **de la suite** (`.e2e-data`), que se
 * borra en cada corrida: la base real no se toca.
 */

import { mkdirSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import AxeBuilder from '@axe-core/playwright';
import { expect, test, type Page } from '@playwright/test';

import { datosEnElTexto, lenguajeInternoEnElTexto } from '../palabrasProhibidas';

const AQUI = path.dirname(fileURLToPath(import.meta.url));
const REPOSITORIO = path.resolve(AQUI, '..', '..', '..', '..');

const API = 'http://127.0.0.1:8765/api/v1';
const ORIGEN = 'http://127.0.0.1:4173';
const CAPTURAS = path.join(REPOSITORIO, 'artifacts', 'capturas-f38');
/** La base de la suite (`.e2e-data`): la única que esta prueba puede tocar. Nunca la real. */
const DATOS_DE_LA_SUITE =
  process.env.OPOFUENTE_E2E_DATA_DIR ?? path.join(REPOSITORIO, '.e2e-data');

const ANCHOS: readonly { ancho: number; alto: number; etiqueta: string }[] = [
  { ancho: 1280, alto: 800, etiqueta: 'escritorio' },
  { ancho: 390, alto: 844, etiqueta: 'movil' },
];

/**
 * Los dos colores que la corrección tiene que ver, con su valor computado.
 *
 * Salen de `src/styles/tokens.css` (`--acierto: #15734a`, `--fallo: #b42318`, `--sobre-acento:
 * #ffffff`). Se escriben aquí como los devuelve el navegador (`rgb(...)`) porque eso es lo que se mide;
 * si el diseño cambia, esta prueba dice que el diseño cambió en vez de dar el color por bueno.
 */
const VERDE = 'rgb(21, 115, 74)';
const ROJO = 'rgb(180, 35, 24)';
const SOBRE_EL_COLOR = 'rgb(255, 255, 255)';
/** El fondo del papel: lo que se veía a través de una casilla a la que no le llegaba el color. */
const TRANSPARENTE = 'rgba(0, 0, 0, 0)';

interface Colores {
  correcta: { fondo: string; letra: string };
  fallada: { fondo: string; letra: string };
}

/**
 * El color computado de las dos casillas corregidas de la hoja.
 *
 * Se pregunta por el **primero** de cada estado: la hoja tiene una casilla correcta y una fallada por
 * fila, y lo que se mide es la pintura, no el recuento.
 */
async function coloresDeLaHoja(page: Page): Promise<Colores> {
  const hoja = page.getByRole('list', { name: 'Hoja de respuestas' });
  await expect(hoja).toBeVisible();
  return hoja.evaluate((lista) => {
    const leer = (estado: string): { fondo: string; letra: string } => {
      const casilla = lista.querySelector(`[data-estado="${estado}"]`);
      if (casilla === null) {
        throw new Error(`la hoja no tiene ninguna casilla en estado «${estado}»`);
      }
      const estilo = getComputedStyle(casilla);
      return { fondo: estilo.backgroundColor, letra: estilo.color };
    };
    return { correcta: leer('correcta'), fallada: leer('fallada') };
  });
}

/** Retrata la pantalla y comprueba lo que el encargo pide de toda captura. */
async function retratarYRevisar(
  page: Page,
  ruta: string,
  fichero: string,
  ancho: number,
  alto: number,
  etiqueta: string,
  /** Lo que hay que hacer **antes** de la foto para que la foto enseñe lo que se compara. */
  preparar?: (page: Page) => Promise<void>,
): Promise<void> {
  const errores: string[] = [];
  page.on('console', (mensaje) => {
    if (mensaje.type() === 'error') {
      errores.push(mensaje.text());
    }
  });
  page.on('pageerror', (error) => errores.push(String(error)));

  await page.setViewportSize({ width: ancho, height: alto });
  await page.goto(ruta, { waitUntil: 'networkidle' });
  await expect(page.locator('main')).toBeVisible();
  if (preparar !== undefined) {
    await preparar(page);
  }

  mkdirSync(CAPTURAS, { recursive: true });
  await page.screenshot({ path: path.join(CAPTURAS, `${fichero}-${etiqueta}.png`), fullPage: true });

  const analisis = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
    .analyze();
  expect(
    analisis.violations.map((violacion) => violacion.id),
    `axe en ${ruta} a ${String(ancho)} px`,
  ).toEqual([]);
  expect(errores, `consola en ${ruta} a ${String(ancho)} px`).toEqual([]);

  // Los datos que no se pueden ver: se miran en **toda** la pantalla (contenido incluido) y la jerga
  // interna solo en la interfaz, que es la regla del detector (`tests/palabrasProhibidas.ts`).
  const textos = await page.evaluate(() => {
    const copia = document.body.cloneNode(true) as HTMLElement;
    for (const nodo of Array.from(copia.querySelectorAll('[data-contenido]'))) {
      nodo.remove();
    }
    return { interfaz: copia.innerText || copia.textContent || '', todo: document.body.innerText };
  });
  expect(datosEnElTexto(textos.todo), `datos del propietario en ${ruta}`).toEqual([]);
  expect(lenguajeInternoEnElTexto(textos.interfaz), `jerga interna en ${ruta}`).toEqual([]);
}

/**
 * Las tres sesiones que hacen falta, sembradas una vez por corrida:
 *
 * - `terminada`: dos bien y dos mal, contestada y cerrada — el resultado que se retrata;
 * - `enCurso`: en marcha con una respuesta correcta y otra fallada, que es la única manera de ver la
 *   hoja pintada de verde y de rojo **en el test** (la corrección es inmediata y la casilla se colorea
 *   al contestar);
 * - `negativa`: cerrada con **una sola respuesta, y fallada**, que es la cifra que no se puede enseñar
 *   (0 aciertos − 1 fallo × 1/3 = −0,33).
 *
 * Todo va por las rutas de la API sobre la base **de la suite** (`.e2e-data`), que se borra en cada
 * corrida: la base real no se toca.
 */
interface SesionesSembradas {
  terminada: string;
  enCurso: string;
  negativa: string;
}

let sembrado: Promise<SesionesSembradas> | null = null;

function sembrar(): Promise<SesionesSembradas> {
  sembrado ??= sembrarDeVerdad();
  return sembrado;
}

/**
 * El conjunto de la siembra: se guarda para **retirar lo que esta prueba aporta al temario**.
 *
 * El diagnóstico del panel (`E2E-06 un diagnóstico reparte la muestra por temas`) compone su muestra
 * sobre **todo** el banco catalogado, dos preguntas por tema. Las cuatro preguntas de esta siembra van
 * catalogadas a IV.1 y IV.7 —hace falta, porque el resultado de un test enseña su desglose por tema y
 * una captura sin temas no sería la que el propietario mira—, y con ellas el diagnóstico pasaba de 6
 * preguntas a 8 y esa prueba se quedaba esperando «0 de 6 respondidas». Medido, no supuesto: fue el
 * único rojo de la suite completa al añadir esta prueba.
 *
 * Se retira **solo la catalogación**, no las preguntas ni las sesiones: así esta prueba no le quita
 * nada a ninguna otra (el banco sigue teniendo su material y sus sesiones siguen siendo coherentes) y
 * el diagnóstico vuelve a repartir sus seis.
 */
let conjuntoDeLaSiembra: string | null = null;

test.afterAll(async () => {
  if (conjuntoDeLaSiembra === null) {
    return;
  }
  // `node:sqlite`, como la captura de la bandeja: es la única manera de tocar una tabla que no tiene
  // ruta de escritura, y se hace sobre la base **de la suite**, nunca sobre la real.
  const { DatabaseSync } = await import('node:sqlite');
  const db = new DatabaseSync(path.join(DATOS_DE_LA_SUITE, 'opofuente.sqlite3'));
  try {
    db.prepare(
      'DELETE FROM curriculum_mappings WHERE subject_type = ? AND subject_id IN ' +
        '(SELECT id FROM question_versions WHERE question_set_id = ?)',
    ).run('question_version', conjuntoDeLaSiembra);
  } finally {
    db.close();
  }
});

async function sembrarDeVerdad(): Promise<SesionesSembradas> {
  const cabeceras = { 'Content-Type': 'application/json', Origin: ORIGEN };
  const leer = async <T>(respuesta: Response): Promise<T> => {
    if (!respuesta.ok) {
      throw new Error(`la API respondió ${String(respuesta.status)} al sembrar el resultado`);
    }
    return (await respuesta.json()) as T;
  };

  const oposiciones = await leer<
    { id: string; active: boolean; active_convocation: { id: string } | null }[]
  >(await fetch(`${API}/oppositions`));
  const activa = oposiciones.find((oposicion) => oposicion.active);
  if (activa?.active_convocation == null) {
    throw new Error('no hay oposición activa con convocatoria: no se puede sembrar el resultado');
  }

  const conjunto = await leer<{ id: string }>(
    await fetch(`${API}/question-sets`, {
      method: 'POST',
      headers: cabeceras,
      body: JSON.stringify({
        title: `Resultado del alumno ${String(Date.now())}`,
        opposition_id: activa.id,
        set_type: 'private_bank',
        convocation_version_id: activa.active_convocation.id,
      }),
    }),
  );
  // Se apunta para retirar su catalogación al terminar (ver `test.afterAll`): el diagnóstico del panel
  // compone su muestra sobre todo el banco catalogado y no puede llevarse las preguntas de esta prueba.
  conjuntoDeLaSiembra = conjunto.id;

  const texto = [
    '1. El modelo TCP/IP tiene cuatro capas.',
    'a) Verdadero',
    'b) Falso',
    'Respuesta correcta: a',
    '2. La sede electronica se regula en la Ley 39/2015.',
    'a) Verdadero',
    'b) Falso',
    'Respuesta correcta: a',
    '3. El Esquema Nacional de Seguridad se regula en el Real Decreto 311/2022.',
    'a) Verdadero',
    'b) Falso',
    'Respuesta correcta: a',
    '4. El plazo del procedimiento administrativo comun es de diez dias habiles.',
    'a) Verdadero',
    'b) Falso',
    'Respuesta correcta: a',
    '',
  ].join('\n');
  await leer<unknown>(
    await fetch(`${API}/question-sets/${conjunto.id}/parse`, {
      method: 'POST',
      headers: cabeceras,
      body: JSON.stringify({ kind: 'questions', text: texto }),
    }),
  );

  const claves = await leer<{ id: string }[]>(
    await fetch(`${API}/question-sets/${conjunto.id}/answer-keys`),
  );
  const clave = claves[0];
  if (clave === undefined) {
    throw new Error('el conjunto no trae plantilla: sin ella no hay test que retratar');
  }
  await leer<unknown>(
    await fetch(`${API}/question-sets/${conjunto.id}/answer-keys/${clave.id}/activate`, {
      method: 'POST',
      headers: cabeceras,
    }),
  );

  const programa = await leer<{ nodes: NodoPrograma[] }>(
    await fetch(`${API}/convocations/${activa.active_convocation.id}/curriculum`),
  );
  const planos = aplanar(programa.nodes);
  const temas = ['IV.1', 'IV.7']
    .map((codigo) => planos.find((nodo) => nodo.path === codigo))
    .filter((nodo): nodo is NodoPrograma => nodo !== undefined);
  if (temas.length === 0) {
    throw new Error('el programa no tiene los temas de la captura');
  }
  const preguntas = await leer<{ questions: { id: string }[] }>(
    await fetch(`${API}/questions?set_id=${conjunto.id}&limit=10`),
  );
  for (const [indice, pregunta] of preguntas.questions.entries()) {
    const tema = temas[indice % temas.length]!;
    await leer<unknown>(
      await fetch(`${API}/questions/${pregunta.id}/topics`, {
        method: 'POST',
        headers: cabeceras,
        body: JSON.stringify({ curriculum_node_id: tema.id }),
      }),
    );
  }

  const montar = async (): Promise<string> => {
    const sesion = await leer<{ id: string }>(
      await fetch(`${API}/student/tests`, {
        method: 'POST',
        headers: cabeceras,
        body: JSON.stringify({
          nodes: temas.map((tema) => tema.path),
          count: preguntas.questions.length,
          filter: 'all',
          feedback: 'immediate',
        }),
      }),
    );
    await leer<unknown>(
      await fetch(`${API}/student/sessions/${sesion.id}/start`, {
        method: 'POST',
        headers: cabeceras,
      }),
    );
    return sesion.id;
  };

  // 1) La sesión que se queda en curso con sus dos primeras respuestas (una bien y una mal): es la que
  //    enseña la hoja corregida **en el test**. La `a` es la correcta de las cuatro.
  const enCurso = await montar();
  for (const [posicion, elegida] of [
    [1, 'a'],
    [2, 'b'],
  ] as const) {
    await leer<unknown>(
      await fetch(`${API}/student/sessions/${enCurso}/answers`, {
        method: 'POST',
        headers: cabeceras,
        body: JSON.stringify({
          position: posicion,
          chosen: [elegida],
          elapsed_ms: 1200,
        }),
      }),
    );
  }

  // 2) La sesión terminada: dos bien y dos mal, que es el resultado que se retrata.
  const terminada = await montar();
  for (let posicion = 1; posicion <= preguntas.questions.length; posicion += 1) {
    await leer<unknown>(
      await fetch(`${API}/student/sessions/${terminada}/answers`, {
        method: 'POST',
        headers: cabeceras,
        body: JSON.stringify({
          position: posicion,
          chosen: [posicion <= 2 ? 'a' : 'b'],
          elapsed_ms: 1200 * posicion,
        }),
      }),
    );
  }
  await leer<unknown>(
    await fetch(`${API}/student/sessions/${terminada}/finish`, {
      method: 'POST',
      headers: cabeceras,
    }),
  );

  // 3) La sesión del cero: una sola respuesta y fallada, y se cierra. Un acierto menos un tercio…
  //    al revés: cero aciertos menos un tercio de fallo.
  const negativa = await montar();
  await leer<unknown>(
    await fetch(`${API}/student/sessions/${negativa}/answers`, {
      method: 'POST',
      headers: cabeceras,
      body: JSON.stringify({ position: 1, chosen: ['b'], elapsed_ms: 1500 }),
    }),
  );
  await leer<unknown>(
    await fetch(`${API}/student/sessions/${negativa}/finish`, {
      method: 'POST',
      headers: cabeceras,
    }),
  );

  return { terminada, enCurso, negativa };
}

interface NodoPrograma {
  id: string;
  path: string;
  children?: NodoPrograma[];
}

function aplanar(nodos: NodoPrograma[]): NodoPrograma[] {
  return nodos.flatMap((nodo) => [nodo, ...aplanar(nodo.children ?? [])]);
}

for (const { ancho, alto, etiqueta } of ANCHOS) {
  test(`F38 el test en curso, a ${String(ancho)} px`, async ({ page }) => {
    const { enCurso } = await sembrar();

    // A 390 la hoja vive detrás de su botón: se abre **antes** de la foto, porque lo que hay que poder
    // comparar es la hoja de las dos pantallas.
    await retratarYRevisar(page, `/test/${enCurso}`, 'test-en-curso', ancho, alto, etiqueta, async (p) => {
      const botonHoja = p.getByRole('button', { name: 'Hoja', exact: true });
      if (await botonHoja.isVisible()) {
        await botonHoja.click();
      }
    });

    const colores = await coloresDeLaHoja(page);
    // Lo que el propietario decía que **sí** se ve bien: verde y rojo de verdad, con la letra blanca
    // encima. Se mide el valor computado, no la clase.
    expect(colores.correcta.fondo, 'la casilla correcta en el test').toBe(VERDE);
    expect(colores.correcta.letra, 'la letra de la casilla correcta en el test').toBe(SOBRE_EL_COLOR);
    expect(colores.fallada.fondo, 'la casilla fallada en el test').toBe(ROJO);
    expect(colores.fallada.letra, 'la letra de la casilla fallada en el test').toBe(SOBRE_EL_COLOR);
  });
}

for (const { ancho, alto, etiqueta } of ANCHOS) {
  test(`F38 el resultado, a ${String(ancho)} px`, async ({ page }) => {
    const { terminada } = await sembrar();

    await retratarYRevisar(page, `/resultado/${terminada}`, 'resultado', ancho, alto, etiqueta);

    const colores = await coloresDeLaHoja(page);
    // La queja era exactamente esta: **la misma hoja se ve distinta** en las dos pantallas. Se exige
    // que sea la misma, y que sea la del diseño.
    expect(colores.correcta.fondo, 'la casilla correcta en el resultado').toBe(VERDE);
    expect(colores.correcta.letra, 'la letra de la casilla correcta en el resultado').toBe(
      SOBRE_EL_COLOR,
    );
    expect(colores.fallada.fondo, 'la casilla fallada en el resultado').toBe(ROJO);
    expect(colores.fallada.letra, 'la letra de la casilla fallada en el resultado').toBe(
      SOBRE_EL_COLOR,
    );
    // Y que ninguna casilla **corregida** se quede sin fondo: un `background` inválido se cae a
    // transparente, que es cómo se veía el defecto (letra blanca sobre papel blanco). Las casillas sin
    // corregir sí son transparentes por diseño.
    const fondos = await page
      .getByRole('list', { name: 'Hoja de respuestas' })
      .locator('[data-estado="correcta"], [data-estado="fallada"]')
      .evaluateAll((casillas) => casillas.map((casilla) => getComputedStyle(casilla).backgroundColor));
    expect(fondos.length).toBeGreaterThan(0);
    expect(fondos.filter((fondo) => fondo === TRANSPARENTE)).toEqual([]);

    // §3.5: un test de práctica dice aciertos, fallos, porcentaje y netos con penalización…
    const cifras = page.locator('.resultado__cifras');
    await expect(cifras).toContainText('2 aciertos');
    await expect(cifras).toContainText('2 fallos');
    await expect(cifras).toContainText('50 % de acierto');
    const linea = page.locator('.resultado__puntos');
    await expect(linea).toHaveCount(1);
    // 2 aciertos − 2 fallos × 1/3 = 4/3 → «1,33», en español y sin banda.
    await expect(linea).toHaveText('Netos con penalización: 1,33');
    // …y **no** la banda del examen, que es del simulacro y del examen oficial.
    await expect(page.locator('.resultado__puntos')).not.toContainText('sobre 50');
    await expect(page.locator('.resultado__partes')).toHaveCount(0);

    // §3.5 / regla general: la hoja ya no lleva encima la frase que explicaba lo que ella misma dice.
    await expect(page.getByText(/Cada casilla dice lo que pasó/i)).toHaveCount(0);
  });
}

for (const { ancho, alto, etiqueta } of ANCHOS) {
  test(`F38 la puntuación directa no baja de 0,00, a ${String(ancho)} px`, async ({ page }) => {
    const { negativa } = await sembrar();

    await retratarYRevisar(page, `/resultado/${negativa}`, 'resultado-en-negativo', ancho, alto, etiqueta);

    // 0 aciertos y 1 fallo con la penalización de un tercio: −1/3 de netos.
    const linea = page.locator('.resultado__puntos');
    await expect(linea).toHaveText('Netos con penalización: 0,00');
    // La cifra exacta existe y está en el pliegue, no a la vista.
    const exacta = page.locator('.resultado__exacta');
    await expect(exacta).toContainText('-0,33');
    await expect(exacta).not.toBeVisible();
    const boton = page.getByRole('button', { name: '¿Por qué 0,00?' });
    await expect(boton).toHaveAttribute('aria-expanded', 'false');
    await boton.click();
    await expect(exacta).toBeVisible();
    // Y el pliegue se cierra otra vez sin dejar la cifra a la vista.
    await boton.click();
    await expect(exacta).not.toBeVisible();
  });
}
