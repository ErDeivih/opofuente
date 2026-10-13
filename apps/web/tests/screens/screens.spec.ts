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
 *
 * El **test en curso** necesita una sesión de verdad para poder retratarse: esta herramienta la monta
 * por la API del alumno (un conjunto, sus preguntas, su plantilla activa y su tema) antes de entrar.
 * No se inventa la pantalla con datos falsos: si la API no está, la captura sale con su estado y se
 * dice en el informe.
 */

import { mkdirSync } from 'node:fs';
import path from 'node:path';

import AxeBuilder from '@axe-core/playwright';
import { expect, test, type Page } from '@playwright/test';

import { revisarPantalla } from '../palabrasProhibidas';
import { escribirInforme, guardarFila, nombreDeFichero } from './informe';

const SALIDA = path.resolve(process.cwd(), '..', '..', 'artifacts', 'screens');

/** Dónde escucha la API local en esta herramienta (la misma dirección que usa la web). */
const API = process.env.OPOFUENTE_API_URL ?? 'http://127.0.0.1:8765';

/** El origen con el que se firman las escrituras, como en el navegador. */
const ORIGEN = 'http://127.0.0.1:4173';

/**
 * El texto que ve el alumno cuando la clave de esa pregunta está en revisión (§1 del objetivo).
 *
 * La API manda un booleano (`in_review`); el rótulo lo pone la interfaz. Estas capturas existen para
 * enseñarlo, así que se comprueba que está: un PNG que hay que mirar a ojo no es evidencia.
 */
const MARCA_EN_REVISION = 'clave en revisión';

/** El directorio de datos de la suite, el mismo que le pasa `playwright.config.ts` a la API. */
const DATOS_DE_LA_SUITE =
  process.env.OPOFUENTE_E2E_DATA_DIR ?? path.resolve(process.cwd(), '..', '..', '.e2e-data');

/**
 * Deja el conjunto recién montado como **dudoso**, que es lo que hace visible la marca «clave en
 * revisión» (§1 del objetivo).
 *
 * La fiabilidad de una clave la decide la **puerta de datos**, midiendo el conjunto contra los
 * apuntes del tema; aquí no hay apuntes ni quince preguntas comprobadas, así que la puerta no puede
 * medirlo y el conjunto se quedaría `fiable`. La captura necesita justo lo contrario —**enseñar** la
 * marca—, así que se escribe el veredicto directamente en la base **de la suite** (`.e2e-data`, que
 * es suya y se borra en cada corrida) con el valor que la puerta habría puesto tras medir una
 * discrepancia de entre el 15 % y el 30 %.
 *
 * Se hace con `node:sqlite`, que viene con Node, para no añadir dependencias ni procesos. Y se hace
 * aquí y no en la puerta a propósito: esto es una **herramienta de capturas**, no el juez.
 */
async function marcarElConjuntoComoDudoso(setId: string): Promise<void> {
  const { DatabaseSync } = await import('node:sqlite');
  const base = new DatabaseSync(path.join(DATOS_DE_LA_SUITE, 'opofuente.sqlite3'));
  try {
    base
      .prepare('UPDATE question_sets SET key_reliability = ? WHERE id = ?')
      .run('dudosa', setId);
  } finally {
    base.close();
  }
}

// El informe se escribe **después** de la última captura de este proceso. Si una captura se pasa de
// tiempo, Playwright reinicia el proceso y este `afterAll` vuelve a correr: cada fila ya está en
// disco, así que el informe sale completo igualmente.
test.afterAll(() => {
  escribirInforme();
});

