/**
 * La revisión de los apuntes, de punta a punta (F24, §4.3 del objetivo).
 *
 * Lo que se prueba: **un borrador se ve con su motivo y su cifra, se lee entero dentro del panel y se
 * decide desde él**. Por pantalla (la tabla con el estado de cada tema, la ficha con los apartados) y
 * por ruta (la decisión, su nota y su **evento de auditoría**), y además:
 *
 * - **aprobar publica**: el tema pasa a estar publicado y el alumno lo ve publicado en su zona;
 * - **rechazar exige motivo**, y con motivo se guarda y se lee al volver a la ficha;
 * - **la decisión sobrevive a una corrida del motor**: el motor vuelve a escribir sus comprobaciones y
 *   su bandeja y la decisión del propietario sigue donde estaba;
 * - y la pantalla **cabe en 390 px** y **no tiene ninguna violación** de accesibilidad.
 *
 * Sobre los apuntes de la prueba: la suite arranca con la base **vacía**, y los apuntes los escribe el
 * motor de apuntes desde las preguntas del tema, que cuesta llamadas al modelo. Aquí se escriben
 * **directamente en la base de la suite** (`.e2e-data`, que se borra al empezar cada pasada y nunca es
 * la del propietario) porque **no hay ruta que los escriba**: los escribe el motor. Es el mismo camino
 * que usan la prueba de los avisos y la de la bandeja del motor, y por el mismo motivo. Nada de esto
 * toca datos reales, y la prueba **retira lo suyo** al terminar.
 *
 * La **firma del grupo** de la comprobación se reconstruye aquí a partir del enunciado y de las
 * opciones que ha guardado la importación, con la misma normalización que el motor
 * (`domain/rag.normalise` + `firma_de_grupo`): sin la firma exacta, la comprobación guardada no cuenta
 * y el tema mediría 0 de 0. La prueba lo comprueba sola: si la firma estuviera mal, la cobertura que
 * espera (1 de 1) no saldría.
 */

import { createHash } from 'node:crypto';
import { DatabaseSync } from 'node:sqlite';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import AxeBuilder from '@axe-core/playwright';
import { expect, test, type APIRequestContext, type Locator, type Page } from '@playwright/test';

import { lenguajeInternoEnElTexto } from '../palabrasProhibidas';

const AQUI = path.dirname(fileURLToPath(import.meta.url));
// `…/apps/web/tests/e2e` → la raíz del repositorio, que es donde vive `.e2e-data`.
const REPOSITORIO = path.resolve(AQUI, '..', '..', '..', '..');

/** La API y el origen de las escrituras, como en el resto de la suite. */
const API = 'http://127.0.0.1:8765/api/v1';
const ORIGEN = 'http://127.0.0.1:4173';
const CABECERAS = { Origin: ORIGEN };

/** El directorio de datos de la suite: el suyo, el de siempre (`playwright.config.ts`). */
const DATOS = process.env.OPOFUENTE_E2E_DATA_DIR ?? path.join(REPOSITORIO, '.e2e-data');
const BASE = path.join(DATOS, 'opofuente.sqlite3');

/** El tema de la prueba y su apartado: es texto de prueba, no del propietario. */
const TEMA = 'IV.1';
const APARTADO = 'powershell-y-cmdlet';
const EPIGRAFE = 'IV.1.1';
const TITULO_APARTADO = 'PowerShell y los cmdlet';
const CUERPO =
  '## PowerShell y los cmdlet\n\nUn cmdlet de PowerShell es un comando del sistema de ' +
  'administración de Windows.';
const ENUNCIADO = '¿Qué cmdlet de PowerShell muestra la información del equipo?';
const NOTA = 'leído el 14 de octubre: el texto contesta lo que se pregunta';
const NOTA_RECHAZO = 'faltan preguntas por contestar: no se publica todavía';

/** Los identificadores de lo que siembra la prueba: fijos, para poder retirarlo al terminar. */
const SECCION = 'seccion-de-la-prueba-f24';
const ANCLA = 'ancla-de-la-prueba-f24';
const INCIDENCIA = 'incidencia-de-la-prueba-f24';

