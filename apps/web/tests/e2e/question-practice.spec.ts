import { expect, test, type Page } from '@playwright/test';

/**
 * E2E-05 «Preguntas», segunda mitad (10_TEST-PLAN §5): **practicar las aceptadas**.
 *
 * El guion de `questions.spec.ts` cubre importar un CSV parcialmente inválido, corregir el mapeo y ver
 * las rechazadas; su punto 5 comprobaba «lo aceptado es utilizable» mirando la ficha y activando la
 * plantilla. Eso no es practicar. Aquí se cierra esa parte con el camino completo:
 *
 * 1. se importa por el **asistente JSON** (la otra mitad del entregable del slice, que antes no
 *    existía): una pregunta buena, una sin enunciado y una con una clave imposible;
 * 2. se activa la plantilla, porque activar es aprobar (ADR-009);
 * 3. se practica de verdad en Estudiar: se responde la pregunta importada, se envía y la corrección
 *    confirma que la clave del JSON viajó hasta la sesión.
 *
 * El material es sintético y se escribe en la pantalla. El título del conjunto lleva un sufijo único
 * porque los datos del E2E se reutilizan entre ejecuciones y la importación es idempotente por huella.
 */

const JSON_PREGUNTAS = JSON.stringify(
  {
    model_code: 'A',
    questions: [
      {
        stem: 'El plazo del procedimiento del caso E es de diez dias habiles',
        options: ['Verdadero', 'Falso'],
        correct: 'Falso',
        number: 1,
      },
      { stem: '', options: ['uno', 'dos'] },
      { stem: 'Clave imposible', options: ['uno', 'dos'], correct: 'z' },
    ],
  },
  null,
  0,
);

/**
 * Abre Estudiar **en su configuración** y espera a que esté.
 *
 * Al entrar, la pantalla retoma la última sesión (una a medias se continúa, una terminada enseña su
 * resultado), así que hay que pedir explícitamente una nueva. La espera **después** del clic no es
 * adorno: pedir otra sesión vuelve a consultar el servidor, y sin esperar a que termine la transición
 * se comprueba el encabezado antes de que exista. La primera versión de esta prueba no esperaba y
 * fallaba a veces cuando la suite corría entera; esperar a que «Preparar otra sesión» desaparezca es
 * esperar a lo que de verdad cambia.
 *
 * Y la espera es un bucle **a propósito**: la pantalla pinta la configuración si todavía no ha leído
 * las sesiones y la sustituye por la sesión abierta cuando la lista llega, así que comprobar una sola
 * vez si el botón está —antes de que la lista llegue— saltaba el clic y luego se esperaba una pantalla
 * que ya no iba a aparecer.
 */
async function irAConfiguracion(page: Page): Promise<void> {
  await page.goto('/estudiar');
  await expect(page.getByRole('heading', { level: 1, name: 'Estudiar' })).toBeVisible();
  const prepararOtra = page.getByRole('button', { name: 'Preparar otra sesión' });
  await expect(async () => {
    if (await prepararOtra.isVisible()) {
      await prepararOtra.click();
      await expect(prepararOtra).toHaveCount(0, { timeout: 1_000 });
    }
    await expect(page.getByRole('heading', { name: 'Preparar la sesión' })).toBeVisible({
      timeout: 1_000,
    });
  }).toPass({ timeout: 20_000 });
}

test('E2E-05 practicar: el JSON importado se activa y se responde en una sesión', async ({
  page,
}) => {
  const titulo = `JSON E2E ${String(Date.now())}-${String(Math.random()).slice(2, 8)}`;

  await page.goto('/preguntas');
  await expect(page.getByRole('heading', { level: 1, name: 'Preguntas' })).toBeVisible();
  await page.locator('summary').filter({ hasText: 'Crear un conjunto' }).click();
  await page.getByLabel('Título', { exact: true }).fill(titulo);
  await page.getByRole('button', { name: 'Crear conjunto: de preguntas' }).click();
  await expect(page.getByText(`Conjunto «${titulo}» creado.`)).toBeVisible();

  // 1. Importación por JSON: lo malo se informa con su causa y lo bueno entra.
  await page.getByRole('tab', { name: 'Importar' }).click();
  await page.getByLabel('Qué se importa').selectOption('json');
  await page.getByLabel(/Contenido del JSON/).fill(JSON_PREGUNTAS);
  await page.getByRole('button', { name: 'Importar en el conjunto' }).click();

  await expect(page.getByText('Importadas 1 preguntas nuevas y 1 claves.')).toBeVisible();
  const informe = page.locator('section[aria-labelledby="informe-importacion"]');
  await expect(informe.getByText('no_stem')).toBeVisible();
  await expect(informe.getByText('key_without_option')).toBeVisible();

  // 2. La plantilla nace en borrador: activarla es aprobarla y es lo que hace utilizable el banco.
  await page.getByRole('tab', { name: 'Plantillas' }).click();
  await page.getByRole('button', { name: 'Activar la plantilla v1' }).click();
  await page.getByRole('button', { name: 'Confirmar la activación de la plantilla v1' }).click();
  await expect(
    page.getByText('Plantilla activada y aprobada con tu acción: queda registrado en la auditoría.'),
  ).toBeVisible();

  // 3. Practicar lo importado, de verdad: la clave del JSON («Falso») tiene que llegar a la corrección.
  await irAConfiguracion(page);

  const conjunto = page.getByLabel('Conjunto de preguntas');
  const opcion = conjunto.locator('option', { hasText: titulo });
  await expect(opcion).toHaveCount(1);
  await conjunto.selectOption((await opcion.first().getAttribute('value')) ?? '');
  await page.getByLabel('Cuántas preguntas').fill('1');
  await page.getByLabel('Corrección').selectOption('immediate');
  await page.getByRole('button', { name: 'Crear y empezar la sesión' }).click();

  await expect(page.getByText(/Sesión de práctica lista/)).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Pregunta 1' })).toBeVisible();
  await expect(
    page.getByText('El plazo del procedimiento del caso E es de diez dias habiles'),
  ).toBeVisible();

  await page.getByLabel('B) Falso').check();
  await page.getByRole('button', { name: 'Responder: enviar la respuesta' }).click();

  await expect(page.getByText('Respuesta guardada.')).toBeVisible();
  await expect(page.getByText('acertada')).toBeVisible();
});
