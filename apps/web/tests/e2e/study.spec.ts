import AxeBuilder from '@axe-core/playwright';
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

/** Los tres anchos de referencia de 07_UI-UX §14. */
const VIEWPORTS = [
  { name: 'escritorio 1440x900', width: 1440, height: 900 },
  { name: 'portátil 1024x768', width: 1024, height: 768 },
  { name: 'móvil 390x844', width: 390, height: 844 },
];

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

/**
 * Un conjunto con las preguntas y las reservas que pide la convocatoria, importadas por texto.
 *
 * Es lo que hace falta para montar un simulacro: el perfil exacto del examen son sus 80 preguntas
 * ordinarias y sus 5 reservas. Cada pregunta lleva su respuesta en la línea de la clave, así que la
 * plantilla nace con desenlaces; activarla es el paso que la vuelve la clave que corrige.
 */
async function crearConjuntoDeExamen(
  page: Page,
  preguntas: number,
  reservas: number,
): Promise<string> {
  const titulo = `Examen E2E ${String(Date.now())}-${String(Math.random()).slice(2, 8)}`;

  await page.goto('/preguntas');
  await page.locator('summary').filter({ hasText: 'Crear un conjunto' }).click();
  await page.getByLabel('Título', { exact: true }).fill(titulo);
  await page.getByRole('button', { name: 'Crear el conjunto de preguntas' }).click();
  await expect(page.getByText(`Conjunto «${titulo}» creado.`)).toBeVisible();

  const lineas: string[] = [];
  for (let numero = 1; numero <= preguntas + reservas; numero += 1) {
    const marca = numero > preguntas ? '[R] ' : '';
    lineas.push(`${String(numero)}. ${marca}El supuesto ${String(numero)} se resuelve así:`);
    lineas.push('a) Opcion A');
    lineas.push('b) Opcion B');
    lineas.push('Respuesta correcta: a');
    lineas.push('');
  }

  await page.getByRole('tab', { name: 'Importar' }).click();
  await page.getByLabel('Texto a importar').fill(lineas.join('\n'));
  await page.getByRole('button', { name: 'Importar en el conjunto' }).click();
  await expect(
    page.getByText(`Importadas ${String(preguntas + reservas)} preguntas nuevas`),
  ).toBeVisible({ timeout: 30_000 });

  await page.getByRole('tab', { name: 'Plantillas' }).click();
  await page.getByRole('button', { name: 'Activar la plantilla v1' }).click();
  await page.getByRole('button', { name: 'Confirmar la activación de la plantilla v1' }).click();
  await expect(
    page.getByText('Plantilla activada y aprobada con tu acción: queda registrado en la auditoría.'),
  ).toBeVisible();

  return titulo;
}