interface NodoPrograma {
  id: string;
  node_type: string;
  path: string;
  children?: NodoPrograma[];
}

interface Pregunta {
  id: string;
  stem: string;
  options: { stable_key: string; text: string; position: number }[];
}

function aplanar(nodos: readonly NodoPrograma[]): NodoPrograma[] {
  return nodos.flatMap((nodo) => [nodo, ...aplanar(nodo.children ?? [])]);
}

/** La fecha como la escribe el motor: UTC sin zona y con espacio, no con la `T` del navegador. */
function ahoraComoLaEscribeElMotor(): string {
  return new Date().toISOString().replace('T', ' ').replace('Z', '');
}

/**
 * La normalización del motor (`domain/rag.normalise`): sin acentos, sin signos y en minúsculas.
 *
 * `unicodedata.normalize("NFKD", …)` y luego quitar los diacríticos es lo que hace Python; aquí se
 * hace lo mismo con `normalize('NFKD')` y el rango de las marcas combinantes.
 */
function normalise(texto: string): string {
  return texto
    .toLowerCase()
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^\w\s]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

/**
 * La firma de un grupo de preguntas, igual que `domain/topic_notes.firma_de_grupo`.
 *
 * Ojo con el último paso, que es el que se me escapó la primera vez: la firma **no es el texto**
 * normalizado, es su `sha256` en hexadecimal **cortado a 32 caracteres**. Sin el corte y sin el hash, la
 * comprobación sembrada no casa con ninguna firma del motor, no cuenta para la cobertura y el tema
 * mediría 0 de 0. La prueba lo detecta sola: espera «1/1».
 */
function firmaDeGrupo(stem: string, opciones: readonly { stable_key: string; text: string }[]): string {
  const cuerpo =
    normalise(stem) + ' || ' + opciones.map((o) => `${o.stable_key}: ${normalise(o.text)}`).join(' | ');
  return createHash('sha256').update(cuerpo, 'utf8').digest('hex').slice(0, 32);
}

/**
 * La fila del tema en la tabla del panel.
 *
 * El filtro es por **texto anclado al principio**: `IV.1` a secas también casa con `IV.10` e `IV.11`
 * (la tabla enseña los 33 temas del programa), y aquí hay que coger la fila de uno solo.
 */
function filaDelTema(page: Page, codigo: string): Locator {
  return page
    .getByRole('listitem')
    .filter({ hasText: new RegExp(`^${codigo.replace('.', '\\.')}\\b`) })
    .first();
}

/** Un banco de la prueba con una pregunta, su clave activa y la pregunta catalogada en el tema. */
async function bancoDeLaPrueba(request: APIRequestContext, temaId: string): Promise<Pregunta> {
  const oposiciones = (await (await request.get(`${API}/oppositions`)).json()) as {
    id: string;
    active: boolean;
    active_convocation: { id: string } | null;
  }[];
  const activa = oposiciones.find((oposicion) => oposicion.active);
  const conjunto = (await (
    await request.post(`${API}/question-sets`, {
      headers: CABECERAS,
      data: {
        title: `Banco de la revisión de apuntes ${String(Date.now())}`,
        opposition_id: activa?.id,
        set_type: 'private_bank',
        convocation_version_id: activa?.active_convocation?.id,
      },
    })
  ).json()) as { id: string };

  await request.post(`${API}/question-sets/${conjunto.id}/parse`, {
    headers: CABECERAS,
    data: {
      kind: 'questions',
      text: [
        `1. ${ENUNCIADO}`,
        'a) Get-ComputerInfo',
        'b) Get-Date',
        'Respuesta correcta: a',
        '',
      ].join('\n'),
    },
  });

  const listas = (await (
    await request.get(`${API}/question-sets/${conjunto.id}/answer-keys`)
  ).json()) as { id: string }[];
  await request.post(
    `${API}/question-sets/${conjunto.id}/answer-keys/${listas[0]?.id ?? ''}/activate`,
    { headers: CABECERAS },
  );

  const listado = (await (
    await request.get(`${API}/questions?set_id=${conjunto.id}`)
  ).json()) as { questions: Pregunta[] };
  const pregunta = listado.questions[0];
  if (pregunta === undefined) {
    throw new Error('el banco de la prueba debería traer una pregunta');
  }
  await request.post(`${API}/questions/${pregunta.id}/topics`, {
    headers: CABECERAS,
    data: { curriculum_node_id: temaId },
  });
  return pregunta;
}