/** Las rutas que se visitan, con el nombre con el que se guarda cada captura. */
const RUTAS: readonly { ruta: string; nombre: string }[] = [
  { ruta: '/', nombre: 'inicio' },
  { ruta: '/temario', nombre: 'temario' },
  { ruta: '/temario/IV.7', nombre: 'tema-apuntes' },
  { ruta: '/temario/I.6', nombre: 'tema-borrador' },
  { ruta: '/simulacros', nombre: 'simulacros' },
  { ruta: '/examenes', nombre: 'examenes' },
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
  { ruta: '/admin/ui', nombre: 'admin-ui' },
  /* El bloque C del panel (F16): lo que el motor dejó fuera de los tests. Lee las marcas de fuera de
     temario que ya estén en los datos —con los del propietario, los 769 enunciados rotos— y se
     retrata tal cual. La bandeja de avisos va aparte, más abajo: necesita que haya un aviso dentro. */
  { ruta: '/admin/no-son-preguntas', nombre: 'no-son-preguntas' },
  /* La bandeja del **motor** (F18): las incidencias que deja la comprobación de los apuntes. Con los
     datos del propietario son 453 —291 de norma cambiada, 110 de clave sospechosa, 40 huecos y 12
     ambiguas—, y se retrata tal cual: **nada de filas inventadas**.
     Va **con el filtro de una categoría** puesta, y se dice por qué: sin filtro la pantalla enseña
     200 filas y el PNG sale de **262.914 px de alto** (medido el 13-oct-2026 en la copia de la base
     real), que no hay visor que abra. Con `hueco_sin_material` —40 incidencias reales, la primera
     categoría del orden de trabajo— se ve la fila entera con sus enlaces y sus botones, y **las
     cuatro cifras siguen ahí**, porque los contadores de los botones se cuentan en la base y no miran
     el filtro: «Todas 453 · Hueco sin material 40 · Clave sospechosa 110 · Norma cambiada 291 ·
     Pregunta ambigua 12». */
  { ruta: '/admin/incidencias?categoria=hueco_sin_material', nombre: 'admin-incidencias' },
];

const ANCHOS: readonly { ancho: number; alto: number; etiqueta: string }[] = [
  { ancho: 1280, alto: 800, etiqueta: 'escritorio' },
  { ancho: 390, alto: 844, etiqueta: 'movil' },
];

/** Visita una ruta, la retrata y guarda su fila del informe.
 *
 * `fichero` es el nombre con el que se guarda el PNG: para una ruta con identificador dentro
 * (`/test/<uuid>`) no se puede usar la ruta, o cada captura tendría un nombre distinto y el informe
 * dejaría de poder compararse con el de ayer.
 */
async function retratar(
  page: Page,
  ruta: string,
  fichero: string,
  ancho: number,
  alto: number,
  etiqueta: string,
): Promise<void> {
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
  await page.screenshot({
    path: path.join(SALIDA, `${nombreFichero}.png`),
    fullPage: true,
  });

  const analisis = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
    .analyze();
  // Dos textos, porque son dos comprobaciones: el de la **interfaz** (todo menos lo que va dentro
  // de un contenedor `data-contenido`: enunciados, opciones, apuntes, títulos de tema) y el de
  // **toda** la pantalla. La jerga solo se busca en el primero; las rutas y los bancos, en los dos.
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

  guardarFila({
    ruta,
    ancho: `${ancho}×${alto}`,
    ms,
    errores,
    violaciones: analisis.violations.map((violacion) => violacion.id),
    prohibidas: revisarPantalla(interfaz, todo),
    fichero: nombreFichero,
  });
}

for (const { ruta, nombre } of RUTAS) {
  for (const { ancho, alto, etiqueta } of ANCHOS) {
    test(`${nombre} a ${ancho} px`, async ({ page }) => {
      await retratar(page, ruta, ruta, ancho, alto, etiqueta);
    });
  }
}

/**
 * El test en curso, con datos de verdad.
 *
 * Se monta por la API del alumno —la misma que usa la pantalla— porque una captura de esta pantalla
 * sin sesión no enseña nada: es la hoja de respuestas lo que hay que ver. Si algo falla, la captura
 * se hace igual (con el estado de error de la pantalla) y el fallo se ve en el informe.
 */
for (const { ancho, alto, etiqueta } of ANCHOS) {
  test(`test-en-curso a ${ancho} px`, async ({ page }) => {
    const sesion = await montarTestDeAlumno();
    await retratar(page, `/test/${sesion}`, '/test-en-curso', ancho, alto, etiqueta);
    // La marca «clave en revisión» es lo que esta captura tiene que enseñar: si no está, la captura
    // no sirve de nada. Se comprueba aquí, sobre la pantalla ya cargada, para que la evidencia no
    // dependa de que alguien mire el PNG.
    await expect(page.getByText(MARCA_EN_REVISION).first()).toBeVisible();
  });
}

