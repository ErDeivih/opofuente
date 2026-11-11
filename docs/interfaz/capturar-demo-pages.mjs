// Verifica y captura la demo estática (local o GitHub Pages): portada corta con continuar,
// convocatorias, cobertura, sellos, búsqueda/filtros, tema completo/pendiente, práctica sin
// «Comprobar», reanudación, corrección con BOE y persistencia.
//
// Uso:
//   node docs/interfaz/capturar-demo-pages.mjs http://localhost:8098
//   BASE_URL=https://<usuario>.github.io/opofuente-demo/ node docs/interfaz/capturar-demo-pages.mjs

import { mkdir, readFile } from 'node:fs/promises';
import path from 'node:path';

import { chromium } from '@playwright/test';

const BASE = (process.env.BASE_URL ?? process.argv[2] ?? '').replace(/\/+$/, '');
if (BASE === '') {
  console.error('Falta BASE_URL o el primer argumento.');
  process.exit(2);
}
const OUT_DIR = path.join(process.cwd(), 'docs', 'capturas', 'demo-pages');
await mkdir(OUT_DIR, { recursive: true });

const checks = [];
function check(name, ok, detail = '') {
  checks.push({ name, ok });
  console.log(`${ok ? 'OK  ' : 'FALLO'} ${name}${detail ? ` — ${detail}` : ''}`);
}

const data = await (await fetch(`${BASE}/data.json`)).json();
const topics = data.curriculum.blocks.flatMap((block) => block.topics);
const completo = topics.find((topic) => topic.apuntesStatus === 'completos');
const pendiente = topics.find((topic) => topic.apuntesStatus === 'pendiente');
const practice = data.practices[0];

const browser = await chromium.launch();
const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, locale: 'es-ES' });
const page = await context.newPage();
const consoleErrors = [];
page.on('pageerror', (error) => {
  consoleErrors.push(String(error));
});

async function captura(hash, nombre, ancho) {
  await page.setViewportSize({ width: ancho, height: ancho === 390 ? 844 : 900 });
  await page.goto(`${BASE}/#/${hash}`, { waitUntil: 'networkidle' });
  await page.waitForSelector('h1', { timeout: 15_000 });
  const texto = await page.locator('body').innerText();
  await page.screenshot({ path: path.join(OUT_DIR, `${nombre}-${ancho}.png`), fullPage: true });
  return texto;
}

// Portada corta: cobertura, continuar, 3 prácticas, convocatorias y un solo aviso.
const portada = await captura('', 'portada', 1280);
check(
  'la portada dice a qué convocatorias sirve',
  /12 convocatorias C1 de informática/.test(portada) && /Ver las 12 convocatorias/.test(portada),
);
check('el aviso de demo aparece una sola vez', (await page.locator('.demo-warning').count()) === 1);
check('el aviso tiene «Cómo funciona»', /Cómo funciona/.test(portada));
check('la portada tiene «Continuar donde lo dejé»', /Continuar donde lo dejé/.test(portada));
check(
  'la portada muestra 3 prácticas siguientes',
  (await page.locator('.demo-next li').count()) === 3,
);
const tabBox = await page.locator('.demo-nav .button').first().boundingBox();
check('las pestañas miden al menos 44 px', tabBox !== null && tabBox.height >= 44);
await captura('', 'portada', 390);
await page.getByText('Ver las 12 convocatorias').click();
const enlaceConvocatoria = page.locator('.demo-convocatorias a').first();
check(
  'el enlace de convocatoria tiene nombre como texto',
  (await enlaceConvocatoria.innerText()).startsWith('Bases de'),
);
check(
  'las 12 convocatorias tienen su enlace con nombre',
  (await page.locator('.demo-convocatorias a').count()) === 12 &&
    (await page.locator('.demo-convocatorias a').allInnerTexts()).every((texto) =>
      texto.startsWith('Bases de'),
    ),
);
const csp = await page.locator('meta[http-equiv="Content-Security-Policy"]').getAttribute('content');
check(
  'la página publica CSP y referrer',
  (csp ?? '').includes("default-src 'none'") &&
    (csp ?? '').includes("connect-src 'none'") &&
    (await page.locator('meta[name="referrer"]').getAttribute('content')) === 'no-referrer',
);
check(
  'la portada muestra la cobertura',
  /apuntes completos/.test(portada) && /con práctica/.test(portada),
);
check(
  'la portada resume el avance por bloque',
  data.curriculum.blocks.every((block) =>
    portada.includes(
      `${block.path}: ${block.coverage.conApuntes}/${block.coverage.total} (${Math.round(
        (block.coverage.conApuntes / block.coverage.total) * 100,
      )}%)`,
    ),
  ),
);

