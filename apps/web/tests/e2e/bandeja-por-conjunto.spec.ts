/**
 * La bandeja agrupada por conjunto, de punta a punta (F31, §2 del cierre del objetivo).
 *
 * Lo que se prueba: que la bandeja se pueda **trabajar**. Un conjunto es **una fila** con lo que
 * espera dentro, la fila **despliega** y admite **acciones en bloque**, lo oficial va en su sección
 * sin botones, y la acción deja su **evento de auditoría** —y solo uno, aunque se pulse dos veces—.
 *
 * Sobre los datos: la suite arranca con la base vacía de `.e2e-data` (nunca la del propietario) y
 * las incidencias las escribe el motor de apuntes. Aquí se escriben **directamente en la base de la
 * suite**, por el mismo camino que la prueba de F18 y por el mismo motivo: no hay ruta que las
 * escriba. Nada de esto toca datos reales, y la prueba **retira lo suyo** al terminar.
 */

import { DatabaseSync } from 'node:sqlite';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import AxeBuilder from '@axe-core/playwright';
import { expect, test, type APIRequestContext, type Page } from '@playwright/test';

import { lenguajeInternoEnElTexto } from '../palabrasProhibidas';

const AQUI = path.dirname(fileURLToPath(import.meta.url));
const REPOSITORIO = path.resolve(AQUI, '..', '..', '..', '..');

const API = 'http://127.0.0.1:8765/api/v1';
const ORIGEN = 'http://127.0.0.1:4173';
const DATOS = process.env.OPOFUENTE_E2E_DATA_DIR ?? path.join(REPOSITORIO, '.e2e-data');
const BASE = path.join(DATOS, 'opofuente.sqlite3');

/** Las capturas: el mismo sitio donde las deja el recorrido del propietario. */
const CAPTURAS = path.join(REPOSITORIO, 'artifacts', 'capturas-f31');

const TEMA = 'IV.1';
const ANCLA = 'modelo-tcp-ip';
const TITULO_APARTADO = 'El modelo TCP/IP y sus cuatro capas';
const ENUNCIADO = 'El modelo TCP/IP tiene cuatro capas.';
const DETALLE = 'la clave contradice los apuntes: los apuntes dicen que el puerto es 636';
const FRASE = 'el puerto de LDAPS es el 636';

interface NodoPrograma {
  id: string;
  node_type: string;
  path: string;
  children?: NodoPrograma[];
}

function aplanar(nodos: readonly NodoPrograma[]): NodoPrograma[] {
  return nodos.flatMap((nodo) => [nodo, ...aplanar(nodo.children ?? [])]);
}

function ahoraComoLoEscribeElMotor(): string {
  return new Date().toISOString().replace('T', ' ').replace('Z', '');
}

