import AxeBuilder from '@axe-core/playwright';
import { expect, test, type APIRequestContext } from '@playwright/test';

import { datosEnElTexto } from '../palabrasProhibidas';

/**
 * E2E-05: la cola de clasificación del panel, despachada **con el teclado**.
 *
 * El recorrido es el que hace el propietario: sembrar dos propuestas dudosas (una de ellas con dos
 * temas candidatos, que es lo que dejaron dos corridas que se pisaron), abrir la pantalla por la
 * dirección que manda la decisión, aceptar con una tecla, marcar fuera de temario con otra, guardar
 * el lote y comprobar contra la API que se escribió lo que dice la pantalla.
 *
 * Los datos son sintéticos y se crean por la API real, con una marca distinta en cada pasada: el
 * directorio del E2E se reutiliza entre ejecuciones y las preguntas se identifican por su contenido.
 */

const API = 'http://127.0.0.1:8765/api/v1';
const ORIGIN = { Origin: 'http://127.0.0.1:5173' };

interface NodoApi {
  id: string;
  path: string;
  node_type: string;
  title: string;
  children?: NodoApi[];
}

interface MapeoApi {
  curriculum_node_id: string;
  title: string;
  status: string;
}

let marca = '';
let conjuntoId = '';
let dudosaId = '';
let rotaId = '';
let temaUno = '';
let temaDos = '';
/** La ruta legible de cada tema (`I.1`, `I.2`…): es lo que se lee en la pantalla. */
let temaDosPath = '';

function aplanar(nodos: NodoApi[]): NodoApi[] {
  return nodos.flatMap((nodo) => [nodo, ...aplanar(nodo.children ?? [])]);
}

/** Dos temas del programa vigente, para proponer dos cosas distintas a la misma pregunta. */
async function temasDelPrograma(
  request: APIRequestContext,
): Promise<{ uno: string; dos: string; dosPath: string }> {
  const oposiciones = (await (await request.get(`${API}/oppositions`)).json()) as {
    id: string;
    code: string;
    active: boolean;
    active_convocation?: { id: string } | null;
  }[];
  const activa = oposiciones.find((oposicion) => oposicion.active) ?? oposiciones[0];
  const convocatoria = activa?.active_convocation?.id ?? '';
  const programa = (await (
    await request.get(`${API}/convocations/${convocatoria}/curriculum`)
  ).json()) as { nodes: NodoApi[] };
  const temas = aplanar(programa.nodes).filter((nodo) => nodo.node_type === 'topic');
  return {
    uno: temas[0]?.id ?? '',
    dos: temas[1]?.id ?? '',
    dosPath: temas[1]?.path ?? '',
  };
}