const temario = await captura('temario', 'temario', 1280);
check('el temario enseña 5 bloques y 40 temas', /5 bloques/.test(temario) && /40 temas/.test(temario));
check('hay avance por bloque con porcentaje', /I: \d+\/12 \(\d+%\) con apuntes/.test(temario));
check('los sellos de apuntes y práctica están visibles', /Apuntes completos/.test(temario) && /Con práctica/.test(temario));
check('hay al menos 5 temas con apuntes', data.progress.apuntesCompletos >= 5, `${data.progress.apuntesCompletos}`);
await captura('temario', 'temario', 390);
check(
  'las pestañas se ven a 390 px y miden 44 px',
  (await page.locator('.demo-nav .button').count()) === 7 &&
    (await page.locator('.demo-nav .button').evaluateAll((botones) =>
      botones.every((boton) => boton.getBoundingClientRect().height >= 44),
    )),
);
const practicas390 = await captura('practicas', 'practicas', 390);
check(
  'la pestaña Prácticas lista todas las prácticas en móvil',
  new RegExp(`${String(data.practices.length)} prácticas`).test(practicas390),
);
check(
  'la pestaña Prácticas lista los casos prácticos',
  /Casos prácticos/.test(practicas390) && (await page.locator('.demo-case').count()) === 5,
);

// Caso práctico: escenario y 10 preguntas.
await page.goto(`${BASE}/#/caso/caso-correo`, { waitUntil: 'networkidle' });
await page.waitForSelector('h1');
const casoTexto = await page.locator('main').innerText();
check('el caso práctico muestra escenario y 10 preguntas', /spam/.test(casoTexto) && /Pregunta 1 de 10/.test(casoTexto));
await page.screenshot({ path: path.join(OUT_DIR, 'caso-practico-390.png'), fullPage: true });

// Mapa de cobertura publicado: 40 filas con apuntes y práctica.
const cobertura = await captura('cobertura', 'cobertura', 1280);
check('el mapa de cobertura publica los 40 temas', /Mapa de cobertura/.test(cobertura));
check(
  'la tabla de cobertura tiene 40 filas',
  (await page.locator('.demo-cobertura tbody tr').count()) === 40,
);
check(
  'los sellos de apuntes coinciden con el progreso',
  (await page.locator('.demo-status--apuntes-completos').count()) === data.progress.apuntesCompletos &&
    (await page.locator('.demo-status--apuntes-pendiente').count()) === data.progress.pendientes,
);
check(
  'los sellos de práctica coinciden con el progreso',
  (await page.locator('.demo-status--practica-con_practica').count()) === data.progress.conPractica &&
    (await page.locator('.demo-status--practica-pendiente').count()) === data.progress.sinPractica,
);
await captura('cobertura', 'cobertura', 390);
check(
  'el mapa conserva las 40 filas a 390 px',
  (await page.locator('.demo-cobertura tbody tr').count()) === 40,
);

