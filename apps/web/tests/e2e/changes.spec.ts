import AxeBuilder from '@axe-core/playwright';
import { expect, test, type APIRequestContext, type Page } from '@playwright/test';

/**
 * E2E-09 «Cambio» (10_TEST-PLAN §5 y demo D de 16_TRACEABILITY): versionar un material, confirmar el
 * diff y comprobar que **solo** los derivados afectados quedan pendientes de revisar.
 *
 * El recorrido es el de una persona, con material sintético que entra por el camino real (pegado en la
 * bandeja → copiado → extraído) y con dos versiones del mismo documento:
 *
 * 1. se pega la versión 1 (dos secciones) y se promociona a documento;
 * 2. desde el lector se crea un **resumen extractivo** de la segunda sección: un derivado de verdad,
 *    con sus dependencias escritas;
 * 3. se pega la versión 2 con esa misma sección modificada y se promociona como versión del mismo
 *    documento → aparece una **propuesta de cambio** con su diff y sus afectados, sin aplicar nada;
 * 4. se confirma: la versión nueva pasa a ser la activa, la anterior queda histórica y el resumen
 *    queda pendiente de revisar;
 * 5. se revisa el resumen («sigue valiendo») y la versión 1 sigue accesible.
 *
 * Lo que **no** se prueba aquí: el caso de la sección intacta que no invalida nada se comprueba en la
 * prueba de integración (`test_changes.py`), porque exige dos derivados y dos secciones; y la
 * exportación o el repaso tienen sus propias pruebas.
 */

const API_BASE = process.env.OPOFUENTE_API_URL ?? 'http://127.0.0.1:8765';
const ALLOWED_ORIGIN = { Origin: 'http://127.0.0.1:5173' };

const SUFIJO = Date.now().toString(36);

/** Versión 1: título y plazo. Dos bloques separados por línea en blanco = dos secciones citables. */
const TITULO = `Plazos E2E-09 ${SUFIJO}`;
const BLOQUE_TITULO = `Tema de plazos ${SUFIJO}`;
const V1 = `${BLOQUE_TITULO}\n\nEl plazo del procedimiento es de diez dias habiles.\n`;
const V2 = `${BLOQUE_TITULO}\n\nEl plazo del procedimiento es de veinte dias habiles.\n`;

interface Promocion {
  document_id: string;
  version_id: string;
  created_document: boolean;
  created_version: boolean;
}

async function pegar(page: Page, texto: string, titulo: string): Promise<void> {
  await page.goto('/bandeja');
  await page.getByLabel('Texto', { exact: true }).fill(texto);
  await page.getByLabel('Título (opcional)').fill(titulo);
  await page.getByRole('button', { name: 'Guardar el texto' }).click();
  await expect(
    page.getByRole('region', { name: 'Importación' }).getByText('terminado', { exact: true }).first(),
  ).toBeVisible({ timeout: 60_000 });
}

/** El artefacto que dejó el pegado: se busca su lote por el nombre y se lee su representación. */
async function artefactoDe(request: APIRequestContext, titulo: string): Promise<string> {
  const lotes = (await (
    await request.get(`${API_BASE}/api/v1/ingestion-batches?limit=25`)
  ).json()) as { id: string }[];
  for (const lote of lotes) {
    const detalle = (await (
      await request.get(`${API_BASE}/api/v1/ingestion-batches/${lote.id}`)
    ).json()) as { entries: { original_name: string }[] };
    if (!detalle.entries.some((entrada) => entrada.original_name === titulo)) {
      continue;
    }
    const representaciones = (await (
      await request.get(`${API_BASE}/api/v1/ingestion-batches/${lote.id}/representations`)
    ).json()) as { artifact_id: string }[];
    const primera = representaciones[0];
    if (primera !== undefined) {
      return primera.artifact_id;
    }
  }
  throw new Error(`ningún lote trae ${titulo} con su representación`);
}

async function promocionar(
  request: APIRequestContext,
  artifactId: string,
  documentId?: string,
): Promise<Promocion> {
  const respuesta = await request.post(`${API_BASE}/api/v1/documents`, {
    data: {
      artifact_id: artifactId,
      title: TITULO,
      document_type: 'curriculum',
      ...(documentId === undefined ? {} : { document_id: documentId }),
    },
    headers: ALLOWED_ORIGIN,
  });
  expect(respuesta.ok(), `POST /documents: ${respuesta.status()} ${await respuesta.text()}`).toBe(
    true,
  );
  return (await respuesta.json()) as Promocion;
}

async function aceptar(
  request: APIRequestContext,
  documentId: string,
  versionId: string,
): Promise<void> {
  const respuesta = await request.post(
    `${API_BASE}/api/v1/documents/${documentId}/versions/${versionId}/accept`,
    { headers: ALLOWED_ORIGIN },
  );
  expect(respuesta.ok(), `aceptar versión: ${respuesta.status()}`).toBe(true);
}