/** El apartado del que habla la incidencia: sin él, la fila no tendría a dónde llevar. */
function sembrarApartado(nodeId: string): void {
  const db = new DatabaseSync(BASE);
  try {
    const ahora = ahoraComoLoEscribeElMotor();
    db.prepare(
      'INSERT OR REPLACE INTO topic_note_sections ' +
        '(id, curriculum_node_id, subsection_key, epigraph_code, title, anchor, position, ' +
        'body_markdown, status, needs_review_reason, model, prompt_template_version, ' +
        'created_at, updated_at) ' +
        'VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, NULL, ?, NULL, ?, ?)',
    ).run(
      'apartado-de-la-bandeja-f31',
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

/** Las incidencias de la prueba, tal como las deja el motor. */
function sembrarIncidencias(nodeId: string, preguntas: readonly string[]): void {
  const db = new DatabaseSync(BASE);
  try {
    const ahora = ahoraComoLoEscribeElMotor();
    const insertar = db.prepare(
      'INSERT OR REPLACE INTO notes_incidents ' +
        '(id, curriculum_node_id, question_version_id, group_signature, category, coverage, ' +
        'reason, section_key, anchor, phrase, detail, attempts, created_at, status, ' +
        'resolution_note, reviewed_at) ' +
        "VALUES (?, ?, ?, ?, 'clave_sospechosa', 'conflict', 'letra_no_coincide', NULL, ?, ?, ?, " +
        "1, ?, 'open', NULL, NULL)",
    );
    preguntas.forEach((pregunta, indice) => {
      insertar.run(
        `incidencia-de-la-bandeja-f31-${String(indice)}`,
        nodeId,
        pregunta,
        'firma-de-la-prueba-f31',
        ANCLA,
        FRASE,
        DETALLE,
        ahora,
      );
    });
  } finally {
    db.close();
  }
}

/** Marca un conjunto como examen oficial: es lo que protege su clave. */
function marcarOficial(setId: string): void {
  const db = new DatabaseSync(BASE);
  try {
    db.prepare("UPDATE question_sets SET set_type = 'official_exam' WHERE id = ?").run(setId);
  } finally {
    db.close();
  }
}

/** Retira lo que la prueba ha dejado: sus incidencias y su apartado, y solo eso. */
function retirarLoDeLaPrueba(cantidad: number): void {
  const db = new DatabaseSync(BASE);
  try {
    const borrar = db.prepare('DELETE FROM notes_incidents WHERE id = ?');
    for (let indice = 0; indice < cantidad; indice += 1) {
      borrar.run(`incidencia-de-la-bandeja-f31-${String(indice)}`);
    }
    db.prepare('DELETE FROM topic_note_sections WHERE id = ?').run('apartado-de-la-bandeja-f31');
  } finally {
    db.close();
  }
}

/** Los eventos de auditoría de una acción, leídos de la base. */
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

/** Un banco con dos preguntas catalogadas. Devuelve su identificador y sus preguntas. */
async function sembrarBanco(
  request: APIRequestContext,
  tema: NodoPrograma,
  titulo: string,
): Promise<{ setId: string; preguntas: string[] }> {
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
        title: titulo,
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
      text: [`1. ${ENUNCIADO}`, 'a) Verdadero', 'b) Falso', 'Respuesta correcta: a', ''].join('\n'),
    },
  });
  const claves = (await (
    await request.get(`${API}/question-sets/${conjunto.id}/answer-keys`)
  ).json()) as { id: string }[];
  await request.post(
    `${API}/question-sets/${conjunto.id}/answer-keys/${claves[0]?.id ?? ''}/activate`,
    { headers: { Origin: ORIGEN, 'Content-Type': 'application/json' } },
  );

  const preguntas = (await (
    await request.get(`${API}/questions?set_id=${conjunto.id}`)
  ).json()) as { questions: { id: string }[] };
  const identificadores: string[] = [];
  for (const pregunta of preguntas.questions) {
    await request.post(`${API}/questions/${pregunta.id}/topics`, {
      headers: { Origin: ORIGEN, 'Content-Type': 'application/json' },
      data: { curriculum_node_id: tema.id },
    });
    identificadores.push(pregunta.id);
  }
  if (identificadores.length === 0) {
    throw new Error('el banco de la prueba no trae ninguna pregunta');
  }
  return { setId: conjunto.id, preguntas: identificadores };
}

/**
 * Prepara las dos secciones: un banco privado con dos incidencias y un examen oficial con una.
 *
 * Deja **dos** conjuntos a propósito: es lo que permite comprobar de una vez que lo oficial va en su
 * sección sin botones y que lo demás se decide en bloque.
 */
async function prepararLaBandeja(
  request: APIRequestContext,
): Promise<{ privado: string; oficial: string; total: number }> {
  const tema = await nodoDelTema(request);
  const privado = await sembrarBanco(request, tema, `Banco de la bandeja f31 ${String(Date.now())}`);
  const oficial = await sembrarBanco(
    request,
    tema,
    `Examen oficial de la bandeja f31 ${String(Date.now())}`,
  );

  sembrarApartado(tema.id);
  // Dos incidencias del banco privado y una del examen oficial: lo justo para que las dos secciones
  // existan y para que la acción en bloque cierre **un** conjunto y no el otro.
  sembrarIncidencias(tema.id, [
    privado.preguntas[0]!,
    privado.preguntas[0]!,
    oficial.preguntas[0]!,
  ]);
  marcarOficial(oficial.setId);
  return { privado: privado.setId, oficial: oficial.setId, total: 3 };
}

/** Recoge los errores de consola y de página: la bandeja es interfaz del propietario. */
function vigilarConsola(page: Page): string[] {
  const errores: string[] = [];
  page.on('console', (mensaje) => {
    if (mensaje.type() === 'error') {
      errores.push(mensaje.text());
    }
  });
  page.on('pageerror', (error) => {
    errores.push(error.message);
  });
  return errores;
}

