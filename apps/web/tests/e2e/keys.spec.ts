import { expect, test, type Page } from '@playwright/test';

/**
 * E2E-07 «Clave corregida» (10_TEST-PLAN §5): importar el conjunto y su clave v1, completar una
 * sesión, importar la v2, activarla, recalcular y ver el resultado anterior y el nuevo.
 *
 * El recorrido es el de una persona que descubre que la plantilla que usó tenía una respuesta mal y
 * la corrige. Nada se reescribe por su cuenta: la sesión guarda lo que se presentó, se añade la
 * corrección nueva y la pantalla explica de dónde a dónde cambió la puntuación.
 *
 * El material es **sintético**: un CSV de cuatro preguntas cuya respuesta correcta es la «a» en la v1
 * y pasa a ser la «b» en la v2.
 */

const CSV = [
  'enunciado;op1;op2;clave',
  'El plazo del expediente numero 11 es de diez dias habiles;Verdadero;Falso;a',
  'El plazo del expediente numero 12 es de veinte dias habiles;Verdadero;Falso;a',
  'El plazo del expediente numero 13 es de treinta dias habiles;Verdadero;Falso;a',
  'El plazo del expediente numero 14 es de cuarenta dias habiles;Verdadero;Falso;a',
].join('\n');

/** Un conjunto con su plantilla v1 activa, importado por la interfaz. */
async function conjuntoConClave(page: Page): Promise<string> {
  const titulo = `Clave E2E ${String(Date.now())}-${String(Math.random()).slice(2, 8)}`;

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

  await page.getByRole('tab', { name: 'Plantillas' }).click();
  await page.getByRole('button', { name: 'Activar la plantilla v1' }).click();
  await page.getByRole('button', { name: 'Confirmar la activación de la plantilla v1' }).click();
  await expect(
    page.getByText('Plantilla activada y aprobada con tu acción: queda registrado en la auditoría.'),
  ).toBeVisible();

  return titulo;
}

/** Responde una práctica de `cantidad` preguntas marcando siempre la «a».
 *
 * La espera es un bucle **a propósito**: al entrar en Estudiar, la pantalla pinta la configuración si
 * todavía no ha leído las sesiones y la sustituye por la sesión abierta cuando la lista llega.
 * Comprobar una sola vez si el botón está —antes de que la lista llegue— saltaba el clic y luego se
 * esperaba una pantalla que ya no iba a aparecer.
 */
async function practicarMarcandoA(page: Page, titulo: string, cantidad: number): Promise<void> {
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
  // Se elige **el conjunto de esta ejecución** por su título irrepetible: el directorio de datos del
  // E2E se reutiliza y hay conjuntos de ejecuciones anteriores con su propia plantilla activa.
  const opcion = conjunto.locator('option').filter({ hasText: titulo });
  await expect(opcion).toHaveCount(1);
  const valor = await opcion.getAttribute('value');
  await conjunto.selectOption(valor ?? '');
  await page.getByLabel('Cuántas preguntas').fill(String(cantidad));
  await page.getByRole('button', { name: 'Crear y empezar la sesión' }).click();
  await expect(page.getByText(/Sesión de práctica lista/)).toBeVisible();

  for (let posicion = 1; posicion <= cantidad; posicion += 1) {
    await expect(page.getByRole('heading', { name: `Pregunta ${String(posicion)}` })).toBeVisible();
    await page.getByLabel('A) Verdadero').check();
    await page.getByRole('button', { name: 'Enviar la respuesta' }).click();
    await expect(page.getByText('Respuesta guardada.')).toBeVisible();
    if (posicion < cantidad) {
      await page.getByRole('button', { name: 'Ir a la pregunta siguiente' }).click();
    }
  }
  await page.getByRole('button', { name: 'Terminar la sesión' }).click();
  await expect(page.getByRole('heading', { name: 'Resultado' })).toBeVisible();
}

