// Verifica y captura la demo estática (local o GitHub Pages): temario, ficha de tema, práctica
// completa y ficha de pregunta, a 1280 y 390. También comprueba que el progreso queda en localStorage.
//
// Uso:
//   node docs/interfaz/capturar-demo-pages.mjs http://127.0.0.1:8098
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
await captura('temario', 'temario', 390);

const tema = await captura('tema/I.1', 'tema-i1', 1280);
check('la ficha del tema I.1 enseña apuntes', /Constitución Española de 1978/.test(tema) && /reforma/i.test(tema));
await captura('tema/I.1', 'tema-i1', 390);

await captura('tema/II.13', 'tema-ii13', 1280);
const pregunta = await captura('pregunta/i-1/0', 'pregunta-i1', 1280);
check('la ficha de pregunta muestra opciones y explicación', /correcta/.test(pregunta) && /Por qué/.test(pregunta));
await captura('pregunta/i-1/0', 'pregunta-i1', 390);

// Práctica completa: 10 preguntas, siempre la primera opción. Al final debe quedar el resultado.
await page.setViewportSize({ width: 1280, height: 900 });
await page.goto(`${BASE}/#/practica/i-1`, { waitUntil: 'networkidle' });
await page.waitForSelector('h1');
let completadas = 0;
for (let i = 0; i < 10; i += 1) {
  const opcion = page.locator('input[type=radio]').first();
  await opcion.check();
  await page.getByRole('button', { name: 'Comprobar' }).click();
  const esUltima = i === 9;
  await page.getByRole('button', { name: esUltima ? 'Ver resultado' : 'Siguiente pregunta' }).click();
  completadas += 1;
  if (esUltima) break;
}
const resultado = await page.locator('main').innerText();
check('la práctica se puede terminar', /correctas/.test(resultado), `${completadas} preguntas`);
check('el resultado guarda el mejor porcentaje', /Mejor resultado guardado/.test(resultado));
const progreso = await page.evaluate(() => window.localStorage.getItem('opofuente-demo-progress-v1'));
check('el progreso queda en localStorage', progreso !== null && progreso.includes('i-1'));
await page.screenshot({ path: path.join(OUT_DIR, 'resultado-1280.png'), fullPage: true });

const practica = await captura('practica/ii-13', 'practica-ii13', 1280);
check('la segunda práctica existe', /Arquitectura de ordenadores/.test(practica));
await captura('practica/ii-13', 'practica-ii13', 390);

check('sin errores de página', consoleErrors.length === 0, consoleErrors.slice(0, 3).join(' | '));

await browser.close();
const fallos = checks.filter((item) => !item.ok);
console.log(`\n${checks.length - fallos.length}/${checks.length} comprobaciones. Capturas en ${OUT_DIR}`);
process.exit(fallos.length === 0 ? 0 : 1);
