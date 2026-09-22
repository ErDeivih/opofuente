import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

import AxeBuilder from '@axe-core/playwright';
import { expect, test, type APIRequestContext } from '@playwright/test';

/**
 * E2E-04 «Documento compartido» (10_TEST-PLAN §5): una fuente, un único artefacto y sus
 * asignaciones.
 *
 * El material es **sintético** y se escribe en el directorio temporal del sistema: nunca se usa
 * nada del usuario. El recorrido es el de una persona: subir el material por la bandeja, esperar a
 * que se extraiga y se clasifique, promocionar el documento (por la API: la biblioteca todavía no
 * promociona desde la interfaz) y trabajar con él desde la pantalla de Biblioteca hasta dejarlo
 * aceptado.
 *
 * Dos cosas del guion original se hacen con lo que hay, y lo que no se puede se deja por escrito en
 * lugar de simularlo:
 *
 * 1. Asignar el documento a **dos oposiciones** se hace con la ruta del contrato §7
 *    (`POST /document-versions/{id}/mappings`), que apunta a la **versión**: un artefacto, una
 *    versión y dos mapeos —TAI y Guardia Civil—. Al final se comprueba además el alta desde la
 *    propia ficha (el formulario de la pestaña de asignaciones).
 * 2. La comparación de versiones la sirve `GET /documents/{id}/diff` (ruta añadida al contrato §7):
 *    la prueba sube una **segunda edición** del mismo documento y comprueba, en la pestaña, que el
 *    servidor dice qué sección cambió. Con una sola versión la pestaña explica que hacen falta dos,
 *    en lugar de simular una comparación.
 */

const API_BASE = process.env.OPOFUENTE_API_URL ?? 'http://127.0.0.1:8765';

interface FilaDeLote {
  id: string;
  status: string;
  total_items: number;
}

interface Entrada {
  original_name: string;
  status: string;
}

interface Representacion {
  artifact_id: string;
  quality: string;
  sources?: { location: string; origin_type?: string | null }[];
}

interface Promocion {
  document_id: string;
  version_id: string;
  created_document: boolean;
  created_version: boolean;
  applied: boolean;
  reason: string | null;
}

interface Oposicion {
  id: string;
  code: string;
  name: string;
  active_convocation: { id: string; code: string } | null;
}

interface NodoPrograma {
  id: string;
  node_type: string;
  official_code: string;
  title: string;
  children: NodoPrograma[];
}

interface Curriculum {
  convocation_id: string;
  convocation_code: string;
  opposition_code: string;
  nodes: NodoPrograma[];
}

interface Mapeo {
  id: string;
  node_id: string;
  node_path: string;
  node_title: string;
  coverage_type: string;
  status: string;
}

/** Escapa un literal de cadena PDF: paréntesis y barra invertida. */
function escaparPdf(text: string): string {
  return text.replace(/\\/g, '\\\\').replace(/\(/g, '\\(').replace(/\)/g, '\\)');
}

/**
 * PDF mínimo **válido**, con su tabla `xref` y sus desplazamientos reales.
 *
 * Se construye a mano, como en la prueba de la bandeja, para no depender de nada: un PDF de mentira
 * haría fallar la extracción de verdad y la prueba mediría el andamio, no la aplicación.
 */
function construirPdf(pages: string[][]): Buffer {
  const pageIds = pages.map((_, index) => 3 + index);
  const contentIds = pages.map((_, index) => 3 + pages.length + index);
  const fontId = 3 + pages.length * 2;

  const objects: string[] = [
    '<< /Type /Catalog /Pages 2 0 R >>',
    `<< /Type /Pages /Kids [${pageIds.map((id) => `${id} 0 R`).join(' ')}]` +
      ` /Count ${pages.length} >>`,
  ];
  for (const id of contentIds) {
    objects.push(
      `<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents ${id} 0 R` +
        ` /Resources << /Font << /F1 ${fontId} 0 R >> >> >>`,
    );
  }
  for (const lines of pages) {
    const stream = [
      'BT /F1 12 Tf 60 780 Td 16 TL',
      ...lines.map((line) => `(${escaparPdf(line)}) Tj T*`),
      'ET',
    ].join('\n');
    objects.push(
      `<< /Length ${Buffer.byteLength(stream, 'latin1')} >>\nstream\n${stream}\nendstream`,
    );
  }
  objects.push(
    '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>',
  );

  const parts: string[] = ['%PDF-1.4\n'];
  const offsets: number[] = [];
  let position = Buffer.byteLength(parts[0] ?? '', 'latin1');
  objects.forEach((body, index) => {
    offsets.push(position);
    const text = `${index + 1} 0 obj\n${body}\nendobj\n`;
    parts.push(text);
    position += Buffer.byteLength(text, 'latin1');
  });
  const entries = offsets
    .map((offset) => `${String(offset).padStart(10, '0')} 00000 n \n`)
    .join('');
  parts.push(
    `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n${entries}` +
      `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${position}\n%%EOF\n`,
  );
  return Buffer.from(parts.join(''), 'latin1');
}

