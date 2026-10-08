import AxeBuilder from '@axe-core/playwright';
import { expect, test, type APIRequestContext } from '@playwright/test';

const API = 'http://127.0.0.1:8765/api/v1';
/** El origen que sirve el build en las pruebas: las escrituras pasan por el control de `Origin`. */
const ALLOWED_ORIGIN = { Origin: 'http://127.0.0.1:4173' };
const GC_NAME = 'Escala de Cabos y Guardias de la Guardia Civil';
const TAI_NAME = 'Cuerpo de Técnicos Auxiliares de Informática de la Administración del Estado';

interface OppositionRow {
  id: string;
  code: string;
  active_convocation: { code: string } | null;
}

interface ConvocationRow {
  id: string;
  code: string;
  status: string;
}

interface OppositionListRow {
  id: string;
  code: string;
}

interface NodoApi {
  id: string;
  title: string;
  children: NodoApi[];
}

interface ProgramaApi {
  nodes: NodoApi[];
}

/** Los tres anchos de referencia de 07_UI-UX §14. */
const VIEWPORTS = [
  { name: 'escritorio 1440x900', width: 1440, height: 900 },
  { name: 'portátil 1024x768', width: 1024, height: 768 },
  { name: 'móvil 390x844', width: 390, height: 844 },
];

/**
 * Cambiar de oposición o de convocatoria es una escritura y afecta a toda la aplicación, así que cada
 * prueba deja TAI activo y la convocatoria de Celador como está en el fixture al terminar.
 *
 * El directorio de datos del E2E se **rehace** en cada corrida (el servidor de la API lo borra antes
 * de migrarlo), así que esto no protege de una corrida a la siguiente: protege a las pruebas que
 * vienen detrás dentro de la misma corrida, cuando una falla a mitad y deja el estado cambiado.
 */
test.afterEach(async ({ request }) => {
  const response = await request.get(`${API}/oppositions`);
  const oppositions = (await response.json()) as OppositionListRow[];
  const tai = oppositions.find((item) => item.code === 'tai-age');
  if (tai !== undefined) {
    await request.post(`${API}/oppositions/${tai.id}/activate`);
  }
  const celador = oppositions.find((item) => item.code === 'celador-sacyl');
  if (celador !== undefined) {
    const rowsResponse = await request.get(`${API}/oppositions/${celador.id}/convocations`);
    const rows = (await rowsResponse.json()) as ConvocationRow[];
    // La vigente que declara el fixture es la convocatoria ordinaria de acceso libre.
    const vigente = rows.find((row) => row.code === 'celador-sacyl-2022');
    if (vigente !== undefined && vigente.status !== 'active') {
      await request.post(`${API}/convocations/${vigente.id}/activate`);
    }
  }
});

test('S01: el Programa muestra el temario oficial de TAI con su procedencia', async ({ page }) => {
  await page.goto('/programa');

  await expect(page.getByRole('heading', { level: 1, name: 'Programa' })).toBeVisible();
  // Cuatro bloques y treinta y tres temas, tal y como se siembran desde el BOE.
  await expect(page.getByText(/4 bloques/)).toBeVisible();
  await expect(page.getByText(/33 temas/)).toBeVisible();
  await expect(
    page.getByText('Organización del Estado y Administración electrónica'),
  ).toBeVisible();

  // Enlace oficial y fecha de publicación visibles.
  await expect(page.getByRole('link', { name: /BOE-A-2025-26262/ })).toBeVisible();
  await expect(page.getByText('2025-12-22')).toBeVisible();
});

test('S01: el Programa muestra las reglas del examen con su cita', async ({ page }) => {
  await page.goto('/programa');

  await expect(page.getByRole('heading', { name: 'Reglas del examen' })).toBeVisible();
  await expect(page.getByText('120 min')).toBeVisible();
  await expect(page.getByText('80 (+5 de reserva)')).toBeVisible();
  await expect(page.getByText('blank_answer_penalty')).toBeVisible();
  // Lo que la convocatoria no publica se declara: TAI no dice cuántas alternativas hay.
  await expect(page.getByText('No consta en la convocatoria')).toBeVisible();
});

