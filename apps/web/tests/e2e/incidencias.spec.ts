/**
 * La bandeja del motor, de punta a punta (F18, §4.1 del objetivo: el bloque C del panel).
 *
 * Lo que se prueba: **lo que el sistema no pudo resolver solo se ve, se puede ir a mirar y se
 * despacha dejándolo escrito**. Por pantalla (la fila con su categoría, su pregunta y sus enlaces, y
 * los botones de decisión) y por ruta (el estado, la nota y su **evento de auditoría**).
 *
 * Sobre las incidencias de la prueba: la suite arranca con la base **vacía**, y las incidencias las
 * escribe el motor de apuntes cuando comprueba un tema contra las preguntas de su banco, que cuesta
 * llamadas al modelo. Aquí se escriben **directamente en la base de la suite** (`.e2e-data`, que se
 * borra al empezar cada pasada y nunca es la del propietario) porque **no hay ruta que las escriba**:
 * las escribe el motor. Es el mismo camino que la prueba de los avisos usa para los apuntes, y por el
 * mismo motivo. Nada de esto toca datos reales, y la prueba **retira lo suyo** al terminar.
 */

import { DatabaseSync } from 'node:sqlite';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import AxeBuilder from '@axe-core/playwright';
import { expect, test, type APIRequestContext } from '@playwright/test';

import { lenguajeInternoEnElTexto } from '../palabrasProhibidas';

const AQUI = path.dirname(fileURLToPath(import.meta.url));
// `…/apps/web/tests/e2e` → la raíz del repositorio, que es donde vive `.e2e-data`.
const REPOSITORIO = path.resolve(AQUI, '..', '..', '..', '..');

/** La API y el origen de las escrituras, como en el resto de la suite. */
const API = 'http://127.0.0.1:8765/api/v1';
const ORIGEN = 'http://127.0.0.1:4173';

/** El directorio de datos de la suite: el suyo, el de siempre (`playwright.config.ts`). */
const DATOS = process.env.OPOFUENTE_E2E_DATA_DIR ?? path.join(REPOSITORIO, '.e2e-data');
const BASE = path.join(DATOS, 'opofuente.sqlite3');

/** El tema de la prueba y su apartado: es texto de prueba, no del propietario. */
const TEMA = 'IV.1';
const ANCLA = 'modelo-tcp-ip';
const TITULO_APARTADO = 'El modelo TCP/IP y sus cuatro capas';
const ENUNCIADO = 'El modelo TCP/IP tiene cuatro capas.';
const DETALLE = 'la clave contradice los apuntes: los apuntes dicen que el puerto es 636';
const FRASE = 'el puerto de LDAPS es el 636';
const NOTA = 'La clave estaba mal; corregida en el banco del 13-oct';

/** El identificador de la incidencia de la prueba: fijo, para poder retirarla al terminar. */
const INCIDENCIA = 'incidencia-de-la-prueba-f18';

interface NodoPrograma {
  id: string;
  node_type: string;
  path: string;
  children?: NodoPrograma[];
}

function aplanar(nodos: readonly NodoPrograma[]): NodoPrograma[] {
  return nodos.flatMap((nodo) => [nodo, ...aplanar(nodo.children ?? [])]);
}

/** La fecha como la escribe el motor: UTC sin zona y con espacio, no con la `T` del navegador. */
function ahoraComoLaEscribeElMotor(): string {
  return new Date().toISOString().replace('T', ' ').replace('Z', '');
}

/**
 * El apartado de los apuntes del que habla la incidencia, en la base de la suite.
 *
 * `topic_note_sections` es la tabla contra la que se resuelve el **ancla** de la incidencia —el
 * enlace que lleva al punto exacto del texto—, así que sin él la fila no tendría a dónde llevar. Se
 * escribe aquí porque no hay ninguna ruta que escriba apuntes a mano: los escribe el motor.
 */