async function json<T>(request: APIRequestContext, ruta: string): Promise<T> {
  const respuesta = await request.get(`${API_BASE}/api/v1${ruta}`);
  expect(respuesta.ok(), `GET ${ruta}: ${respuesta.status()} ${await respuesta.text()}`).toBe(true);
  return (await respuesta.json()) as T;
}

async function enviar<T>(
  request: APIRequestContext,
  ruta: string,
  cuerpo: unknown,
): Promise<T> {
  const respuesta = await request.post(`${API_BASE}/api/v1${ruta}`, { data: cuerpo });
  const detalle = `${respuesta.status()} ${await respuesta.text()}`;
  expect(respuesta.ok(), `POST ${ruta}: ${detalle}`).toBe(true);
  return (await respuesta.json()) as T;
}

function primero<T>(items: T[], mensaje: string): T {
  const first = items[0];
  if (first === undefined) {
    throw new Error(mensaje);
  }
  return first;
}

/** El programa llega como árbol; para buscar un tema se aplana sin perder el orden. */
function aplanar(nodos: NodoPrograma[]): NodoPrograma[] {
  return nodos.flatMap((nodo) => [nodo, ...aplanar(nodo.children)]);
}

/**
 * El lote que trae ese fichero.
 *
 * Otros guiones comparten servidor y base, así que «el último lote» no sirve: se busca el que
 * contiene la entrada con ese nombre.
 */
async function loteCon(request: APIRequestContext, nombre: string): Promise<FilaDeLote> {
  const lotes = await json<FilaDeLote[]>(request, '/ingestion-batches?limit=25');
  for (const candidato of lotes) {
    const detalle = await json<{ entries: Entrada[] }>(
      request,
      `/ingestion-batches/${candidato.id}`,
    );
    if (detalle.entries.some((entrada) => entrada.original_name === nombre)) {
      return candidato;
    }
  }
  throw new Error(`ningún lote trae ${nombre}`);
}

/** Primer tema del programa de una oposición: la asignación tiene que apuntar a un nodo real. */
async function primerTemaDe(
  request: APIRequestContext,
  oposicion: Oposicion,
  nombre: string,
): Promise<NodoPrograma> {
  const convocatoriaId =
    oposicion.active_convocation?.id ??
    primero(
      (
        await json<{ convocations: { id: string }[] }>(
          request,
          `/oppositions/${oposicion.id}/convocations`,
        )
      ).convocations,
      `${nombre} no tiene ninguna convocatoria sembrada`,
    ).id;
  const curriculum = await json<Curriculum>(
    request,
    `/convocations/${convocatoriaId}/curriculum`,
  );
  return primero(
    aplanar(curriculum.nodes).filter((nodo) => nodo.node_type === 'topic'),
    `el programa de ${nombre} no trae temas`,
  );
}

let temporal = '';

test.beforeAll(() => {
  temporal = fs.mkdtempSync(path.join(os.tmpdir(), 'opofuente-e2e-04-'));
});

test.afterAll(() => {
  fs.rmSync(temporal, { recursive: true, force: true });
});

