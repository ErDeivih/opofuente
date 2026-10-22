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

const SALIDA = process.env.OPOFUENTE_SCREENS_SALIDA
  ? path.resolve(process.env.OPOFUENTE_SCREENS_SALIDA)
  : path.resolve(process.cwd(), '..', '..', 'artifacts', 'screens');

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
  /* La bandeja de explicaciones (M1 de la fase 3): la cola que revisa el propietario, con el
     enunciado de cada pregunta y la cita literal del apartado en el que se apoya. */
  { ruta: '/admin/explicaciones', nombre: 'admin-explicaciones' },
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
  await page.screenshot({
    path: path.join(SALIDA, `${nombreFichero}.png`),
    fullPage: true,
  });

  const analisis = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
    .analyze();
  const { interfaz, todo } = await textosDeLaPantalla(page);

  guardarFila({
    ruta,
    ancho: `${ancho}×${alto}`,
    ms,
    errores,
    violaciones: analisis.violations.map((violacion) => violacion.id),
    prohibidas: revisarPantalla(interfaz, todo),
    fichero: nombreFichero,
  });
  // Se devuelven las violaciones para que la captura que exige **cero** pueda exigirlo de verdad:
  // el informe las apunta siempre, pero quien pide un cero lo comprueba aquí, no mirando el PNG.
  return analisis.violations.map((violacion) => violacion.id);
}

/**
 * Los dos textos de una pantalla, que son dos comprobaciones distintas.
 *
 * El de la **interfaz** (todo menos lo que va dentro de un contenedor `data-contenido`: enunciados,
 * opciones, apuntes, títulos de tema) y el de **toda** la pantalla. La jerga solo se busca en el
 * primero; las rutas del propietario y los nombres de otras oposiciones, en los dos.
 */