/**
 * La ficha de pregunta (F20), con una pregunta **de verdad** y del caso de uso: una de un banco con la
 * respuesta correcta en duda.
 *
 * La pregunta se elige por la **bandeja del motor**, que es de donde se llega a la ficha de verdad: se
 * piden las incidencias de los bancos en cuarentena (`clave_no_fiable`), se lee su ficha por la API y
 * se retrata la primera que **manda hoy** (no una vista ya sustituida) y cuyo banco trae el veredicto
 * de fiabilidad del §1. Así la captura enseña el caso entero: la letra, de dónde sale, el veredicto del
 * banco y lo que dicen los apuntes en contra.
 *
 * Si los datos no traen ninguna —la base de la suite nace vacía— se cae a la primera pregunta del
 * banco, y lo que salga se ve en la captura: **nada de filas inventadas**.
 *
 * Se retrata a los dos anchos porque es una pantalla larga —enunciado, opciones, procedencia, apuntes,
 * incidencias, los dos botones y dos tablas— y el móvil es donde se desborda.
 */
for (const { ancho, alto, etiqueta } of ANCHOS) {
  test(`ficha-de-pregunta a ${ancho} px`, async ({ page }) => {
    const pregunta = await preguntaEnCuarentena();
    await retratar(
      page,
      `/admin/preguntas?pregunta=${pregunta}`,
      '/admin/preguntas-ficha',
      ancho,
      alto,
      etiqueta,
    );
  });
}

/** La ficha de una pregunta, por la API: se usa para elegir la que se retrata. */
async function fichaDe(pregunta: string): Promise<{
  superseded_by: string | null;
  key_reliability: string | null;
} | null> {
  const respuesta = await fetch(`${API}/api/v1/question-files/${pregunta}`);
  if (!respuesta.ok) {
    return null;
  }
  return (await respuesta.json()) as { superseded_by: string | null; key_reliability: string | null };
}

/**
 * La primera pregunta **vigente** de un banco en cuarentena, o la primera del banco.
 *
 * Se piden veinte candidatas y no una: después de una corrida de reparaciones, parte de la bandeja
 * apunta a vistas ya sustituidas, y retratar una de esas enseñaría el aviso de «esta vista está
 * sustituida» en lugar de la ficha del caso de uso.
 */
async function preguntaEnCuarentena(): Promise<string> {
  const incidencias = await fetch(
    `${API}/api/v1/notes-incidents?category=clave_no_fiable&limit=20`,
  );
  if (incidencias.ok) {
    const cuerpo = (await incidencias.json()) as {
      incidents?: { question_version_id: string }[];
    };
    const candidatas = (cuerpo.incidents ?? []).map(
      (incidencia) => incidencia.question_version_id,
    );
    let primeraVigente: string | undefined;
    for (const candidata of candidatas) {
      const ficha = await fichaDe(candidata);
      if (ficha?.superseded_by !== null && ficha !== null) {
        continue;
      }
      primeraVigente ??= candidata;
      if (ficha?.key_reliability === 'no_fiable' || ficha?.key_reliability === 'dudosa') {
        return candidata;
      }
    }
    if (primeraVigente !== undefined) {
      return primeraVigente;
    }
  }
  const preguntas = await fetch(`${API}/api/v1/questions?limit=1`);
  if (!preguntas.ok) {
    throw new Error('no se pudo leer ninguna pregunta del banco para la captura de la ficha');
  }
  const listado = (await preguntas.json()) as { questions: { id: string }[] };
  const primera = listado.questions[0]?.id;
  if (primera === undefined) {
    throw new Error('el banco no tiene ninguna pregunta: no hay ficha que retratar');
  }
  return primera;
}

/**
 * La bandeja de avisos del alumno, con un aviso dentro (F16).
 *
 * Se siembra por la ruta del alumno —la misma que usa el botón «Esto está mal»— sobre los apuntes
 * reales del tema que los tenga, porque una bandeja vacía no demuestra nada de lo que hay que ver:
 * el tema, el apartado, el motivo del alumno, su fecha y los botones de despacho. Si los datos no
 * traen ningún tema con apuntes, la captura sale con su estado vacío y así se dice en el informe.
 */
for (const { ancho, alto, etiqueta } of ANCHOS) {
  test(`avisos a ${ancho} px`, async ({ page }) => {
    await prepararAvisos();
    await retratar(page, '/admin/avisos', '/admin/avisos', ancho, alto, etiqueta);
  });
}