// Revisión de los dos temas de la tanda: contenido, tabla y 10 preguntas.
for (const temaId of ['III.19', 'III.20', 'III.26', 'IV.30', 'V.40']) {
  const nombre = temaId.toLowerCase().replace('.', '-');
  const texto = await captura(`tema/${temaId}`, `tema-${nombre}`, 390);
  check(
    `${temaId} está completo y con 10 preguntas`,
    /Apuntes completos/.test(texto) &&
      /Fuente:/.test(texto) &&
      (await page.locator('main table').count()) >= 1 &&
      (await page.locator('ol.demo-questions li').count()) === 10,
  );
}

// Búsqueda y filtro.
await page.setViewportSize({ width: 1280, height: 900 });
await page.goto(`${BASE}/#/temario`, { waitUntil: 'networkidle' });
await page.locator('input[type=search]').fill('II.13');
await page.waitForTimeout(200);
check('la búsqueda por código deja un tema', (await page.locator('.demo-topic').count()) === 1);
await page.locator('input[type=search]').fill('');
await page.getByRole('button', { name: 'Con práctica', exact: true }).click();
await page.waitForTimeout(200);
check(
  'el filtro «Con práctica» deja las prácticas',
  (await page.locator('.demo-topic').count()) === data.progress.conPractica,
);
await page.getByRole('button', { name: 'Todos', exact: true }).click();

// Buscador en móvil: una búsqueda por código deja un tema.
await page.setViewportSize({ width: 390, height: 844 });
await page.goto(`${BASE}/#/temario`, { waitUntil: 'networkidle' });
await page.locator('input[type=search]').fill('III.20');
await page.waitForTimeout(200);
check('el buscador funciona a 390 px', (await page.locator('.demo-topic').count()) === 1);
await page.screenshot({ path: path.join(OUT_DIR, 'buscador-390.png'), fullPage: true });
await page.locator('input[type=search]').fill('');

if (completo !== undefined) {
  const texto = await captura(`tema/${completo.path}`, 'tema-completo', 1280);
  check(`el tema ${completo.path} tiene apuntes completos y fuente`, /Apuntes completos/.test(texto) && /Revisión y fuente/.test(texto) && /Fuente:/.test(texto));
  check(`el tema ${completo.path} tiene su práctica`, /Práctica de este tema/.test(texto));
  check(
    `el tema ${completo.path} muestra memorizar y errores típicos`,
    /Lo que hay que memorizar/.test(texto) && /Errores típicos/.test(texto),
  );
  check(
    `el tema ${completo.path} muestra la fecha de revisión`,
    /Última actualización: 10\/11\/2026/.test(texto),
  );
  check(
    `el tema ${completo.path} tiene desarrollo largo, tests y fuentes`,
    /Casos tipo test/.test(texto) && /Fuentes citadas/.test(texto) && texto.split(/\s+/).length >= 1500,
  );
  check(
    `el tema ${completo.path} incluye un diagrama SVG propio`,
    (await page.locator('.demo-diagram svg').count()) > 0,
  );
  check(
    `el tema ${completo.path} enlaza a las convocatorias`,
    /Forma parte del temario común/.test(texto) && /Ver convocatorias/.test(texto),
  );
  check(
    `la ficha tiene migas «Temario › ${completo.path}»`,
    (await page.locator('.demo-breadcrumbs').innerText()).includes('Temario') &&
      (await page.locator('.demo-breadcrumbs').innerText()).includes(completo.path),
  );
  await captura(`tema/${completo.path}`, 'tema-completo', 390);

  // Reporte de errata: descarga un JSON con la constancia.
  await page.locator('textarea').fill('Errata de prueba del verificador');
  const [descarga] = await Promise.all([
    page.waitForEvent('download'),
    page.getByRole('button', { name: 'Descargar constancia de errata' }).click(),
  ]);
  const ruta = await descarga.path();
  const erratas = ruta === null ? [] : JSON.parse(await readFile(ruta, 'utf8'));
  check(
    'la errata se guarda en un fichero JSON',
    Array.isArray(erratas) && erratas.some((item) => item.topic === completo.path && item.comment.includes('verificador')),
  );
}

