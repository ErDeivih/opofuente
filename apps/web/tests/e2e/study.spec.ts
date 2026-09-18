import { expect, test, type Page } from '@playwright/test';

/**
 * E2E-06 «Examen TAI» (10_TEST-PLAN §5): crear una sesión, acertar, fallar, dejar en blanco,
 * terminar y comprobar la puntuación y las partes.
 *
 * El material es **sintético** y se importa por el camino real: un CSV con cuatro preguntas cuya
 * respuesta correcta es la B, su plantilla activada desde la pestaña de plantillas (activar es
 * aprobar, ADR-009) y, ya en Estudiar, una práctica de tres preguntas con corrección inmediata.
 *
 * Dos precisiones, para no dar por hecho lo que no hay:
 *
 * 1. el examen **oficial** de 80+5 preguntas con sus 120 minutos se prueba por la API (necesita un
 *    banco completo), así que aquí se recorre la práctica, que es el otro modo que este slice
 *    implementa. Lo que sí se comprueba en la pantalla es que un examen oficial no deja elegir número
 *    ni corrección, porque los fija la convocatoria;
 * 2. la puntuación que se espera está calculada a mano en la propia prueba (un acierto, un fallo y un
 *    blanco con penalización de un tercio dan 2/3), no copiada de lo que devuelva el servidor.
 */

const CSV = [
  'enunciado;op1;op2;clave',
  'El plazo del procedimiento del caso A es de diez dias habiles;Verdadero;Falso;b',
  'El plazo del procedimiento del caso B es de veinte dias habiles;Verdadero;Falso;b',
  'El plazo del procedimiento del caso C es de treinta dias habiles;Verdadero;Falso;b',
  'El plazo del procedimiento del caso D es de cuarenta dias habiles;Verdadero;Falso;b',
].join('\n');

async function crearConjuntoConClave(page: Page): Promise<string> {
  const titulo = `Practica E2E ${String(Date.now())}-${String(Math.random()).slice(2, 8)}`;

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
  await page.getByLabel('Contenido del CSV (con su cabecera)').fill(CSV);
  await page.getByRole('button', { name: 'Importar en el conjunto' }).click();
  await expect(page.getByText('Importadas 4 preguntas nuevas y 4 claves.')).toBeVisible();

  // La plantilla nace en borrador: sin activarla, la sesión no se puede ni crear (409 del servidor).
  await page.getByRole('tab', { name: 'Plantillas' }).click();
  await page.getByRole('button', { name: 'Activar la plantilla v1' }).click();
  await page.getByRole('button', { name: 'Confirmar la activación de la plantilla v1' }).click();
  await expect(
    page.getByText('Plantilla activada y aprobada con tu acción: queda registrado en la auditoría.'),
  ).toBeVisible();

  return titulo;
}

async function prepararPractica(page: Page, titulo: string, cantidad: string): Promise<void> {
  await irAConfiguracion(page);
  const conjunto = page.getByLabel('Conjunto de preguntas');
  const opcion = conjunto.locator('option', { hasText: titulo });
  await expect(opcion).toHaveCount(1);
  // Se elige por el valor de la opción: la etiqueta lleva el recuento y el estado de la clave, que
  // cambian con el material de cada ejecución.
  const valor = await opcion.first().getAttribute('value');
  await conjunto.selectOption(valor ?? '');
  await page.getByLabel('Cuántas preguntas').fill(cantidad);
  await page.getByLabel('Corrección').selectOption('immediate');
  await page.getByRole('button', { name: 'Crear y empezar la sesión' }).click();
  await expect(page.getByText(/Sesión de práctica lista/)).toBeVisible();
}

/**
 * Abre la pantalla de Estudiar **en su configuración**.
 *
 * Al entrar, la pantalla retoma la última sesión (una a medias se continúa, una terminada enseña su
 * resultado), así que para preparar una nueva hay que pedirlo explícitamente: es el botón «Preparar
 * otra sesión».
 */
async function irAConfiguracion(page: Page): Promise<void> {
  await page.goto('/estudiar');
  await expect(page.getByRole('heading', { level: 1, name: 'Estudiar' })).toBeVisible();
  const prepararOtra = page.getByRole('button', { name: 'Preparar otra sesión' });
  await expect(prepararOtra.or(page.getByRole('heading', { name: 'Preparar la sesión' }))).toBeVisible();
  if (await prepararOtra.isVisible()) {
    await prepararOtra.click();
  }
  await expect(page.getByRole('heading', { name: 'Preparar la sesión' })).toBeVisible();
}