/**
 * El resultado, los fallos y el progreso, con un test **terminado** de verdad (F14).
 *
 * Estas tres pantallas no enseñan nada sin datos: un resultado sin preguntas contestadas no tiene
 * desglose por tema, y la lista de fallos y el progreso salen vacíos. Se siembra por la API —un
 * conjunto con sus preguntas, su plantilla activa, su catalogación y un test contestado y cerrado—
 * porque inventarse la pantalla con datos falsos no demuestra que funcione con los de verdad.
 */
for (const { ruta, fichero } of [
  { ruta: '/fallos', fichero: '/fallos' },
  { ruta: '/progreso', fichero: '/progreso' },
] as const) {
  for (const { ancho, alto, etiqueta } of ANCHOS) {
    test(`${ruta} a ${ancho} px`, async ({ page }) => {
      await zonaSembrada();
      await retratar(page, ruta, fichero, ancho, alto, etiqueta);
    });
  }
}

for (const { ancho, alto, etiqueta } of ANCHOS) {
  test(`resultado a ${ancho} px`, async ({ page }) => {
    const { sesion } = await zonaSembrada();
    await retratar(page, `/resultado/${sesion}`, '/resultado', ancho, alto, etiqueta);
    // En el resultado la marca importa más que en el test: un fallo puede ser de la clave y no del
    // alumno. Si no sale en la captura, la captura no enseña lo que tiene que enseñar.
    await expect(page.getByText(MARCA_EN_REVISION).first()).toBeVisible();
  });
}

/** La zona del alumno con datos: se siembra una vez y se reutiliza en las tres capturas. */
let sembrado: Promise<{ sesion: string }> | null = null;

function zonaSembrada(): Promise<{ sesion: string }> {
  sembrado ??= sembrarUnTestTerminado();
  return sembrado;
}

