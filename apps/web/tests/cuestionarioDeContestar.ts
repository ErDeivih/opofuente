/**
 * La siembra del ciclo de contestar, **y su retirada** (§3.2 del encargo F36).
 *
 * Vive aparte porque la usan dos herramientas que escriben en la misma base de la suite: la prueba de
 * extremo a extremo del ciclo (`tests/e2e/contestar.spec.ts`) y la de capturas
 * (`tests/screens/contestar.spec.ts`). Tener dos copias de una siembra es tener dos copias de su
 * limpieza, y la que se olvide deja datos que aparecen tres ficheros más allá.
 *
 * **Lo que se siembra**: un banco de cuatro preguntas con su clave activa, catalogadas en `IV.1`. Sin
 * catálogo la zona del alumno no monta ningún test —compone con las preguntas catalogadas que tengan
 * clave—, así que la siembra es el mínimo que hace falta para poder recorrer el ciclo.
 *
 * **Lo que se retira, y por qué no es celo**: `workers: 1` corre las specs en orden alfabético, así
 * que `contestar` va **antes** que `study.spec.ts`, y cuatro preguntas catalogadas en `IV.1` son un
 * tema más y cuatro preguntas más para el diagnóstico de aquella prueba. Medido, con su volcado: de
 * «6 en 3» a «8 en 4», y su aserción de «0 de 6 respondidas» se cae. Es la misma fuga que documenta
 * `bandeja-por-conjunto.spec.ts` —«una prueba que deja datos no es una prueba»— y se cierra igual.
 * Además, la herramienta de capturas se puede lanzar con `--datos` contra una **copia de la base del
 * propietario**: allí, dejar la siembra no es una fuga de una corrida, es escribir en sus datos.
 */

import { DatabaseSync } from 'node:sqlite';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { expect, type APIRequestContext } from '@playwright/test';

/** La API y el origen de las escrituras, como en el resto de la suite. */
const API_BASE = process.env.OPOFUENTE_API_URL ?? 'http://127.0.0.1:8765';
export const API = `${API_BASE}/api/v1`;
export const ORIGEN = 'http://127.0.0.1:4173';

/** El tema en el que se cataloga la siembra: es donde la zona del alumno compone el test. */
export const TEMA = 'IV.1';

const AQUI = path.dirname(fileURLToPath(import.meta.url));
// `…/apps/web/tests` → la raíz del repositorio, que es donde vive `.e2e-data`.
const REPOSITORIO = path.resolve(AQUI, '..', '..', '..');
const DATOS = process.env.OPOFUENTE_E2E_DATA_DIR ?? path.join(REPOSITORIO, '.e2e-data');
export const BASE = path.join(DATOS, 'opofuente.sqlite3');

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
 * hay ciclo que medir. Las cuatro se contestan con la misma letra a propósito (la A es la correcta),
 * así que las pruebas saben de antemano cuál es el acierto y cuál el fallo.
 *
 * El identificador del conjunto se apunta en `creados` **en cuanto existe**, no al final: si la
 * siembra se cae a mitad, la retirada tiene que poder llevarse lo que ya se creó. Es lo que hace
 * `bandeja-por-conjunto.spec.ts`, y el motivo está medido: una siembra que murió a mitad dejó sus
 * bancos en `.e2e-data` contaminando dos pruebas que corrían después.
 */
export async function sembrarCuestionario(
  request: APIRequestContext,
  creados: string[],
): Promise<void> {
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
  creados.push(conjunto.id);

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
  expect(preguntas.questions, 'el banco de la prueba tiene sus cuatro preguntas').toHaveLength(4);
  for (const pregunta of preguntas.questions) {
    await request.post(`${API}/questions/${pregunta.id}/topics`, {
      headers: cabeceras,
      data: { curriculum_node_id: tema.id },
    });
  }
}

/** El identificador de la sesión tal como viaja en la dirección del test: `/test/<uuid>`. */
export function sesionDeLaDireccion(url: string): string | null {
  const encontrado = /\/test\/([0-9a-f-]{36})/i.exec(url);
  return encontrado === null ? null : (encontrado[1] ?? null);
}

/**
 * Retira **todo** lo que la prueba ha dejado: la sesión que se abrió, sus intentos, sus repasos y el
 * banco con su catalogación.
 *
 * Las tablas se borran **de la hoja hacia la raíz**: el SQLite de `node:sqlite` no trae las claves
 * foráneas encendidas y ninguna cascada va a hacerlo por nosotros. La catalogación va **antes** que la
 * versión de la pregunta por el mismo motivo (`session_questions` la referencia con `RESTRICT`).
 */
