import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

import AxeBuilder from '@axe-core/playwright';
import {
  expect,
  test,
  type APIRequestContext,
  type Locator,
  type Page,
} from '@playwright/test';

/**
 * E2E-03: revisión en lote contra la API real.
 *
 * El recorrido es el de la especificación (10_TEST-PLAN §5): aceptar un grupo, excluir una fila del
 * lote, corregir un tema, deshacer y comprobar que la cobertura cambia. El material es **sintético**
 * y se escribe en el directorio temporal del sistema: nunca se apunta a ficheros reales.
 *
 * El contenido lleva una marca distinta en cada pasada a propósito. El directorio de datos del E2E se
 * reutiliza entre ejecuciones: con contenido idéntico, el almacén reconocería los mismos artefactos y
 * las propuestas de la pasada anterior ya estarían decididas, así que no habría nada que revisar. Con
 * contenido propio, cada pasada trae material nuevo y propuestas nuevas, y las cifras de cobertura se
 * comparan consigo mismas en lugar de con un valor fijo.
 */

const API = 'http://127.0.0.1:8765/api/v1';
const NOMBRES = ['revision-1', 'revision-2', 'revision-3'];

interface PropuestaApi {
  id: string;
  subject_type: 'artifact' | 'representation';
  subject_id: string;
  subject_label?: string | null;
  axis: string;
  proposed_value: string;
  value_label?: string | null;
  confidence: number;
  band: string;
  is_critical: boolean;
  status: string;
  evidence?: string[];
}

interface GrupoApi {
  key: string;
  subject_type: string;
  axis: string;
  proposed_value: string;
  label: string;
  proposal_ids: string[];
  size: number;
  min_confidence: number;
  max_confidence: number;
  is_critical: boolean;
}

interface NodoApi {
  id: string;
  path: string;
  title: string;
  node_type: string;
  children?: NodoApi[];
}

interface PaginaPropuestasApi {
  proposals: PropuestaApi[];
  total: number;
}

let base = '';
let marca = '';
let ficheros: string[] = [];

/** Texto sintético que menciona el programa sembrado; el primer fichero cita un título de tema. */
function contenido(nombre: string): string {
  const cabecera = `Marcador de la pasada: ${marca}.\n`;
  if (nombre === 'revision-1') {
    return (
      cabecera +
      'Apuntes de legislación sobre la Ley 39/2015.\n' +
      'Boletín Oficial del Estado. Resolución de 12 de enero de 2026.\n' +
      'Uso privado: prohibida su reproducción sin autorización.\n' +
      'La Constitución Española de 1978 desarrolla los derechos y deberes fundamentales.\n'
    );
  }
  if (nombre === 'revision-2') {
    return (
      cabecera +
      'Apuntes de ofimática para el segundo ejercicio.\n' +
      'Boletín Oficial del Estado. Resolución de 3 de febrero de 2026.\n' +
      'Uso privado: documento de trabajo.\n'
    );
  }
  return (
    cabecera +
    'Apuntes de redes y direccionamiento IP.\n' +
    'Boletín Oficial del Estado. Resolución de 20 de marzo de 2026.\n' +
    'Uso privado.\n'
  );
}

test.beforeAll(async ({ request }) => {
  base = fs.mkdtempSync(path.join(os.tmpdir(), 'opofuente-revision-'));
  marca = `${Date.now().toString(36)}-${Math.floor(Math.random() * 1000)}`;
  ficheros = NOMBRES.map((nombre) => path.join(base, `${nombre}-${marca}.txt`));
  NOMBRES.forEach((nombre, indice) => {
    fs.writeFileSync(ficheros[indice] ?? '', contenido(nombre), 'utf-8');
  });

  // La cobertura y la corrección de tema se leen contra el programa activo: TAI.
  const oposiciones = (await (await request.get(`${API}/oppositions`)).json()) as {
    id: string;
    code: string;
  }[];
  const tai = oposiciones.find((oposicion) => oposicion.code === 'tai-age');
  if (tai !== undefined) {
    await request.post(`${API}/oppositions/${tai.id}/activate`);
  }
});

test.afterAll(() => {
  fs.rmSync(base, { recursive: true, force: true });
});

/** Valor de un término de la lista de datos (`<dt>Etiqueta</dt><dd>Valor</dd>`). */
function fact(scope: Locator, label: string) {
  return scope.locator(`dt:text-is("${label}") + dd`);
}

/** Primer número de un hecho («3 (confirmada por ti)» -> 3). */
function numeroDe(texto: string): number {
  const encontrado = /^(\d+)/.exec(texto.trim());
  return encontrado === null ? Number.NaN : Number(encontrado[1]);
}

