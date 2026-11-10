// Verifica y captura la demo estática (local o GitHub Pages): temario con progreso, tema completo,
// tema en preparación, práctica completa, ficha de pregunta y persistencia en localStorage.
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

// Datos publicados: el script no asume qué temas están completos; los descubre del propio build.
const data = await (await fetch(`${BASE}/data.json`)).json();
const topics = data.curriculum.blocks.flatMap((block) => block.topics);
const completo = topics.find((topic) => topic.status === 'completo');
const pendiente = topics.find((topic) => topic.status === 'pendiente');
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

const temario = await captura('temario', 'temario', 1280);
check('el temario enseña 5 bloques y 40 temas', /5 bloques/.test(temario) && /40 temas/.test(temario));
check(
  'la demo marca el progreso (completos / en preparación)',
  /temas completos/.test(temario) && /en preparación/.test(temario),
);
check('hay al menos 5 temas completos', data.progress.complete >= 5, `${data.progress.complete}`);
await captura('temario', 'temario', 390);

if (completo !== undefined) {
  const texto = await captura(`tema/${completo.path}`, 'tema-completo', 1280);
  check(
    `el tema ${completo.path} tiene apartados y fuente`,
    /apartados/.test(texto) && /Fuente:/.test(texto),
  );
  check(`el tema ${completo.path} tiene su práctica`, /Práctica de este tema/.test(texto));
  await captura(`tema/${completo.path}`, 'tema-completo', 390);
}

if (pendiente !== undefined) {
  const texto = await captura(`tema/${pendiente.path}`, 'tema-pendiente', 1280);
  check(
    `el tema ${pendiente.path} dice «En preparación»`,
    /En preparación/.test(texto) && /todavía no está redactado/.test(texto),
  );
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
  for (let i = 0; i < 10; i += 1) {
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
