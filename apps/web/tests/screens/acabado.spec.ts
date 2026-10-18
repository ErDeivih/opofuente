/**
 * Las capturas del **acabado** (§2 del cierre del objetivo), a 1280 y a 390.
 *
 * Es la herramienta que pidió el propietario: revisa **capturas**, no descripciones. Retrata lo que él
 * vio en las suyas —el carril que no llega abajo, las notas con punto, el resultado que explica
 * demasiado, la hoja de respuestas que falta y las pantallas que esperan al servidor sin decirlo— y
 * **comprueba** lo que el entregable exige, para que la evidencia no dependa de que alguien mire el
 * PNG:
 *
 * 1. **cero violaciones** de accesibilidad (axe, A/AA) en cada pantalla y en cada ancho;
 * 2. **cero errores de consola**: una pantalla que carga con un error está avisando de algo;
 * 3. **ningún dato prohibido** en toda la pantalla (rutas del propietario, otras oposiciones, bancos);
 * 4. el **carril** llega a toda la altura de su columna en escritorio, y a 390 px se comporta como
 *    manda el diseño (barra inferior, sin desbordamiento horizontal);
 * 5. la nota del resultado es **una línea**, la explicación está **plegada** y la hoja de respuestas
 *    está **arriba**, con sus casillas.
 *
 * Las capturas de la siembra (`screens.spec.ts`) se quedan donde están y siguen siendo las de las
 * pruebas: estas van a su propia carpeta (`OPOFUENTE_SCREENS_SALIDA`), y el PNG de antes y el de
 * después se guardan en carpetas distintas para poder compararlos.
 *
 * Se captura contra los datos de la suite (`.e2e-data`), que **es suya y se borra en cada corrida**: la
 * siembra de un test terminado se monta por las rutas de la API, y los dos enlaces que no tienen ruta
 * —el apartado de los apuntes y su anclaje— se escriben con `node:sqlite`, que es el mismo atajo (y por
 * el mismo motivo) que usa la captura del examen oficial.
 */

import { mkdirSync } from 'node:fs';
import path from 'node:path';

import AxeBuilder from '@axe-core/playwright';
import { expect, test, type Page } from '@playwright/test';

import { datosEnElTexto, lenguajeInternoEnElTexto } from '../palabrasProhibidas';
import { escribirInforme, guardarFila, nombreDeFichero } from './informe';

const SALIDA = process.env.OPOFUENTE_SCREENS_SALIDA
  ? path.resolve(process.env.OPOFUENTE_SCREENS_SALIDA)
  : path.resolve(process.cwd(), '..', '..', 'artifacts', 'acabado');

const API = process.env.OPOFUENTE_API_URL ?? 'http://127.0.0.1:8765';
const ORIGEN = 'http://127.0.0.1:4173';
const DATOS_DE_LA_SUITE =
  process.env.OPOFUENTE_E2E_DATA_DIR ?? path.resolve(process.cwd(), '..', '..', '.e2e-data');

const ANCHOS: readonly { ancho: number; alto: number; etiqueta: string }[] = [
  { ancho: 1280, alto: 800, etiqueta: 'escritorio' },
  { ancho: 390, alto: 844, etiqueta: 'movil' },
];

interface Captura {
  violaciones: string[];
  errores: string[];
  prohibidos: string[];
}

/** Retrata una ruta en un ancho, guarda la fila del informe y devuelve lo que hay que exigirle. */
async function retratar(
  page: Page,
  ruta: string,
  fichero: string,
  ancho: number,
  alto: number,
  etiqueta: string,
): Promise<Captura> {
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
  await page.screenshot({ path: path.join(SALIDA, `${nombreFichero}.png`), fullPage: true });

  const analisis = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
    .analyze();

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
  const datos = datosEnElTexto(textos.todo);
  const jerga = lenguajeInternoEnElTexto(textos.interfaz);
  // Las palabras prohibidas se **informan** —es la regla del proyecto, y la herramienta de capturas no
  // es el juez—: van al informe con su contexto. Lo que sí se exige es lo que el encargo pide de una
  // captura: axe en cero y consola en cero.
  guardarFila({
    ruta,
    ancho: `${ancho}×${alto}`,
    ms,
    errores,
    violaciones: analisis.violations.map((violacion) => violacion.id),
    prohibidas: [...datos, ...jerga],
    fichero: nombreFichero,
  });

  return {
    violaciones: analisis.violations.map((violacion) => violacion.id),
    errores,
    prohibidos: datos.map((encontrado) => encontrado.palabra),
  };
}

