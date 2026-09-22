import AxeBuilder from '@axe-core/playwright';
import { expect, test, type APIRequestContext, type Page } from '@playwright/test';

/**
 * S10 — errores, repaso y exportación (07_UI-UX §9, 06_QUESTIONS §8 y 08_API-CONTRACT §11).
 *
 * El recorrido es el de una persona: practicar, fallar, decir **por qué** se ha fallado, ver el fallo
 * en la cola de repaso, repasarlo de verdad en una sesión compuesta con lo vencido y exportar el
 * banco con su procedencia.
 *
 * El material es **sintético** y entra por el camino real (un CSV con cuatro preguntas y su plantilla
 * activada). Cada ejecución lleva su sufijo en el título del conjunto **y en los enunciados**: el
 * directorio de datos del E2E se conserva entre ejecuciones y dos preguntas idénticas de dos
 * ejecuciones no se pueden distinguir en la cola.
 *
 * Antes de empezar, la prueba deja la cola de repaso **vacía** con la propia API (aplaza lo que
 * estuviera vencido de ejecuciones anteriores). Sin eso, la sesión de repaso traería preguntas de
 * otras ejecuciones y lo que se mide dejaría de ser este recorrido.
 *
 * Lo que **no** se prueba aquí: el aviso de material restringido necesita un documento con derechos
 * restringidos y se monta en la prueba de integración (`test_exports.py`); la exportación a Markdown
 * tiene su prueba de API y de interfaz.
 */

const API_BASE = process.env.OPOFUENTE_API_URL ?? 'http://127.0.0.1:8765';
const ALLOWED_ORIGIN = { Origin: 'http://127.0.0.1:5173' };

/** Deja la cola de repaso sin nada vencido, aplazando lo que hubiera de otras ejecuciones. */
async function vaciarColaDeRepaso(request: APIRequestContext): Promise<void> {
  const respuesta = await request.get(`${API_BASE}/api/v1/reviews/due?limit=200`);
  if (!respuesta.ok()) {
    return;
  }
  const cola = (await respuesta.json()) as { items: { review: { id: string } }[] };
  for (const item of cola.items) {
    await request.post(`${API_BASE}/api/v1/reviews/${item.review.id}/snooze`, {
      data: { days: 30 },
      headers: ALLOWED_ORIGIN,
    });
  }
}

interface Material {
  readonly titulo: string;
  readonly enunciado: string;
  readonly csv: string;
}

/**
 * Material sintético propio de cada prueba: el sufijo va en el título **y en los enunciados**.
 *
 * El directorio de datos del E2E se conserva entre ejecuciones (y entre pruebas), así que dos
 * preguntas idénticas de dos ejecuciones no se pueden distinguir en la cola; y dos conjuntos con el
 * mismo título tampoco se pueden elegir en el selector sin ambigüedad.
 */
function material(etiqueta: string): Material {
  const sufijo = `${Date.now().toString(36)}-${etiqueta}`;
  const enunciado = `El plazo del procedimiento del caso ${sufijo} es de diez dias habiles`;
  return {
    titulo: `Errores E2E ${sufijo}`,
    enunciado,
    csv: [
      'enunciado;op1;op2;clave',
      `${enunciado};Verdadero;Falso;b`,
      `El plazo del procedimiento del caso B ${sufijo} es de veinte dias habiles;Verdadero;Falso;b`,
      `El plazo del procedimiento del caso C ${sufijo} es de treinta dias habiles;Verdadero;Falso;b`,
      `El plazo del procedimiento del caso D ${sufijo} es de cuarenta dias habiles;Verdadero;Falso;b`,
    ].join('\n'),
  };
}

/** La fila de **esta** prueba en la cola de repaso. */
function filaDe(page: Page, material_: Material) {
  return page.getByRole('listitem').filter({ hasText: material_.enunciado }).first();
}