/** El tema del programa, por su código legible, con el identificador de su nodo. */
async function temaDelPrograma(request: APIRequestContext, codigo: string): Promise<NodoPrograma> {
  const oposiciones = (await (await request.get(`${API}/oppositions`)).json()) as {
    active: boolean;
    active_convocation: { id: string } | null;
  }[];
  const activa = oposiciones.find((oposicion) => oposicion.active);
  const programa = (await (
    await request.get(`${API}/convocations/${activa?.active_convocation?.id ?? ''}/curriculum`)
  ).json()) as { nodes: NodoPrograma[] };
  const tema = aplanar(programa.nodes).find(
    (nodo) => nodo.node_type === 'topic' && nodo.path === codigo,
  );
  if (tema === undefined) {
    throw new Error(`el programa no tiene el tema ${codigo}`);
  }
  return tema;
}

/**
 * Escribe los apuntes del tema **en la base de la suite**: el apartado y la comprobación que lo cubre.
 *
 * `text_sha256` se deja nulo a propósito: la huella solo sirve para saber si la comprobación sigue
 * valiendo para el texto de hoy, y lo que se mide aquí es la cobertura, que no depende de ella.
 */
function sembrarApuntes(nodeId: string, pregunta: Pregunta): void {
  const db = new DatabaseSync(BASE);
  try {
    const ahora = ahoraComoLaEscribeElMotor();
    db.prepare(
      'INSERT OR REPLACE INTO topic_note_sections ' +
        '(id, curriculum_node_id, subsection_key, epigraph_code, title, anchor, position, ' +
        'body_markdown, status, needs_review_reason, model, prompt_template_version, ' +
        'created_at, updated_at) ' +
        'VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, NULL, ?, ?, ?, ?)',
    ).run(
      SECCION,
      nodeId,
      APARTADO,
      EPIGRAFE,
      TITULO_APARTADO,
      APARTADO,
      CUERPO,
      'reviewed',
      'modelo-de-la-prueba',
      'apuntes-2',
      ahora,
      ahora,
    );
    db.prepare(
      'INSERT OR REPLACE INTO question_note_anchors ' +
        '(id, question_version_id, curriculum_node_id, section_id, anchor, group_signature, ' +
        'quoted_sentence, answer_letter, expected_letters, key_status, result, note, attempts, ' +
        'text_sha256, checked_at) ' +
        'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, 1, NULL, ?)',
    ).run(
      ANCLA,
      pregunta.id,
      nodeId,
      SECCION,
      APARTADO,
      firmaDeGrupo(pregunta.stem, pregunta.options),
      'Un cmdlet de PowerShell es un comando del sistema de administración de Windows',
      'a',
      '["a"]',
      'active',
      'covered',
      ahora,
    );
  } finally {
    db.close();
  }
}

/**
 * Una corrida del motor sobre el tema: vuelve a escribir su comprobación (ahora dudosa) y deja una
 * incidencia en su bandeja. Es lo que la prueba usa para comprobar que la decisión **sobrevive**.
 */
function correrElMotor(nodeId: string, pregunta: Pregunta): void {
  const db = new DatabaseSync(BASE);
  try {
    const ahora = ahoraComoLaEscribeElMotor();
    db.prepare(
      'UPDATE question_note_anchors SET result = ?, note = ?, attempts = 2 WHERE id = ?',
    ).run('doubtful', 'letra_no_coincide', ANCLA);
    db.prepare(
      'INSERT OR REPLACE INTO notes_incidents ' +
        '(id, curriculum_node_id, question_version_id, group_signature, category, coverage, ' +
        'reason, section_key, anchor, phrase, detail, attempts, created_at, status, ' +
        'resolution_note, reviewed_at) ' +
        "VALUES (?, ?, ?, ?, 'clave_sospechosa', 'conflict', 'letra_no_coincide', ?, ?, NULL, " +
        "'la corrida nueva vuelve a señalar lo mismo', 1, ?, 'open', NULL, NULL)",
    ).run(
      INCIDENCIA,
      nodeId,
      pregunta.id,
      firmaDeGrupo(pregunta.stem, pregunta.options),
      APARTADO,
      APARTADO,
      ahora,
    );
  } finally {
    db.close();
  }
}

