/**
 * Sonda (F34): ¿cuántas veces pide el navegador `POST /start` al abrir un test, y cómo son las
 * preguntas con `[]`?
 */

import { chromium } from 'playwright';

const API = 'http://127.0.0.1:8765/api/v1';
const WEB = 'http://127.0.0.1:4173';

const sesion = await fetch(`${API}/student/tests`, {
  method: 'POST',
  headers: { 'content-type': 'application/json', origin: WEB },
  body: JSON.stringify({ nodes: ['IV.7'], count: 10, filter: 'all', feedback: 'immediate', timed: false }),
}).then((r) => r.json());

const navegador = await chromium.launch();
const pagina = await (await navegador.newContext({ viewport: { width: 1280, height: 800 } })).newPage();

const cuentas = { start: 0, run: 0, answers: 0, otras: 0 };
const t0 = Date.now();
pagina.on('request', (r) => {
  const u = r.url();
  if (!u.includes('/student/')) return;
  if (u.endsWith('/start')) cuentas.start += 1;
  else if (u.endsWith('/answers')) cuentas.answers += 1;
  else if (r.method() === 'GET' && u.includes('/sessions/')) cuentas.run += 1;
  else cuentas.otras += 1;
});

await pagina.goto(`${WEB}/test/${sesion.id}`, { waitUntil: 'networkidle' });
console.log('tras networkidle (', Date.now() - t0, 'ms ):', JSON.stringify(cuentas));
await pagina.waitForTimeout(3000);
console.log('3 s después:', JSON.stringify(cuentas));
await pagina.waitForTimeout(5000);
console.log('8 s después:', JSON.stringify(cuentas));

// Una pregunta con `[]`: ¿las opciones son las palabras que rellenan el hueco?
const conCorchetes = await pagina.evaluate(() => {
  const h1 = document.querySelector('h1')?.textContent ?? '';
  const opciones = [...document.querySelectorAll('.test-opciones .test-opcion__texto')].map((o) =>
    o.textContent.trim(),
  );
  return { h1: h1.replace(/\s+/g, ' ').trim(), opciones };
});
console.log('pregunta en pantalla:', JSON.stringify(conCorchetes, null, 2));

await navegador.close();