/**
 * Deja **una** pregunta catalogada en el primer tema del programa de TAI, por la API real.
 *
 * La prueba del badge «preguntas: N» necesita un tema con preguntas, y en un directorio de datos
 * recién creado no hay ninguno: las pruebas que importan y catalogan preguntas (`questions.spec.ts`,
 * `question-practice.spec.ts`) corren **después** que esta. Antes se leía lo que dejaran aquellas, así
 * que la prueba pasaba por el orden de los ficheros y no por lo que dice comprobar (y con el
 * directorio limpio fallaba). Lo que necesita lo fabrica aquí, que es lo único que la hace
 * independiente del orden.
 *
 * Devuelve el título del tema para poder mirar **su** fila y no un badge cualquiera.
 */
async function catalogarUnaPreguntaEnElPrimerTemaDeTai(
  request: APIRequestContext,
): Promise<string> {
  const oppositions = (await (await request.get(`${API}/oppositions`)).json()) as OppositionRow[];
  const tai = oppositions.find((item) => item.code === 'tai-age');
  expect(tai, 'la siembra tiene que traer la oposición de TAI').toBeDefined();

  const convocatorias = (await (
    await request.get(`${API}/oppositions/${tai!.id}/convocations`)
  ).json()) as ConvocationRow[];
  const programa = (await (
    await request.get(`${API}/convocations/${convocatorias[0]!.id}/curriculum`)
  ).json()) as ProgramaApi;
  const tema = programa.nodes[0]!.children[0]!;

  const sufijo = `${String(Date.now())}-${String(Math.random()).slice(2, 8)}`;
  const conjunto = (await (
    await request.post(`${API}/question-sets`, {
      data: {
        title: `Programa E2E ${sufijo}`,
        opposition_id: tai!.id,
        set_type: 'private_bank',
        convocation_version_id: convocatorias[0]!.id,
      },
      headers: ALLOWED_ORIGIN,
    })
  ).json()) as { id: string };

  const importadas = await request.post(`${API}/question-sets/${conjunto.id}/parse`, {
    data: {
      kind: 'json',
      text: JSON.stringify([
        { stem: `Pregunta del programa ${sufijo}`, options: ['uno', 'dos'], correct: 'uno' },
      ]),
    },
    headers: ALLOWED_ORIGIN,
  });
  expect(importadas.ok(), `importar la pregunta: ${String(importadas.status())}`).toBe(true);

  const pagina = (await (
    await request.get(`${API}/question-sets/${conjunto.id}/questions`)
  ).json()) as { questions: { id: string }[] };
  const asignada = await request.post(`${API}/questions/${pagina.questions[0]!.id}/topics`, {
    data: { curriculum_node_id: tema.id },
    headers: ALLOWED_ORIGIN,
  });
  expect(asignada.ok(), `catalogar la pregunta en el tema: ${String(asignada.status())}`).toBe(true);

  return tema.title;
}

test('DEBT-027 §5: el Programa enseña preguntas y próximo repaso de cada tema', async ({
  page,
  request,
}) => {
  // Las dos columnas que faltaban, servidas por `/reviews/mastery`. Esta prueba es también la que
  // habría cazado el defecto de S12.2: la ruta literal `/reviews/mastery` estaba declarada detrás de
  // `/reviews/{review_id}`, así que contestaba un 404 y la columna de dominio nunca llegó a pintarse.
  //
  // El material lo crea la prueba: sin esto, el badge «preguntas: N» dependía de lo que dejaran otras
  // pruebas que corren después (ver `catalogarUnaPreguntaEnElPrimerTemaDeTai`).
  const temaCatalogado = await catalogarUnaPreguntaEnElPrimerTemaDeTai(request);

  await page.goto('/programa');

  await expect(page.getByRole('heading', { level: 1, name: 'Programa' })).toBeVisible();
  // La nota la compone el servidor: solo llega si la ruta contesta de verdad.
  await expect(page.getByText(/con dominio estimado/)).toBeVisible();
  // La fila del tema que acaba de recibir la pregunta lleva el recuento de verdad: es la prueba de
  // que la cifra sale del mapeo y no de un cero pintado.
  const fila = page.getByRole('button', { name: temaCatalogado });
  await expect(fila.getByText(/^preguntas: \d+$/)).toBeVisible();
  // Y la otra columna, con la fecha o diciendo que no hay nada programado.
  await expect(
    page
      .getByText(/^(repaso: \d{4}-\d{2}-\d{2}|repaso vencido: \d+|sin repaso programado)$/)
      .first(),
  ).toBeVisible();
});