async function sembrar(request: APIRequestContext): Promise<void> {
  const oposiciones = (await (await request.get(`${API}/oppositions`)).json()) as {
    id: string;
    active: boolean;
  }[];
  const activa = oposiciones.find((oposicion) => oposicion.active) ?? oposiciones[0];

  const creado = await request.post(`${API}/question-sets`, {
    headers: ORIGIN,
    data: {
      title: `E2E cola de clasificación ${marca}`,
      opposition_id: activa?.id ?? '',
      set_type: 'private_bank',
    },
  });
  expect(creado.ok(), await creado.text()).toBeTruthy();
  conjuntoId = ((await creado.json()) as { id: string }).id;

  const texto =
    `1. Pregunta dudosa ${marca}: ¿quién es el jefe del Estado?\n` +
    'a) El Rey\n' +
    'b) El Presidente del Gobierno\n' +
    'Respuesta correcta: a\n' +
    `2. Pregunta rota ${marca}: ¿cuál es la orden?\n` +
    'a) mkdri\n' +
    'b) ls\n' +
    'Respuesta correcta: a\n';
  const importado = await request.post(`${API}/question-sets/${conjuntoId}/parse`, {
    headers: ORIGIN,
    data: { kind: 'questions', text: texto },
  });
  expect(importado.ok(), await importado.text()).toBeTruthy();

  const listado = (await (
    await request.get(`${API}/questions?set_id=${conjuntoId}`)
  ).json()) as { questions: { id: string; stem: string }[] };
  dudosaId = listado.questions.find((pregunta) => pregunta.stem.includes(marca))?.id ?? '';
  rotaId = listado.questions.find((pregunta) => pregunta.stem.includes('orden'))?.id ?? '';
  expect(dudosaId).not.toBe('');
  expect(rotaId).not.toBe('');

  const temas = await temasDelPrograma(request);
  temaUno = temas.uno;
  temaDos = temas.dos;
  temaDosPath = temas.dosPath;

  // Las propuestas las escribe el mismo camino que usa el clasificador: la ruta por lotes con
  // `status: provisional`. A la pregunta dudosa se le proponen **dos** temas distintos (el caso real
  // de las dos corridas que se pisaron) y a la otra, uno.
  const propuestas = await request.post(`${API}/questions/topics/bulk`, {
    headers: ORIGIN,
    data: {
      actor: 'llm:deepseek-flash',
      assignments: [
        {
          question_version_id: dudosaId,
          curriculum_node_id: temaUno,
          confidence: 0.5,
          reason: `duda de la primera corrida ${marca}`,
          status: 'provisional',
        },
        {
          question_version_id: dudosaId,
          curriculum_node_id: temaDos,
          confidence: 0.62,
          reason: `duda de la segunda corrida ${marca}`,
          status: 'provisional',
        },
        {
          question_version_id: rotaId,
          curriculum_node_id: temaUno,
          confidence: 0.55,
          reason: `duda de la pregunta rota ${marca}`,
          status: 'provisional',
        },
      ],
    },
  });
  expect(propuestas.ok(), await propuestas.text()).toBeTruthy();
}

async function cola(request: APIRequestContext): Promise<{ stem: string; propuestas: number }[]> {
  const pagina = (await (await request.get(`${API}/question-topic-proposals?limit=200`)).json()) as {
    questions: { stem: string; proposals: unknown[] }[];
  };
  return pagina.questions
    .filter((tarjeta) => tarjeta.stem.includes(marca))
    .map((tarjeta) => ({ stem: tarjeta.stem, propuestas: tarjeta.proposals.length }));
}

/**
 * Siembra una pregunta suelta con una propuesta provisional y devuelve su enunciado.
 *
 * La usan las pruebas que solo necesitan la pantalla **con datos dentro** (la de datos prohibidos y
 * la de accesibilidad): la primera prueba de este fichero despacha la cola entera, así que las
 * siguientes no pueden depender de lo que dejó.
 */
async function sembrarSuelta(request: APIRequestContext, etiqueta: string): Promise<string> {
  const oposiciones = (await (await request.get(`${API}/oppositions`)).json()) as {
    id: string;
    active: boolean;
  }[];
  const activa = oposiciones.find((oposicion) => oposicion.active) ?? oposiciones[0];
  const creado = await request.post(`${API}/question-sets`, {
    headers: ORIGIN,
    data: {
      title: `E2E cola suelta ${etiqueta}`,
      opposition_id: activa?.id ?? '',
      set_type: 'private_bank',
    },
  });
  expect(creado.ok(), await creado.text()).toBeTruthy();
  const setSuelto = ((await creado.json()) as { id: string }).id;

  const enunciado = `Pregunta suelta ${etiqueta} ${String(Date.now())}`;
  const importado = await request.post(`${API}/question-sets/${setSuelto}/parse`, {
    headers: ORIGIN,
    data: {
      kind: 'questions',
      text: `1. ${enunciado}: ¿cuál es la respuesta?\na) una\nb) otra\nRespuesta correcta: a\n`,
    },
  });
  expect(importado.ok(), await importado.text()).toBeTruthy();

  const listado = (await (await request.get(`${API}/questions?set_id=${setSuelto}`)).json()) as {
    questions: { id: string }[];
  };
  const pregunta = listado.questions[0]?.id ?? '';
  const propuesta = await request.post(`${API}/questions/topics/bulk`, {
    headers: ORIGIN,
    data: {
      actor: 'llm:deepseek-flash',
      assignments: [
        {
          question_version_id: pregunta,
          curriculum_node_id: temaUno,
          confidence: 0.55,
          reason: `duda sembrada para ${etiqueta}`,
          status: 'provisional',
        },
      ],
    },
  });
  expect(propuesta.ok(), await propuesta.text()).toBeTruthy();
  return enunciado;
}