function sembrarApartado(nodeId: string): void {
  const db = new DatabaseSync(BASE);
  try {
    const ahora = ahoraComoLaEscribeElMotor();
    db.prepare(
      'INSERT OR REPLACE INTO topic_note_sections ' +
        '(id, curriculum_node_id, subsection_key, epigraph_code, title, anchor, position, ' +
        'body_markdown, status, needs_review_reason, model, prompt_template_version, ' +
        'created_at, updated_at) ' +
        'VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, NULL, ?, NULL, ?, ?)',
    ).run(
      'apartado-de-la-incidencia',
      nodeId,
      ANCLA,
      'IV.1.1',
      TITULO_APARTADO,
      ANCLA,
      '## Las cuatro capas\n\nEl modelo TCP/IP describe la comunicación en cuatro capas.\n',
      'pending',
      'modelo-de-la-prueba',
      ahora,
      ahora,
    );
  } finally {
    db.close();
  }
}

/** La incidencia, tal como la deja el motor: con su categoría, su motivo, su detalle y su ancla. */
function sembrarIncidencia(nodeId: string, preguntaId: string): void {
  const db = new DatabaseSync(BASE);
  try {
    db.prepare(
      'INSERT OR REPLACE INTO notes_incidents ' +
        '(id, curriculum_node_id, question_version_id, group_signature, category, coverage, ' +
        'reason, section_key, anchor, phrase, detail, attempts, created_at, status, ' +
        'resolution_note, reviewed_at) ' +
        "VALUES (?, ?, ?, ?, 'clave_sospechosa', 'conflict', 'letra_no_coincide', NULL, ?, ?, ?, " +
        "1, ?, 'open', NULL, NULL)",
    ).run(INCIDENCIA, nodeId, preguntaId, 'firma-de-la-prueba-f18', ANCLA, FRASE, DETALLE, ahoraComoLaEscribeElMotor());
  } finally {
    db.close();
  }
}

/** Retira lo que la prueba ha dejado: sus incidencias y su apartado, y solo eso. */
function retirarLoDeLaPrueba(): void {
  const db = new DatabaseSync(BASE);
  try {
    db.prepare('DELETE FROM notes_incidents WHERE id = ?').run(INCIDENCIA);
    db.prepare('DELETE FROM topic_note_sections WHERE id = ?').run('apartado-de-la-incidencia');
  } finally {
    db.close();
  }
}

/** Los eventos de auditoría de una acción, leídos de la base: quién, sobre qué y qué queda. */
function eventos(accion: string): { actor: string; object_id: string; despues: string | null }[] {
  const db = new DatabaseSync(BASE);
  try {
    const filas = db
      .prepare(
        'SELECT actor, object_id, after_json FROM audit_events WHERE action = ? ORDER BY created_at',
      )
      .all(accion) as { actor: string; object_id: string; after_json: string | null }[];
    return filas.map((fila) => ({
      actor: fila.actor,
      object_id: fila.object_id,
      despues: fila.after_json,
    }));
  } finally {
    db.close();
  }
}

/** El tema del programa que usa la prueba, leído de la ruta del programa. */
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
 * Prepara la bandeja: un banco con la pregunta que provoca la incidencia, el apartado y la
 * incidencia. Devuelve el identificador de la pregunta, que es lo que la fila enlaza.
 */
async function prepararLaBandeja(
  request: APIRequestContext,
  tema: NodoPrograma,
): Promise<string> {
  const oposiciones = (await (await request.get(`${API}/oppositions`)).json()) as {
    id: string;
    active: boolean;
    active_convocation: { id: string } | null;
  }[];
  const activa = oposiciones.find((oposicion) => oposicion.active);
  const conjunto = (await (
    await request.post(`${API}/question-sets`, {
      headers: { Origin: ORIGEN, 'Content-Type': 'application/json' },
      data: {
        title: `Banco de la bandeja del motor ${String(Date.now())}`,
        opposition_id: activa?.id,
        set_type: 'private_bank',
        convocation_version_id: activa?.active_convocation?.id,
      },
    })
  ).json()) as { id: string };

  await request.post(`${API}/question-sets/${conjunto.id}/parse`, {
    headers: { Origin: ORIGEN, 'Content-Type': 'application/json' },
    data: {
      kind: 'questions',
      text: [
        `1. ${ENUNCIADO}`,
        'a) Verdadero',
        'b) Falso',
        'Respuesta correcta: a',
        '',
      ].join('\n'),
    },
  });
  const claves = (await (
    await request.get(`${API}/question-sets/${conjunto.id}/answer-keys`)
  ).json()) as { id: string }[];
  await request.post(`${API}/question-sets/${conjunto.id}/answer-keys/${claves[0]?.id ?? ''}/activate`, {
    headers: { Origin: ORIGEN, 'Content-Type': 'application/json' },
  });

  const preguntas = (await (await request.get(`${API}/questions?set_id=${conjunto.id}`)).json()) as {
    questions: { id: string }[];
  };
  const pregunta = preguntas.questions[0];
  if (pregunta === undefined) {
    throw new Error('el banco de la prueba no trae ninguna pregunta');
  }

  sembrarApartado(tema.id);
  sembrarIncidencia(tema.id, pregunta.id);
  return pregunta.id;
}