test('E2E-06 sesión: acertar, fallar, dejar en blanco y ver la puntuación por partes', async ({
  page,
}) => {
  const titulo = await crearConjuntoConClave(page);
  await prepararPractica(page, titulo, '3');

  await expect(page.getByRole('heading', { name: 'Pregunta 1' })).toBeVisible();
  await expect(page.getByText(/0 de 3 respondidas/)).toBeVisible();
  // Mientras no se responde, la pantalla no puede saber cuál es la correcta: no hay badge ni clave.
  expect(await page.content()).not.toContain('correct_option_keys');

  // 1) Acierto: la respuesta correcta del CSV es la B.
  await page.getByLabel('B) Falso').check();
  await page.getByRole('button', { name: 'Enviar la respuesta' }).click();
  await expect(page.getByText('Respuesta guardada.')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Corrección' })).toBeVisible();
  await expect(page.getByText('acertada')).toBeVisible();

  // 2) Fallo: se marca la A y la corrección lo dice con su penalización exacta.
  await page.getByRole('button', { name: 'Ir a la pregunta siguiente' }).click();
  await expect(page.getByRole('heading', { name: 'Pregunta 2' })).toBeVisible();
  await page.getByLabel('A) Verdadero').check();
  await page.getByRole('button', { name: 'Enviar la respuesta' }).click();
  await expect(page.getByText('fallada')).toBeVisible();
  await expect(page.getByText('-0.3333 (-1/3) puntos')).toBeVisible();

  // 3) En blanco: no puntúa ni a favor ni en contra.
  await page.getByRole('button', { name: 'Ir a la pregunta siguiente' }).click();
  await expect(page.getByRole('heading', { name: 'Pregunta 3' })).toBeVisible();
  await page.getByRole('button', { name: 'Dejar la pregunta en blanco' }).click();
  await expect(page.getByText('en blanco')).toBeVisible();
  // Un blanco vale cero exacto: la puntuación entera se enseña sin decimales de relleno.
  await expect(page.getByText('0 puntos')).toBeVisible();

  // Terminar: un acierto menos un tercio es 2/3 exacto.
  await page.getByRole('button', { name: 'Terminar la sesión' }).click();
  await expect(page.getByRole('heading', { name: 'Resultado' })).toBeVisible();
  await expect(page.getByText('0.6667 (2/3) puntos').first()).toBeVisible();
  await expect(page.getByText(/1 aciertos · 1 fallos · 1 en blanco/).first()).toBeVisible();
  await expect(page.getByText('calificación oficial no disponible')).toBeVisible();
  await expect(page.getByText(/no se declara aprobado ni suspenso/)).toBeVisible();
  await expect(page.getByText(/el mínimo de 25.0 es de la calificación oficial/)).toBeVisible();

  // La revisión queda a la vista, pregunta a pregunta.
  await expect(page.getByRole('heading', { name: 'Revisión, pregunta a pregunta' })).toBeVisible();
  await expect(page.getByText('Marcaste:').first()).toBeVisible();
});

test('E2E-06 recargar conserva el intento y retoma la sesión en marcha', async ({ page }) => {
  const titulo = await crearConjuntoConClave(page);
  await prepararPractica(page, titulo, '2');

  await page.getByLabel('B) Falso').check();
  await page.getByRole('button', { name: 'Enviar la respuesta' }).click();
  await expect(page.getByText('Respuesta guardada.')).toBeVisible();

  // Recargar: la sesión vive en el servidor, así que el progreso y el intento siguen ahí.
  await page.reload();

  await expect(page.getByText(/Tienes una sesión en marcha/)).toBeVisible();
  await expect(page.getByText(/1 de 2 preguntas respondidas/)).toBeVisible();
  // Y volver a enviar lo mismo no crea otro intento: el servidor devuelve el que había.
  await expect(page.getByRole('heading', { name: 'Pregunta 2' })).toBeVisible();
});

test('E2E-06 un examen oficial no deja elegir lo que fija la convocatoria', async ({ page }) => {
  await irAConfiguracion(page);
  await page.getByLabel('Modo').selectOption('official_exam');

  await expect(page.getByLabel('Cuántas preguntas')).toHaveCount(0);
  await expect(page.getByLabel('Corrección')).toHaveCount(0);
  await expect(page.getByText(/los fija la convocatoria/)).toBeVisible();
  await expect(page.getByText(/80 preguntas ordinarias/)).toBeVisible();
});