async function mapeos(request: APIRequestContext, preguntaId: string): Promise<MapeoApi[]> {
  return (await (await request.get(`${API}/questions/${preguntaId}/topics`)).json()) as MapeoApi[];
}

test.beforeAll(async ({ request }) => {
  marca = `${Date.now().toString(36)}-${Math.floor(Math.random() * 1000)}`;
  await sembrar(request);
});

test('E2E-05 la cola se despacha con el teclado y se escribe en un solo lote', async ({
  page,
  request,
}) => {
  // --- 1. La dirección que manda la decisión del propietario lleva a la cola --------------------
  await page.goto('/admin/preguntas?revisar_tema=1');
  await expect(page).toHaveURL(/\/admin\/clasificacion$/);
  await expect(page.getByRole('heading', { level: 1, name: 'Clasificación' })).toBeVisible();

  // La pantalla está en el menú del panel, y el alumno no la ve nunca: es del panel por la dirección.
  await expect(page.getByRole('link', { name: 'Clasificación' })).toBeVisible();

  // --- 2. Una pregunta con dos propuestas sale UNA sola vez, con los dos candidatos -------------
  const colaApi = await cola(request);
  const dudosa = colaApi.find((entrada) => entrada.stem.includes('quién es el jefe'));
  expect(dudosa?.propuestas, 'las dos propuestas van en la misma tarjeta').toBe(2);
  expect(
    colaApi.filter((entrada) => entrada.stem.includes('quién es el jefe')),
    'la misma pregunta no puede salir dos veces',
  ).toHaveLength(1);

  const tarjeta = page
    .getByRole('listitem')
    .filter({ hasText: 'quién es el jefe del Estado' })
    .first();
  await expect(tarjeta).toBeVisible();
  await expect(tarjeta.getByText(/El Rey/)).toBeVisible();
  // Las dos propuestas se leen juntas, cada una con su confianza: por eso hay dos.
  await expect(tarjeta.getByText(/de confianza/)).toHaveCount(2);
  await expect(tarjeta.getByText(/50 % de confianza/)).toBeVisible();
  await expect(tarjeta.getByText(/62 % de confianza/)).toBeVisible();
  await expect(tarjeta.getByText(/duda de la (primera|segunda) corrida/).first()).toBeVisible();
  await expect(tarjeta.getByText('[1]')).toBeVisible();
  await expect(tarjeta.getByText('[2]')).toBeVisible();

  // --- 3. Teclado: elegir la segunda propuesta, aceptarla y saltar la siguiente -----------------
  // La tarjeta de la pregunta dudosa es la de menos confianza (0,5), así que es la primera de la
  // cola de esta pasada: el cursor ya está ahí y no hace falta ratón para nada.
  await page.keyboard.press('2');
  await page.keyboard.press('a');
  await expect(page.getByText(/1 decisión\(es\) sin guardar/)).toBeVisible();

  // La siguiente es la pregunta rota: se marca fuera de temario por enunciado roto.
  await page.keyboard.press('x');
  await expect(page.getByText(/2 decisión\(es\) sin guardar/)).toBeVisible();

  // --- 4. Guardar: una sola llamada para las dos decisiones -------------------------------------
  const lotes: string[] = [];
  page.on('request', (peticion) => {
    if (peticion.url().includes('/questions/topics/bulk') && peticion.method() === 'POST') {
      lotes.push(peticion.postData() ?? '');
    }
  });
  await page.keyboard.press('g');
  await expect(page.getByText(/Última llamada:/)).toBeVisible({ timeout: 15_000 });
  expect(lotes, 'las dos decisiones van en una sola llamada').toHaveLength(1);
  const cuerpo = JSON.parse(lotes[0] ?? '{}') as { assignments: Record<string, unknown>[] };
  expect(cuerpo.assignments).toHaveLength(2);
  expect(cuerpo.assignments[0]).toMatchObject({
    question_version_id: dudosaId,
    curriculum_node_id: temaDos,
    status: 'accepted',
    retire_others: true,
  });

  // --- 5. Lo que se ve es lo que quedó escrito ---------------------------------------------------
  const escritos = await mapeos(request, dudosaId);
  expect(escritos).toHaveLength(2);
  expect(escritos.find((mapeo) => mapeo.curriculum_node_id === temaDos)?.status).toBe('accepted');
  expect(
    escritos.find((mapeo) => mapeo.curriculum_node_id === temaUno)?.status,
    'la otra propuesta se retira: no puede quedar un segundo tema',
  ).toBe('rejected');

  const marcas = (await (await request.get(`${API}/question-exclusions?limit=200`)).json()) as {
    exclusions: { question_version_id: string; reason: string; actor: string; stem?: string }[];
  };
  const rota = marcas.exclusions.find((marca) => marca.question_version_id === rotaId);
  expect(rota?.reason).toBe('enunciado_roto');
  expect(rota?.actor).toBe('local');

  // --- 6. La cola de esta pasada queda despachada y se dice ---------------------------------------
  await expect(page.getByText('No queda ninguna propuesta')).toBeVisible({ timeout: 15_000 });

  // --- 7. Y la marca se puede deshacer: asignar un tema la levanta --------------------------------
  const fuera = page.getByRole('region', { name: 'Fuera de temario' });
  await expect(fuera.getByText(new RegExp(`Pregunta rota ${marca}`))).toBeVisible();
  await fuera.getByLabel('Tema').selectOption({ index: 1 });
  await fuera.getByRole('button', { name: 'Asignar y levantar la marca' }).click();
  await expect(fuera.getByText('Ninguna pregunta está fuera de temario.')).toBeVisible({
    timeout: 15_000,
  });
  const despues = (await (await request.get(`${API}/question-exclusions`)).json()) as {
    total: number;
  };
  expect(despues.total, 'la marca se levantó de verdad').toBe(0);
});