if (pendiente !== undefined) {
  const texto = await captura(`tema/${pendiente.path}`, 'tema-pendiente', 1280);
  check(
    `el tema ${pendiente.path} dice «Apuntes pendientes»`,
    /Apuntes pendientes/.test(texto) && /todavía no está redactado/.test(texto),
  );
  check('el tema pendiente enlaza a temas completos', /Ver temas completos/.test(texto));
  await captura(`tema/${pendiente.path}`, 'tema-pendiente', 390);
  await page.getByRole('button', { name: 'Ver temas completos' }).click();
  await page.waitForSelector('.demo-topic');
  check(
    'el enlace filtra el temario por «con apuntes»',
    (await page.locator('.demo-topic').count()) === data.progress.apuntesCompletos &&
      (await page.getByRole('button', { name: 'Con apuntes', exact: true }).getAttribute('aria-pressed')) === 'true',
  );
}

if (practice !== undefined) {
  await captura(`practica/${practice.slug}`, 'practica', 1280);
  await captura(`practica/${practice.slug}`, 'practica', 390);
  await captura(`pregunta/${practice.slug}/0`, 'pregunta', 1280);
  await captura(`pregunta/${practice.slug}/0`, 'pregunta', 390);

  await page.setViewportSize({ width: 1280, height: 900 });
  await page.goto(`${BASE}/#/practica/${practice.slug}`, { waitUntil: 'networkidle' });
  await page.waitForSelector('h1');
  check(
    'la práctica no tiene botón «Comprobar»',
    (await page.getByRole('button', { name: 'Comprobar' }).count()) === 0,
  );
  check(
    `la práctica tiene «Volver a ${practice.tema_path}»`,
    /Volver a/.test(await page.locator('main').innerText()),
  );
  await page.locator('input[type=radio]').first().check();
  const correccion = await page.locator('main').innerText();
  check('elegir opción corrige al momento', /Correcto|Incorrecto/.test(correccion));
  check(
    'tras elegir aparece Siguiente',
    (await page.getByRole('button', { name: 'Siguiente pregunta' }).count()) > 0,
  );
  check('la corrección enlaza el texto oficial', /Texto oficial/.test(correccion));
  check(
    'el enlace de la corrección apunta al BOE',
    (await page.locator('main .demo-source a').first().getAttribute('href'))?.includes('boe.es') ?? false,
  );
  await page.screenshot({ path: path.join(OUT_DIR, 'correccion-1280.png'), fullPage: true });
  await page.getByRole('button', { name: 'Siguiente pregunta' }).click();

  // Segunda pregunta y vuelta a la portada: debe ofrecer continuar.
  await page.locator('input[type=radio]').first().check();
  await page.getByRole('button', { name: 'Siguiente pregunta' }).click();
  await page.goto(`${BASE}/#/`, { waitUntil: 'networkidle' });
  check('la portada ofrece continuar tras dejar la práctica', /Continuar donde lo dejé/.test(await page.locator('main').innerText()));
  await page.getByRole('button', { name: 'Continuar donde lo dejé' }).click();
  await page.waitForSelector('input[type=radio]');
  check(
    'continuar reanuda por la pregunta 3',
    /Pregunta 3 de 10/.test(await page.locator('main').innerText()),
  );

  for (let i = 2; i < 10; i += 1) {
    await page.locator('input[type=radio]').first().check();
    const esUltima = i === 9;
    await page.getByRole('button', { name: esUltima ? 'Ver resultado' : 'Siguiente pregunta' }).click();
  }
  const resultado = await page.locator('main').innerText();
  check('la práctica se puede terminar', /correctas/.test(resultado));
  check('el resultado guarda el mejor porcentaje', /Mejor resultado guardado/.test(resultado));
  const progreso = await page.evaluate(() => window.localStorage.getItem('opofuente-demo-progress-v1'));
  check('el progreso queda en localStorage', progreso !== null && progreso.includes(practice.slug));
  await page.screenshot({ path: path.join(OUT_DIR, 'resultado-1280.png'), fullPage: true });
}