/** Un test de cuatro preguntas en dos temas, contestado y terminado: devuelve su identificador. */
async function sembrarUnTestTerminado(): Promise<{ sesion: string }> {
  const cabeceras = { 'Content-Type': 'application/json', Origin: ORIGEN };
  const leer = async <T>(respuesta: Response): Promise<T> => {
    if (!respuesta.ok) {
      throw new Error(`la API respondió ${respuesta.status} al sembrar el test`);
    }
    return (await respuesta.json()) as T;
  };

  const oposiciones = await leer<{ id: string; active: boolean; active_convocation: { id: string } | null }[]>(
    await fetch(`${API}/api/v1/oppositions`),
  );
  const activa = oposiciones.find((oposicion) => oposicion.active);
  if (activa?.active_convocation == null) {
    throw new Error('no hay oposición activa con convocatoria: no se puede sembrar la zona');
  }

  const conjunto = await leer<{ id: string }>(
    await fetch(`${API}/api/v1/question-sets`, {
      method: 'POST',
      headers: cabeceras,
      body: JSON.stringify({
        title: `Capturas del cierre ${String(Date.now())}`,
        opposition_id: activa.id,
        set_type: 'private_bank',
        convocation_version_id: activa.active_convocation.id,
      }),
    }),
  );

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
    await fetch(`${API}/api/v1/question-sets/${conjunto.id}/parse`, {
      method: 'POST',
      headers: cabeceras,
      body: JSON.stringify({ kind: 'questions', text: texto }),
    }),
  );

  const claves = await leer<{ id: string }[]>(
    await fetch(`${API}/api/v1/question-sets/${conjunto.id}/answer-keys`),
  );
  const clave = claves[0];
  if (clave === undefined) {
    throw new Error('el conjunto no trae plantilla: sin ella no hay test que retratar');
  }
  await leer<unknown>(
    await fetch(`${API}/api/v1/question-sets/${conjunto.id}/answer-keys/${clave.id}/activate`, {
      method: 'POST',
      headers: cabeceras,
    }),
  );

  const programa = await leer<{ nodes: NodoPrograma[] }>(
    await fetch(`${API}/api/v1/convocations/${activa.active_convocation.id}/curriculum`),
  );
  const planos = aplanar(programa.nodes);
  const temas = ['IV.1', 'IV.10']
    .map((path) => planos.find((nodo) => nodo.path === path))
    .filter((nodo): nodo is NodoPrograma => nodo !== undefined);
  if (temas.length === 0) {
    throw new Error('el programa no tiene los temas de la captura');
  }
  const preguntas = await leer<{ questions: { id: string }[] }>(
    await fetch(`${API}/api/v1/questions?set_id=${conjunto.id}&limit=10`),
  );
  for (const [indice, pregunta] of preguntas.questions.entries()) {
    const tema = temas[indice % temas.length];
    if (tema !== undefined) {
      await leer<unknown>(
        await fetch(`${API}/api/v1/questions/${pregunta.id}/topics`, {
          method: 'POST',
          headers: cabeceras,
          body: JSON.stringify({ curriculum_node_id: tema.id }),
        }),
      );
    }
  }

  // La clave de este conjunto también queda en revisión: el resultado tiene que enseñar la marca.
  await marcarElConjuntoComoDudoso(conjunto.id);

  const sesion = await leer<{ id: string }>(
    await fetch(`${API}/api/v1/student/tests`, {
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
    await fetch(`${API}/api/v1/student/sessions/${sesion.id}/start`, {
      method: 'POST',
      headers: cabeceras,
    }),
  );
  // Una acierta y tres fallan: así el resultado tiene los dos desenlaces y el desglose por tema dice
  // algo. La `a` es la correcta en las cuatro.
  const cuantas = preguntas.questions.length;
  for (let posicion = 1; posicion <= cuantas; posicion += 1) {
    await leer<unknown>(
      await fetch(`${API}/api/v1/student/sessions/${sesion.id}/answers`, {
        method: 'POST',
        headers: cabeceras,
        body: JSON.stringify({
          position: posicion,
          chosen: [posicion === 1 ? 'a' : 'b'],
          elapsed_ms: 1200 * posicion,
        }),
      }),
    );
  }
  await leer<unknown>(
    await fetch(`${API}/api/v1/student/sessions/${sesion.id}/finish`, {
      method: 'POST',
      headers: cabeceras,
    }),
  );
  return { sesion: sesion.id };
}

/** Monta un test de tres preguntas de un tema y lo deja empezado: devuelve su identificador. */
async function montarTestDeAlumno(): Promise<string> {  const cabeceras = { 'Content-Type': 'application/json', Origin: ORIGEN };
  const leer = async <T>(respuesta: Response): Promise<T> => {
    if (!respuesta.ok) {
      throw new Error(`la API respondió ${respuesta.status} al montar el test`);
    }
    return (await respuesta.json()) as T;
  };

  const oposiciones = await leer<{ id: string; active: boolean; active_convocation: { id: string } | null }[]>(
    await fetch(`${API}/api/v1/oppositions`),
  );
  const activa = oposiciones.find((oposicion) => oposicion.active);
  if (activa?.active_convocation == null) {
    throw new Error('no hay oposición activa con convocatoria: no se puede montar el test');
  }

  const conjunto = await leer<{ id: string }>(
    await fetch(`${API}/api/v1/question-sets`, {
      method: 'POST',
      headers: cabeceras,
      body: JSON.stringify({
        title: `Capturas ${String(Date.now())}`,
        opposition_id: activa.id,
        set_type: 'private_bank',
        convocation_version_id: activa.active_convocation.id,
      }),
    }),
  );

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
    '',
  ].join('\n');
  await leer<unknown>(
    await fetch(`${API}/api/v1/question-sets/${conjunto.id}/parse`, {
      method: 'POST',
      headers: cabeceras,
      body: JSON.stringify({ kind: 'questions', text: texto }),
    }),
  );

  const claves = await leer<{ id: string }[]>(
    await fetch(`${API}/api/v1/question-sets/${conjunto.id}/answer-keys`),
  );
  const clave = claves[0];
  if (clave === undefined) {
    throw new Error('el conjunto no trae plantilla: sin ella no hay test que retratar');
  }
  await leer<unknown>(
    await fetch(`${API}/api/v1/question-sets/${conjunto.id}/answer-keys/${clave.id}/activate`, {
      method: 'POST',
      headers: cabeceras,
    }),
  );

  const programa = await leer<{ nodes: NodoPrograma[] }>(
    await fetch(`${API}/api/v1/convocations/${activa.active_convocation.id}/curriculum`),
  );
  const tema = aplanar(programa.nodes).find((nodo) => nodo.path === 'IV.1');
  if (tema === undefined) {
    throw new Error('el programa no tiene el tema IV.1: no se puede catalogar el test');
  }
  const preguntas = await leer<{ questions: { id: string }[] }>(
    await fetch(`${API}/api/v1/questions?set_id=${conjunto.id}&limit=10`),
  );
  for (const pregunta of preguntas.questions) {
    await leer<unknown>(
      await fetch(`${API}/api/v1/questions/${pregunta.id}/topics`, {
        method: 'POST',
        headers: cabeceras,
        body: JSON.stringify({ curriculum_node_id: tema.id }),
      }),
    );
  }

  // La clave del conjunto que se acaba de montar queda **en revisión**, que es lo que hay que ver en
  // la captura: la marca sale en el test en curso y en el resultado.
  await marcarElConjuntoComoDudoso(conjunto.id);

  const sesion = await leer<{ id: string }>(
    await fetch(`${API}/api/v1/student/tests`, {
      method: 'POST',
      headers: cabeceras,
      body: JSON.stringify({ nodes: ['IV.1'], count: 3, filter: 'all', feedback: 'immediate' }),
    }),
  );
  await leer<unknown>(
    await fetch(`${API}/api/v1/student/sessions/${sesion.id}/start`, {
      method: 'POST',
      headers: cabeceras,
    }),
  );
  // Y una respuesta marcada como dudosa, para que la captura enseñe la casilla ámbar y la corrección.
  await leer<unknown>(
    await fetch(`${API}/api/v1/student/sessions/${sesion.id}/answers`, {
      method: 'POST',
      headers: cabeceras,
      body: JSON.stringify({ position: 1, chosen: ['a'], elapsed_ms: 2400, confidence: 'low' }),
    }),
  );
  return sesion.id;
}