/**
 * Retira **lo de la prueba**: su decisión, sus apuntes, su comprobación, su incidencia y —lo que más
 * importa— el **catálogo de su pregunta en el tema**.
 *
 * El catálogo se retira porque la muestra de un **diagnóstico** la compone el servidor con las preguntas
 * que tienen tema: dejarlo puesto cambiaría el diagnóstico de otra prueba de la suite. Se descubrió así
 * (la prueba de E2E-06 esperaba «0 de 6 respondidas» y con mis preguntas catalogadas eran más), y por
 * eso esta limpieza lleva su comentario.
 *
 * Lo que **no** se retira es el banco de preguntas: la suite entera nace vacía en cada corrida y los
 * bancos se crean por las rutas de la API, como en la prueba de la ficha de pregunta.
 */
function retirarLoDeLaPrueba(nodeId: string, preguntaId: string): void {
  const db = new DatabaseSync(BASE);
  try {
    db.prepare('DELETE FROM topic_notes_reviews WHERE curriculum_node_id = ?').run(nodeId);
    db.prepare('DELETE FROM question_note_anchors WHERE id = ?').run(ANCLA);
    db.prepare('DELETE FROM notes_incidents WHERE id = ?').run(INCIDENCIA);
    db.prepare('DELETE FROM topic_note_sections WHERE id = ?').run(SECCION);
    db.prepare('DELETE FROM dossier_snapshots WHERE curriculum_node_id = ?').run(nodeId);
    db.prepare(
      "DELETE FROM curriculum_mappings WHERE subject_type = 'question_version' AND subject_id = ?",
    ).run(preguntaId);
  } finally {
    db.close();
  }
}

/**
 * Lo que quedó en la base sobre el tema: su decisión, su versión y su evento de auditoría.
 *
 * Los eventos se cuentan **con una base tomada antes de decidir** y no en absoluto: el registro de
 * auditoría es de solo añadir (no se borra, tampoco desde una prueba) y otra prueba de esta misma
 * suite puede haber dejado el suyo sobre el mismo tema. Contar la diferencia es lo que se quiere saber
 * —«mi decisión dejó su evento»— sin depender del orden en el que corran las pruebas.
 */
function loQueQuedo(nodeId: string): {
  decisiones: number;
  versiones: number;
  eventos: number;
} {
  const db = new DatabaseSync(BASE);
  try {
    const cuenta = (sql: string): number =>
      Number((db.prepare(sql).get(nodeId) as { total?: number } | undefined)?.total ?? 0);
    return {
      decisiones: cuenta(
        'SELECT count(*) AS total FROM topic_notes_reviews WHERE curriculum_node_id = ?',
      ),
      versiones: cuenta(
        'SELECT count(*) AS total FROM dossier_snapshots WHERE curriculum_node_id = ?',
      ),
      eventos: cuenta(
        "SELECT count(*) AS total FROM audit_events WHERE action = 'notes.topic_reviewed' " +
          'AND object_id = ?',
      ),
    };
  } finally {
    db.close();
  }
}

/** La pantalla pasa axe sin violaciones automatizables. */
async function sinViolaciones(page: Page, donde: string): Promise<void> {
  const resultados = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
    .analyze();
  expect(resultados.violations, `axe en ${donde}`).toEqual([]);
}

/** La interfaz no enseña la jerga de la trastienda (lo que va marcado como contenido no cuenta). */
async function sinJerga(page: Page): Promise<void> {
  const interfaz = await page.evaluate(() => {
    const copia = document.body.cloneNode(true) as HTMLElement;
    for (const nodo of Array.from(copia.querySelectorAll('[data-contenido]'))) {
      nodo.remove();
    }
    return copia.innerText || copia.textContent || '';
  });
  expect(lenguajeInternoEnElTexto(interfaz).map((encontrado) => encontrado.palabra)).toEqual([]);
}

