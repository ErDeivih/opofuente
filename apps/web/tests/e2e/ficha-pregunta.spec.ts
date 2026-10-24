/**
 * La ficha de pregunta, de punta a punta (F20, §4.2 del objetivo: el bloque C del panel).
 *
 * Lo que se prueba, y es lo que el encargo pide demostrar:
 *
 * 1. **la pantalla existe y la abre el enlace que ya se usaba**: `/admin/preguntas?pregunta=<id>` es la
 *    ficha, y desde la bandeja del motor se llega a ella. Enseña el enunciado, las opciones con su
 *    letra y cuál está marcada hoy como respuesta correcta;
 * 2. **se ve de dónde sale la respuesta correcta**: la lista de respuestas del banco, su estado y el
 *    material del que salió con el estado de su versión;
 * 3. **marcar la respuesta correcta es una escritura auditada**: por pantalla, con la anterior
 *    conservada (queda sustituida), y con el **evento de auditoría** en la base, con el antes y el
 *    después;
 * 4. **una respuesta correcta oficial no se cambia**: se monta un examen oficial, la ficha dice por qué
 *    y **no deja**; la lista de respuestas del banco no cambia;
 * 5. **la reparación funciona y es reversible**: se prepara una pregunta con la referencia del examen
 *    pegada al enunciado, se repara por pantalla y queda una vista nueva con la anterior sustituida y
 *    con su motivo. Y una pregunta sin reparación posible dice por qué, sin ofrecer el botón.
 *
 * Los datos los monta la prueba por las **rutas reales** (banco, importación, corrección local); lo
 * único que se escribe en la base de la suite (`.e2e-data`, que se borra al empezar cada pasada y
 * nunca es la del propietario) es el documento del que se enlaza una plantilla, porque no hay ninguna
 * ruta que invente un material sin pasar por la extracción entera. La prueba retira lo suyo.
 */

import { DatabaseSync } from 'node:sqlite';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import AxeBuilder from '@axe-core/playwright';
import { expect, test, type APIRequestContext } from '@playwright/test';

import { lenguajeInternoEnElTexto } from '../palabrasProhibidas';

const AQUI = path.dirname(fileURLToPath(import.meta.url));
const REPOSITORIO = path.resolve(AQUI, '..', '..', '..', '..');

const API = 'http://127.0.0.1:8765/api/v1';
const ORIGEN = 'http://127.0.0.1:4173';
const CABECERAS = { Origin: ORIGEN, 'Content-Type': 'application/json' };

const DATOS = process.env.OPOFUENTE_E2E_DATA_DIR ?? path.join(REPOSITORIO, '.e2e-data');
const BASE = path.join(DATOS, 'opofuente.sqlite3');

/** El enunciado con la referencia del examen pegada: el caso que una regla puede limpiar. */
const ENUNCIADO_CON_REFERENCIA =
  'El puerto de LDAPS es el 389: 2013 Cuerpo de Gestión de Sistemas e Informática de la AGE - Gr.B';

/** Y el que se queda como está: una opción que nombra a otra no es una opción fundida. */
const ENUNCIADO_CON_MENCION = 'Las Cámaras se reunirán anualmente:';

const TEXTO = [
  `1. ${ENUNCIADO_CON_REFERENCIA}`,
  'a) Verdadero',
  'b) Falso',
  'Respuesta correcta: a',
  `2. ${ENUNCIADO_CON_MENCION}`,
  'a) En dos periodos ordinarios, conforme a lo indicado en la opción c).',
  'b) En un solo periodo ordinario de sesiones, de septiembre a junio.',
  'c) En dos periodos ordinarios, el primero de septiembre a diciembre.',
  'Respuesta correcta: a',
  '',
].join('\n');

interface Pregunta {
  id: string;
}

/** La fecha como la escribe el motor: UTC sin zona y con espacio, no con la `T` del navegador. */
function ahoraComoLaEscribeElMotor(): string {
  return new Date().toISOString().replace('T', ' ').replace('Z', '');
}