/**
 * Exige lo que el entregable pide de **cualquier** captura de este guion.
 *
 * Las palabras prohibidas **no** se exigen en cero: el proyecto las informa, y en la interfaz de hoy
 * salen solas (el informe de las 24 capturas trae `Celador`, `bandeja`, `revision`… en Inicio). Lo que
 * se comprueba —y es lo que el encargo pide— es que los **textos nuevos** del acabado no añadan
 * ninguna: eso se mide en `tests/unit/acabadoTextos.test.ts`, sobre las frases, no sobre la pantalla
 * entera, que no es de este cambio.
 */
function exigirLimpias(captura: Captura, donde: string): void {
  expect(captura.violaciones, `axe en ${donde}: ${captura.violaciones.join(', ')}`).toEqual([]);
  expect(captura.errores, `consola en ${donde}: ${captura.errores.join(' | ')}`).toEqual([]);
  expect(captura.prohibidos, `datos del propietario en ${donde}`).toEqual([]);
}

// La siembra se hace una vez y se reutiliza en las cuatro pantallas.
let sembrado: Promise<string> | null = null;

function sesionSembrada(): Promise<string> {
  sembrado ??= sembrarUnTestTerminado();
  return sembrado;
}

/**
 * El informe se escribe **solo** cuando las capturas van a su propia carpeta.
 *
 * En la carpeta de siempre (`artifacts/screens`) las filas se dejan en `filas/` y las recoge el informe
 * de `screens.spec.ts`, que es el que las junta todas. En una carpeta propia —que es como se hacen las
 * de antes y las de después— nadie más va a escribir ese informe, así que se escribe aquí.
 */
test.afterAll(() => {
  if (process.env.OPOFUENTE_SCREENS_SALIDA) {
    escribirInforme();
  }
});

for (const { ancho, alto, etiqueta } of ANCHOS) {
  test(`acabado: inicio a ${ancho} px`, async ({ page }) => {
    await sesionSembrada();
    const captura = await retratar(page, '/', '/acabado-inicio', ancho, alto, etiqueta);
    exigirLimpias(captura, 'inicio');

    const medidas = await page.evaluate(() => {
      const carril = document.querySelector('.carril');
      const cuerpo = document.querySelector('.marco-alumno__cuerpo');
      return {
        carril: carril === null ? 0 : carril.getBoundingClientRect().height,
        cuerpo: cuerpo === null ? 0 : cuerpo.getBoundingClientRect().height,
        carrilVisible: carril !== null && getComputedStyle(carril).display !== 'none',
        barraVisible:
          document.querySelector('.barra-inferior') !== null &&
          getComputedStyle(document.querySelector('.barra-inferior') as Element).display !== 'none',
        anchoVentana: window.innerWidth,
        desborde: document.documentElement.scrollWidth - window.innerWidth,
      };
    });

    if (ancho === 1280) {
      // §2.1: el carril llega **a toda la altura** de su columna. Con `height: 100vh` a secas se
      // quedaba en los 800 px de la ventana y debajo se veía el gris.
      expect(medidas.carrilVisible, 'el carril se ve en escritorio').toBe(true);
      expect(
        medidas.carril,
        `el carril mide ${medidas.carril} px y su columna ${medidas.cuerpo} px`,
      ).toBeGreaterThanOrEqual(medidas.cuerpo - 1);
      expect(medidas.barraVisible, 'la barra inferior no se pinta en escritorio').toBe(false);
    } else {
      // §2.1 a 390 px: no hay carril, hay barra inferior, y la página no se desborda.
      expect(medidas.carrilVisible, 'el carril no se pinta en el móvil').toBe(false);
      expect(medidas.barraVisible, 'la barra inferior se pinta en el móvil').toBe(true);
      expect(medidas.anchoVentana, 'el ancho de la captura de móvil').toBe(390);
      expect(medidas.desborde, 'la página se desborda en horizontal').toBeLessThanOrEqual(0);
    }
  });
}