interface NodoPrograma {
  id: string;
  path: string;
  children?: NodoPrograma[];
}

function aplanar(nodos: NodoPrograma[]): NodoPrograma[] {
  return nodos.flatMap((nodo) => [nodo, ...aplanar(nodo.children ?? [])]);
}

/**
 * La bandeja de avisos, con un aviso de verdad dentro (F16).
 *
 * La captura de esta pantalla vacía no enseña nada: lo que hay que ver es un aviso con su tema, su
 * apartado, su motivo, su fecha y sus botones. El aviso **no se inventa**: se manda por la ruta del
 * alumno (`POST /student/topics/{codigo}/reports`), que es la que usaría el propietario estudiando, y
 * sobre los apuntes reales de un tema que ya los tenga escritos.
 *
 * Si en estos datos no hay ningún tema con apuntes —la suite del E2E arranca vacía— la captura sale
 * con el estado «ningún aviso esperando», que es lo que hay. Y es **idempotente**: si el aviso de la
 * captura ya está en la bandeja, no se manda otra vez.
 */
const AVISO_DE_LA_CAPTURA = 'El puerto de LDAPS del ejemplo no es 389: la captura dice 636.';

async function prepararAvisos(): Promise<void> {
  const cabeceras = { 'Content-Type': 'application/json', Origin: ORIGEN };
  const ya = await fetch(`${API}/api/v1/notes-reports?limit=200`);
  if (ya.ok) {
    const bandeja = (await ya.json()) as { reports: { reason: string }[] };
    if (bandeja.reports.some((aviso) => aviso.reason === AVISO_DE_LA_CAPTURA)) {
      return;
    }
  }

  for (const codigo of ['IV.7', 'I.1', 'I.2', 'I.6', 'I.4']) {
    const respuesta = await fetch(`${API}/api/v1/student/topics/${codigo}/notes`);
    if (!respuesta.ok) {
      continue;
    }
    const apuntes = (await respuesta.json()) as {
      sections: { key: string; title: string }[];
    };
    const apartado = apuntes.sections[0];
    if (apartado === undefined) {
      continue;
    }
    await fetch(`${API}/api/v1/student/topics/${codigo}/reports`, {
      method: 'POST',
      headers: cabeceras,
      body: JSON.stringify({ section_key: apartado.key, reason: AVISO_DE_LA_CAPTURA }),
    });
    return;
  }
}