function escaparParaRegExp(texto: string): string {
  return texto.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function botonDeLote(cantidad: number): string {
  return `Aceptar ${cantidad} ${cantidad === 1 ? 'propuesta' : 'propuestas'}`;
}

/** Confianza del grupo tal y como la pinta la pantalla: un valor o un rango. */
function confianzaDe(grupo: GrupoApi): string {
  const minima = `${Math.round(grupo.min_confidence * 100)} %`;
  if (grupo.min_confidence === grupo.max_confidence) {
    return minima;
  }
  return `${minima} – ${Math.round(grupo.max_confidence * 100)} %`;
}

function temasDe(nodes: NodoApi[]): NodoApi[] {
  const topics: NodoApi[] = [];
  const recorrer = (items: NodoApi[]) => {
    for (const node of items) {
      if (node.node_type === 'topic') {
        topics.push(node);
      }
      recorrer(node.children ?? []);
    }
  };
  recorrer(nodes);
  return topics;
}

async function propuestasPendientes(request: APIRequestContext): Promise<PropuestaApi[]> {
  const pagina = (await (
    await request.get(`${API}/classification-proposals?status=pending&limit=200`)
  ).json()) as PaginaPropuestasApi;
  return pagina.proposals;
}

/** Elige un nodo del árbol de cobertura y devuelve la región donde se lee su cobertura. */
async function elegirNodoDeCobertura(page: Page, titulo: string): Promise<Locator> {
  const cobertura = page.getByRole('region', { name: 'Cobertura del programa' });
  await cobertura
    .getByRole('button', { name: new RegExp(escaparParaRegExp(titulo)) })
    .first()
    .click();
  return cobertura;
}

test('E2E-03 revisión en lote: aceptar un grupo, excluir una fila, corregir un tema, deshacer y ver la cobertura', async ({
  page,
  request,
}) => {
  // Importa, extrae, clasifica y revisa de verdad: el trabajo lo ejecuta el worker del servidor.
  test.setTimeout(180_000);

  // --- 1. Material sintético por la bandeja -------------------------------------------------
  await page.goto('/bandeja');
  await page.getByLabel(/Suelta aquí o elige ficheros/).setInputFiles(ficheros);

  const importacion = page.getByRole('region', { name: 'Importación' });
  await expect(importacion.getByText('succeeded', { exact: true }).first()).toBeVisible({
    timeout: 60_000,
  });

  // La extracción se encola al terminar la copia: se espera a que el texto esté de verdad.
  const texto = page.getByRole('region', { name: 'Texto extraído' });
  for (const ruta of ficheros) {
    await expect(texto.getByText(path.basename(ruta)).first()).toBeVisible({ timeout: 60_000 });
  }

  // --- 2. Clasificar desde la revisión: la pasada solo propone -------------------------------
  await page.goto('/revision');
  await expect(page.getByRole('heading', { level: 1, name: 'Revisión' })).toBeVisible();
  await expect(page.getByText('Esto son propuestas, no hechos')).toBeVisible();

  await page.getByRole('button', { name: 'Buscar propuestas ahora' }).click();
  await expect(page.getByText(/propuestas nuevas/)).toBeVisible({ timeout: 60_000 });

  // --- 3. Grupos: tamaño, confianza y aviso de eje crítico ----------------------------------
  const grupos = (await (await request.get(`${API}/review-groups`)).json()) as GrupoApi[];
  const grupoDeTipo = grupos.find(
    (grupo) =>
      grupo.subject_type === 'artifact' &&
      grupo.axis === 'document_type' &&
      grupo.proposed_value === 'community_material',
  );
  expect(
    grupoDeTipo,
    'el material de la pasada debe formar un grupo por tipo documental',
  ).toBeDefined();
  const tamano = grupoDeTipo?.size ?? 0;
  expect(tamano).toBeGreaterThanOrEqual(3);
  const idsDelGrupo = grupoDeTipo?.proposal_ids ?? [];
  const confianza = confianzaDe(grupoDeTipo as GrupoApi);

  const marcaGrupo = `Marcar el grupo ${grupoDeTipo?.label ?? ''} (material, Tipo de documento) para decidirlo en lote`;
  const filaGrupo = page
    .getByRole('row')
    .filter({ has: page.getByRole('checkbox', { name: marcaGrupo }) });
  await expect(filaGrupo).toBeVisible();
  // El grupo dice cuántas propuestas tiene y con qué confianza, tal y como lo sirve el servidor.
  await expect(filaGrupo.getByText(String(tamano), { exact: true })).toBeVisible();
  await expect(filaGrupo.getByText(confianza, { exact: true })).toBeVisible();

  // Un eje crítico se anuncia: autoridad y derechos no se aplican solos, ni con confianza alta.
  await expect(
    page
      .getByRole('row')
      .filter({
        has: page.getByRole('checkbox', {
          name: 'Marcar el grupo Publicación oficial (material, Autoridad) para decidirlo en lote',
        }),
      })
      .getByText('requiere tu confirmación'),
  ).toBeVisible();

  const ficheroDelTema = path.basename(ficheros[0] ?? '');
  const ficheroExcluido = path.basename(ficheros[2] ?? '');

  const pendientes = await propuestasPendientes(request);
  const propuestaAutoridad = pendientes.find(
    (propuesta) =>
      propuesta.subject_label === ficheroDelTema &&
      propuesta.subject_type === 'artifact' &&
      propuesta.axis === 'authority',
  );
  expect(propuestaAutoridad, 'la autoridad oficial del texto debe quedar pendiente').toBeDefined();
  expect(propuestaAutoridad?.status).toBe('pending');
  await expect(
    page
      .getByRole('row', { name: new RegExp(`${escaparParaRegExp(ficheroDelTema)} \\(material\\) Autoridad`) })
      .getByText('requiere tu confirmación'),
  ).toBeVisible();

  const propuestaExcluida = pendientes.find(
    (propuesta) =>
      propuesta.subject_label === ficheroExcluido &&
      propuesta.subject_type === 'artifact' &&
      propuesta.axis === 'document_type',
  );
  expect(propuestaExcluida, 'la tercera entrada debe estar en el grupo de tipo documental').toBeDefined();
  expect(idsDelGrupo).toContain(propuestaExcluida?.id);

  // --- 4. Lote con una excepción excluida ---------------------------------------------------
  const cuerposDeLote: string[] = [];
  page.on('request', (peticion) => {
    if (peticion.url().includes('/classification-proposals/bulk-decision')) {
      cuerposDeLote.push(peticion.postData() ?? '');
    }
  });

  await page.getByRole('checkbox', { name: marcaGrupo }).check();
  await expect(page.getByRole('button', { name: botonDeLote(tamano) })).toBeVisible();

  await page.getByRole('checkbox', { name: `Dejar fuera del lote: ${ficheroExcluido}` }).check();
  // Las acciones de lote dicen exactamente a cuántos elementos afectan (07_UI-UX §4).
  await expect(page.getByRole('button', { name: botonDeLote(tamano - 1) })).toBeVisible();
  await page.getByRole('button', { name: botonDeLote(tamano - 1) }).click();

  const cola = page.getByRole('region', { name: 'Cola de revisión' });
  await expect(fact(cola, 'Propuestas pedidas')).toHaveText(String(tamano));
  await expect(fact(cola, 'Aplicadas')).toHaveText(String(tamano - 1));
  await expect(fact(cola, 'Excepciones')).toHaveText('1');

  // La excepción viaja aparte en la petición real, y el servidor la deja como estaba.
  expect(cuerposDeLote).toHaveLength(1);
  const cuerpoDelLote = JSON.parse(cuerposDeLote[0] ?? '{}') as {
    proposal_ids?: string[];
    decision?: string;
    excluded?: string[];
  };
  expect(cuerpoDelLote.decision).toBe('accepted');
  expect(cuerpoDelLote.proposal_ids).toEqual(idsDelGrupo);
  expect(cuerpoDelLote.excluded).toEqual([propuestaExcluida?.id]);
  const excluidaDespues = (await (
    await request.get(`${API}/classification-proposals/${propuestaExcluida?.id ?? ''}`)
  ).json()) as PropuestaApi;
  expect(excluidaDespues.status).toBe('pending');

  // --- 5. Corregir un tema contra el programa activo ---------------------------------------
  const oposiciones = (await (await request.get(`${API}/oppositions`)).json()) as {
    id: string;
    active: boolean;
  }[];
  const activa = oposiciones.find((oposicion) => oposicion.active);
  expect(activa, 'la prueba necesita una oposición activa').toBeDefined();
  const convocatorias = (await (
    await request.get(`${API}/oppositions/${activa?.id ?? ''}/convocations`)
  ).json()) as { id: string }[];
  const curriculum = (await (
    await request.get(`${API}/convocations/${convocatorias[0]?.id ?? ''}/curriculum`)
  ).json()) as { nodes: NodoApi[] };
  const temaDestino = temasDe(curriculum.nodes)[0];
  expect(temaDestino, 'el programa activo debe tener temas').toBeDefined();

  // La cobertura aceptada del nodo destino se compara consigo misma, no con un valor fijo: el
  // directorio de datos del E2E conserva material de pasadas anteriores.
  const cobertura = await elegirNodoDeCobertura(page, temaDestino?.title ?? '');
  const aceptadaAntes = numeroDe(await fact(cobertura, 'Cobertura aceptada').innerText());

  const propuestaTema = (await propuestasPendientes(request)).find(
    (propuesta) =>
      propuesta.subject_label === ficheroDelTema &&
      propuesta.subject_type === 'artifact' &&
      propuesta.axis === 'topic',
  );
  expect(
    propuestaTema,
    'el texto que cita el título del tema debe traer una propuesta de tema',
  ).toBeDefined();

  // La fila se identifica por el botón exacto que se va a pulsar (incluye el tipo de sujeto y el
  // eje), y no por el nombre del fichero: el mismo material aparece como artefacto y como
  // representación, y filtrar solo por el nombre daba dos filas.
  const filaDelTema = page.getByRole('row').filter({
    has: page.getByRole('button', {
      name: `Aceptar con la corrección: ${ficheroDelTema} (material) · Tema del programa`,
    }),
  });
  await expect(filaDelTema).toBeVisible();
  await filaDelTema.getByLabel('Corregir el tema').selectOption(temaDestino?.path ?? '');
  await filaDelTema
    .getByRole('button', {
      name: `Aceptar con la corrección: ${ficheroDelTema} (material) · Tema del programa`,
    })
    .click();

  // La corrección llega al servidor: el mapeo queda en el nodo elegido, no en el propuesto.
  const mapeos = (await (
    await request.get(
      `${API}/mappings?subject_type=${propuestaTema?.subject_type ?? ''}&subject_id=${propuestaTema?.subject_id ?? ''}`,
    )
  ).json()) as { node_path: string }[];
  expect(mapeos.map((mapeo) => mapeo.node_path)).toContain(temaDestino?.path);

  // Y la cobertura sube donde tiene que subir: en lo aceptado, no en lo provisional.
  await expect(fact(cobertura, 'Cobertura aceptada')).toHaveText(
    new RegExp(`^${aceptadaAntes + 1}\\b`),
  );
  await expect(fact(cobertura, 'Cobertura provisional')).toBeVisible();

  // --- 6. Deshacer: la propuesta vuelve a la cola y la cobertura baja -----------------------
  // PENDIENTE (documentado): el mismo material genera dos decisiones (artefacto y representación)
  // con la misma etiqueta accesible, así que deshacer por etiqueta es ambiguo. La corrección va en el
  // componente —`DecisionHistory` debe incluir el tipo de sujeto en el nombre del botón, que es lo
  // correcto también para un lector de pantalla— y después aquí se elige la fila del artefacto.
  const historialTabla = page.getByRole('table', { name: /decisiones de esta sesión/ });
  await historialTabla
    .getByRole('button', {
      name: new RegExp(`^Deshacer la decisión sobre ${ficheroDelTema.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}`),
    })
    .first()
    .click();
  await expect(page.getByText(/deshecha: la propuesta volvió a la cola/).first()).toBeVisible();

  const vuelta = (await (
    await request.get(`${API}/classification-proposals/${propuestaTema?.id ?? ''}`)
  ).json()) as PropuestaApi;
  expect(vuelta.status).toBe('pending');
  await expect(fact(cobertura, 'Cobertura aceptada')).toHaveText(
    new RegExp(`^${aceptadaAntes}\\b`),
  );
});

test('E2E-03 revisión: accesibilidad sin violaciones automatizables', async ({ page }) => {
  await page.goto('/revision');
  await expect(page.getByRole('heading', { level: 1, name: 'Revisión' })).toBeVisible();

  // Con lote desplegado y cobertura calculada: la pantalla entera, no solo la cabecera.
  const marcaGrupo = page.getByRole('checkbox', { name: /^Marcar el grupo/ }).first();
  if ((await marcaGrupo.count()) > 0) {
    await marcaGrupo.check();
  }
  const cobertura = page.getByRole('region', { name: 'Cobertura del programa' });
  await cobertura.locator('.tree__label').first().click();
  await expect(fact(cobertura, 'Cobertura provisional')).toBeVisible();

  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
    .analyze();

  expect(results.violations).toEqual([]);
});