test('S01: cambiar de oposición cambia el programa (25 temas de Guardia Civil)', async ({ page }) => {
  await page.goto('/programa');

  await page.getByLabel('Oposición').selectOption({ label: GC_NAME });

  await expect(page.getByRole('heading', { level: 1, name: 'Programa' })).toBeVisible();
  await expect(page.getByText(/25 temas/)).toBeVisible();
  // El botón del tema 1 incluye su código y su nivel en el nombre accesible.
  await expect(page.getByRole('button', { name: /DERECHOS HUMANOS/ })).toBeVisible();
  await expect(page.getByRole('link', { name: /BOE-A-2026-9982/ })).toBeVisible();

  // Y se puede volver.
  await page.getByLabel('Oposición').selectOption({ label: TAI_NAME });
  await expect(page.getByText(/33 temas/)).toBeVisible();
});

test('S12.2: una oposición con dos convocatorias deja elegir con cuál se estudia', async ({
  page,
  request,
}) => {
  const oppositions = (await (await request.get(`${API}/oppositions`)).json()) as OppositionRow[];
  const celador = oppositions.find((item) => item.code === 'celador-sacyl');
  expect(celador, 'la siembra tiene que traer la oposición de Celador').toBeDefined();
  await request.post(`${API}/oppositions/${celador!.id}/activate`);

  await page.goto('/programa');

  const selector = page.getByLabel('Convocatoria');
  await expect(selector).toBeVisible();
  // La vigente es la convocatoria ordinaria de acceso libre: dieciséis temas y 70 preguntas en 90
  // minutos. La de estabilización está publicada, pendiente de ejercicio y se puede elegir.
  await expect(selector).toHaveValue(await idDe(request, 'celador-sacyl-2022'));
  await expect(page.locator('option', { hasText: 'sin fecha de ejercicio' })).toHaveCount(1);
  await expect(page.getByText(/16 temas/)).toBeVisible();
  await expect(page.getByText('90 min', { exact: true })).toBeVisible();
  await expect(page.getByText('70 (+7 de reserva)', { exact: true })).toBeVisible();
  await expect(page.locator('time[datetime="2023-11-12"]')).toBeVisible();

  // Se cambia a la del proceso de estabilización: otro programa y otras reglas.
  await selector.selectOption({ label: 'ORDEN SAN/1917/2022 · 2022-12-28 · sin fecha de ejercicio' });

  await expect(page.getByText(/14 temas/)).toBeVisible();
  await expect(page.getByText('60 min', { exact: true })).toBeVisible();
  await expect(page.getByText('40 (+4 de reserva)', { exact: true })).toBeVisible();
  // La penalización es la de esta convocatoria: una novena parte, no un cuarto.
  await expect(page.getByText('wrong_answer_penalty')).toBeVisible();
  await expect(page.getByText('1/9 del valor de una respuesta correcta')).toBeVisible();
  await expect(page.getByText('No consta en la convocatoria')).toBeVisible();
  // Y dice por qué no consta: el plazo cerró y la fecha la fijará la resolución de admitidos.
  await expect(page.getByText(/El plazo de solicitudes cerró en enero de 2023/)).toBeVisible();

  // Y se puede volver: cambiar de convocatoria no borra la anterior. Ahora la vigente es la otra,
  // así que su etiqueta ya no lo dice.
  await selector.selectOption({ label: 'ORDEN SAN/1828/2022 · 2022-12-22' });
  await expect(page.getByText(/16 temas/)).toBeVisible();
  await expect(page.getByText('90 min', { exact: true })).toBeVisible();
});

/** Identificador de una convocatoria de Celador, para comprobar qué opción está seleccionada. */
async function idDe(request: APIRequestContext, code: string): Promise<string> {
  const oppositions = (await (await request.get(`${API}/oppositions`)).json()) as OppositionRow[];
  const celador = oppositions.find((item) => item.code === 'celador-sacyl');
  const rows = (await (
    await request.get(`${API}/oppositions/${celador!.id}/convocations`)
  ).json()) as ConvocationRow[];
  return rows.find((row) => row.code === code)!.id;
}