test('E2E-05 una pregunta en dos temas se ve con su autor y se deja con uno', async ({
  page,
  request,
}) => {
  // Se siembran **dos temas aceptados** para la misma pregunta, que es lo que dejaron la
  // catalogación heredada, las migraciones y las dos corridas que se pisaron.
  const oposiciones = (await (await request.get(`${API}/oppositions`)).json()) as {
    id: string;
    active: boolean;
  }[];
  const activa = oposiciones.find((oposicion) => oposicion.active) ?? oposiciones[0];
  const creado = await request.post(`${API}/question-sets`, {
    headers: ORIGIN,
    data: {
      title: `E2E dos temas ${marca}`,
      opposition_id: activa?.id ?? '',
      set_type: 'private_bank',
    },
  });
  expect(creado.ok(), await creado.text()).toBeTruthy();
  const setDoble = ((await creado.json()) as { id: string }).id;
  const enunciado = `Pregunta en dos temas ${marca}: ¿qué regla es correcta?`;
  const importado = await request.post(`${API}/question-sets/${setDoble}/parse`, {
    headers: ORIGIN,
    data: {
      kind: 'questions',
      text: `1. ${enunciado}\na) una\nb) otra\nRespuesta correcta: a\n`,
    },
  });
  expect(importado.ok(), await importado.text()).toBeTruthy();
  const listado = (await (await request.get(`${API}/questions?set_id=${setDoble}`)).json()) as {
    questions: { id: string }[];
  };
  const dobleId = listado.questions[0]?.id ?? '';
  const doble = await request.post(`${API}/questions/topics/bulk`, {
    headers: ORIGIN,
    data: {
      assignments: [
        { question_version_id: dobleId, curriculum_node_id: temaUno, status: 'accepted' },
        { question_version_id: dobleId, curriculum_node_id: temaDos, status: 'accepted' },
      ],
    },
  });
  expect(doble.ok(), await doble.text()).toBeTruthy();

  await page.goto('/admin/clasificacion');
  const dosTemas = page.getByRole('region', { name: /Preguntas en dos temas/ });
  await expect(dosTemas.getByText(new RegExp(enunciado))).toBeVisible();

  // Cada tema con quién lo escribió: aquí los dos son de la persona local, y se dice.
  await expect(dosTemas.getByText(/a mano o heredado/).first()).toBeVisible();

  // Y se deja con uno: se elige el segundo y se pulsa. Hasta aquí, nada se ha tocado.
  const antes = (await (await request.get(`${API}/questions/${dobleId}/topics`)).json()) as {
    status: string;
  }[];
  expect(antes.filter((mapeo) => mapeo.status === 'accepted')).toHaveLength(2);

  await dosTemas
    .getByRole('radio', { name: new RegExp(temaDosPath.replace('.', '\\.')) })
    .check();
  await dosTemas.getByRole('button', { name: /Dejar este tema/ }).click();

  await expect
    .poll(async () => {
      const mapeos = (await (await request.get(`${API}/questions/${dobleId}/topics`)).json()) as {
        curriculum_node_id: string;
        status: string;
      }[];
      return mapeos.filter((mapeo) => mapeo.status === 'accepted').length;
    })
    .toBe(1);
  const despues = (await (await request.get(`${API}/questions/${dobleId}/topics`)).json()) as {
    curriculum_node_id: string;
    status: string;
  }[];
  expect(
    despues.find((mapeo) => mapeo.curriculum_node_id === temaDos)?.status,
    'el tema elegido se queda',
  ).toBe('accepted');
  expect(
    despues.find((mapeo) => mapeo.curriculum_node_id === temaUno)?.status,
    'el otro se retira, con su evento',
  ).toBe('rejected');
  // Y sale de la lista: ya no cuenta en dos temas.
  await expect(
    page.getByRole('region', { name: /Preguntas en dos temas/ }).getByText(new RegExp(enunciado)),
  ).toHaveCount(0, { timeout: 15_000 });
});