test('E2E-04 documento compartido: un artefacto, sus asignaciones y la versión aceptada', async ({
  page,
  request,
}) => {
  // Esta prueba hace más trabajo que las demás y su presupuesto tiene que decirlo: dos ingestas que
  // pasan por el worker de verdad (copiar, extraer y clasificar), la promoción, la comparación de
  // versiones, el alta de una asignación y el análisis de accesibilidad de la ficha. Con el
  // presupuesto por defecto (30 s) se queda a segundos del límite y falla por reloj, no por producto.
  test.slow();

  // El portapapeles se usa en la prueba para comprobar la cita copiada.
  await page.context().grantPermissions(['clipboard-read', 'clipboard-write']);

  const sufijo = Date.now().toString(36);
  const titulo = `Temario sintetico E2E-04 ${sufijo}`;
  const original = path.join(temporal, `e2e-04-${sufijo}-tema.pdf`);
  const copia = path.join(temporal, `e2e-04-${sufijo}-tema-copia.pdf`);
  // El contenido lleva el sufijo para que cada ejecución tenga su propio artefacto (el almacén es
  // direccionado por contenido) y para que las señales del clasificador sean deterministas.
  const pdf = construirPdf([
    [
      'Temario oficial E2E-04 ' + sufijo,
      'El proceso de seleccion estara formado por un ejercicio unico.',
    ],
    [
      'Boletin Oficial del Estado. Resolucion de 18 de diciembre.',
      'La Ley 39/2015 regula el procedimiento administrativo comun.',
    ],
  ]);
  fs.writeFileSync(original, pdf);
  // Copia byte a byte: debe producir **un** artefacto con dos orígenes.
  fs.writeFileSync(copia, pdf);

  // --- 1. Entrada: el material entra por la bandeja, copiándose ---------------
  await page.goto('/bandeja');
  await page.getByLabel(/Suelta aquí ficheros o carpetas/).setInputFiles([original, copia]);

  const importacion = page.getByRole('region', { name: 'Importación' });
  await expect(importacion.getByText('terminado', { exact: true }).first()).toBeVisible({
    timeout: 60_000,
  });
  const entradas = page.getByRole('table', { name: /entradas/ });
  await expect(entradas.getByText(path.basename(original))).toBeVisible();
  await expect(entradas.getByText(path.basename(copia))).toBeVisible();

  // --- 2. Un único artefacto, con sus dos orígenes ---------------------------
  const lote = primero(
    await json<FilaDeLote[]>(request, '/ingestion-batches?limit=25'),
    'la subida no creó ningún lote',
  );
  expect(lote.status).toBe('succeeded');
  const detalleLote = await json<{ entries: Entrada[] }>(
    request,
    `/ingestion-batches/${lote.id}`,
  );
  expect(detalleLote.entries).toHaveLength(2);

  const representaciones = await json<Representacion[]>(
    request,
    `/ingestion-batches/${lote.id}/representations`,
  );
  // Dos ficheros idénticos comparten representación: un artefacto, dos procedencias.
  expect(representaciones).toHaveLength(1);
  const representacion = primero(
    representaciones,
    'la extracción no dejó ninguna representación',
  );
  expect(representacion.quality).not.toBe('failed');
  expect(representacion.sources?.map((source) => path.basename(source.location))).toEqual(
    expect.arrayContaining([path.basename(original), path.basename(copia)]),
  );
  const artifactId = representacion.artifact_id;

  // --- 3. Clasificación: la pasada real del servidor sobre el texto extraído --
  // La pasada es un **trabajo** (DEBT-024): se encola, el worker la ejecuta y aquí se espera a que
  // termine de verdad, en lugar de suponer que ya está.
  const trabajo = await enviar<{ id: string }>(request, '/classification-runs', undefined);
  await expect
    .poll(async () => (await json<{ status: string }>(request, `/jobs/${trabajo.id}`)).status, {
      timeout: 60_000,
      message: 'la clasificación no terminó',
    })
    .toBe('succeeded');

  const propuestas = await json<{ proposals: { axis: string }[]; total: number }>(
    request,
    `/classification-proposals?subject_type=artifact&subject_id=${artifactId}&limit=200`,
  );
  // El texto del PDF lo dice: «temario oficial» y «Boletín Oficial del Estado».
  expect(propuestas.proposals.map((proposal) => proposal.axis)).toEqual(
    expect.arrayContaining(['document_type', 'authority']),
  );

  // --- 4. Promoción a documento por la API -----------------------------------
  const promocion = await enviar<Promocion>(request, '/documents', {
    artifact_id: artifactId,
    title: titulo,
    document_type: 'curriculum',
  });
  expect(promocion.applied).toBe(true);
  expect(promocion.created_document).toBe(true);
  expect(promocion.created_version).toBe(true);

  // --- 5. Dos asignaciones: la misma versión en TAI y en Guardia Civil --------
  const oposiciones = await json<Oposicion[]>(request, '/oppositions');
  expect(oposiciones.map((oposicion) => oposicion.code)).toEqual(
    expect.arrayContaining(['tai-age', 'gc-cabos-guardias']),
  );
  const tai = primero(
    oposiciones.filter((oposicion) => oposicion.code === 'tai-age'),
    'falta la oposición de TAI en la siembra',
  );
  const gc = primero(
    oposiciones.filter((oposicion) => oposicion.code === 'gc-cabos-guardias'),
    'falta la oposición de Guardia Civil en la siembra',
  );
  const temaTai = await primerTemaDe(request, tai, 'TAI');
  const temaGc = await primerTemaDe(request, gc, 'Guardia Civil');

  // La ruta del contrato §7 apunta a la **versión**: un artefacto, una versión y dos mapeos.
  const asignaciones = [];
  for (const tema of [temaTai, temaGc]) {
    asignaciones.push(
      await enviar<Mapeo>(
        request,
        `/document-versions/${promocion.version_id}/mappings`,
        { curriculum_node_id: tema.id, coverage_type: 'partial' },
      ),
    );
  }
  expect(asignaciones.map((asignacion) => asignacion.status)).toEqual(['accepted', 'accepted']);

  const mapeos = await json<Mapeo[]>(
    request,
    `/mappings?subject_type=document_version&subject_id=${promocion.version_id}`,
  );
  expect(mapeos).toHaveLength(2);
  expect(mapeos.map((mapeo) => mapeo.node_id).sort()).toEqual([temaTai.id, temaGc.id].sort());
  // Y el material sigue siendo uno: dos asignaciones no crean otra versión ni otro documento.
  const asignado = await json<{ document: { id: string }; versions: unknown[] }>(
    request,
    `/documents/${promocion.document_id}`,
  );
  expect(asignado.versions).toHaveLength(1);

  // --- 6. La biblioteca: listado, avisos y ficha ------------------------------
  await page.goto('/biblioteca');
  await page.getByLabel('Tipo documental').selectOption('curriculum');

  const tabla = page.getByRole('table', { name: /documentos en la biblioteca/ });
  const fila = tabla.getByRole('row').filter({ hasText: titulo });
  await expect(fila).toBeVisible();
  await expect(fila.getByText('propuesta de cambio, sin aceptar')).toBeVisible();
  await expect(fila.getByText('derechos restringidos')).toBeVisible();

  await fila.getByRole('button', { name: `Abrir la ficha: ${titulo}` }).click();
  await expect(page.getByRole('tablist', { name: 'Partes de la ficha' })).toBeVisible();
  // La candidata y los derechos desconocidos se avisan antes de cualquier pestaña.
  await expect(
    page.getByRole('region', { name: /La versión activa es una propuesta de cambio/ }),
  ).toBeVisible();
  await expect(
    page.getByRole('region', { name: /Derechos restringidos: no se puede compartir/ }),
  ).toBeVisible();

  // El lector sincroniza el texto extraído con la página del original.
  await expect(
    page.getByText('El proceso de seleccion estara formado por un ejercicio unico.'),
  ).toBeVisible();
  await expect(page.getByText(/página 1 del original/)).toBeVisible();
  await expect(page.getByText(/sin URL oficial/)).toBeVisible();

  // El original **copiado** sí se puede abrir: lo sirve la API de la versión (contrato §7).
  const enlaceOriginal = page.getByRole('link', {
    name: 'abrir el fichero original que se copió',
  });
  await expect(enlaceOriginal).toBeVisible();
  await expect(enlaceOriginal).toHaveAttribute(
    'href',
    new RegExp(`/api/v1/document-versions/${promocion.version_id}/original$`),
  );

  // Copiar cita: título, versión y página del fragmento.
  await page
    .getByRole('button', {
      name: `Copiar la cita: ${titulo}, página 1, pág. 1`,
      exact: true,
    })
    .click();
  await expect(page.getByText(/copiado: título, versión, página 1, pág\. 1 y URL/)).toBeVisible();
  const cita = await page.evaluate(() => navigator.clipboard.readText());
  expect(cita).toContain(titulo);
  expect(cita).toContain(promocion.version_id);
  expect(cita).toContain('página 1, pág. 1');

  // La estructura viene de la extracción: dos páginas, con su página.
  await page.getByRole('tab', { name: 'Estructura' }).click();
  const arbol = page.getByRole('tabpanel');
  await expect(arbol.getByText('página 1', { exact: true })).toBeVisible();
  await expect(arbol.getByText('página 2', { exact: true })).toBeVisible();

  // Las asignaciones de la versión son las dos que se acaban de crear, cada una con su nodo.
  await page.getByRole('tab', { name: 'Asignaciones' }).click();
  const panelAsignaciones = page.getByRole('tabpanel');
  const tablaAsignaciones = panelAsignaciones.getByRole('table', {
    name: /2 asignaciones de programa de la versión/,
  });
  await expect(tablaAsignaciones).toBeVisible();
  // El título se busca **en la tabla**: el mismo nodo aparece también en el selector del formulario.
  await expect(tablaAsignaciones.getByText(temaTai.title)).toBeVisible();
  await expect(tablaAsignaciones.getByText(temaGc.title)).toBeVisible();

  // La comparación de versiones la sirve la API; con una sola versión se explica qué falta.
  await page.getByRole('tab', { name: 'Versiones y diff' }).click();
  await expect(page.getByText(/Comparar necesita al menos dos versiones/)).toBeVisible();

  // --- 7. Aceptar la versión desde la ficha ----------------------------------
  await page.getByRole('button', { name: `Aceptar la versión: ${promocion.version_id}` }).click();
  await page
    .getByRole('button', { name: `Confirmar la aceptación de la versión: ${promocion.version_id}` })
    .click();
  await expect(page.getByText('versión activa y aceptada')).toBeVisible();

  // El servidor es el que manda: su respuesta dice que la versión activa está aceptada.
  const detalle = await json<{
    document: { active_version: { status: string; is_accepted: boolean } | null };
  }>(request, `/documents/${promocion.document_id}`);
  expect(detalle.document.active_version?.status).toBe('accepted');
  expect(detalle.document.active_version?.is_accepted).toBe(true);

  // --- 8. El listado refleja el estado aceptado ------------------------------
  await page.getByRole('button', { name: 'Volver a la lista' }).click();
  await expect(fila.getByText('aceptada')).toBeVisible();
  await expect(fila.getByText('propuesta de cambio, sin aceptar')).toHaveCount(0);

  // --- 9. Segunda edición del mismo documento y comparación real --------------
  const originalV2 = path.join(temporal, `e2e-04-${sufijo}-tema-v2.pdf`);
  fs.writeFileSync(
    originalV2,
    construirPdf([
      [
        'Temario oficial E2E-04 ' + sufijo + ' (segunda edicion)',
        'El proceso de seleccion estara formado por dos ejercicios.',
      ],
      [
        'Boletin Oficial del Estado. Resolucion de 18 de diciembre.',
        'La Ley 39/2015 regula el procedimiento administrativo comun.',
      ],
    ]),
  );
  await page.goto('/bandeja');
  await page.getByLabel(/Suelta aquí ficheros o carpetas/).setInputFiles([originalV2]);
  await expect(importacion.getByText('terminado', { exact: true }).first()).toBeVisible({
    timeout: 60_000,
  });

  const loteV2 = await loteCon(request, path.basename(originalV2));
  const representacionesV2 = await json<Representacion[]>(
    request,
    `/ingestion-batches/${loteV2.id}/representations`,
  );
  const artifactV2 = primero(
    representacionesV2,
    'la segunda edición no dejó ninguna representación',
  ).artifact_id;
  // Segunda versión del **mismo** documento: el fichero es otro, la obra es la misma.
  const promocionV2 = await enviar<Promocion>(request, '/documents', {
    artifact_id: artifactV2,
    title: titulo,
    document_type: 'curriculum',
    document_id: promocion.document_id,
  });
  expect(promocionV2.created_version).toBe(true);
  expect(promocionV2.version_id).not.toBe(promocion.version_id);

  // La ficha compara por defecto la penúltima con la última: aquí, la primera con la segunda.
  await page.goto('/biblioteca');
  await page.getByLabel('Tipo documental').selectOption('curriculum');
  await fila.getByRole('button', { name: `Abrir la ficha: ${titulo}` }).click();
  await page.getByRole('tab', { name: 'Versiones y diff' }).click();

  await expect(page.getByText(/con el texto cambiado: 1/)).toBeVisible();
  await expect(page.getByText(/Nuevas: 0/)).toBeVisible();
  const tablaDiff = page.getByRole('table', { name: /Comparación de/ });
  await expect(tablaDiff.getByText('texto cambiado').first()).toBeVisible();
  await expect(tablaDiff.getByText(/dos ejercicios/)).toBeVisible();
  await expect(tablaDiff.getByText(/sin cambios/).first()).toBeVisible();

  // --- 10. Asignar un nodo del programa desde la propia ficha -----------------
  await page.getByRole('tab', { name: 'Asignaciones' }).click();
  await expect(
    page.getByRole('table', { name: /2 asignaciones de programa de la versión/ }),
  ).toBeVisible();
  const selectorNodo = page.getByLabel('Nodo del programa');
  await expect(selectorNodo).toBeEnabled();
  await selectorNodo.selectOption({ index: 1 });
  await page.getByRole('button', { name: 'Asignar el nodo elegido a esta versión' }).click();
  await expect(
    page.getByRole('table', { name: /3 asignaciones de programa de la versión/ }),
  ).toBeVisible();

  // --- 11. Colecciones: agrupar sin duplicar y quitar sin borrar (DEBT-017) ---
  const nombreColeccion = `Coleccion E2E-04 ${sufijo}`;
  const regionColecciones = page.getByRole('region', { name: 'Colecciones', exact: true });
  const regionDocumento = page.getByRole('region', {
    name: 'Colecciones del documento abierto',
    exact: true,
  });

  await regionColecciones.getByLabel('Nombre de la colección').fill(nombreColeccion);
  await regionColecciones.getByRole('button', { name: 'Crear la colección' }).click();

  // El filtro de la colección recién creada: empieza vacía y lo dice. Se ancla el nombre al
  // principio porque, en cuanto la colección tiene miembros, aparece además el desplegable «Ver los
  // miembros de «…»», que también lleva el nombre dentro.
  const filtroColeccion = regionColecciones.getByRole('button', {
    name: new RegExp(`^${nombreColeccion} `),
  });
  await expect(filtroColeccion).toContainText('0 miembros');

  // Se añade la **versión activa** del documento abierto, que es lo que la ficha sabe que está
  // mirando. Es un POST real: el selector se rellena con lo que devuelve el servidor.
  await regionDocumento
    .getByLabel('Añadir a una colección')
    .selectOption({ label: nombreColeccion });
  await regionDocumento.getByRole('button', { name: 'Añadir a la colección' }).click();
  await expect(regionDocumento.getByRole('status')).toContainText('ahora tiene 1 miembro');
  await expect(filtroColeccion).toContainText('1 miembro');

  // El filtro lo aplica el servidor: se pide por `collection_id` y el documento sigue saliendo.
  await filtroColeccion.click();
  await expect(page.getByText(/filtrados por la colección elegida, en el servidor/)).toBeVisible();
  await expect(fila).toBeVisible();

  // Quitar el miembro: es un DELETE del sujeto, no un borrado de material. El navegador manda el
  // cuerpo de verdad, así que esto comprueba además que la ruta acepta un cuerpo en un DELETE.
  await regionColecciones
    .getByRole('button', { name: `Ver los miembros de «${nombreColeccion}»` })
    .click();
  const quitar = regionColecciones.getByRole('button', {
    name: new RegExp(`^Quitar el miembro .+ de «${nombreColeccion}»$`),
  });
  await expect(quitar).toHaveCount(1);
  await quitar.click();

  // El aviso se da donde se hizo, y dice lo que de verdad ha pasado.
  await expect(regionColecciones.getByRole('status')).toContainText('El documento no se ha borrado');
  await expect(filtroColeccion).toContainText('0 miembros');
  // La colección está vacía, no la biblioteca: el listado lo dice así en lugar de anunciar que no
  // hay ningún documento.
  await expect(page.getByText(/Esta colección no tiene ningún documento todavía/)).toBeVisible();
  await expect(page.getByText('Todavía no hay ningún documento')).toHaveCount(0);

  // Y el documento sigue existiendo, con sus dos versiones: solo ha dejado de estar agrupado.
  const trasQuitar = await json<{ document: { id: string }; versions: unknown[] }>(
    request,
    `/documents/${promocion.document_id}`,
  );
  expect(trasQuitar.versions).toHaveLength(2);
  const colecciones = await json<{ name: string; item_count: number }[]>(request, '/collections');
  expect(colecciones.find((coleccion) => coleccion.name === nombreColeccion)?.item_count).toBe(0);

  const sinViolaciones = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
    .analyze();
  expect(sinViolaciones.violations).toEqual([]);
});