interface IncidenciaApi {
  id: string;
  status: string;
  category: string;
  category_help: string;
  section_title: string | null;
  resolution_note?: string | null;
}

/** La bandeja del motor, por la ruta que lee la pantalla. */
async function bandeja(
  request: APIRequestContext,
  consulta = '',
): Promise<{
  pending: number;
  total: number;
  totals_by_category: Record<string, number>;
  incidents: IncidenciaApi[];
}> {
  return (await (await request.get(`${API}/notes-incidents${consulta}`)).json()) as {
    pending: number;
    total: number;
    totals_by_category: Record<string, number>;
    incidents: IncidenciaApi[];
  };
}

test('E2E-F18 una incidencia del motor se ve, lleva a lo que la provoca y se despacha', async ({
  page,
  request,
}) => {
  const tema = await nodoDelTema(request);
  const pregunta = await prepararLaBandeja(request, tema);

  try {
    // --- 1. Está en la bandeja, con lo que hace falta para juzgarla ------------------------------
    const inicial = await bandeja(request);
    expect(inicial.pending, 'la incidencia nace pendiente: espera al propietario').toBe(1);
    expect(inicial.totals_by_category['clave_sospechosa']).toBe(1);
    expect(inicial.incidents[0]?.section_title).toBe(TITULO_APARTADO);
    expect(inicial.incidents[0]?.category_help).toContain('otra letra');

    await page.goto('/admin/incidencias');
    await expect(
      page.getByRole('heading', { level: 1, name: 'Incidencias del motor' }),
    ).toBeVisible();

    // El contador del menú enseña lo que espera: es el número que el propietario mira al entrar.
    await expect(
      page.getByRole('link', { name: /Incidencias 1: 1 incidencia del motor sin decidir/ }),
    ).toBeVisible();

    const fila = page.getByRole('listitem').filter({ hasText: DETALLE });
    await expect(fila).toBeVisible();
    await expect(fila.getByText('Clave sospechosa')).toBeVisible();
    await expect(fila.getByText(ENUNCIADO)).toBeVisible();
    await expect(fila.getByText(FRASE)).toBeVisible();

    // Y los tres enlaces a lo que la provoca, sin buscarlo a mano: el apartado de los apuntes, la
    // pregunta del banco y el material del que salió la clave.
    await expect(fila.getByRole('link', { name: /Ver el apartado en los apuntes/ })).toHaveAttribute(
      'href',
      `/temario/${TEMA}#apartado-${ANCLA}`,
    );
    await expect(fila.getByRole('link', { name: /Ver la pregunta en el banco/ })).toHaveAttribute(
      'href',
      `/admin/preguntas?pregunta=${pregunta}`,
    );

    // Y el enlace a la pregunta **abre su ficha**, que es para lo que está: desde F20 esa dirección
    // (`/admin/preguntas?pregunta=…`) es la ficha donde se arregla la respuesta correcta, no la tabla
    // del banco.
    await fila.getByRole('link', { name: /Ver la pregunta en el banco/ }).click();
    await expect(page).toHaveURL(new RegExp(`/admin/preguntas\\?pregunta=${pregunta}$`));
    await expect(page.getByRole('heading', { name: 'Ficha de la pregunta' })).toBeVisible();
    await expect(page.getByText(ENUNCIADO)).toBeVisible();

    // --- 2. Se despacha, con la nota de lo que se ha decidido ------------------------------------
    await page.goto('/admin/incidencias');
    const otraVez = page.getByRole('listitem').filter({ hasText: DETALLE });
    await otraVez.getByLabel(/Qué has decidido/).fill(NOTA);
    await otraVez.getByRole('button', { name: /^Resuelta:/ }).click();

    // La expectativa cambió **a propósito** con F31, y no para que la prueba calle: el resumen de
    // arriba dejó de contar incidencias sueltas («0 pendientes») y ahora cuenta **lo que de verdad
    // espera al propietario**, que es la cifra que manda el §2.4 del cierre del objetivo (una fila
    // por examen, una por incidencia oficial). Al resolver la única incidencia de esta prueba, esa
    // cifra es cero. El texto viejo ya no existe en la pantalla, así que la espera se actualiza.
    await expect(page.getByText(/0 avisos que esperan tu criterio/)).toBeVisible({
      timeout: 15_000,
    });
    await expect(page.getByRole('listitem').filter({ hasText: /Lo que decidiste:/ })).toContainText(
      NOTA,
    );

    // --- 3. Y quedó escrito: la fila y su evento --------------------------------------------------
    const resuelta = await bandeja(request, '?status=reviewed');
    expect(resuelta.total).toBe(1);
    expect(resuelta.incidents[0]?.status).toBe('reviewed');
    expect(resuelta.incidents[0]?.resolution_note).toBe(NOTA);

    const despachos = eventos('notes.incident_updated');
    expect(despachos).toHaveLength(1);
    expect(despachos[0]?.actor).toBe('local');
    expect(despachos[0]?.object_id).toBe(INCIDENCIA);
    expect(despachos[0]?.despues).toContain('"status": "reviewed"');
    expect(despachos[0]?.despues, 'la auditoría guarda referencias, no la nota').not.toContain(NOTA);
  } finally {
    retirarLoDeLaPrueba();
  }
});