async function crearConjuntoConClave(page: Page, material_: Material): Promise<string> {
  const titulo = material_.titulo;

  await page.goto('/preguntas');
  await page.locator('summary').filter({ hasText: 'Crear un conjunto' }).click();
  await page.getByLabel('Título', { exact: true }).fill(titulo);
  await page.getByRole('button', { name: 'Crear el conjunto de preguntas' }).click();
  await expect(page.getByText(`Conjunto «${titulo}» creado.`)).toBeVisible();

  await page.getByRole('tab', { name: 'Importar' }).click();
  await page.getByLabel('Qué se importa').selectOption('csv');
  await page.getByLabel('Columna del enunciado').fill('enunciado');
  await page.getByLabel('Columnas de opciones (separadas por comas)').fill('op1, op2');
  await page.getByLabel('Columna de la clave').fill('clave');
  await page.getByLabel('Contenido del CSV (con su cabecera)').fill(material_.csv);
  await page.getByRole('button', { name: 'Importar en el conjunto' }).click();
  await expect(page.getByText('Importadas 4 preguntas nuevas y 4 claves.')).toBeVisible();

  await page.getByRole('tab', { name: 'Plantillas' }).click();
  await page.getByRole('button', { name: 'Activar la plantilla v1' }).click();
  await page.getByRole('button', { name: 'Confirmar la activación de la plantilla v1' }).click();
  await expect(
    page.getByText('Plantilla activada y aprobada con tu acción: queda registrado en la auditoría.'),
  ).toBeVisible();

  return titulo;
}

/** Prepara una práctica de una pregunta y la falla, declarando después por qué.
 *
 * La espera es un bucle **a propósito**, y no un `if` seguido de una espera: al entrar en Estudiar, la
 * pantalla pinta la configuración si todavía no ha leído las sesiones y la sustituye por la sesión
 * abierta cuando la lista llega. Comprobar una sola vez si el botón está —antes de que la lista llegue—
 * saltaba el clic y luego se esperaba una pantalla que ya no iba a aparecer. El bucle pulsa «Preparar
 * otra sesión» cuando aparece y comprueba el resultado; lo que se afirma es lo mismo.
 */
async function practicarYFallar(page: Page, titulo: string): Promise<void> {
  await page.goto('/estudiar');
  const prepararOtra = page.getByRole('button', { name: 'Preparar otra sesión' });
  await expect(async () => {
    if (await prepararOtra.isVisible()) {
      await prepararOtra.click();
    }
    await expect(page.getByRole('heading', { name: 'Preparar la sesión' })).toBeVisible({
      timeout: 1_000,
    });
  }).toPass({ timeout: 20_000 });

  const conjunto = page.getByLabel('Conjunto de preguntas');
  const opcion = conjunto.locator('option', { hasText: titulo });
  await expect(opcion).toHaveCount(1);
  await conjunto.selectOption((await opcion.first().getAttribute('value')) ?? '');
  await page.getByLabel('Cuántas preguntas').fill('1');
  await page.getByLabel('Corrección').selectOption('immediate');
  await page.getByRole('button', { name: 'Crear y empezar la sesión' }).click();
  await expect(page.getByText(/Sesión de práctica lista/)).toBeVisible();

  // La clave correcta del CSV es la B: se marca la A y se falla.
  await page.getByLabel('A) Verdadero').check();
  await page.getByRole('button', { name: 'Enviar la respuesta' }).click();
  await expect(page.getByText('fallada')).toBeVisible();

  // Y se declara por qué: el fallo entra en el repaso solo, la causa la pone la persona.
  await page.getByLabel('¿Por qué has fallado?').selectOption('confusion');
  await page.getByLabel('Sobre qué era').fill('plazos');
  await page.getByLabel('Nota propia').fill('Lo confundí con el cómputo');
  await page.getByRole('button', { name: 'Guardar la causa' }).click();
  await expect(page.getByText(/Causa declarada: lo confundí con otra cosa/)).toBeVisible();
}