test('E2E-F31 la bandeja se agrupa por conjunto y una acción en bloque la despacha entera', async ({
  page,
  request,
}) => {
  const errores = vigilarConsola(page);
  const conjuntos = await prepararLaBandeja(request);

  try {
    await page.goto('/admin/incidencias');
    await expect(page.getByRole('heading', { level: 2, name: 'La bandeja por conjunto' })).toBeVisible();

    // --- 1. Lo oficial, aparte y arriba, y sin botones -------------------------------------------
    const seccionOficial = page.getByRole('region', { name: 'Exámenes oficiales' });
    await expect(seccionOficial).toBeVisible();
    await expect(
      seccionOficial.getByText(/no se cambia desde aquí/i),
    ).toBeVisible();
    await expect(
      seccionOficial.getByRole('button', { name: /Aceptar todas las derivadas/i }),
    ).toHaveCount(0);

    // --- 2. El conjunto no oficial es **una** fila, y despliega ----------------------------------
    const lista = page.getByRole('list', { name: 'La bandeja agrupada por conjunto' });
    const filaPrivada = page.locator(`li[data-conjunto="${conjuntos.privado}"]`);
    await expect(filaPrivada).toBeVisible();
    await expect(filaPrivada).toContainText('2 claves sospechosas');
    await filaPrivada.getByRole('button', { name: /Ver lo que tiene dentro/i }).click();
    await expect(
      filaPrivada.getByRole('list', { name: /Incidencias de /i }).getByText(FRASE).first(),
    ).toBeVisible();

    // --- 3. La acción en bloque, y su evento -----------------------------------------------------
    await filaPrivada.getByRole('button', { name: /Dejar el conjunto fuera/i }).click();
    await expect(filaPrivada).toHaveCount(0, { timeout: 15_000 });
    // Y el conjunto oficial **sigue ahí**: la acción era de un conjunto, no de la bandeja.
    await expect(page.locator(`li[data-conjunto="${conjuntos.oficial}"]`)).toHaveCount(1);

    const despachos = eventos('notes.incident_bulk_dispatched');
    expect(despachos).toHaveLength(2);
    expect(despachos.every((evento) => evento.actor === 'local')).toBe(true);
    expect(despachos.every((evento) => evento.despues?.includes('dejar_fuera'))).toBe(true);
    await expect(lista).toBeVisible();

    // --- 4. Idempotencia: volver a pedirlo no duplica --------------------------------------------
    const antes = eventos('notes.incident_bulk_dispatched').length;
    const repetida = await request.post(`${API}/notes-incidents/tray/bulk`, {
      headers: { Origin: ORIGEN, 'Content-Type': 'application/json' },
      data: { action: 'dejar_fuera', set_id: conjuntos.privado },
    });
    expect(repetida.status()).toBe(200);
    expect(((await repetida.json()) as { incidents: number }).incidents).toBe(0);
    expect(eventos('notes.incident_bulk_dispatched').length).toBe(antes);

    expect(errores, `errores de consola: ${errores.join(' | ')}`).toEqual([]);
    expect(conjuntos.total).toBe(3);
  } finally {
    retirarLoDeLaPrueba(3);
  }
});

/**
 * La pantalla, a los dos anchos y sin violaciones.
 *
 * Se retrata **con la bandeja llena**: un conjunto con su resumen, sus botones y su despliegue
 * abierto, y la sección oficial arriba. Con la lista vacía no se mide nada de lo que puede
 * desbordarse.
 */
for (const viewport of [
  { name: 'escritorio', width: 1280, height: 900 },
  { name: 'movil', width: 390, height: 844 },
]) {
  test(`E2E-F31 la bandeja por conjunto cabe y no tiene violaciones (${viewport.name})`, async ({
    page,
    request,
  }) => {
    const errores = vigilarConsola(page);
    const conjuntos = await prepararLaBandeja(request);

    try {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.goto('/admin/incidencias');
      await expect(
        page.getByRole('heading', { level: 2, name: 'La bandeja por conjunto' }),
      ).toBeVisible();
      await expect(page.getByRole('region', { name: 'Exámenes oficiales' })).toBeVisible();

      // El despliegue, abierto: es la parte que más puede desbordar.
      const fila = page.locator(`li[data-conjunto="${conjuntos.privado}"]`);
      await fila.getByRole('button', { name: /Ver lo que tiene dentro/i }).click();
      await expect(fila.getByRole('button', { name: /Ocultar lo que tiene dentro/i })).toBeVisible();

      await page.screenshot({
        path: path.join(CAPTURAS, `bandeja-por-conjunto-${viewport.name}.png`),
        fullPage: true,
      });

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

      expect(errores, `errores de consola: ${errores.join(' | ')}`).toEqual([]);
    } finally {
      retirarLoDeLaPrueba(3);
    }
  });
}