/**
 * La pantalla, a los dos anchos y sin violaciones de accesibilidad.
 *
 * Se retrata **con una incidencia dentro**: con la lista vacía no se mide nada de lo que puede
 * desbordarse —un enunciado largo, una cita, los tres enlaces y los cuatro botones de decisión—.
 */
for (const viewport of [
  { name: 'escritorio', width: 1280, height: 800 },
  { name: 'móvil', width: 390, height: 844 },
]) {
  test(`E2E-F18 la bandeja del motor cabe y no tiene violaciones (${viewport.name})`, async ({
    page,
    request,
  }) => {
    const tema = await nodoDelTema(request);
    await prepararLaBandeja(request, tema);

    try {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.goto('/admin/incidencias');
      await expect(
        page.getByRole('heading', { level: 1, name: 'Incidencias del motor' }),
      ).toBeVisible();
      await expect(page.getByRole('listitem').filter({ hasText: DETALLE })).toBeVisible();

      const ancho = await page.evaluate(() => document.documentElement.scrollWidth);
      expect(ancho, `scroll horizontal (${viewport.name})`).toBeLessThanOrEqual(
        viewport.width + 1,
      );

      const analisis = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
        .analyze();
      expect(
        analisis.violations.map((violacion) => violacion.id),
        `violaciones de accesibilidad (${viewport.name})`,
      ).toEqual([]);

      // Y la jerga de la aplicación **en la interfaz**: los títulos del programa que enseña el filtro
      // de tema van marcados como contenido, porque son material del temario y no vocabulario de la
      // trastienda. Los textos del motor (el enunciado, el detalle, la cita) también están marcados.
      const { interfaz } = await page.evaluate(() => {
        const copia = document.body.cloneNode(true) as HTMLElement;
        for (const nodo of Array.from(copia.querySelectorAll('[data-contenido]'))) {
          nodo.remove();
        }
        return { interfaz: copia.innerText || copia.textContent || '' };
      });
      expect(
        lenguajeInternoEnElTexto(interfaz).map((encontrado) => encontrado.palabra),
        `jerga interna en la interfaz (${viewport.name})`,
      ).toEqual([]);
    } finally {
      retirarLoDeLaPrueba();
    }
  });
}