test('E2E-05 la pantalla del panel no enseña datos del propietario', async ({ page, request }) => {
  const enunciado = await sembrarSuelta(request, 'datos');
  await page.goto('/admin/clasificacion');
  await expect(page.getByRole('heading', { level: 1, name: 'Clasificación' })).toBeVisible();
  await page.getByText(new RegExp(enunciado)).first().waitFor();

  const todo = await page.evaluate(
    () => document.querySelector('#contenido')?.textContent ?? '',
  );
  // Se mira **la pantalla** y no el marco entero: el panel enseña en su cabecera el selector de
  // oposición con todas las oposiciones dadas de alta —eso es la trastienda, y ahí sí aparece
  // Celador—, mientras que lo que no puede salir en ninguna parte es una ruta del propietario, un
  // banco privado o un identificador crudo dentro de la propia pantalla.
  expect(datosEnElTexto(todo), 'datos prohibidos en la pantalla de clasificación').toEqual([]);
});

test('E2E-05 accesibilidad sin violaciones automatizables', async ({ page, request }) => {
  const enunciado = await sembrarSuelta(request, 'accesibilidad');
  await page.goto('/admin/clasificacion');
  await expect(page.getByRole('heading', { level: 1, name: 'Clasificación' })).toBeVisible();
  await page.getByText(new RegExp(enunciado)).first().waitFor();

  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
    .analyze();

  expect(results.violations).toEqual([]);
});