test('S10 errores: el fallo entra en la cola, se declara su causa, se repasa y se exporta', async ({
  page,
  request,
}) => {
  test.slow();
  await vaciarColaDeRepaso(request);
  const datos = material('cola');
  const titulo = await crearConjuntoConClave(page, datos);
  await practicarYFallar(page, titulo);

  // --- 1. La cola de hoy: qué toca, desde cuándo y por qué -------------------
  await page.goto('/errores');
  await expect(page.getByRole('heading', { level: 1, name: 'Errores' })).toBeVisible();
  // La cola solo tiene **vencido** el fallo de esta ejecución: lo demás se acaba de aplazar.
  await expect(page.getByText(/1 de \d+ vencidos/)).toBeVisible();
  const fila = filaDe(page, datos);
  await expect(fila).toBeVisible();
  await expect(fila.getByText('toca hoy')).toBeVisible();
  await expect(fila.getByText('un fallo entra en la cola de hoy mismo').first()).toBeVisible();
  // La cola deja repasar, pero no dice cuál es la correcta antes del intento.
  await expect(fila.getByText('Verdadero')).toBeVisible();
  expect(await fila.innerHTML()).not.toContain('correct_option_keys');

  // --- 2. Los conceptos: el error con su causa y su historial ----------------
  await page.getByRole('tab', { name: 'Conceptos' }).click();
  const panel = page.getByRole('tabpanel');
  await expect(panel.getByText('plazos')).toBeVisible();
  await panel.getByRole('button', { name: `Abrir el error de «${datos.enunciado}»` }).click();
  await expect(page.getByRole('heading', { name: 'Error declarado' })).toBeVisible();
  const ficha = page.getByRole('region', { name: 'Error declarado' });
  await expect(ficha.getByText('lo confundí con otra cosa')).toBeVisible();
  // La nota propia es editable, así que vive en un campo: se comprueba su valor.
  await expect(ficha.getByLabel('Nota propia')).toHaveValue('Lo confundí con el cómputo');
  await expect(ficha.getByText('0 → 0 día(s)').first()).toBeVisible();
  await expect(page.getByText('un fallo entra en la cola de hoy mismo').first()).toBeVisible();

  // --- 3. Repasar de verdad: una sesión compuesta con lo vencido -------------
  await page.getByRole('tab', { name: 'Hoy' }).click();
  await page.getByRole('button', { name: /Repasar en una sesión/ }).click();
  await expect(page.getByRole('heading', { level: 1, name: 'Estudiar' })).toBeVisible();
  // La sesión nace sin empezar, como cualquier otra: se arranca y se contesta.
  await expect(page.getByText(/ya está creada con su composición congelada/)).toBeVisible();
  await page.getByRole('button', { name: 'Empezar la sesión pendiente' }).click();
  await expect(page.getByText(/repaso de errores/).first()).toBeVisible();
  await page.getByLabel('B) Falso').check();
  await page.getByRole('button', { name: 'Enviar la respuesta' }).click();
  await expect(page.getByText('acertada')).toBeVisible();

  // --- 4. El repaso reprograma: sale de la cola y el intervalo sube ----------
  await page.goto('/errores');
  await expect(page.getByText(/No hay nada vencido/).first()).toBeVisible();
  await page.getByRole('tab', { name: 'Conceptos' }).click();
  await page.getByRole('button', { name: `Abrir el error de «${datos.enunciado}»` }).click();
  await expect(ficha.getByText(/cada 4 día\(s\)/)).toBeVisible();
  await expect(ficha.getByText(/acertada después de un fallo: cuatro días/)).toBeVisible();

  // --- 5. Exportar: el fichero con su procedencia y sus avisos ---------------
  await page.getByLabel('Título del fichero').fill(`Errores E2E ${titulo}`);
  await page.getByRole('button', { name: 'Exportar el banco para Anki' }).click();
  await expect(page.getByRole('heading', { name: 'Última exportación' })).toBeVisible();
  await expect(page.getByText(/\.csv$/).first()).toBeVisible();
  // Sin documentos de origen no hay cita: se exporta, pero se dice que no se puede comprobar.
  await expect(page.getByText('Antes de usarlo fuera de aquí')).toBeVisible();
  await expect(page.getByText(/no citan ninguna evidencia/)).toBeVisible();
  await expect(page.getByRole('button', { name: 'Descargar el fichero exportado' })).toBeVisible();

  // --- 6. La pantalla se puede usar -----------------------------------------
  const sinViolaciones = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
    .analyze();
  expect(sinViolaciones.violations).toEqual([]);
});

test('S10 errores: un repaso se puede aplazar sin contarlo como repasado', async ({
  page,
  request,
}) => {
  test.slow();
  await vaciarColaDeRepaso(request);
  const datos = material('cola');
  const titulo = await crearConjuntoConClave(page, datos);
  await practicarYFallar(page, titulo);

  await page.goto('/errores');
  const fila = filaDe(page, datos);
  await expect(fila).toBeVisible();
  await fila.getByRole('button', { name: `Aplazar el repaso de «${datos.enunciado}» tres días` }).click();

  // Aplazar no es repasar: sale de la cola de hoy y sigue esperando su fecha.
  await expect(fila).toHaveCount(0);
  await expect(page.getByText(/No hay nada vencido/).first()).toBeVisible();
});
