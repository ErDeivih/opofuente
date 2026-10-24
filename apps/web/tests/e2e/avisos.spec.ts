/**
 * El ciclo del aviso del alumno, de punta a punta (F16, decisiones D2 y del bloque C).
 *
 * Lo que se prueba, y es lo que el propietario pidió: **el alumno manda un aviso y el propietario lo
 * ve y lo resuelve**. Por pantalla (los dos clics, en sus dos pantallas) y por ruta (la escritura del
 * alumno y el despacho del propietario, cada una con su evento de auditoría).
 *
 * Sobre los apuntes de la prueba: la suite arranca con la base **vacía** y el texto de los apuntes lo
 * escribe el motor, que cuesta llamadas al modelo. Aquí se escribe un apartado **directamente en la
 * base de la suite** (`.e2e-data`, que se borra al empezar cada pasada y nunca es la del propietario)
 * para poder recorrer el ciclo de verdad: la pantalla del alumno lee esos apuntes por su ruta, el
 * botón «Esto está mal» los reporta por la suya y la bandeja del propietario los lee por la suya.
 * Nada de esto toca datos reales.
 */

import { DatabaseSync } from 'node:sqlite';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import AxeBuilder from '@axe-core/playwright';
import { expect, test, type APIRequestContext, type Page } from '@playwright/test';

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
const CLAVE = 'modelo-tcp-ip';
const TITULO = 'El modelo TCP/IP y sus cuatro capas';
const MOTIVO = 'El puerto de LDAPS no es 389, es 636.';
const NOTA = 'Arreglado en la versión del 12-oct';
/** El apartado lejano del enlace: dos apartados con el primero muy largo lo dejan al final. */
const CLAVE_LEJANA = 'ancla-lejana';
const MOTIVO_LEJANO = 'El ejemplo del enlace está al final del tema.';

interface NodoPrograma {
  id: string;
  node_type: string;
  path: string;
  children?: NodoPrograma[];
}

function aplanar(nodos: readonly NodoPrograma[]): NodoPrograma[] {
  return nodos.flatMap((nodo) => [nodo, ...aplanar(nodo.children ?? [])]);
}

/**
 * Escribe el apartado de los apuntes del tema en la base de la suite.
 *
 * `topic_note_sections` es la tabla que lee la pantalla del alumno (y la que el aviso necesita para
 * saber de qué apartado habla). Se escribe con `node:sqlite` y no por una ruta porque **no hay
 * ninguna ruta** que escriba apuntes a mano: los escribe el motor, y hacerlo aquí costaría llamadas
 * al modelo dentro de una puerta de calidad.
 */
function sembrarApuntes(nodeId: string): void {
  const db = new DatabaseSync(BASE);
  try {
    const ahora = new Date().toISOString();
    db.prepare(
      // `OR IGNORE`: el apartado es de la prueba y varias pruebas de este fichero lo necesitan; la
      // segunda no puede volver a insertarlo (hay índice único por tema y clave).
      'INSERT OR IGNORE INTO topic_note_sections ' +
        '(id, curriculum_node_id, subsection_key, epigraph_code, title, anchor, position, ' +
        'body_markdown, status, needs_review_reason, model, prompt_template_version, ' +
        'created_at, updated_at) ' +
        'VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, NULL, ?, NULL, ?, ?)',
    ).run(
      'apartado-de-la-prueba',
      nodeId,
      CLAVE,
      'IV.1.1',
      TITULO,
      CLAVE,
      '## Las cuatro capas\n\nEl modelo TCP/IP describe la comunicación en cuatro capas.\n',
      // `pending` es el estado con el que nace un apartado recién escrito: revisado lo marca el
      // propietario desde el panel de apuntes, que todavía no existe.
      'pending',
      'modelo-de-la-prueba',
      ahora,
      ahora,
    );
  } finally {
    db.close();
  }
}

/**
 * Dos apartados, el primero **muy largo**, para dejar el segundo al final del documento.
 *
 * Es lo que hace falta para medir el enlace al apartado: con el apartado a la vista desde el
 * principio, «está en pantalla» sería verdad sin que nadie hubiera bajado. Con 120 párrafos por
 * delante, el apartado objetivo solo se ve si la vista baja de verdad.
 */