/**
 * El documento del que sale una plantilla, por SQL y solo de preparación.
 *
 * Es el segundo camino a «oficial»: una plantilla que vino de un papel. No hay ninguna ruta que cree
 * un material sin pasar por la extracción entera, así que aquí se escriben el artefacto, el documento
 * y su versión, y se apunta la lista de respuestas del banco a esa versión. La prueba los retira.
 */
function sembrarDocumentoDelQueSaleLaPlantilla(setId: string): void {
  const db = new DatabaseSync(BASE);
  try {
    const ahora = ahoraComoLaEscribeElMotor();
    db.prepare(
      'INSERT OR REPLACE INTO source_artifacts (id, sha256, size_bytes, media_type, storage_key, ' +
        'first_seen_at) VALUES (?, ?, 100, ?, ?, ?)',
    ).run('art-plantilla-f20', 'a'.repeat(64), 'text/plain', 'k-f20', ahora);
    db.prepare(
      'INSERT OR REPLACE INTO logical_documents (id, canonical_title, document_type, ' +
        'authority_tier, owner_scope, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
    ).run(
      'doc-plantilla-f20',
      'Plantilla de respuestas de la prueba',
      'answer_key',
      'A',
      'public',
      ahora,
      ahora,
    );
    db.prepare(
      'INSERT OR REPLACE INTO document_versions (id, logical_document_id, artifact_id, ' +
        'version_label, retrieved_at, language, status, approved_at, approved_by, created_at) ' +
        'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
    ).run(
      'ver-plantilla-f20',
      'doc-plantilla-f20',
      'art-plantilla-f20',
      'definitiva',
      ahora,
      'es',
      'accepted',
      ahora,
      'local',
      ahora,
    );
    db.prepare(
      'UPDATE answer_key_versions SET source_document_version_id = ? WHERE question_set_id = ?',
    ).run('ver-plantilla-f20', setId);
  } finally {
    db.close();
  }
}

/** Retira lo que la prueba ha dejado: su documento y su apunte. */
function retirarLoDeLaPrueba(): void {
  const db = new DatabaseSync(BASE);
  try {
    db.prepare('DELETE FROM answer_key_versions WHERE source_document_version_id = ?').run(
      'ver-plantilla-f20',
    );
    db.prepare('DELETE FROM document_versions WHERE id = ?').run('ver-plantilla-f20');
    db.prepare('DELETE FROM logical_documents WHERE id = ?').run('doc-plantilla-f20');
    db.prepare('DELETE FROM source_artifacts WHERE id = ?').run('art-plantilla-f20');
  } finally {
    db.close();
  }
}

/** Los eventos de auditoría de una acción sobre **una** pregunta: quién y qué quedó escrito. */
function eventos(
  accion: string,
  pregunta: string,
): { actor: string; object_id: string; antes: string; despues: string }[] {
  const db = new DatabaseSync(BASE);
  try {
    const filas = db
      .prepare(
        'SELECT actor, object_id, before_json, after_json FROM audit_events WHERE action = ? ' +
          'AND object_id = ? ORDER BY created_at',
      )
      .all(accion, pregunta) as {
      actor: string;
      object_id: string;
      before_json: string | null;
      after_json: string | null;
    }[];
    return filas.map((fila) => ({
      actor: fila.actor,
      object_id: fila.object_id,
      antes: fila.before_json ?? '',
      despues: fila.after_json ?? '',
    }));
  } finally {
    db.close();
  }
}

/** Las listas de respuestas de un banco, en el orden en que las escribe el servidor. */
function listasDeRespuestas(setId: string): { id: string; version_no: number; status: string; fuente: string | null }[] {
  const db = new DatabaseSync(BASE);
  try {
    return db
      .prepare(
        'SELECT id, version_no, status, source_document_version_id AS fuente ' +
          'FROM answer_key_versions WHERE question_set_id = ? ORDER BY version_no',
      )
      .all(setId) as { id: string; version_no: number; status: string; fuente: string | null }[];
  } finally {
    db.close();
  }
}

