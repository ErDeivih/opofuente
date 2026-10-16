/**
 * Sonda de comprobación, segunda parte (F34).
 *
 * 1. El índice de un tema largo: ¿se puede llegar a sus últimos apartados?
 * 2. «Ver en apuntes» con más tiempo: ¿baja al apartado o no?
 * 3. `POST /student/mock-exams`: cuánto tarda de verdad.
 * 4. «Test con mis fallos»: ¿monta y navega?
 * 5. Cambiar de respuesta desde la pantalla: ¿qué ve el alumno?
 */

import { chromium } from 'playwright';

const API = 'http://127.0.0.1:8765/api/v1';
const WEB = 'http://127.0.0.1:4173';
const cabecera = { origin: WEB, 'content-type': 'application/json' };

const navegador = await chromium.launch();
const contexto = await navegador.newContext({ viewport: { width: 1280, height: 800 }, locale: 'es-ES' });
const pagina = await contexto.newPage();

// ---------------------------------------------------------------- 1 · índices largos
console.log('=== 1 · índice de IV.7 y de I.1 ===');
for (const codigo of ['IV.7', 'I.1']) {
  await pagina.goto(`${WEB}/temario/${codigo}`, { waitUntil: 'networkidle' });
  await pagina.waitForTimeout(1800);
  const info = await pagina.evaluate(() => {
    const nav = document.querySelector('nav.apuntes__indice');
    const enlaces = [...nav.querySelectorAll('a')];
    const ultimo = enlaces[enlaces.length - 1];
    const primero = enlaces[0];
    return {
      enlaces: enlaces.length,
      navAlto: Math.round(nav.getBoundingClientRect().height),
      navPosicion: getComputedStyle(nav).position,
      primeroTop: Math.round(primero.getBoundingClientRect().top),
      ultimoTop: Math.round(ultimo.getBoundingClientRect().top),
      ventanaAlto: window.innerHeight,
      ultimoALaVista: ultimo.getBoundingClientRect().top < window.innerHeight,
    };
  });
  console.log(codigo, JSON.stringify(info));
  try {
    await pagina.locator('nav.apuntes__indice a').last().click({ timeout: 6000 });
    await pagina.waitForTimeout(600);
    console.log(`   ${codigo}: el último SÍ se puede pulsar (hash ${await pagina.evaluate(() => location.hash)})`);
  } catch (error) {
    console.log(`   ${codigo}: el último NO se puede pulsar — ${String(error).split('\n')[0]}`);
  }
  // ¿Y el 20.º de 25?
  try {
    await pagina.locator('nav.apuntes__indice a').nth(19).click({ timeout: 4000 });
    console.log(`   ${codigo}: el 20.º SÍ se puede pulsar`);
  } catch (error) {
    console.log(`   ${codigo}: el 20.º NO se puede pulsar`);
  }
}

// ---------------------------------------------------------------- 2 · Ver en apuntes
console.log('\n=== 2 · «Ver en apuntes» con tiempo de sobra ===');
const sesion = await fetch(`${API}/student/tests`, {
  method: 'POST',
  headers: cabecera,
  body: JSON.stringify({ nodes: ['IV.7'], count: 5, filter: 'all', feedback: 'immediate', timed: false }),
}).then((r) => r.json());
await fetch(`${API}/student/sessions/${sesion.id}/start`, { method: 'POST', headers: cabecera });
for (let i = 1; i <= 5; i += 1) {
  await fetch(`${API}/student/sessions/${sesion.id}/answers`, {
    method: 'POST',
    headers: cabecera,
    body: JSON.stringify({ position: i, chosen: ['a'], elapsed_ms: 0, confidence: null }),
  });
}
await fetch(`${API}/student/sessions/${sesion.id}/finish`, { method: 'POST', headers: cabecera });
await pagina.goto(`${WEB}/resultado/${sesion.id}`, { waitUntil: 'networkidle' });
await pagina.waitForTimeout(1500);
const enlaces = pagina.locator('main a', { hasText: 'Ver en apuntes' });
const cuantos = await enlaces.count();
console.log('enlaces «Ver en apuntes»:', cuantos);
for (let i = 0; i < Math.min(2, cuantos); i += 1) {
  await pagina.goto(`${WEB}/resultado/${sesion.id}`, { waitUntil: 'networkidle' });
  await pagina.waitForTimeout(1000);
  const href = await enlaces.nth(i).getAttribute('href');
  await enlaces.nth(i).click();
  for (const espera of [1500, 4000]) {
    await pagina.waitForTimeout(espera === 1500 ? 1500 : 2500);
    const donde = await pagina.evaluate((h) => {
      const ancla = decodeURIComponent((h ?? '').split('#')[1] ?? '');
      const el = document.getElementById(`apartado-${ancla}`);
      const r = el?.getBoundingClientRect();
      return {
        scrollY: Math.round(window.scrollY),
        top: r === undefined ? null : Math.round(r.top),
        aLaVista: r === undefined ? null : r.top > -50 && r.top < window.innerHeight,
      };
    }, href);
    console.log(`   ${href} tras ${espera === 1500 ? '1,5' : '4'} s:`, JSON.stringify(donde));
  }
}