test('E2E-09 cambio: versionar, confirmar el diff y revisar el derivado afectado', async ({
  page,
  request,
}) => {
  test.slow();

  // --- 1. La versión 1 entra y se acepta -------------------------------------
  await pegar(page, V1, `e2e-09-${SUFIJO}-v1.txt`);
  const promocion1 = await promocionar(request, await artefactoDe(request, `e2e-09-${SUFIJO}-v1.txt`));
  expect(promocion1.created_document).toBe(true);
  await aceptar(request, promocion1.document_id, promocion1.version_id);

  // --- 2. Un resumen de la segunda sección, desde el lector ------------------
  await page.goto(`/biblioteca?documento=${promocion1.document_id}`);
  await expect(page.getByRole('tab', { name: 'Lector' })).toBeVisible();
  // La segunda sección es la del plazo: se elige en la lista de secciones.
  await page.getByRole('button', { name: 'sección 2', exact: true }).click();
  await page.getByRole('button', { name: /Resumir la sección/ }).click();
  await expect(page.getByText(/Resumen guardado/)).toBeVisible();
  await expect(page.getByText(/queda.{0,20}pendiente de revisar en Cambios/)).toBeVisible();

  // --- 3. La versión 2 con la sección modificada: se propone el cambio -------
  await pegar(page, V2, `e2e-09-${SUFIJO}-v2.txt`);
  const promocion2 = await promocionar(
    request,
    await artefactoDe(request, `e2e-09-${SUFIJO}-v2.txt`),
    promocion1.document_id,
  );
  expect(promocion2.created_version).toBe(true);

  await page.goto('/cambios');
  await expect(page.getByRole('heading', { level: 1, name: 'Cambios' })).toBeVisible();
  // La pantalla lista **todas** las propuestas, y el directorio de datos del E2E se reutiliza: una
  // corrida anterior interrumpida puede haber dejado las suyas sin confirmar. Por eso se busca la
  // propuesta de **este** documento por su título (que lleva el sufijo de la corrida) y se selecciona
  // antes de mirar el detalle, en lugar de dar por hecho que la primera de la lista es la nuestra.
  const lista = page.getByRole('list', { name: 'Cambios de versión' });
  const propio = lista.getByRole('listitem').filter({ hasText: TITULO });
  await expect(propio.getByText('propuesto, sin aplicar')).toBeVisible();
  await propio.getByRole('button', { name: new RegExp(TITULO) }).click();

  const tabla = page.getByRole('table', { name: 'Diff por sección' });
  await expect(tabla.getByText('con el texto cambiado')).toBeVisible();
  await expect(tabla.getByText(/veinte dias habiles/)).toBeVisible();
  await expect(page.getByText(/depende de «sección 2», que ha cambiado/)).toBeVisible();
  // El aviso de lo que la aplicación no decide, a la vista.
  await expect(page.getByText(/No decide si una norma sigue vigente/)).toBeVisible();
  // El resumen todavía no está marcado: nada se ha aplicado.
  await expect(page.getByText('Resúmenes pendientes de revisar')).toHaveCount(0);

  // --- 4. Confirmar: se acepta la versión, se sustituye la anterior ----------
  await page.getByRole('button', { name: 'Confirmar el cambio' }).click();
  await expect(page.getByText(/Cambio aplicado/)).toBeVisible();
  // La lista se relee del servidor: el cambio pasa a estar confirmado, no lo dice la pantalla sola.
  await expect(page.getByText(/Este cambio está confirmado/)).toBeVisible({ timeout: 15_000 });

  // La versión anterior queda histórica y accesible (demo D, paso 5).
  await page.goto(`/biblioteca?documento=${promocion1.document_id}`);
  await page.getByRole('tab', { name: 'Versiones y diff' }).click();
  const panelVersiones = page.getByRole('tabpanel');
  await expect(panelVersiones.getByText('sustituida').first()).toBeVisible();

  // --- 5. El derivado afectado queda pendiente y se revisa -------------------
  await page.goto('/cambios');
  const pendientes = page.getByRole('list', { name: 'Resúmenes pendientes de revisar' });
  // El directorio de datos del E2E se conserva: se mira **este** resumen, el de esta ejecución.
  const mio = pendientes.getByRole('listitem').filter({ hasText: SUFIJO }).first();
  await expect(mio.getByText(/el material del que sale ha cambiado/)).toBeVisible();
  await expect(mio.getByText(/secciones: sección 2/)).toBeVisible();
  await page
    .getByRole('button', {
      name: `Marcar que el resumen sigue valiendo: ${TITULO}: resumen de una sección`,
    })
    .click();
  // Revisado: deja de estar pendiente y sigue guardado con el motivo de la marca.
  await expect(mio).toHaveCount(0, { timeout: 15_000 });

  // --- 6. La pantalla se puede usar -----------------------------------------
  const sinViolaciones = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
    .analyze();
  expect(sinViolaciones.violations).toEqual([]);
});