/**
 * Un banco con las dos preguntas de la prueba y su lista de respuestas activa.
 *
 * Las preguntas **no se catalogan en ningún tema**, y es a propósito: el diagnóstico de la zona del
 * alumno compone su muestra con dos preguntas por tema, así que una pregunta de más en un tema le
 * cambiaría el tamaño de la muestra a la prueba del diagnóstico (medido: 6 → 8, y `study.spec.ts` se
 * pone rojo). El sitio de la pregunta —sus temas y sus apuntes— se prueba donde toca, en la prueba de
 * integración de la ficha y en la corrida sobre la copia de la base real.
 *
 * `tipo` decide si el banco es un examen oficial: en ese caso no se activa su lista de respuestas
 * —activar una oficial exige la plantilla oficial enlazada—, y para probar que su respuesta correcta
 * no se cambia desde aquí tampoco hace falta.
 */
async function bancoDeLaPrueba(
  request: APIRequestContext,
  tipo: 'private_bank' | 'official_exam',
  titulo: string,
): Promise<{ setId: string; preguntas: Pregunta[] }> {
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
        title: `${titulo} ${String(Date.now())}`,
        opposition_id: activa?.id,
        set_type: tipo,
        convocation_version_id: activa?.active_convocation?.id,
      },
    })
  ).json()) as { id: string };

  await request.post(`${API}/question-sets/${conjunto.id}/parse`, {
    headers: CABECERAS,
    data: { kind: 'questions', text: TEXTO },
  });

  // La lista de respuestas nace en borrador: se aprueba y se activa por la ruta, que es lo que hace
  // que una respuesta correcta corrija algo. En un examen oficial no se activa —necesitaría la
  // plantilla oficial enlazada—, y para probar que no se puede cambiar tampoco hace falta.
  const listas = (await (
    await request.get(`${API}/question-sets/${conjunto.id}/answer-keys`)
  ).json()) as { id: string }[];
  if (tipo === 'private_bank') {
    await request.post(
      `${API}/question-sets/${conjunto.id}/answer-keys/${listas[0]?.id ?? ''}/activate`,
      { headers: CABECERAS },
    );
  }

  const listado = (await (
    await request.get(`${API}/questions?set_id=${conjunto.id}`)
  ).json()) as { questions: Pregunta[] };
  const preguntas = listado.questions;
  if (preguntas.length < 2) {
    throw new Error('el banco de la prueba debería traer dos preguntas');
  }
  return { setId: conjunto.id, preguntas };
}