export function retirarLoDeLaPrueba(
  conjuntos: readonly string[],
  sesiones: readonly string[],
): void {
  const db = new DatabaseSync(BASE);
  try {
    // 1. La sesión que abrió el ciclo: repaso, evaluaciones, intentos, preguntas y la sesión.
    if (sesiones.length > 0) {
      const marcas = sesiones.map(() => '?').join(', ');
      const deLaSesion = `SELECT id FROM session_questions WHERE session_id IN (${marcas})`;
      const intentosDeLaSesion = `SELECT id FROM attempts WHERE session_question_id IN (${deLaSesion})`;
      db.prepare(`DELETE FROM learning_errors WHERE attempt_id IN (${intentosDeLaSesion})`).run(
        ...sesiones,
      );
      db.prepare(`DELETE FROM attempt_evaluations WHERE attempt_id IN (${intentosDeLaSesion})`).run(
        ...sesiones,
      );
      db.prepare(`DELETE FROM attempts WHERE session_question_id IN (${deLaSesion})`).run(
        ...sesiones,
      );
      db.prepare(`DELETE FROM session_questions WHERE session_id IN (${marcas})`).run(...sesiones);
      db.prepare(`DELETE FROM study_sessions WHERE id IN (${marcas})`).run(...sesiones);
    }

    // 2. El banco: su catalogación, sus claves, sus preguntas y el conjunto.
    if (conjuntos.length > 0) {
      const huecos = conjuntos.map(() => '?').join(', ');
      const versiones = db
        .prepare(`SELECT id FROM question_versions WHERE question_set_id IN (${huecos})`)
        .all(...conjuntos) as { id: string }[];
      const ids = versiones.map((fila) => fila.id);

      if (ids.length > 0) {
        const marcas = ids.map(() => '?').join(', ');
        // El repaso va por pregunta y no por sesión: `review_items` es único por versión de pregunta,
        // así que la fila es de las mías aunque la sesión ya no esté.
        db.prepare(
          `DELETE FROM review_events WHERE review_item_id IN ` +
            `(SELECT id FROM review_items WHERE question_version_id IN (${marcas}))`,
        ).run(...ids);
        db.prepare(`DELETE FROM review_items WHERE question_version_id IN (${marcas})`).run(...ids);
        db.prepare(
          `DELETE FROM curriculum_mappings WHERE subject_type = 'question_version' ` +
            `AND subject_id IN (${marcas})`,
        ).run(...ids);
        db.prepare(`DELETE FROM notes_incidents WHERE question_version_id IN (${marcas})`).run(
          ...ids,
        );
        db.prepare(`DELETE FROM answer_key_entries WHERE question_version_id IN (${marcas})`).run(
          ...ids,
        );
        db.prepare(`DELETE FROM option_versions WHERE question_version_id IN (${marcas})`).run(
          ...ids,
        );
        db.prepare(`DELETE FROM question_versions WHERE id IN (${marcas})`).run(...ids);
      }

      db.prepare(`DELETE FROM answer_key_versions WHERE question_set_id IN (${huecos})`).run(
        ...conjuntos,
      );
      db.prepare(`DELETE FROM question_sets WHERE id IN (${huecos})`).run(...conjuntos);
    }
  } finally {
    db.close();
  }
}

/**
 * Cuánto de lo que siembra la prueba queda en la base: es lo que se exige **cero** al terminar.
 *
 * Se mide por el mismo camino que se borra (los conjuntos y las sesiones que la prueba conoce), así
 * que un `DELETE` que no llega —una tabla renombrada, una columna que ya no existe— se ve como un
 * número y no como una limpieza que uno supone hecha.
 */
export function quedaAlgoDeLaPrueba(
  conjuntos: readonly string[],
  sesiones: readonly string[],
): { conjuntos: number; sesiones: number; preguntas: number; catalogaciones: number } {
  const db = new DatabaseSync(BASE);
  try {
    const cuenta = (sql: string, valores: readonly string[]): number => {
      const fila = db.prepare(sql).get(...valores) as { total: number } | undefined;
      return fila === undefined ? 0 : fila.total;
    };
    const huecos = conjuntos.map(() => '?').join(', ');
    const marcas = sesiones.map(() => '?').join(', ');
    return {
      conjuntos:
        conjuntos.length === 0
          ? 0
          : cuenta(`SELECT COUNT(*) AS total FROM question_sets WHERE id IN (${huecos})`, conjuntos),
      preguntas:
        conjuntos.length === 0
          ? 0
          : cuenta(
              `SELECT COUNT(*) AS total FROM question_versions WHERE question_set_id IN (${huecos})`,
              conjuntos,
            ),
      catalogaciones:
        conjuntos.length === 0
          ? 0
          : cuenta(
              `SELECT COUNT(*) AS total FROM curriculum_mappings WHERE subject_type = ` +
                `'question_version' AND subject_id IN ` +
                `(SELECT id FROM question_versions WHERE question_set_id IN (${huecos}))`,
              conjuntos,
            ),
      sesiones:
        sesiones.length === 0
          ? 0
          : cuenta(`SELECT COUNT(*) AS total FROM study_sessions WHERE id IN (${marcas})`, sesiones),
    };
  } finally {
    db.close();
  }
}