test('E2E-F24 la tabla enseña el estado de cada tema y el motivo del borrador con su cifra', async ({
  page,
  request,
}) => {
  const tema = await temaDelPrograma(request, TEMA);
  const pregunta = await bancoDeLaPrueba(request, tema.id);
  sembrarApuntes(tema.id, pregunta);
  try {
    await page.goto('/admin/apuntes');

    await expect(page.getByRole('heading', { level: 1, name: 'Apuntes' })).toBeVisible();
    // El contador de la cabecera: hay un borrador esperando decisión.
    await expect(page.locator('.avisos__resumen')).toContainText('esperan tu decisión');

    const fila = filaDelTema(page, TEMA);
    await expect(fila).toContainText('En borrador');
    // El motivo, con su cifra: el tema cumple las dos puertas y no está publicado.
    await expect(fila).toContainText('1/1 = 100.0 %');
    await expect(fila).toContainText('Cumple las dos puertas');
    await expect(fila).toContainText('Aprobarlo la publica');
    await expect(fila).toContainText('Nadie ha revisado este tema todavía');

    // Y sin jerga de la trastienda en la interfaz (el motivo va marcado como contenido).
    await sinJerga(page);
    await sinViolaciones(page, '/admin/apuntes');
  } finally {
    retirarLoDeLaPrueba(tema.id, pregunta.id);
  }
});

test('E2E-F24 un borrador se lee entero en el panel y se aprueba: aprobar publica', async ({
  page,
  request,
}) => {
  const tema = await temaDelPrograma(request, TEMA);
  const pregunta = await bancoDeLaPrueba(request, tema.id);
  sembrarApuntes(tema.id, pregunta);
  // La base del registro de auditoría, **antes** de decidir: lo que se comprueba es que mi decisión
  // deja su evento, no cuántos hay en total (los de otra prueba de la suite no se borran).
  const eventosAntes = loQueQuedo(tema.id).eventos;
  try {
    // --- 1. La ficha: el texto, apartado a apartado, como lo lee el alumno --------------------
    await page.goto(`/admin/apuntes/${TEMA}`);
    await expect(page.getByRole('heading', { level: 1, name: new RegExp(TEMA) })).toBeVisible();
    const cuerpoEnElPanel = page.locator('.apartado__cuerpo').first();
    await expect(cuerpoEnElPanel).toContainText('PowerShell y los cmdlet');
    await expect(cuerpoEnElPanel).toContainText(
      'Un cmdlet de PowerShell es un comando del sistema de administración',
    );
    // El **mismo** texto que sirve la zona del alumno: es la promesa de esta ficha.
    const enElPanel = await cuerpoEnElPanel.innerText();
    await page.goto(`/temario/${TEMA}`);
    const enLaZonaDelAlumno = await page.locator('.apartado__cuerpo').first().innerText();
    expect(enElPanel.trim()).toBe(enLaZonaDelAlumno.trim());

    // --- 2. Aprobar desde el panel ------------------------------------------------------------
    await page.goto(`/admin/apuntes/${TEMA}`);
    // El localizador de la nota va **sin distinguir mayúsculas**: la etiqueta empieza por «Qué» y un
    // `getByLabel(/qué …/)` de Playwright es sensible a mayúsculas y no la encuentra (fue un fallo real
    // de esta prueba, que tardó 30 s en rendirse en vez de decir por qué).
    await page.getByLabel(/has decidido/i).fill(NOTA);
    await page.getByRole('button', { name: 'Aprobar los apuntes' }).click();
    await expect(page.locator('.apuntes-revision__resultado')).toContainText('publicado');

    // --- 3. Y el alumno lo ve publicado -------------------------------------------------------
    await page.goto(`/temario/${TEMA}`);
    await expect(page.getByText('Versión generada · en revisión')).toBeVisible();

    // --- 4. La decisión, su nota y su evento han quedado escritos ------------------------------
    const quedó = loQueQuedo(tema.id);
    expect(quedó.decisiones).toBe(1);
    expect(quedó.versiones).toBeGreaterThan(0);
    expect(quedó.eventos - eventosAntes).toBe(1);

    // La ficha lo cuenta al volver.
    await page.goto(`/admin/apuntes/${TEMA}`);
    await expect(page.locator('.apuntes-revision__decision')).toContainText(NOTA);
    await expect(page.locator('.apuntes-revision__estado')).toContainText('Publicado');
  } finally {
    retirarLoDeLaPrueba(tema.id, pregunta.id);
  }
});