// Guía de estudio: detecta un tema flojo a partir del progreso guardado.
await page.evaluate(({ slug }) => {
  const key = 'opofuente-demo-progress-v1';
  const previous = JSON.parse(window.localStorage.getItem(key) ?? '{}');
  previous[slug] = {
    best: 40,
    attempts: 1,
    lastScore: 4,
    lastTotal: 10,
    updatedAt: new Date().toISOString(),
  };
  window.localStorage.setItem(key, JSON.stringify(previous));
}, { slug: practice?.slug ?? '' });
await captura('guia', 'guia', 390);
const guia = await page.locator('main').innerText();
check('la guía recomienda el orden de bloques', /Orden recomendado/.test(guia));
check(
  'la guía detecta el tema flojo de la práctica',
  /Tus temas flojos/.test(guia) && /Repasar tema/.test(guia) && guia.includes(practice?.tema_path ?? ''),
);

// Estadísticas por tema y bloque.
await captura('estadisticas', 'estadisticas', 390);
const estadisticas = await page.locator('main').innerText();
check('las estadísticas muestran el acierto por bloque', /Estadísticas de prácticas/.test(estadisticas) && /%/.test(estadisticas));
check(
  'las estadísticas listan los temas más flojos',
  /Temas más flojos/.test(estadisticas) && estadisticas.includes(practice?.tema_path ?? ''),
);

// Supuestos: listado, filtro y resolución de 20 preguntas sin corrección.
await page.setViewportSize({ width: 390, height: 844 });
await page.goto(`${BASE}/#/supuestos`, { waitUntil: 'networkidle' });
await page.waitForSelector('h1');
const supuestos = await page.locator('main').innerText();
check('la pestaña Supuestos lista los supuestos oficiales', /Supuestos/.test(supuestos) && (await page.locator('.demo-card, section.card h2').count()) >= 3);
check('los supuestos indican año, bloque y dificultad', /2024/.test(supuestos) && /Bloque IV/.test(supuestos) && /Dificultad media/.test(supuestos));
await page.screenshot({ path: path.join(OUT_DIR, 'supuestos-390.png'), fullPage: true });
await page.getByRole('button', { name: '2024', exact: true }).click();
await page.waitForTimeout(150);
check('el filtro por año deja el supuesto de 2024', /Becas para personas opositoras/.test(await page.locator('main').innerText()));
await page.goto(`${BASE}/#/supuesto/tai-2024-a-s1`, { waitUntil: 'networkidle' });
await page.waitForSelector('h1');
const detalle = await page.locator('main').innerText();
check('el supuesto muestra enunciado, resolución y temas', /Enunciado/.test(detalle) && /Resolución paso a paso/.test(detalle) && /Temas que toca/.test(detalle));
await page.getByRole('button', { name: /Resolver como examen/ }).click();
await page.waitForSelector('input[type=radio]');
for (let i = 0; i < 20; i += 1) {
  await page.locator('input[type=radio]').first().check();
  await page.getByRole('button', { name: i === 19 ? 'Terminar y ver resultado' : 'Siguiente pregunta' }).click();
}
const resultadoSupuesto = await page.locator('main').innerText();
check('el supuesto da nota al terminar', /Resultado del supuesto/.test(resultadoSupuesto) && /nota/.test(resultadoSupuesto));
check('el supuesto revisa las 20 preguntas', /Revisión de las 20 preguntas/.test(resultadoSupuesto));
await page.screenshot({ path: path.join(OUT_DIR, 'supuesto-resultado-390.png'), fullPage: true });

// Examen completo: mezcla de bloques, tiempo total y penalización.
await page.setViewportSize({ width: 390, height: 844 });
await page.goto(`${BASE}/#/examen/TODOS`, { waitUntil: 'networkidle' });
await page.waitForSelector('h1');
const completoSetup = await page.locator('main').innerText();
check('el examen completo mezcla todos los bloques', /Examen completo/.test(completoSetup) && /Todos · 40\/40/.test(completoSetup) && /400 preguntas disponibles/.test(completoSetup));
await page.screenshot({ path: path.join(OUT_DIR, 'examen-completo-390.png'), fullPage: true });