// ---------------------------------------------------------------- 3 · el simulacro
console.log('\n=== 3 · POST /student/mock-exams ===');
const plan = await fetch(`${API}/student/mock-exams`, { headers: { origin: WEB } }).then((r) => r.json());
console.log('bloques del supuesto:', JSON.stringify(plan.case_blocks?.map((b) => b.code)));
for (const cuerpo of [
  { variant: 'full', case_block: 'III' },
  { variant: 'short', case_block: null },
]) {
  const t0 = Date.now();
  const r = await fetch(`${API}/student/mock-exams`, { method: 'POST', headers: cabecera, body: JSON.stringify(cuerpo) });
  const texto = await r.text();
  console.log(
    `${JSON.stringify(cuerpo)} -> ${r.status} en ${((Date.now() - t0) / 1000).toFixed(1)} s ·`,
    texto.slice(0, 160),
  );
}

// ---------------------------------------------------------------- 4 · Test con mis fallos
console.log('\n=== 4 · «Test con mis fallos» ===');
const peticiones = [];
pagina.on('response', async (r) => {
  if (r.url().includes('/student/tests') || r.url().includes('/sessions')) {
    peticiones.push(`${String(r.status())} ${r.request().method()} ${r.url().split('/api/v1')[1]}`);
  }
});
await pagina.goto(`${WEB}/fallos`, { waitUntil: 'networkidle' });
await pagina.waitForTimeout(1200);
const boton = pagina.locator('main button, main a').filter({ hasText: /Test con mis fallos|Solo los de/ });
console.log('botones de repaso:', await boton.count());
if ((await boton.count()) > 0) {
  console.log('el primero dice:', (await boton.first().innerText()).replace(/\s+/g, ' '));
  await boton.first().click();
  await pagina.waitForTimeout(6000);
  console.log('URL tras pulsar:', pagina.url());
  console.log('peticiones vistas:', JSON.stringify(peticiones));
  console.log('lo que dice la pantalla:', (await pagina.locator('main').innerText()).replace(/\s+/g, ' ').slice(0, 300));
}

// ---------------------------------------------------------------- 5 · cambiar de respuesta desde la pantalla
console.log('\n=== 5 · cambiar de respuesta desde la pantalla ===');
const otra = await fetch(`${API}/student/tests`, {
  method: 'POST',
  headers: cabecera,
  body: JSON.stringify({ nodes: ['IV.7'], count: 5, filter: 'all', feedback: 'immediate', timed: false }),
}).then((r) => r.json());
await pagina.goto(`${WEB}/test/${otra.id}`, { waitUntil: 'networkidle' });
await pagina.waitForTimeout(1500);
await pagina.locator('.test-opciones button.test-opcion').nth(0).click();
await pagina.waitForTimeout(1000);
console.log('cabecera:', await pagina.locator('.test-cabecera__progreso').innerText());
const vuelta = await pagina.evaluate(() => document.querySelector('.hoja__numero')?.getAttribute('aria-label'));
console.log('la fila 1 de la hoja:', vuelta);
await pagina.locator('.hoja__numero').first().click();
await pagina.waitForTimeout(1000);
console.log('cabecera tras pulsar la fila 1:', await pagina.locator('.test-cabecera__progreso').innerText());

await navegador.close();