test('E2E-F20 la ficha enseña la pregunta, de dónde sale su respuesta y deja cambiarla', async ({
  page,
  request,
}) => {
    const { setId, preguntas } = await bancoDeLaPrueba(request, 'private_bank', 'Banco de la ficha');
  const pregunta = preguntas[0]!;
  const enunciado = ENUNCIADO_CON_REFERENCIA;

  try {
    // --- 1. La pantalla existe en la dirección que ya se usaba -------------------------------
    await page.goto(`/admin/preguntas?pregunta=${pregunta.id}`);
    await expect(page.getByRole('heading', { level: 1, name: 'Ficha de la pregunta' })).toBeVisible();
    await expect(page.getByText(enunciado)).toBeVisible();
    // Una sola opción está marcada como la que vale, y se dice con palabras y no solo con el color.
    const marcada = page.locator('.resultado__opcion--correcta');
    await expect(marcada).toHaveCount(1);
    await expect(marcada).toContainText('respuesta correcta');

    // Y se llega a ella desde el banco: la dirección del banco a secas sigue siendo el banco.
    await page.goto('/admin/preguntas');
    await expect(page.getByRole('heading', { level: 1, name: 'Preguntas' })).toBeVisible();

    // --- 2. De dónde sale la respuesta correcta ----------------------------------------------
    await page.goto(`/admin/preguntas?pregunta=${pregunta.id}`);
    await expect(page.getByRole('heading', { name: 'De dónde sale la respuesta correcta' })).toBeVisible();
    await expect(page.getByText(/vista 1 de la lista de respuestas del banco/)).toBeVisible();
    // «En uso» sale dos veces —la procedencia y el historial de la lista— y las dos son el mismo
    // hecho: la lista que corrige es esa.
    await expect(page.getByText('en uso').first()).toBeVisible();

    // --- 3. Marcar la respuesta correcta, con su evento --------------------------------------
    const antes = listasDeRespuestas(setId);
    expect(antes).toHaveLength(1);
    await page.getByRole('radio', { name: /^B/ }).check();
    await page.getByLabel('Por qué (opcional)').fill('los apuntes lo contestan en el apartado de puertos');
    await page.getByRole('button', { name: 'Guardar la respuesta correcta' }).click();

    await expect(page.getByText(/Respuesta correcta guardada/)).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText(/antes A; la lista anterior se conserva/)).toBeVisible();

    const despues = listasDeRespuestas(setId);
    expect(despues, 'una lista nueva, y la anterior conservada').toHaveLength(2);
    expect(despues[0]?.status).toBe('superseded');
    expect(despues[1]?.status).toBe('active');

    const marcados = eventos('question.answer_key_marked', pregunta.id);
    expect(marcados).toHaveLength(1);
    expect(marcados[0]?.actor).toBe('local');
    expect(marcados[0]?.object_id).toBe(pregunta.id);
    expect(marcados[0]?.antes).toContain('"correct_option_keys": ["a"]');
    expect(marcados[0]?.despues).toContain('"correct_option_keys": ["b"]');
    expect(marcados[0]?.despues, 'la nota del propietario no se copia a la auditoría').not.toContain(
      'los apuntes lo contestan',
    );

    // Y la ficha, al recargar, enseña la respuesta nueva y el historial con la anterior.
    await page.reload();
    await expect(page.getByText(/vista 2 de la lista de respuestas del banco/)).toBeVisible();
    await expect(page.getByText('sustituida').first()).toBeVisible();

    // --- 4. Reparar: la referencia del examen pegada al enunciado -----------------------------
    const reparada = page.getByRole('heading', { name: 'Reparar el texto importado' });
    await expect(reparada).toBeVisible();
    await expect(page.getByText('Quitar la referencia del examen')).toBeVisible();
    await page
      .getByLabel('Por qué se repara (obligatorio)')
      .fill('la referencia del examen quedó pegada al enunciado');
    await page.getByRole('button', { name: 'Reparar el texto de la pregunta' }).click();
    await expect(page.getByText(/Reparada: se escribió la vista/)).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText('El puerto de LDAPS es el 389:')).toBeVisible();
    // La vista anterior queda en el historial, y el motivo con el que se reparó se lee dos veces —bajo
    // el enunciado y en la fila de la versión nueva—, que es el mismo dato dicho en dos sitios.
    await expect(page.getByText(/quedó pegada al enunciado/).first()).toBeVisible();
    // Y la ficha se ha mudado a la versión nueva: la dirección lleva la que manda ahora.
    const nueva = new URL(page.url()).searchParams.get('pregunta');
    expect(nueva).not.toBe(pregunta.id);
    expect(nueva).not.toBeNull();
    const reparaciones = eventos('question.repaired', nueva ?? '');
    expect(reparaciones).toHaveLength(1);
    expect(reparaciones[0]?.despues).toContain('"reglas": ["quitar_referencia_del_examen"]');
    // Esta prueba no cataloga sus preguntas en ningún tema (para no cambiarle la muestra al
    // diagnóstico), así que el sitio que viaja son cero temas: que viaje de verdad cuando los tiene
    // lo prueba la prueba de integración de la ficha, con su tema y su ancla.
    expect(reparaciones[0]?.despues).toContain('"temas_movidos": 0');

    // --- 5. Una pregunta sin reparación posible lo dice, sin ofrecer el botón ------------------
    await page.goto(`/admin/preguntas?pregunta=${preguntas[1]!.id}`);
    await expect(page.getByText(/nombra a otra opción/)).toBeVisible();
    await expect(page.getByRole('button', { name: 'Reparar el texto de la pregunta' })).toHaveCount(0);
  } finally {
    retirarLoDeLaPrueba();
  }
});