function sembrarApartadosLejanos(nodeId: string): void {
  const db = new DatabaseSync(BASE);
  try {
    const ahora = new Date().toISOString();
    const insertar = db.prepare(
      'INSERT OR IGNORE INTO topic_note_sections ' +
        '(id, curriculum_node_id, subsection_key, epigraph_code, title, anchor, position, ' +
        'body_markdown, status, needs_review_reason, model, prompt_template_version, ' +
        'created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, NULL, ?, ?)',
    );
    const largo = Array.from({ length: 120 }, (_valor, i) => `Párrafo ${String(i)}.`).join('\n\n');
    insertar.run(
      'apartado-largo',
      nodeId,
      'primero-largo',
      'IV.1.1',
      'Un apartado largo al principio',
      'primero-largo',
      1,
      largo,
      'pending',
      'modelo-de-la-prueba',
      ahora,
      ahora,
    );
    insertar.run(
      'apartado-lejano',
      nodeId,
      CLAVE_LEJANA,
      'IV.1.2',
      'El apartado del final',
      CLAVE_LEJANA,
      2,
      '## Al final\n\nEste apartado está detrás de otros ciento veinte párrafos.\n',
      'pending',
      'modelo-de-la-prueba',
      ahora,
      ahora,
    );
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

interface AvisoApi {
  id: string;
  status: string;
  section_title: string | null;
  resolution_note?: string | null;
}

/** Los avisos que espera el propietario, por la ruta que lee su bandeja. */
async function bandeja(
  request: APIRequestContext,
  consulta = '',
): Promise<{ pending: number; total: number; reports: AvisoApi[] }> {
  return (await (await request.get(`${API}/notes-reports${consulta}`)).json()) as {
    pending: number;
    total: number;
    reports: AvisoApi[];
  };
}

/** El alumno avisa desde la pantalla de los apuntes: es el primer tramo del ciclo. */
async function elAlumnoAvisa(page: Page): Promise<void> {
  await page.goto(`/temario/${TEMA}`);
  await expect(page.getByRole('heading', { level: 1, name: new RegExp(TEMA) })).toBeVisible();

  const apartado = page.locator(`#apartado-${CLAVE}`);
  await expect(apartado).toBeVisible();
  await expect(apartado.getByText(/El modelo TCP\/IP describe la comunicación/)).toBeVisible();

  await apartado.getByRole('button', { name: /Esto está mal/ }).click();
  await apartado.getByLabel('Motivo (una línea)').fill(MOTIVO);
  await apartado.getByRole('button', { name: /Enviar el aviso/ }).click();
  await expect(page.getByText(/Queda apuntado/)).toBeVisible();
}

test('E2E-F16 el ciclo del aviso: el alumno lo manda y el propietario lo ve y lo resuelve', async ({
  page,
  request,
}) => {
  const tema = await nodoDelTema(request);
  sembrarApuntes(tema.id);

  // --- 1. El alumno lo manda ------------------------------------------------------------------
  await elAlumnoAvisa(page);

  // La escritura del alumno está donde tiene que estar: en su tabla y con su evento.
  const enviado = await bandeja(request);
  expect(enviado.pending, 'el aviso nace pendiente: espera al propietario').toBe(1);
  expect(enviado.reports[0]?.section_title).toBe(TITULO);
  const creado = eventos('notes.report_created');
  expect(creado, 'el aviso entra con su evento de auditoría').toHaveLength(1);
  expect(creado[0]?.actor).toBe('alumno');

  // --- 2. El propietario lo ve en su bandeja ---------------------------------------------------
  await page.goto('/admin/avisos');
  await expect(
    page.getByRole('heading', { level: 1, name: 'Avisos de los apuntes' }),
  ).toBeVisible();

  // El contador del menú enseña lo que espera: es el número que el propietario mira al entrar.
  await expect(
    page.getByRole('link', { name: /Avisos 1: 1 aviso de los apuntes sin mirar/ }),
  ).toBeVisible();

  const fila = page.getByRole('listitem').filter({ hasText: MOTIVO });
  await expect(fila).toBeVisible();
  await expect(fila.getByText(TITULO)).toBeVisible();
  // Y el enlace al apartado exacto: se puede ir a mirarlo sin buscarlo a mano.
  await expect(fila.getByRole('link', { name: /Ver el apartado en los apuntes/ })).toHaveAttribute(
    'href',
    `/temario/${TEMA}#apartado-${CLAVE}`,
  );

  // --- 3. Lo resuelve, con la nota de lo que ha hecho ------------------------------------------
  await fila.getByLabel(/Qué has hecho/).fill(NOTA);
  await fila.getByRole('button', { name: /^Resuelto:/ }).click();

  await expect(page.getByText(/0 pendientes/)).toBeVisible({ timeout: 15_000 });
  await expect(page.getByRole('listitem').filter({ hasText: /Lo que se hizo:/ })).toContainText(
    NOTA,
  );

  // --- 4. Y quedó escrito: la fila y su evento -------------------------------------------------
  const resuelto = await bandeja(request, '?status=reviewed');
  expect(resuelto.total).toBe(1);
  expect(resuelto.reports[0]?.status).toBe('reviewed');
  expect(resuelto.reports[0]?.resolution_note).toBe(NOTA);

  const despachos = eventos('notes.report_updated');
  expect(despachos).toHaveLength(1);
  expect(despachos[0]?.actor).toBe('local');
  expect(despachos[0]?.object_id).toBe(resuelto.reports[0]?.id);
  expect(despachos[0]?.despues).toContain('"status": "reviewed"');
  expect(despachos[0]?.despues, 'la auditoría guarda referencias, no la nota').not.toContain(NOTA);
});

/**
 * El enlace al apartado exacto, **medido**: al pulsarlo, el apartado queda a la vista.
 *
 * Es la mitad de la decisión del propietario que no se puede dar por hecha: el enlace apunta al ancla
 * (`/temario/IV.1#apartado-<ancla>`) y el ancla del navegador **no basta**, porque los apuntes llegan
 * por la API después del primer pintado. Aquí se mide con el apartado detrás de 120 párrafos: si la
 * vista no baja, la prueba falla.
 *
 * Y desde F35 los apuntes se leen **por capítulos** (§3.1 del encargo): este apartado va en `IV.1.2`,
 * que **no** es el capítulo que la página abre por defecto, así que la pantalla abre el suyo y la
 * dirección se queda con el capítulo **y** el párrafo. Es la expectativa la que cambia, no la
 * pantalla: el enlace al que apunta el aviso sigue siendo el mismo ancla.
 */
test('E2E-F16 el enlace al apartado deja el apartado a la vista', async ({ page, request }) => {
  const tema = await nodoDelTema(request);
  sembrarApartadosLejanos(tema.id);

  const creado = await request.post(`${API}/student/topics/${TEMA}/reports`, {
    headers: { Origin: ORIGEN, 'Content-Type': 'application/json' },
    data: { section_key: CLAVE_LEJANA, reason: MOTIVO_LEJANO },
  });
  expect(creado.status()).toBe(201);

  await page.goto('/admin/avisos');
  const fila = page.getByRole('listitem').filter({ hasText: MOTIVO_LEJANO });
  await expect(fila).toBeVisible();
  await fila.getByRole('link', { name: /Ver el apartado en los apuntes/ }).click();

  await expect(page).toHaveURL(
    new RegExp(`/temario/${TEMA}\\?capitulo=IV\\.1\\.2#apartado-${CLAVE_LEJANA}$`),
  );
  const apartado = page.locator(`#apartado-${CLAVE_LEJANA}`);
  await expect(apartado).toHaveClass(/apartado/);
  await expect(apartado, 'el apartado tiene que quedar a la vista, no al principio').toBeInViewport();

  // Y la vista **bajó al párrafo**. Antes esta prueba pedía `scrollY > 1000`, porque el tema entero
  // era **una sola página** y el apartado estaba detrás de los 120 párrafos del primer apartado;
  // desde F35 el enlace **abre el capítulo que lo contiene** —eso es lo que se acaba de comprobar en
  // la dirección— y este apartado es el primero de su capítulo, así que lo que se mide es que la
  // vista haya ido **hasta él**: el filo del apartado en el filo de la ventana o, si la página es más
  // corta que la ventana y no da para tanto, hasta el final de lo que se puede desplazar. Medido en
  // esta pantalla: el apartado está en 377 y la página solo se desplaza 153, así que la vista llega
  // hasta el final y el apartado queda a la vista. Exigir `scrollY == offsetTop` sería exigirle a la
  // página que sea más larga de lo que es.
  //
  // Y se **espera** a que se mueva, porque el salto es asíncrono: el capítulo que contiene el
  // apartado llega por la API después de la navegación y el efecto que baja al párrafo reintenta
  // hasta encontrarlo. Medirlo en el mismo instante que la dirección es una carrera —la primera
  // corrida de esta prueba dio 153 px y la segunda 0, sin que nada hubiera cambiado—.
  await expect
    .poll(
      async () =>
        page.evaluate((ancla) => {
          const elemento = document.getElementById(ancla);
          if (elemento === null) {
            return Number.NEGATIVE_INFINITY;
          }
          const maximo = document.documentElement.scrollHeight - window.innerHeight;
          const destino = Math.min(
            Math.round(elemento.getBoundingClientRect().top + window.scrollY),
            maximo,
          );
          return Math.round(window.scrollY) - destino;
        }, `apartado-${CLAVE_LEJANA}`),
      { timeout: 15_000 },
    )
    .toBeGreaterThanOrEqual(-8);
});

test('E2E-F16 el propietario también puede dejarlo en curso y volver a abrirlo', async ({
  page,
  request,
}) => {
  const tema = await nodoDelTema(request);
  sembrarApuntes(tema.id);

  // El alumno manda el aviso por su ruta (la pantalla ya se recorre en la prueba de arriba).
  const creado = await request.post(`${API}/student/topics/${TEMA}/reports`, {
    headers: { Origin: ORIGEN, 'Content-Type': 'application/json' },
    data: { section_key: CLAVE, reason: 'La tabla mezcla capas con protocolos.' },
  });
  expect(creado.status()).toBe(201);

  await page.goto('/admin/avisos');
  const fila = page.getByRole('listitem').filter({ hasText: 'La tabla mezcla capas' });
  await expect(fila).toBeVisible();
  await expect(fila.locator('.badge__text', { hasText: 'Pendiente' })).toBeVisible();

  await fila.getByRole('button', { name: /^En curso:/ }).click();
  // El estado queda escrito y la fila lo dice. Lo que se mira es la **insignia**, no el botón: los
  // dos llevan el mismo texto y el botón dice lo que se puede hacer, no lo que hay.
  await expect(fila.locator('.badge__text', { hasText: 'En curso' })).toBeVisible({
    timeout: 15_000,
  });

  // Y el contador de la bandeja lo cuenta como en curso: un aviso en la mano de alguien ya no espera
  // a nadie. Se comprueba por la ruta, que es la que sostiene el número del menú.
  const enCurso = await bandeja(request, '?status=in_progress');
  expect(enCurso.reports.map((aviso) => aviso.status)).toEqual(['in_progress']);
  expect(enCurso.reports).toHaveLength(1);

  // Y se puede volver a dejar pendiente: reabrir no borra el aviso ni su nota.
  await fila.getByRole('button', { name: /^Pendiente:/ }).click();
  await expect(fila.locator('.badge__text', { hasText: 'Pendiente' })).toBeVisible({
    timeout: 15_000,
  });
  expect((await bandeja(request, '?status=in_progress')).reports).toHaveLength(0);
});

test('E2E-F16 «No son preguntas» enseña lo que el motor dejó fuera y no deja tocarlo', async ({
  page,
  request,
}) => {
  // Una pregunta de un banco nuevo, marcada como enunciado roto: lo que la sección lista. El tema
  // (el del programa) hace falta al final, para levantar la marca por la ruta que la levanta.
  const tema = await nodoDelTema(request);
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
        title: `Banco de la prueba de avisos ${String(Date.now())}`,
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
        '1. Los funcionarios tendrán derecho a vacaciones, permisos y licencias.',
        'a) Verdadero',
        'b) Falso',
        'Respuesta correcta: a',
        '',
      ].join('\n'),
    },
  });
  const preguntas = (await (await request.get(`${API}/questions?set_id=${conjunto.id}`)).json()) as {
    questions: { id: string }[];
  };
  const pregunta = preguntas.questions[0];
  expect(pregunta).toBeDefined();

  await request.post(`${API}/questions/topics/bulk`, {
    headers: { Origin: ORIGEN, 'Content-Type': 'application/json', 'X-OpoFuente-Actor': 'local' },
    data: {
      assignments: [
        {
          question_version_id: pregunta?.id,
          exclusion_reason: 'enunciado_roto',
          reason: 'el enunciado es un trozo de norma',
          retire_others: true,
        },
      ],
    },
  });

  await page.goto('/admin/no-son-preguntas');
  await expect(page.getByRole('heading', { level: 1, name: 'No son preguntas' })).toBeVisible();

  const lista = page.getByRole('list', { name: /Preguntas que no son preguntas/i });
  const fila = lista.getByRole('listitem').filter({ hasText: 'vacaciones, permisos y licencias' });
  await expect(fila).toBeVisible();
  await expect(fila.getByText('Enunciado roto')).toBeVisible();
  await expect(fila.getByText(/el enunciado es un trozo de norma/)).toBeVisible();
  await expect(fila.getByText(/lo decidió local/)).toBeVisible();
  // Aquí solo se mira: no hay nada que borre ni que edite la marca.
  await expect(fila.getByRole('button')).toHaveCount(0);

  // Y el buscador encuentra por el texto del enunciado.
  await page.getByLabel(/Buscar en el enunciado/i).fill('vacaciones');
  await page.getByRole('button', { name: /^Buscar$/ }).click();
  await expect(lista.getByRole('listitem')).toHaveCount(1);

  // --- y se deja la base como estaba -------------------------------------------------------------
  // La suite comparte una sola base de datos y la cola de clasificación (`topic-review.spec.ts`)
  // espera encontrar **solo sus** marcas de fuera de temario: deja la pregunta marcada y después
  // comprueba que la bandeja se queda vacía al levantar la suya. Por eso esta prueba **retira la
  // suya** al terminar, y lo hace por la ruta que la retira en la aplicación: asignarle un tema (una
  // pregunta no puede ser de un tema y no ser del temario a la vez).
  await request.post(`${API}/questions/${pregunta?.id ?? ''}/topics`, {
    headers: { Origin: ORIGEN, 'Content-Type': 'application/json', 'X-OpoFuente-Actor': 'local' },
    data: { curriculum_node_id: tema.id },
  });
  const quedan = (await (await request.get(`${API}/question-exclusions`)).json()) as {
    total: number;
  };
  expect(quedan.total, 'la prueba no puede dejar marcas a las demás').toBe(0);
});