test('E2E-07 clave corregida: la v2 recalcula y la pantalla dice de dónde a dónde cambió', async ({
  page,
}) => {
  const titulo = await conjuntoConClave(page);
  await practicarMarcandoA(page, titulo, 3);

  // Con la clave v1 las tres respuestas son correctas: 3 puntos exactos.
  // **El formato es el nuevo** (§2.2 del cierre): la nota va en español, con coma y dos decimales. Esta
  // aserción esperaba `3 puntos` —el formato de `decimal_text`, punto y cuatro cifras—, que es
  // exactamente el «0.0000» que el propietario vio en sus capturas. El que tiene razón es la pantalla.
  await expect(page.getByText('3,00 puntos').first()).toBeVisible();
  await expect(page.getByText(/3 aciertos · 0 fallos · 0 en blanco/).first()).toBeVisible();

  // La plantilla v2 corrige la clave: ahora la buena es la «b». Se importa sola y sustituye a la v1.
  await page.goto('/preguntas');
  await page.getByRole('tab', { name: 'Importar' }).click();
  await page.getByLabel('Qué se importa').selectOption('answer_key');
  await page.getByLabel('Texto a importar').fill('1. b\n2. b\n3. b\n4. b\n');
  await page.getByRole('button', { name: 'Importar en el conjunto' }).click();
  await expect(page.getByText(/1 plantillas|1 plantilla/)).toBeVisible();

  await page.getByRole('tab', { name: 'Plantillas' }).click();
  await page.getByRole('button', { name: 'Activar la plantilla v2' }).click();
  await page.getByRole('button', { name: 'Confirmar la activación de la plantilla v2' }).click();
  await expect(
    page.getByText('Plantilla activada y aprobada con tu acción: queda registrado en la auditoría.'),
  ).toBeVisible();

  // La sesión guardó su corrección con la v1 y no cambia sola: hay que pedir el recálculo.
  await page.goto('/estudiar');
  await expect(page.getByRole('heading', { name: 'Resultado' })).toBeVisible();
  // La nota guardada con la v1, en el formato nuevo (antes esperaba `3 puntos`).
  await expect(page.getByText('3,00 puntos').first()).toBeVisible();
  await page.getByRole('button', { name: 'Recalcular con la plantilla activa' }).click();

  // Y ahora la pantalla explica el cambio: de 3 a -1, porque las tres respuestas pasan a erróneas.
  await expect(page.getByText(/Sesión recalculada/)).toBeVisible();
  await expect(page.getByRole('heading', { name: /Recálculo con una plantilla nueva/ })).toBeVisible();
  await expect(page.getByText('la puntuación cambió').first()).toBeVisible();
  // `-1,00` y no `-1`: el §2.2 pide dos decimales en **todas** las cifras de nota, también en las
  // negativas. Aquí la aserción era `/-1 puntos/`, que dejó de casar en cuanto la pantalla se arregló.
  await expect(page.getByText(/-1,00 puntos/).first()).toBeVisible();
  await expect(page.getByText(/0 aciertos · 3 fallos · 0 en blanco/).first()).toBeVisible();
  // Y con el antes a la vista: la puntuación que se dio con la v1 no se borra.
  // El «antes» es una cifra de nota y va **con dos decimales y coma** (`3,00`), igual que el «ahora»
  // (`-1,00`). Esta aserción esperaba `3 · Primera parte…`, el formato viejo; y no se veía al mirar el
  // rojo de la puerta, porque la prueba **moría antes**, en la aserción de `-1 puntos`. Es la lección
  // del encargo: a las de este género hay que buscarlas por patrón, no por rojo.
  await expect(page.getByText(/3,00 · Primera parte.*plantilla v1/)).toBeVisible();

  // Recargar no pierde la comparación: viaja con el resultado guardado.
  await page.reload();
  await expect(page.getByRole('heading', { name: /Recálculo con una plantilla nueva/ })).toBeVisible();
  await expect(page.getByText(/-1,00 puntos/).first()).toBeVisible();
});