test('E2E-F20 la respuesta correcta de un examen oficial no se cambia y se dice por qué', async ({
  page,
  request,
}) => {
    const { setId, preguntas } = await bancoDeLaPrueba(request, 'official_exam', 'Examen oficial de la ficha');
  sembrarDocumentoDelQueSaleLaPlantilla(setId);

  try {
    const antes = listasDeRespuestas(setId);
    await page.goto(`/admin/preguntas?pregunta=${preguntas[0]!.id}`);

    await expect(page.getByRole('heading', { level: 1, name: 'Ficha de la pregunta' })).toBeVisible();
    // La ficha lo dice con el motivo del dominio y con la **lista** de bancos protegidos.
    await expect(page.getByText(/es un examen oficial/).first()).toBeVisible();
    await expect(page.getByText(/bancos están protegidos y por qué/)).toBeVisible();
    // Y no hay nada que marcar: no es un botón apagado, es que no se puede.
    await expect(page.getByRole('radio')).toHaveCount(0);
    await expect(page.getByRole('button', { name: 'Guardar la respuesta correcta' })).toHaveCount(0);

    // La lista de respuestas del banco no se ha tocado, y de esta pregunta no hay ningún cambio de
    // respuesta en la auditoría.
    expect(listasDeRespuestas(setId)).toEqual(antes);
    expect(eventos('question.answer_key_marked', preguntas[0]!.id)).toHaveLength(0);
  } finally {
    retirarLoDeLaPrueba();
  }
});

/**
 * La pantalla, a los dos anchos y sin violaciones de accesibilidad.
 *
 * Se retrata **con una pregunta de verdad dentro**: con la ficha vacía no se mide nada de lo que puede
 * desbordarse —un enunciado largo, cuatro opciones, la cita de los apuntes y las dos tablas del
 * historial—.
 */
for (const viewport of [
  { name: 'escritorio', width: 1280, height: 800 },
  { name: 'móvil', width: 390, height: 844 },
]) {
  test(`E2E-F20 la ficha de pregunta cabe y no tiene violaciones (${viewport.name})`, async ({
    page,
    request,
  }) => {
        const { preguntas } = await bancoDeLaPrueba(request, 'private_bank', 'Banco de la ficha (medida)');

    try {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.goto(`/admin/preguntas?pregunta=${preguntas[0]!.id}`);
      await expect(
        page.getByRole('heading', { level: 1, name: 'Ficha de la pregunta' }),
      ).toBeVisible();
      await expect(page.getByText(ENUNCIADO_CON_REFERENCIA)).toBeVisible();

      const ancho = await page.evaluate(() => document.documentElement.scrollWidth);
      expect(ancho, `scroll horizontal (${viewport.name})`).toBeLessThanOrEqual(
        viewport.width + 1,
      );

      const analisis = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
        .analyze();
      expect(
        // **Se dice el NODO, no solo la regla**: adivinar cual es ha costado rondas.
        analisis.violations.map(
          (v) =>
            `${v.id} -> ${v.nodes.map((n) => `${n.target.join(' ')} :: ${n.html}`).join(' | ')}`,
        ),
        `violaciones de accesibilidad (${viewport.name})`,
      ).toEqual([]);

      // Y la jerga de la aplicación en la interfaz: lo que viene del servidor —el enunciado, las
      // opciones, el porqué de cada negativa, el título del material— va dentro de `data-contenido`,
      // porque es un dato y no una frase nuestra.
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