async function textosDeLaPantalla(page: Page): Promise<{ interfaz: string; todo: string }> {
  return page.evaluate(() => {
    const copia = document.body.cloneNode(true) as HTMLElement;
    for (const nodo of Array.from(copia.querySelectorAll('[data-contenido]'))) {
      nodo.remove();
    }
    return {
      interfaz: copia.innerText || copia.textContent || '',
      todo: document.body.innerText,
    };
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
 * La revisión de los apuntes (F24, §4.3 del objetivo) con los datos que haya, a los dos anchos.
 *
 * Es la captura que pide el entregable: **un tema publicado y un borrador con su motivo**. Se retrata
 * contra la copia de la base real (`F:\temp-opofuente\f24-datos`, pasada como
 * `OPOFUENTE_E2E_DATA_DIR`), y por eso la tabla sale con quince temas publicados y **los cuatro
 * borradores** (I.4, I.6, I.7 e I.8) con su cifra, y la ficha con **I.7**: un borrador de verdad, con
 * su motivo y sus diecinueve apartados. Con la base vacía de la suite las dos pantallas salen igual
 * —la tabla, con los temas sin apuntes— y la captura lo dice; no se inventa ninguna fila.
 *
 * Y no se limita a retratar: **comprueba** lo que el entregable exige de las capturas, para que la
 * evidencia no dependa de mirar el PNG.
 *
 * 1. **cero violaciones** de accesibilidad en las dos pantallas;
 * 2. **390 px exactos** de ancho de ventana en la captura de móvil (una captura de página completa más
 *    ancha que el viewport sería un desplazamiento horizontal);
 * 3. y que la tabla **enseña temas** (o lo dice): la captura no puede salir en blanco sin que se sepa.
 */
for (const { ancho, alto, etiqueta } of ANCHOS) {
  test(`la revisión de apuntes a ${ancho} px`, async ({ page }) => {
    const tabla = await retratar(page, '/admin/apuntes', '/admin/apuntes', ancho, alto, etiqueta);
    await expect(page.getByRole('heading', { level: 1, name: 'Apuntes' })).toBeVisible();
    await expect(page.getByRole('heading', { name: /Temas con apuntes/ })).toBeVisible();
    // Con los datos del propietario la tabla trae las dos cosas que pide el entregable: **temas
    // publicados** y **borradores**, y el borrador con su motivo. Se comprueba aquí (y no solo
    // mirando el PNG) para que la captura diga lo que tiene que decir; con la base vacía de la suite
    // las dos marcas no están y esta prueba se salta esas dos comprobaciones, no las finge.
    const publicados = page.getByText('Publicado', { exact: true });
    if ((await publicados.count()) > 0) {
      await expect(publicados.first()).toBeVisible();
      // El motivo **del borrador** (no el del primer tema de la tabla, que puede estar publicado y no
      // llevar cifra de cobertura): su primera razón es la del listón, con su porcentaje.
      const filaBorrador = page
        .getByRole('listitem')
        .filter({ hasText: 'En borrador' })
        .first();
      await expect(filaBorrador).toContainText('En borrador');
      await expect(filaBorrador.locator('.apuntes-revision__motivos')).toContainText(/%/);
      await expect(filaBorrador.locator('.apuntes-revision__cifras')).toBeVisible();
    }

    const ficha = await retratar(
      page,
      '/admin/apuntes/I.7',
      '/admin/apuntes/I.7',
      ancho,
      alto,
      etiqueta,
    );
    await expect(page.getByRole('heading', { level: 1, name: /I\.7/ })).toBeVisible();
    // La ficha del borrador: su motivo («Por qué está así») y su texto, apartado a apartado.
    await expect(page.getByRole('heading', { name: 'Por qué está así' })).toBeVisible();
    const motivos = page.locator('.apuntes-revision__motivos');
    await expect(motivos).toContainText(/%/);
    if ((await page.locator('.apartado__cuerpo').count()) > 0) {
      await expect(page.locator('.apartado__cuerpo').first()).toBeVisible();
      await expect(page.getByRole('button', { name: 'Los peores primero' })).toBeVisible();
    }

    expect(tabla, `axe en la tabla de apuntes: ${tabla.join(', ')}`).toEqual([]);
    expect(ficha, `axe en la ficha del borrador: ${ficha.join(', ')}`).toEqual([]);
    if (ancho === 390) {
      const medido = await page.evaluate(() => window.innerWidth);
      expect(medido, 'el ancho de la captura de móvil').toBe(390);
    }
  });
}

/**
 * La pantalla de **Exámenes** con un examen oficial de verdad (D10), a los dos anchos.
 *
 * La captura genérica de `/examenes` sale con la base de la suite, que nace sin exámenes oficiales:
 * no enseña ni la procedencia ni el número de preguntas, que es justo lo que hay que ver. Esta monta
 * un examen oficial **por las rutas de la API** —conjunto `official_exam`, procedencia `age`, sus
 * preguntas, su plantilla enlazada a una versión de documento y la clave activada— y luego comprueba
 * dos cosas sobre la pantalla ya cargada, para que la evidencia no dependa de mirar el PNG:
 *
 * 1. que la **procedencia** se lee («Administración General del Estado») y con su número de preguntas;
 * 2. que no hay **ninguna** violación de accesibilidad.
 *
 * La plantilla se enlaza con `node:sqlite` sobre la base **de la suite** (`.e2e-data`, que es suya y se
 * borra en cada corrida) porque activar la clave de un examen oficial exige la plantilla enlazada a un
 * documento y no hay ninguna ruta que invente un material sin pasar por la extracción entera: es el
 * mismo atajo, y por el mismo motivo, que usa la prueba de la ficha de pregunta.
 */
for (const { ancho, alto, etiqueta } of ANCHOS) {
  test(`examenes-oficiales a ${ancho} px`, async ({ page }) => {
    await montarExamenOficial();
    const violaciones = await retratar(
      page,
      '/examenes',
      '/examenes-oficiales',
      ancho,
      alto,
      etiqueta,
    );
    await expect(page.getByText('Administración General del Estado').first()).toBeVisible();
    // **85 y no 135** (F39, §3.7): el conjunto sembrado trae las 135 del cuestionario —120 ordinarias
    // y 15 de reserva—, y el examen sirve 85, porque la primera parte de TAI publica 80 + 5. La fila
    // decía la cifra del banco y el examen servía otra; ahora dice la del examen, que es lo que el
    // alumno se va a encontrar. Antes de F39 esta línea pedía «135 preguntas», y esa expectativa era
    // parte del defecto.
    await expect(page.getByText('85 preguntas').first()).toBeVisible();
    expect(violaciones, `axe en la pantalla de exámenes: ${violaciones.join(', ')}`).toEqual([]);
  });
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
 * Monta un **examen oficial** con datos de verdad, para que la captura de `/examenes` enseñe lo que
 * tiene que enseñar: la procedencia y el número de preguntas.
 *
 * Todo va por las rutas de la API (conjunto `official_exam` con `origin_scope: 'age'`, sus 135
 * preguntas con sus reservas —que la pantalla ya no enseña todas, ver la aserción—, su clave, la
 * activación) menos el enlace de la plantilla, que se escribe
 * con `node:sqlite` sobre `.e2e-data` por el mismo motivo que en la prueba de la ficha: activar la
 * clave de un examen oficial exige la plantilla enlazada a una versión de documento, y no hay ninguna
 * ruta que invente un material sin pasar por la extracción entera.
 */
async function montarExamenOficial(): Promise<string> {
  const cabeceras = { 'Content-Type': 'application/json', Origin: ORIGEN };
  const leer = async <T>(respuesta: Response): Promise<T> => {
    if (!respuesta.ok) {
      throw new Error(`la API respondió ${respuesta.status} al montar el examen oficial`);
    }
    return (await respuesta.json()) as T;
  };

  const oposiciones = await leer<
    { id: string; active: boolean; active_convocation: { id: string } | null }[]
  >(await fetch(`${API}/api/v1/oppositions`));
  const activa = oposiciones.find((oposicion) => oposicion.active);
  if (activa?.active_convocation == null) {
    throw new Error('no hay oposición activa con convocatoria: no se puede montar el examen');
  }

  const conjunto = await leer<{ id: string; title: string }>(
    await fetch(`${API}/api/v1/question-sets`, {
      method: 'POST',
      headers: cabeceras,
      body: JSON.stringify({
        title: `TAI ingreso libre 2025 · modelo A (examen oficial INAP) · capturas`,
        opposition_id: activa.id,
        set_type: 'official_exam',
        origin_scope: 'age',
        convocation_version_id: activa.active_convocation.id,
      }),
    }),
  );

  // 135 preguntas con la numeración oficial por secciones (80 + 5 + 20 + 5 + 20 + 5), reiniciando en
  // cada una y con las reservas marcadas: la pantalla enseña el número de preguntas de verdad, y la
  // numeración que se retrata es la del examen, no una inventada.
  const SECCIONES: readonly { preguntas: number; reservas: boolean }[] = [
    { preguntas: 80, reservas: false },
    { preguntas: 5, reservas: true },
    { preguntas: 20, reservas: false },
    { preguntas: 5, reservas: true },
    { preguntas: 20, reservas: false },
    { preguntas: 5, reservas: true },
  ];
  const lineas: string[] = [];
  let total = 0;
  for (const seccion of SECCIONES) {
    for (let numero = 1; numero <= seccion.preguntas; numero += 1) {
      total += 1;
      const marca = seccion.reservas ? '[R] ' : '';
      lineas.push(`${numero}. ${marca}El supuesto practico ${total} se resuelve en diez dias:`);
      for (const letra of ['a', 'b', 'c', 'd']) {
        lineas.push(`${letra}) Opcion ${letra.toUpperCase()} del supuesto ${total}`);
      }
      lineas.push('Respuesta correcta: a');
      lineas.push('');
    }
  }
  await leer<unknown>(
    await fetch(`${API}/api/v1/question-sets/${conjunto.id}/parse`, {
      method: 'POST',
      headers: cabeceras,
      body: JSON.stringify({ kind: 'questions', text: lineas.join('\n') }),
    }),
  );

  await leer<unknown>(
    await fetch(`${API}/api/v1/question-sets/${conjunto.id}`, {
      method: 'PATCH',
      headers: cabeceras,
      // La visibilidad va aparte de la creación, como en la aplicación: un conjunto nace `personal` y
      // se hace `public` a propósito. Sin esto el examen no sale en la lista del alumno, que es justo
      // la pantalla que se retrata.
      body: JSON.stringify({ distribution: 'public' }),
    }),
  );

  const claves = await leer<{ id: string }[]>(
    await fetch(`${API}/api/v1/question-sets/${conjunto.id}/answer-keys`),
  );
  const clave = claves[0];
  if (clave === undefined) {
    throw new Error('el examen no trae plantilla: sin ella no se puede activar');
  }

  // La plantilla en la biblioteca: artefacto, documento y versión, y la clave apuntando a ella. Es
  // preparación de la captura sobre la base **de la suite**, no un camino que exista en producción.
  const { DatabaseSync } = await import('node:sqlite');
  const base = new DatabaseSync(path.join(DATOS_DE_LA_SUITE, 'opofuente.sqlite3'));
  try {
    const sufijo = String(Date.now());
    const artefacto = `art-captura-${sufijo}`;
    const documento = `doc-captura-${sufijo}`;
    const version = `ver-captura-${sufijo}`;
    base
      .prepare(
        'INSERT INTO source_artifacts (id, sha256, size_bytes, media_type, storage_key, ' +
          'first_seen_at) VALUES (?, ?, 100, ?, ?, ?)',
      )
      .run(artefacto, sufijo.padEnd(64, '0').slice(0, 64), 'text/plain', 'k', new Date().toISOString());
    base
      .prepare(
        'INSERT INTO logical_documents (id, canonical_title, document_type, authority_tier, ' +
          'owner_scope, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
      )
      .run(
        documento,
        'Plantilla de respuestas del examen de las capturas',
        'answer_key',
        'A',
        'public',
        new Date().toISOString(),
        new Date().toISOString(),
      );
    base
      .prepare(
        'INSERT INTO document_versions (id, logical_document_id, artifact_id, version_label, ' +
          'status, approved_at, approved_by, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
      )
      .run(
        version,
        documento,
        artefacto,
        'definitiva',
        'accepted',
        new Date().toISOString(),
        'local',
        new Date().toISOString(),
      );
    base
      .prepare('UPDATE answer_key_versions SET source_document_version_id = ? WHERE id = ?')
      .run(version, clave.id);
  } finally {
    base.close();
  }

  await leer<unknown>(
    await fetch(`${API}/api/v1/question-sets/${conjunto.id}/answer-keys/${clave.id}/activate`, {
      method: 'POST',
      headers: cabeceras,
    }),
  );
  return conjunto.id;
}

/**
 * La ficha de pregunta (F20), con una pregunta **de verdad** y del caso de uso: una de un banco con la
 * respuesta correcta en duda.
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

/**
 * La pantalla de Tests (F22), que es la que faltaba de la zona del alumno.
 *
 * Se retrata **con datos**: el temario de la suite nace sin preguntas, y una captura de esta pantalla
 * con todo desactivado no enseña lo que hace. Se reutiliza la siembra de las capturas del cierre —dos
 * temas con dos preguntas cada uno— y se retratan las dos caras del caso de uso:
 *
 * 1. **el formulario tal como se abre** desde el menú, con lo que hay para preguntar y lo que ya se ha
 *    contestado en cada tema;
 * 2. **el formulario con lo que trae la dirección**, que es la mitad del asunto: el enlace del Temario
 *    (`?tema=IV.1`) y el atajo de Inicio (`?count=20`) tienen que llegar con la elección hecha. La
 *    aserción lo comprueba sobre la pantalla cargada, para que la evidencia no dependa de mirar el
 *    PNG: una casilla marcada en la captura de al lado no dice nada por sí sola.
 */
for (const { ancho, alto, etiqueta } of ANCHOS) {
  test(`tests a ${ancho} px`, async ({ page }) => {
    await zonaSembrada();
    await retratar(page, '/tests', '/tests', ancho, alto, etiqueta);
  });
}

for (const { ancho, alto, etiqueta } of ANCHOS) {
  test(`tests con un tema elegido a ${ancho} px`, async ({ page }) => {
    await zonaSembrada();
    await retratar(page, '/tests?tema=IV.1&count=20', '/tests-elegido', ancho, alto, etiqueta);
    await expect(page.getByRole('checkbox', { name: /^IV\.1\b/ })).toBeChecked();
    await expect(page.getByRole('radio', { name: /20 preguntas/ })).toBeChecked();
  });
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

/**
 * La plataforma desplegable (§8 y §9 del objetivo vivo): los textos legales y el aviso de cookies.
 *
 * **Este bloque solo corre con las banderas encendidas** (`OPOFUENTE_SCREENS_PLATAFORMA=1` y la API
 * arrancada con `OPOFUENTE_LEGAL_ENABLED=1`). Es a propósito: con las banderas apagadas estas rutas
 * no existen, y una captura de «No hay páginas legales» no enseña lo que hay que revisar. Se lanza
 * aparte, con su propia carpeta de salida (`OPOFUENTE_SCREENS_SALIDA`), para no pisar las capturas de
 * la configuración de siempre.
 *
 * Y no se limita a retratar: **comprueba** lo que el entregable exige, para que la evidencia no
 * dependa de que alguien mire el PNG.
 *
 * 1. **cero violaciones** de accesibilidad en las tres páginas y en el aviso —el aviso de cookies es
 *    donde más se falla, y por eso se comprueba y no se supone—;
 * 2. **cero palabras prohibidas**: los textos legales son interfaz, y la interfaz de la zona del
 *    alumno no puede llevar la jerga interna ni rutas del propietario;
 * 3. que el aviso está **de verdad** delante en Inicio, con sus dos botones.
 */
if (process.env.OPOFUENTE_SCREENS_PLATAFORMA === '1') {
  const PAGINAS: readonly { ruta: string; fichero: string; titulo: string }[] = [
    { ruta: '/legal/aviso-legal', fichero: '/legal-aviso-legal', titulo: 'Aviso legal' },
    { ruta: '/legal/privacidad', fichero: '/legal-privacidad', titulo: 'Privacidad' },
    { ruta: '/legal/cookies', fichero: '/legal-cookies', titulo: 'Cookies' },
  ];

  for (const { ancho, alto, etiqueta } of ANCHOS) {
    for (const { ruta, fichero, titulo } of PAGINAS) {
      test(`plataforma: ${fichero} a ${ancho} px`, async ({ page }) => {
        const violaciones = await retratar(page, ruta, fichero, ancho, alto, etiqueta);
        await expect(page.getByRole('heading', { level: 1, name: titulo })).toBeVisible();
        // El texto tiene que estar de verdad: una página legal vacía pasa axe y no sirve de nada.
        await expect(page.locator('.legal__parrafo').first()).toBeVisible();
        const textos = await textosDeLaPantalla(page);
        expect(
          revisarPantalla(textos.interfaz, textos.todo),
          `palabras prohibidas en ${ruta}`,
        ).toEqual([]);
        expect(violaciones, `axe en ${ruta}: ${violaciones.join(', ')}`).toEqual([]);
        if (ancho === 390) {
          const medido = await page.evaluate(() => window.innerWidth);
          expect(medido, 'el ancho de la captura de móvil').toBe(390);
        }
      });
    }

    test(`plataforma: el aviso de cookies a ${ancho} px`, async ({ page }) => {
      const violaciones = await retratar(page, '/', '/aviso-cookies', ancho, alto, etiqueta);
      const aviso = page.getByRole('region', { name: 'Cookies' });
      await expect(aviso).toBeVisible();
      // Aceptar y rechazar, los dos delante y con el mismo peso: es lo que el §9 exige.
      await expect(aviso.getByRole('button', { name: 'Aceptar' })).toBeVisible();
      await expect(aviso.getByRole('button', { name: 'Rechazar' })).toBeVisible();
      const textos = await textosDeLaPantalla(page);
      expect(
        revisarPantalla(textos.interfaz, textos.todo),
        'palabras prohibidas en el aviso',
      ).toEqual([]);
      expect(violaciones, `axe en el aviso: ${violaciones.join(', ')}`).toEqual([]);
    });
  }
}