// Modo examen por bloque: sin corrección hasta el final y revisión de fallos.
await page.goto(`${BASE}/#/examen/III`, { waitUntil: 'networkidle' });
await page.waitForSelector('h1');
const examenSetup = await page.locator('main').innerText();
check('el examen permite elegir bloque y preguntas', /Examen por bloque/.test(examenSetup) && /Simulación/.test(examenSetup));
check('el examen muestra convocatoria, tiempo y penalización', /Convocatoria y formato/.test(examenSetup) && /120 minutos/.test(examenSetup) && /1\/3/.test(examenSetup));
await page.screenshot({ path: path.join(OUT_DIR, 'examen-390.png'), fullPage: true });
await page.getByRole('button', { name: 'Empezar examen' }).click();
await page.waitForSelector('input[type=radio]');
check('el examen muestra el tiempo restante', /Tiempo restante/.test(await page.locator('main').innerText()));
for (let i = 0; i < 10; i += 1) {
  await page.locator('input[type=radio]').first().check();
  if (i === 0) {
    const durante = await page.locator('main').innerText();
    check(
      'el examen no corrige durante las preguntas',
      (await page.locator('.demo-feedback').count()) === 0 && !/Incorrecto: era/.test(durante),
    );
  }
  const esUltima = i === 9;
  await page.getByRole('button', { name: esUltima ? 'Ver resultado' : 'Siguiente pregunta' }).click();
}
const examen = await page.locator('main').innerText();
check('el examen da nota al terminar', /Resultado del examen/.test(examen) && /Nota:/.test(examen));
check('el examen aplica penalización', /Penalización aplicada/.test(examen));
check('el examen revisa los fallos', /Revisión de fallos/.test(examen));
check(
  'el resultado muestra nota, tiempo, aciertos, fallos y blancos',
  /Nota:/.test(examen) && /Tiempo/.test(examen) && /Aciertos/.test(examen) && /Fallos/.test(examen) && /En blanco/.test(examen),
);
check(
  'Revisar mis errores es la primera acción',
  (await page.locator('main .demo-actions .button').first().innerText()).includes('Revisar mis errores'),
);
await page.screenshot({ path: path.join(OUT_DIR, 'examen-resultado-390.png'), fullPage: true });

// Historial unificado: práctica + examen.
await page.goto(`${BASE}/#/estadisticas`, { waitUntil: 'networkidle' });
await page.waitForSelector('h1');
const historial = await page.locator('main').innerText();
check('las estadísticas separan prácticas e historial', /Estadísticas de prácticas/.test(historial) && /Historial de intentos/.test(historial));
check('el historial incluye práctica y examen', /Práctica/.test(historial) && /Examen/.test(historial));
check('el historial muestra el tiempo', /Historial de intentos/.test(historial) && /\d{2}:\d{2}/.test(historial));
await page.screenshot({ path: path.join(OUT_DIR, 'estadisticas-390.png'), fullPage: true });

// Estados vacíos con acción: sin progreso ni intentos.
await page.evaluate(() => { window.localStorage.clear(); });
await page.reload({ waitUntil: 'networkidle' });
const vacia = await page.locator('main').innerText();
check('los estados vacíos ofrecen práctica y simulacro', /Hacer práctica/.test(vacia) && /Empezar simulacro/.test(vacia));
await page.screenshot({ path: path.join(OUT_DIR, 'estadisticas-vacia-390.png'), fullPage: true });

check('sin errores de página', consoleErrors.length === 0, consoleErrors.slice(0, 3).join(' | '));

await browser.close();
const fallos = checks.filter((item) => !item.ok);
console.log(`\n${checks.length - fallos.length}/${checks.length} comprobaciones. Capturas en ${OUT_DIR}`);
process.exit(fallos.length === 0 ? 0 : 1);