/**
 * Las dos pantallas nuevas del panel, a 390 px y sin violaciones de accesibilidad.
 *
 * La puerta de responsividad de `first-run.spec.ts` recorre las pantallas del alumno y el panel se
 * comprueba en la suya: aquí van las dos que estrena este bloque, con datos de verdad dentro (un
 * aviso y una marca de fuera de temario), que es cuando una fila larga se desborda.
 */
for (const viewport of [
  { name: 'escritorio', width: 1280, height: 800 },
  { name: 'móvil', width: 390, height: 844 },
]) {
  test(`E2E-F16 las pantallas del panel caben y no tienen violaciones (${viewport.name})`, async ({
    page,
  }) => {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });

    for (const [ruta, titulo] of [
      ['/admin/avisos', 'Avisos de los apuntes'],
      ['/admin/no-son-preguntas', 'No son preguntas'],
    ] as const) {
      await page.goto(ruta);
      await expect(page.getByRole('heading', { level: 1, name: titulo })).toBeVisible();
      // La lista puede estar vacía si otra prueba no ha dejado nada: lo que se mide es la pantalla.
      await expect(page.locator('main')).toBeVisible();

      const ancho = await page.evaluate(() => document.documentElement.scrollWidth);
      expect(ancho, `scroll horizontal en ${ruta} (${viewport.name})`).toBeLessThanOrEqual(
        viewport.width + 1,
      );

      const analisis = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
        .analyze();
      expect(
        analisis.violations.map((violacion) => violacion.id),
        `violaciones de accesibilidad en ${ruta} (${viewport.name})`,
      ).toEqual([]);

      // Y la jerga de la aplicación **en la interfaz**, que es la mitad del detector que le toca a
      // estas pantallas: los títulos del programa que enseña el filtro de tema van marcados como
      // contenido, porque son material del temario y no vocabulario de la trastienda.
      //
      // La otra mitad (`datosEnElTexto`: otras oposiciones, bancos privados, rutas) **no se le pide al
      // panel**: su regla está escrita para la zona del alumno —«esta zona es solo de TAI»— y el panel
      // enseña a propósito el selector de oposición del propietario, con las suyas. La puerta del
      // rediseño aplica esa mitad solo a `STUDENT_NAV_ITEMS` por el mismo motivo.
      const { interfaz } = await page.evaluate(() => {
        const copia = document.body.cloneNode(true) as HTMLElement;
        for (const nodo of Array.from(copia.querySelectorAll('[data-contenido]'))) {
          nodo.remove();
        }
        return { interfaz: copia.innerText || copia.textContent || '' };
      });
      expect(
        lenguajeInternoEnElTexto(interfaz).map((encontrado) => encontrado.palabra),
        `jerga interna en la interfaz de ${ruta} (${viewport.name})`,
      ).toEqual([]);
    }
  });
}