test('E2E-F24 rechazar exige motivo y la decisión sobrevive a una corrida del motor', async ({
  page,
  request,
}) => {
  const tema = await temaDelPrograma(request, TEMA);
  const pregunta = await bancoDeLaPrueba(request, tema.id);
  sembrarApuntes(tema.id, pregunta);
  // La base del registro de auditoría, antes de nada: el rechazo sin motivo **no** puede dejar evento,
  // y el que sí lleva motivo deja **uno**; contar la diferencia es lo que se mide (ver `loQueQuedo`).
  const eventosAntes = loQueQuedo(tema.id).eventos;
  try {
    await page.goto(`/admin/apuntes/${TEMA}`);

    // Sin motivo no se puede rechazar: la pantalla no deja, y la API tampoco.
    const rechazar = page.getByRole('button', { name: 'Rechazar con este motivo' });
    await expect(rechazar).toBeDisabled();
    const sinMotivo = await request.post(`${API}/notes-review/${TEMA}/decision`, {
      headers: CABECERAS,
      data: { decision: 'rejected' },
    });
    expect(sinMotivo.status()).toBe(422);
    expect(loQueQuedo(tema.id).decisiones).toBe(0);
    // Un rechazo rechazado por el servidor no escribe **nada**: ni decisión ni evento.
    expect(loQueQuedo(tema.id).eventos - eventosAntes).toBe(0);

    // Con motivo, se guarda y se lee al volver.
    await page.getByLabel(/has decidido/i).fill(NOTA_RECHAZO);
    await expect(rechazar).toBeEnabled();
    await rechazar.click();
    await expect(page.locator('.apuntes-revision__resultado')).toContainText('no se ha publicado');

    // **Una corrida del motor**: reescribe su comprobación y deja una incidencia en su bandeja.
    correrElMotor(tema.id, pregunta);

    await page.reload();
    // La decisión sigue donde estaba, con su nota, y el motivo de datos se ha refrescado.
    await expect(page.locator('.apuntes-revision__decision')).toContainText(NOTA_RECHAZO);
    await expect(page.locator('.apuntes-revision__motivos')).toContainText('1 incidencia(s)');

    // Y en la tabla del panel también.
    await page.goto('/admin/apuntes');
    const fila = filaDelTema(page, TEMA);
    await expect(fila).toContainText('Rechazado');
    await expect(fila).toContainText(NOTA_RECHAZO);

    const quedó = loQueQuedo(tema.id);
    expect(quedó.decisiones).toBe(1);
    expect(quedó.versiones).toBe(0);
    expect(quedó.eventos - eventosAntes).toBe(1);
  } finally {
    retirarLoDeLaPrueba(tema.id, pregunta.id);
  }
});

test('E2E-F24 accesibilidad y móvil: la ficha de un borrador a 390 px, sin violaciones', async ({
  page,
  request,
}) => {
  const tema = await temaDelPrograma(request, TEMA);
  const pregunta = await bancoDeLaPrueba(request, tema.id);
  sembrarApuntes(tema.id, pregunta);
  try {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(`/admin/apuntes/${TEMA}`);
    await expect(page.getByRole('heading', { level: 1, name: new RegExp(TEMA) })).toBeVisible();

    // La pantalla **cabe**: el ancho del documento no pasa del viewport (390 px exactos).
    const ancho = await page.evaluate(() => document.documentElement.scrollWidth);
    expect(ancho).toBeLessThanOrEqual(391);
    const anchoDeLaVentana = await page.evaluate(() => window.innerWidth);
    expect(anchoDeLaVentana).toBe(390);

    await sinViolaciones(page, `/admin/apuntes/${TEMA} a 390 px`);
    await sinJerga(page);
  } finally {
    retirarLoDeLaPrueba(tema.id, pregunta.id);
  }
});
