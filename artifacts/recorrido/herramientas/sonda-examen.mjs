/** Sonda (F34): un examen oficial, ¿avanza al contestar? ¿qué dice el cierre? */

import { chromium } from 'playwright';

const API = 'http://127.0.0.1:8765/api/v1';
const WEB = 'http://127.0.0.1:4173';

const examenes = await fetch(`${API}/student/official-exams`, { headers: { origin: WEB } }).then((r) =>
  r.json(),
);
console.log('exámenes oficiales:', JSON.stringify(examenes, null, 2).slice(0, 1500));

const lista = Array.isArray(examenes) ? examenes : (examenes.items ?? examenes.exams ?? []);
const indice = lista.findIndex((e) => JSON.stringify(e).includes('2025') && JSON.stringify(e).includes('modelo A'));
console.log('índice del INAP 2025 A:', indice, indice >= 0 ? JSON.stringify(lista[indice]) : '(no está)');
if (indice < 0) process.exit(0);

const sesion = await fetch(`${API}/student/official-exams/${String(indice + 1)}/sessions`, {
  method: 'POST',
  headers: { origin: WEB },
}).then((r) => r.json());
console.log('sesión:', JSON.stringify(sesion));

const navegador = await chromium.launch();
const pagina = await (await navegador.newContext({ viewport: { width: 1280, height: 800 } })).newPage();
pagina.on('response', async (r) => {
  if (r.url().includes('/answers') || r.url().includes('/finish') || r.url().includes('/start')) {
    console.log('HTTP', r.status(), r.request().method(), r.url().split('/api/v1')[1]);
  }
});
await pagina.goto(`${WEB}/test/${sesion.id}`, { waitUntil: 'networkidle' });
await pagina.waitForTimeout(1200);

const cabecera = async () => (await pagina.locator('.test-cabecera__progreso').innerText()).trim();
console.log('cabecera al abrir:', await cabecera());
console.log('opciones:', await pagina.locator('.test-opciones button.test-opcion').count());
console.log('¿hoja con onIr? (los números tienen manejador):', await pagina.evaluate(() => {
  const b = document.querySelector('.hoja__numero');
  return b === null ? 'sin hoja' : `botones=${document.querySelectorAll('.hoja__numero').length}`;
}));

await pagina.locator('.test-opciones button.test-opcion').nth(0).click();
await pagina.waitForTimeout(1200);
console.log('cabecera tras contestar 1:', await cabecera());
const estado = await pagina.evaluate(() => {
  const filas = [...document.querySelectorAll('ol.hoja li')].slice(0, 3);
  return filas.map((li) => ({
    numero: li.querySelector('.hoja__numero')?.textContent?.trim(),
    casillas: [...li.querySelectorAll('.hoja__casilla')].map((c) => `${c.textContent.trim()}:${c.getAttribute('data-estado')}`),
  }));
});
console.log('hoja:', JSON.stringify(estado));

// ¿Se puede ir a la pregunta 2 con la hoja?
await pagina.locator('.hoja__numero').nth(1).click({ timeout: 5000 }).catch((e) => console.log('click hoja falló:', String(e).split('\n')[0]));
await pagina.waitForTimeout(800);
console.log('cabecera tras pulsar el 2 de la hoja:', await cabecera());

// Teclado: ¿hacen algo las flechas?
await pagina.keyboard.press('ArrowRight');
await pagina.waitForTimeout(600);
console.log('cabecera tras ArrowRight:', await cabecera());
await pagina.keyboard.press('b');
await pagina.waitForTimeout(600);
console.log('cabecera tras pulsar «b»:', await cabecera());

// Cierre
await pagina.locator('button', { hasText: /^Terminar/ }).first().click();
await pagina.waitForTimeout(2500);
console.log('URL tras Terminar:', pagina.url());
console.log(
  'texto del resultado:',
  (await pagina.locator('main').innerText().catch(() => '')).replace(/\s+/g, ' ').slice(0, 400),
);
await navegador.close();