for (const { ancho, alto, etiqueta } of ANCHOS) {
  test(`acabado: resultado a ${ancho} px`, async ({ page }) => {
    const sesion = await sesionSembrada();
    const captura = await retratar(page, `/resultado/${sesion}`, '/acabado-resultado', ancho, alto, etiqueta);
    exigirLimpias(captura, 'resultado');

    // §2.3: **una línea**, con la cifra en español. El «sobre N» solo sale si la convocatoria publica
    // el máximo de la parte **y la sesión es un examen**: con la sesión sembrada —una práctica, que no
    // declara parte— no hay banda que enseñar, y desde F38 (§3.5) la línea dice los **netos con
    // penalización** en vez de la puntuación directa de un examen que no es. El pliegue sigue ahí con
    // otro nombre cuando no hay estimación que explicar.
    const linea = page.locator('.resultado__puntos');
    await expect(linea).toHaveCount(1);
    await expect(linea).toContainText(/^(Puntuación directa|Netos con penalización): \d+,\d{2}/);
    await expect(linea).not.toContainText(/\d\.\d/);

    // Y la explicación **no se borra**: se pliega.
    const boton = page.getByRole('button', { name: /por qué estimada|por qué 0,00|qué significa/i });
    await expect(boton).toHaveAttribute('aria-expanded', 'false');
    const aviso = page.locator('.resultado__aviso').first();
    await expect(aviso).not.toBeVisible();
    await boton.click();
    await expect(aviso).toBeVisible();

    // §2.4: la hoja de respuestas **arriba**, con la correcta en verde y la fallada en rojo.
    const hoja = page.getByRole('list', { name: /hoja de respuestas/i });
    await expect(hoja).toBeVisible();
    expect(await hoja.locator('[data-estado="correcta"]').count()).toBeGreaterThan(0);
    expect(await hoja.locator('[data-estado="fallada"]').count()).toBeGreaterThan(0);

    // Y cada fallada con su salida al **apartado** que la explica.
    const enlaces = page.getByRole('link', { name: /ver en apuntes/i });
    expect(await enlaces.count()).toBeGreaterThan(0);
    const primero = await enlaces.first().getAttribute('href');
    expect(primero, 'el enlace de los apuntes no lleva a un apartado').toMatch(/^\/temario\/[^#]+#.+/);
  });
}

for (const { ancho, alto, etiqueta } of ANCHOS) {
  for (const ruta of ['/temario', '/progreso'] as const) {
    test(`acabado: ${ruta} a ${ancho} px`, async ({ page }) => {
      await sesionSembrada();
      const captura = await retratar(page, ruta, `/acabado-${ruta.replace('/', '')}`, ancho, alto, etiqueta);
      exigirLimpias(captura, ruta);
      // §2.5: mientras el servidor tarda, la pantalla lo dice. La captura se hace con la respuesta ya
      // llegada; lo que se exige aquí es que la pantalla esté **cargada** y no a medias.
      await expect(page.locator('main')).toBeVisible();
    });
  }
}

/**
 * Un test terminado **de verdad**: cuatro preguntas de dos temas, una bien y tres mal, con la clave
 * activa y —lo que hace falta para «Ver en apuntes»— el apartado de los apuntes que contesta cada
 * pregunta y su anclaje.
 *
 * Todo va por las rutas de la API menos el apartado y el ancla, que no tienen ruta de escritura: los
 * escribe la corrida de apuntes del motor. Se escriben aquí, sobre la base **de la suite**, con las
 * mismas columnas que escribe el motor.
 */
async function sembrarUnTestTerminado(): Promise<string> {
  const cabeceras = { 'Content-Type': 'application/json', Origin: ORIGEN };
  const leer = async <T>(respuesta: Response): Promise<T> => {
    if (!respuesta.ok) {
      throw new Error(`la API respondió ${respuesta.status} al sembrar el acabado`);
    }
    return (await respuesta.json()) as T;
  };

  const oposiciones = await leer<
    { id: string; active: boolean; active_convocation: { id: string } | null }[]
  >(await fetch(`${API}/api/v1/oppositions`));
  const activa = oposiciones.find((oposicion) => oposicion.active);
  if (activa?.active_convocation == null) {
    throw new Error('no hay oposición activa con convocatoria: no se puede sembrar el acabado');
  }

  const conjunto = await leer<{ id: string }>(
    await fetch(`${API}/api/v1/question-sets`, {
      method: 'POST',
      headers: cabeceras,
      body: JSON.stringify({
        title: `Acabado de la interfaz ${String(Date.now())}`,
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
  const temas = ['IV.1', 'IV.7']
    .map((codigo) => planos.find((nodo) => nodo.path === codigo))
    .filter((nodo): nodo is NodoPrograma => nodo !== undefined);
  if (temas.length === 0) {
    throw new Error('el programa no tiene los temas de la captura');
  }
  const preguntas = await leer<{ questions: { id: string }[] }>(
    await fetch(`${API}/api/v1/questions?set_id=${conjunto.id}&limit=10`),
  );
  for (const [indice, pregunta] of preguntas.questions.entries()) {
    const tema = temas[indice % temas.length]!;
    await leer<unknown>(
      await fetch(`${API}/api/v1/questions/${pregunta.id}/topics`, {
        method: 'POST',
        headers: cabeceras,
        body: JSON.stringify({ curriculum_node_id: tema.id }),
      }),
    );
  }

  await sembrarApartadosYAnclas(temas, preguntas.questions.map((pregunta) => pregunta.id));

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
  // Una acierta y tres fallan: así el resultado tiene los dos desenlaces y la hoja las dos casillas.
  const cuantas = preguntas.questions.length;
  for (let posicion = 1; posicion <= cuantas; posicion += 1) {
    await leer<unknown>(
      await fetch(`${API}/api/v1/student/sessions/${sesion.id}/answers`, {
        method: 'POST',
        headers: cabeceras,
        body: JSON.stringify({
          position: posicion,
          chosen: [posicion === 2 ? 'a' : 'b'],
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
 * Los apartados de los apuntes y el ancla de cada pregunta, escritos con `node:sqlite`.
 *
 * Es la parte que no tiene ruta: el apartado lo redacta la corrida de apuntes (`topic_note_sections`)
 * y el ancla la escribe la comprobación del motor (`question_note_anchors`). La captura necesita las
 * dos para poder enseñar «Ver en apuntes» yendo al párrafo, así que se escriben aquí, sobre la base
 * **de la suite**, con las columnas y los `CHECK` que declara el esquema.
 */
async function sembrarApartadosYAnclas(
  temas: readonly NodoPrograma[],
  preguntas: readonly string[],
): Promise<void> {
  const { DatabaseSync } = await import('node:sqlite');
  const base = new DatabaseSync(path.join(DATOS_DE_LA_SUITE, 'opofuente.sqlite3'));
  const ahora = new Date().toISOString();
  try {
    const anclas = ['el-modelo-tcp-ip-y-sus-capas', 'la-sede-electronica', 'el-ens-y-su-norma'];
    const secciones = new Map<string, string>();
    temas.forEach((tema, indice) => {
      const ancla = anclas[indice] ?? `apartado-${String(indice)}`;
      const id = `sec-captura-${tema.path}-${String(Date.now())}`;
      secciones.set(tema.id, ancla);
      base
        .prepare(
          // `INSERT OR REPLACE` y no `INSERT` a secas: la captura se siembra una vez por proceso, y
          // Playwright **reinicia el worker** cuando una prueba falla, así que la siembra vuelve a
          // correr contra la misma base. Un `INSERT` chocaba con la clave única del apartado (nodo +
          // clave de subsección) y el segundo intento moría con una excepción que no era del código.
          'INSERT OR REPLACE INTO topic_note_sections (id, curriculum_node_id, subsection_key, ' +
            'epigraph_code, title, anchor, position, body_markdown, status, created_at, updated_at) ' +
            'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
        )
        .run(
          id,
          tema.id,
          ancla,
          `${tema.path}.1`,
          `El apartado que explica ${tema.path}`,
          ancla,
          1,
          'Aqui se explica, con sus palabras, lo que la pregunta pregunta.',
          'reviewed',
          ahora,
          ahora,
        );
      void id;
    });

    preguntas.forEach((pregunta, indice) => {
      const tema = temas[indice % temas.length]!;
      const ancla = secciones.get(tema.id)!;
      base
        .prepare(
          'INSERT OR REPLACE INTO question_note_anchors (id, question_version_id, ' +
            'curriculum_node_id, section_id, anchor, group_signature, quoted_sentence, ' +
            'answer_letter, expected_letters, key_status, result, note, attempts, text_sha256, ' +
            'checked_at) VALUES (?, ?, ?, NULL, ?, ?, ?, NULL, NULL, ?, ?, NULL, ?, NULL, ?)',
        )
        .run(
          `anc-captura-${String(indice)}-${String(Date.now())}`,
          pregunta,
          tema.id,
          ancla,
          `grupo-${String(indice)}`,
          'La frase que los apuntes dan y que el motor verificó contra el texto.',
          'active',
          'covered',
          1,
          ahora,
        );
    });
  } finally {
    base.close();
  }
}