test('S12.2: la convocatoria vigente se elige por la API, no solo en pantalla', async ({
  request,
}) => {
  const oppositions = (await (await request.get(`${API}/oppositions`)).json()) as OppositionRow[];
  const celador = oppositions.find((item) => item.code === 'celador-sacyl');
  const rows = (await (
    await request.get(`${API}/oppositions/${celador!.id}/convocations`)
  ).json()) as ConvocationRow[];
  const estabilizacion = rows.find((row) => row.code === 'celador-sacyl-estabilizacion-2022');

  const activada = await request.post(`${API}/convocations/${estabilizacion!.id}/activate`);
  expect(activada.status()).toBe(200);

  const despues = (await (
    await request.get(`${API}/oppositions/${celador!.id}/convocations`)
  ).json()) as ConvocationRow[];
  expect(despues.find((row) => row.code === 'celador-sacyl-estabilizacion-2022')?.status).toBe(
    'active',
  );
  // La ordinaria no queda «superada»: nada la ha reemplazado, queda publicada y disponible.
  expect(despues.find((row) => row.code === 'celador-sacyl-2022')?.status).toBe('available');
});

test('S13: abrir un tema enseña su dossier, y guardarlo es un POST de verdad', async ({ page }) => {
  await page.goto('/programa');

  await expect(page.getByText(/33 temas/)).toBeVisible();
  await page.getByRole('button', { name: /La Constitución Española/ }).click();

  // La ficha del tema ya no dice dónde se calcula la cobertura: enseña lo que el corpus dice de él.
  // `exact` es necesario: en Playwright el `name` de un rol casa por subcadena, y «El tema» está
  // contenido en «Preguntas del tema» (el `<h3>` del panel de dossier), que aparece en cuanto el
  // dossier termina de leerse. Sin `exact`, la prueba dependía de que la respuesta llegara tarde.
  await expect(page.getByRole('heading', { name: 'El tema', exact: true })).toBeVisible();
  await expect(page.getByText('I.1', { exact: true })).toBeVisible();
  await expect(page.getByText(/leído el \d{4}-\d{2}-\d{2}/)).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Versiones guardadas' })).toBeVisible();

  // Las preguntas del tema (S13, parte 3): o se pueden practicar, o se dice que no hay ninguna y se
  // lleva al banco. Lo que **no** hay es un botón que prometa una sesión que no se puede montar.
  const preguntas = page.getByRole('region', { name: 'Preguntas del tema' });
  await expect(preguntas).toBeVisible();
  await expect(
    preguntas.getByRole('button', { name: 'Practicar este tema' }).or(
      preguntas.getByRole('link', { name: 'Ir al banco de preguntas' }),
    ),
  ).toBeVisible();

  // Archivar la lectura llama a la API de verdad y la pantalla dice qué ha pasado: «guardada» la
  // primera vez y «ya estaba» la segunda, porque el archivo es idempotente por contenido.
  await page.getByRole('button', { name: 'Guardar esta lectura' }).click();
  await expect(
    page.getByText(/Lectura guardada como versión nueva\.|Esa lectura ya estaba guardada/),
  ).toBeVisible();
});

test('S01: accesibilidad del Programa sin violaciones automatizables', async ({ page }) => {
  await page.goto('/programa');
  await expect(page.getByRole('heading', { level: 1, name: 'Programa' })).toBeVisible();
  await expect(page.getByText(/33 temas/)).toBeVisible();

  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
    .analyze();

  expect(results.violations).toEqual([]);
});

/**
 * 07_UI-UX §14: los tres anchos de referencia, sin scroll horizontal.
 *
 * El árbol del programa es lo más ancho de la aplicación —rutas, títulos oficiales largos y las cifras
 * de cada nodo—, así que es donde un desbordamiento se ve primero. Faltaba: Programa solo tenía la
 * comprobación de accesibilidad.
 */
for (const viewport of VIEWPORTS) {
  test(`S01: responsive sin scroll horizontal (${viewport.name})`, async ({ page }) => {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await page.goto('/programa');
    await expect(page.getByRole('heading', { level: 1, name: 'Programa' })).toBeVisible();
    await expect(page.getByText(/33 temas/)).toBeVisible();

    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    expect(scrollWidth, `scroll horizontal en ${viewport.name}`).toBeLessThanOrEqual(
      viewport.width + 1,
    );
  });
}