async function prepararPractica(page: Page, titulo: string, cantidad: string): Promise<void> {  await irAConfiguracion(page);
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
 *
 * La espera es un bucle **a propósito**, y no un `if` seguido de una espera: la pantalla pinta la
 * configuración si todavía no ha leído las sesiones y la sustituye por la sesión abierta cuando la
 * lista llega. Comprobar una sola vez si el botón está —antes de que la lista llegue— saltaba el clic y
 * luego se esperaba una pantalla que ya no iba a aparecer. Lo que se afirma es lo mismo: la
 * configuración a la vista.
 */
async function irAConfiguracion(page: Page): Promise<void> {
  await page.goto('/estudiar');
  await expect(page.getByRole('heading', { level: 1, name: 'Estudiar' })).toBeVisible();
  const prepararOtra = page.getByRole('button', { name: 'Preparar otra sesión' });
  await expect(async () => {
    if (await prepararOtra.isVisible()) {
      await prepararOtra.click();
    }
    await expect(page.getByRole('heading', { name: 'Preparar la sesión' })).toBeVisible({
      timeout: 1_000,
    });
  }).toPass({ timeout: 20_000 });
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
  // El formato de la nota es **el nuevo** (§2.2 del cierre): coma y dos decimales. Esta aserción
  // esperaba `-0.3333 (-1/3)`, el decimal crudo del servidor —el «0.0000» que el propietario vio en sus
  // capturas—. La que tiene razón es la pantalla; lo que se actualiza es la expectativa.
  await expect(page.getByText('-0,33 (-1/3) puntos')).toBeVisible();

  // 3) En blanco: no puntúa ni a favor ni en contra.
  await page.getByRole('button', { name: 'Ir a la pregunta siguiente' }).click();
  await expect(page.getByRole('heading', { name: 'Pregunta 3' })).toBeVisible();
  await page.getByRole('button', { name: 'Dejar la pregunta en blanco' }).click();
  await expect(page.getByText('en blanco')).toBeVisible();
  // Un blanco vale cero, y el cero de una **nota** también va con dos decimales: `0,00 puntos`. Aquí
  // ponía `0 puntos` y **pasaba por casualidad**: `0,00 puntos` contiene `0 puntos` como trozo, así que
  // la aserción no habría notado nunca un cambio de formato. Es el caso que el aislamiento no ve,
  // porque solo mira las que fallan.
  await expect(page.getByText('0,00 puntos')).toBeVisible();

  // Terminar: un acierto menos un tercio es 2/3 exacto.
  await page.getByRole('button', { name: 'Terminar la sesión' }).click();
  await expect(page.getByRole('heading', { name: 'Resultado' })).toBeVisible();
  // La fracción exacta sigue detrás —`(2/3)`—, y delante va la cifra en español: `0,67`.
  await expect(page.getByText('0,67 (2/3) puntos').first()).toBeVisible();
  await expect(page.getByText(/1 aciertos · 1 fallos · 1 en blanco/).first()).toBeVisible();
  await expect(page.getByText('calificación oficial no disponible')).toBeVisible();
  await expect(page.getByText(/no se declara aprobado ni suspenso/)).toBeVisible();
  // El aviso del mínimo lo compone **el dominio**, no la interfaz, y sigue con su punto (`25.0`): el
  // §2.2 formatea las cifras que pinta la pantalla, y este texto viaja ya escrito desde el servidor.
  // El punto va **escapado** a propósito: con `/25.0/` el `.` era un comodín y la aserción casaba
  // también con `25,0`, así que no habría cazado nunca un cambio de formato. Ahora sí lo caza.
  // El mínimo va **sin ceros de más** (`25`, no `25.0` ni `25,00`): es una escala publicada, no una
  // nota. Antes decía `25.0` —el flotante crudo del servidor— y esta aserción lo daba por bueno
  // porque el `.` del regex era un comodín, así que no habría cazado nunca un cambio de formato.
  await expect(page.getByText('el mínimo de 25 es de la calificación oficial')).toBeVisible();

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

test('E2E-06 activar una clave corregida avisa y recalcula lo ya corregido (DEBT-013)', async ({
  page,
}) => {
  const titulo = await crearConjuntoConClave(page);
  await prepararPractica(page, titulo, '3');

  // Se fallan las tres: la plantilla del CSV dice que la buena es la B.
  for (const posicion of [1, 2, 3]) {
    await expect(page.getByRole('heading', { name: `Pregunta ${String(posicion)}` })).toBeVisible();
    await page.getByLabel('A) Verdadero').check();
    await page.getByRole('button', { name: 'Enviar la respuesta' }).click();
    await expect(page.getByText('Respuesta guardada.')).toBeVisible();
    if (posicion < 3) {
      await page.getByRole('button', { name: 'Ir a la pregunta siguiente' }).click();
    }
  }
  await page.getByRole('button', { name: 'Terminar la sesión' }).click();
  await expect(page.getByRole('heading', { name: 'Resultado' })).toBeVisible();
  // Tres fallos con un tercio de castigo: −1 exacto, y escrito como el §2.2 pide (`-1,00`). La
  // aserción esperaba `-1 puntos`, que es el formato viejo del servidor.
  await expect(page.getByText('-1,00 puntos').first()).toBeVisible();

  // La plantilla estaba mal: la buena es la A. Se importa corregida y se activa desde la pantalla.
  // Importar **no** activa nada (es la regla del importador), así que la activación es el clic
  // siguiente, y es lo que tiene que hacer que la pantalla avise.
  await page.goto('/preguntas');
  const conjunto = page.getByLabel('Conjunto abierto');
  const opcion = conjunto.locator('option', { hasText: titulo });
  await expect(opcion).toHaveCount(1);
  await conjunto.selectOption((await opcion.first().getAttribute('value')) ?? '');
  await page.getByRole('tab', { name: 'Importar' }).click();
  await page.getByLabel('Qué se importa').selectOption('answer_key');
  await page.getByLabel('Texto a importar').fill('1. a\n2. a\n3. a\n4. a\n');
  await page.getByRole('button', { name: 'Importar en el conjunto' }).click();
  await expect(page.getByText('Importadas 0 preguntas nuevas y 4 claves.')).toBeVisible();

  await page.getByRole('tab', { name: 'Plantillas' }).click();
  // Antes de activarla, la clave en borrador no corrige nada: la sesión está «al día» con la v1.
  await expect(page.getByText('0 sesiones desactualizadas')).toBeVisible();
  await page.getByRole('button', { name: 'Activar la plantilla v2' }).click();
  await page
    .getByRole('button', { name: 'Confirmar la activación de la plantilla v2' })
    .click();

  // Y aquí está lo que faltaba: la pantalla dice cuántas sesiones se quedan con la corrección vieja.
  await expect(page.getByText('1 sesión desactualizada')).toBeVisible();

  await page.getByRole('button', { name: 'Recalcular la sesión desactualizada' }).click();

  // El informe dice qué cambió, con las dos puntuaciones: −1 (todo mal) pasa a 3 (todo bien).
  await expect(page.getByText(/1 sesión\(es\) recalculadas con la plantilla v2/)).toBeVisible();
  await expect(page.getByText(/de -1 a 3/)).toBeVisible();
  await expect(page.getByText('0 sesiones desactualizadas')).toBeVisible();
});

test('E2E-06 un diagnóstico reparte la muestra por temas y la lee con su intervalo (DEBT-012)', async ({
  page,
}) => {
  const titulo = await crearConjuntoConClave(page);

  // Se importan seis preguntas con su tema: la muestra se reparte por temas del programa, así que sin
  // temas no hay diagnóstico. Es la vía documentada (la columna `topic` del CSV).
  await page.goto('/preguntas');
  const conjunto = page.getByLabel('Conjunto abierto');
  const opcion = conjunto.locator('option', { hasText: titulo });
  await expect(opcion).toHaveCount(1);
  await conjunto.selectOption((await opcion.first().getAttribute('value')) ?? '');
  await page.getByRole('tab', { name: 'Importar' }).click();
  await page.getByLabel('Qué se importa').selectOption('csv');
  await page.getByLabel('Columna del enunciado').fill('enunciado');
  await page.getByLabel('Columnas de opciones (separadas por comas)').fill('op1, op2');
  await page.getByLabel('Columna de la clave').fill('clave');
  await page.getByLabel('Columna del tema').fill('tema');
  await page.getByLabel('Contenido del CSV (con su cabecera)').fill(
    [
      'enunciado;op1;op2;clave;tema',
      'La Constitucion se aprobo en;1976;1978;a;I.1',
      'Las Cortes Generales son;bicamerales;unicamerales;a;I.2',
      'El Gobierno se compone de;presidente y ministros;diputados;a;I.3',
      'El DNI electronico sirve para;identificarse;firmar;a;I.1',
      'La proteccion de datos se regula en;la LOPDGDD;la LEC;a;I.2',
      'La sede electronica es;un punto de acceso;un registro;a;I.3',
    ].join('\n'),
  );
  await page.getByRole('button', { name: 'Importar en el conjunto' }).click();
  await expect(page.getByText('Importadas 6 preguntas nuevas y 6 claves.')).toBeVisible();

  // La plantilla que llega con el CSV nace en borrador: sin activarla no se corrige nada.
  await page.getByRole('tab', { name: 'Plantillas' }).click();
  await page.getByRole('button', { name: 'Activar la plantilla v2' }).click();
  await page
    .getByRole('button', { name: 'Confirmar la activación de la plantilla v2' })
    .click();
  await expect(page.getByText(/Plantilla activada y aprobada/)).toBeVisible();

  // Y el diagnóstico: sin elegir conjunto ni parte, porque la muestra la compone el servidor.
  await irAConfiguracion(page);
  await page.getByText('¿No sabes por dónde empezar? Haz un diagnóstico').click();
  await expect(page.getByText(/muestra pequeña repartida por temas/)).toBeVisible();
  await page.getByRole('button', { name: 'Crear el diagnóstico' }).click();

  await expect(page.getByText(/Sesión de diagnóstico lista/)).toBeVisible();
  // Dos preguntas por tema: tres temas del CSV, seis preguntas.
  await expect(page.getByText(/0 de 6 respondidas/)).toBeVisible();

  // Se contestan las seis (todas correctas: la clave del CSV es la opción A, la primera). El
  // diagnóstico corrige al terminar, así que aquí solo se confirma que la respuesta se guardó.
  for (let posicion = 1; posicion <= 6; posicion += 1) {
    await expect(
      page.getByRole('heading', { name: `Pregunta ${String(posicion)}` }),
    ).toBeVisible();
    await page.getByRole('radio').first().check();
    await page.getByRole('button', { name: 'Enviar la respuesta' }).click();
    await expect(page.getByText('Respuesta guardada.', { exact: true })).toBeVisible();
    if (posicion < 6) {
      await page.getByRole('button', { name: 'Ir a la pregunta siguiente' }).click();
    }
  }
  await page.getByRole('button', { name: 'Terminar la sesión' }).click();

  // La lectura por temas, con su intervalo y su muestra: lo que un diagnóstico tiene que decir.
  await expect(page.getByRole('heading', { name: 'Estimación por tema' })).toBeVisible();
  await expect(page.getByText(/un intervalo estrecho no es posible/)).toBeVisible();
  const tabla = page.getByRole('table', { name: /Muestra por tema con su intervalo/ });
  await expect(tabla).toBeVisible();
  await expect(tabla.getByRole('row')).toHaveCount(4, { timeout: 10_000 });
  // El tema se llama como el programa oficial (el nodo del temario), no como la columna del CSV.
  const filaTema = tabla.getByRole('row', { name: /Constitución Española de 1978/ });
  await expect(filaTema).toContainText('2 de 2');
  // El intervalo del diagnóstico, en el formato nuevo: era el **otro** sitio donde la pantalla pintaba
  // un número con punto (`0.34 – 1.00`), y el §2.2 lo manda en español. Misma razón que arriba.
  await expect(filaTema).toContainText('0,34 – 1,00');
  // Y el resultado no se llama nota: es el recuento de una muestra.
  await expect(page.getByText(/no son una nota ni un dominio/)).toBeVisible();
});

test('E2E-06 un simulacro monta el perfil exacto y el resultado no se llama oficial (DEBT-012)', async ({
  page,
}) => {
  // Se importan 85 preguntas y se monta el examen entero: con el presupuesto por defecto se queda al
  // límite por reloj, no por producto.
  test.slow();
  const titulo = await crearConjuntoDeExamen(page, 80, 5);

  await irAConfiguracion(page);
  await page.getByLabel('Modo').selectOption('mock_exam');
  const conjunto = page.getByLabel('Conjunto de preguntas');
  const opcion = conjunto.locator('option', { hasText: titulo });
  await expect(opcion).toHaveCount(1);
  await conjunto.selectOption((await opcion.first().getAttribute('value')) ?? '');
  // El simulacro usa el perfil exacto: ni tamaño ni corrección se eligen a mano.
  await expect(page.getByText(/El simulacro usa el perfil exacto del examen/)).toBeVisible();
  await expect(page.getByLabel('Cuántas preguntas')).toHaveCount(0);
  await page.getByRole('button', { name: 'Crear y empezar la sesión' }).click();

  // 80 ordinarias y las 5 reservas de la convocatoria, y se corrige al terminar.
  await expect(page.getByText(/Sesión de simulacro lista: 85 preguntas/)).toBeVisible();
  await expect(page.getByText(/0 de 85 respondidas/)).toBeVisible();
  // Y la composición se dice delante: en esta ejecución, nada se había visto hace poco.
  await expect(
    page.getByRole('note', { name: 'Cómo se compuso esta sesión' }),
  ).toContainText('ninguna de sus preguntas se había intentado');

  // Se termina sin contestar (la pantalla lo permite y lo dice): el resultado es de un simulacro. Las
  // reservas que no hicieron falta no entran en el cálculo, así que lo pendiente son las 80 ordinarias.
  await page.getByRole('button', { name: 'Terminar la sesión' }).click();
  await expect(page.getByRole('heading', { name: 'Resultado' })).toBeVisible();
  await expect(page.getByText(/Es un simulacro: el perfil es el del examen/)).toBeVisible();
  await expect(page.getByText('no es un examen oficial')).toBeVisible();
  await expect(page.getByText(/no puntúan, ni a favor ni en contra/)).toBeVisible();
  // La composición también queda en el resultado: no solo mientras se contesta.
  await expect(
    page.getByRole('note', { name: 'Cómo se compuso esta sesión' }),
  ).toBeVisible();
});

/**
 * 07_UI-UX §13 y §14 sobre la pantalla que más se usa: la pregunta y su corrección.
 *
 * §14 pide los tres anchos de referencia para «Pregunta y Corrección» y §13 pide que el flujo
 * completo se pueda hacer **con teclado**. Ninguna de las dos cosas estaba comprobada: Estudiar no
 * tenía prueba de accesibilidad ni de responsive, y la de teclado no existía en ninguna pantalla.
 */
test('E2E-06 accesibilidad y responsive: la pregunta y la corrección, con teclado y a tres anchos', async ({
  page,
}) => {
  const titulo = await crearConjuntoConClave(page);
  await prepararPractica(page, titulo, '2');
  await expect(page.getByRole('heading', { name: 'Pregunta 1' })).toBeVisible();

  // Los tres anchos, sin scroll horizontal: el enunciado y las opciones son lo más largo de la
  // aplicación y donde un desbordamiento se nota.
  for (const viewport of VIEWPORTS) {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await expect(page.getByRole('heading', { name: 'Pregunta 1' })).toBeVisible();
    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    expect(scrollWidth, `scroll horizontal en la pregunta (${viewport.name})`).toBeLessThanOrEqual(
      viewport.width + 1,
    );
  }
  await page.setViewportSize({ width: 1440, height: 900 });

  // Accesibilidad de la pregunta **sin corregir**: aquí es donde no puede aparecer la solución.
  const pregunta = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
    .analyze();
  expect(pregunta.violations).toEqual([]);

  // Y se responde con el teclado, que es lo que §13 pide: foco en la opción, espacio para marcarla,
  // tabulador hasta el botón y enter para enviar. Sin ratón en ningún paso.
  await page.getByLabel('B) Falso').focus();
  await page.keyboard.press(' ');
  await expect(page.getByLabel('B) Falso')).toBeChecked();
  await page.getByRole('button', { name: 'Enviar la respuesta' }).focus();
  await page.keyboard.press('Enter');
  await expect(page.getByText('Respuesta guardada.')).toBeVisible();

  // La corrección también se comprueba: enseña la solución, así que su accesibilidad importa igual.
  const correccion = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
    .analyze();
  expect(correccion.violations).toEqual([]);
});
