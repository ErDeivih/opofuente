// Verifica y captura la demo estática (local o GitHub Pages): portada con convocatorias, cobertura
// por bloque, sellos de apuntes/práctica, búsqueda y filtro, tema completo, pendiente, práctica
// completa, ficha de pregunta con texto oficial y persistencia en localStorage.
//
// Uso:
//   node docs/interfaz/capturar-demo-pages.mjs http://localhost:8098
//   BASE_URL=https://<usuario>.github.io/opofuente-demo/ node docs/interfaz/capturar-demo-pages.mjs

import { mkdir } from 'node:fs/promises';
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

// Portada: convocatorias y un solo aviso.
const portada = await captura('', 'portada', 1280);
check(
  'la portada dice a qué convocatorias sirve',
  /12 convocatorias C1 de informática/.test(portada) && /Ver las 12 convocatorias/.test(portada),
);
check('el aviso de demo aparece una sola vez', (await page.locator('.demo-warning').count()) === 1);
check(
  'la portada muestra la cobertura',
  /apuntes completos/.test(portada) && /con práctica/.test(portada),
);
await captura('', 'portada', 390);

const temario = await captura('temario', 'temario', 1280);
check('el temario enseña 5 bloques y 40 temas', /5 bloques/.test(temario) && /40 temas/.test(temario));
check('hay avance por bloque', /I: \d+\/12 con apuntes/.test(temario));
check('los sellos de apuntes y práctica están visibles', /Apuntes completos/.test(temario) && /Con práctica/.test(temario));
check('hay al menos 5 temas con apuntes', data.progress.apuntesCompletos >= 5, `${data.progress.apuntesCompletos}`);
await captura('temario', 'temario', 390);

// Mapa de cobertura publicado: 40 filas con apuntes y práctica.
const cobertura = await captura('cobertura', 'cobertura', 1280);
check('el mapa de cobertura publica los 40 temas', /Mapa de cobertura/.test(cobertura));
check(
  'la tabla de cobertura tiene 40 filas',
  (await page.locator('.demo-cobertura tbody tr').count()) === 40,
);
await captura('cobertura', 'cobertura', 390);

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

if (completo !== undefined) {
  const texto = await captura(`tema/${completo.path}`, 'tema-completo', 1280);
  check(`el tema ${completo.path} tiene apuntes completos y fuente`, /Apuntes completos/.test(texto) && /Fuente:/.test(texto));
  check(`el tema ${completo.path} tiene su práctica`, /Práctica de este tema/.test(texto));
  await captura(`tema/${completo.path}`, 'tema-completo', 390);
}

if (pendiente !== undefined) {
  const texto = await captura(`tema/${pendiente.path}`, 'tema-pendiente', 1280);
  check(`el tema ${pendiente.path} dice «Pendiente»`, /Pendiente/.test(texto) && /todavía no está redactado/.test(texto));
  await captura(`tema/${pendiente.path}`, 'tema-pendiente', 390);
}

if (practice !== undefined) {
  await captura(`practica/${practice.slug}`, 'practica', 1280);
  await captura(`practica/${practice.slug}`, 'practica', 390);
  await captura(`pregunta/${practice.slug}/0`, 'pregunta', 1280);
  await captura(`pregunta/${practice.slug}/0`, 'pregunta', 390);

  await page.setViewportSize({ width: 1280, height: 900 });
  await page.goto(`${BASE}/#/practica/${practice.slug}`, { waitUntil: 'networkidle' });
  await page.waitForSelector('h1');
  await page.locator('input[type=radio]').first().check();
  await page.getByRole('button', { name: 'Comprobar' }).click();
  const correccion = await page.locator('main').innerText();
  check('la corrección enlaza el texto oficial', /Texto oficial/.test(correccion));
  check(
    'el enlace de la corrección apunta al BOE',
    (await page.locator('main .demo-source a').first().getAttribute('href'))?.includes('boe.es') ?? false,
  );
  await page.screenshot({ path: path.join(OUT_DIR, 'correccion-1280.png'), fullPage: true });
  await page.getByRole('button', { name: 'Siguiente pregunta' }).click();
  for (let i = 1; i < 10; i += 1) {
    await page.locator('input[type=radio]').first().check();
    await page.getByRole('button', { name: 'Comprobar' }).click();
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

check('sin errores de página', consoleErrors.length === 0, consoleErrors.slice(0, 3).join(' | '));

await browser.close();
const fallos = checks.filter((item) => !item.ok);
console.log(`\n${checks.length - fallos.length}/${checks.length} comprobaciones. Capturas en ${OUT_DIR}`);
process.exit(fallos.length === 0 ? 0 : 1);
