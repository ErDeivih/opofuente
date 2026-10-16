/** Sonda del test en curso: qué hay en el DOM y qué pasa al contestar (F34). */

import { chromium } from 'playwright';

const API = 'http://127.0.0.1:8765/api/v1';
const WEB = 'http://127.0.0.1:4173';

const sesion = await fetch(`${API}/student/tests`, {
  method: 'POST',
  headers: { 'content-type': 'application/json', origin: WEB },
  body: JSON.stringify({ nodes: ['IV.7'], count: 10, filter: 'all', feedback: 'immediate', timed: false }),
}).then((r) => r.json());
console.log('sesión creada:', sesion.id, sesion.status, sesion.total_questions);

const navegador = await chromium.launch();
const pagina = await (await navegador.newContext({ viewport: { width: 1280, height: 800 } })).newPage();
pagina.on('console', (m) => {
  if (m.type() === 'error') console.log('CONSOLA:', m.text().slice(0, 200));
});
pagina.on('requestfailed', (r) => console.log('FALLO DE PETICIÓN:', r.url(), r.failure()?.errorText));
pagina.on('response', (r) => {
  if (r.url().includes('/student/')) console.log('HTTP', r.status(), r.request().method(), r.url().replace(API, ''));
});

await pagina.goto(`${WEB}/test/${sesion.id}`, { waitUntil: 'networkidle' });
await pagina.waitForTimeout(1500);

const censo = await pagina.evaluate(() => {
  const vis = (el) => {
    if (el === null) return null;
    const r = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    return { ancho: Math.round(r.width), alto: Math.round(r.height), display: s.display, visibility: s.visibility };
  };
  return {
    h1: document.querySelector('h1')?.textContent?.replace(/\s+/g, ' ').trim() ?? null,
    opciones: document.querySelectorAll('.test-opciones button.test-opcion').length,
    opcionVis: vis(document.querySelector('.test-opciones button.test-opcion')),
    hojaFilas: document.querySelectorAll('ol.hoja li').length,
    irA1: vis(document.querySelector('[aria-label="Ir a la pregunta 1"]')),
    irA2Vis: vis(document.querySelector('[aria-label="Ir a la pregunta 2"]')),
    asideVis: vis(document.querySelector('aside.test-hoja')),
    botonesCabecera: [...document.querySelectorAll('.test-cabecera button, .test-cabecera a')].map((b) => b.textContent.trim()),
    clasesAside: document.querySelector('aside.test-hoja')?.className ?? null,
  };
});
console.log('CENSO:', JSON.stringify(censo, null, 2));

console.log('--- clic en la opción 1 ---');
const respuesta = await pagina
  .waitForResponse((r) => r.url().endsWith('/answers') && r.request().method() === 'POST', { timeout: 10_000 })
  .catch(() => null);
await pagina.locator('.test-opciones button.test-opcion').nth(0).click();
await pagina.waitForTimeout(1500);
if (respuesta !== null) {
  const cuerpo = await respuesta.json().catch(() => null);
  if (cuerpo !== null) {
    console.log('CUERPO DE /answers (recortado):', JSON.stringify({
      finished: cuerpo.finished,
      posicion_siguiente: cuerpo.position,
      pregunta_actual: cuerpo.question?.stem?.slice(0, 60),
      correccion_de_la_actual: cuerpo.question?.correction ?? null,
      correccion_en_la_hoja: (cuerpo.sheet ?? []).map((f) => ({ p: f.position, o: f.outcome, c: f.correct, e: f.chosen })),
    }, null, 2));
  }
}
const despues = await pagina.evaluate(() => ({
  h1: document.querySelector('h1')?.textContent?.replace(/\s+/g, ' ').trim() ?? null,
  clasesDeOpciones: [...document.querySelectorAll('.test-opciones button.test-opcion')].map((b) => b.className),
  marcaTuRespuesta: document.querySelectorAll('.test-opcion__marca').length,
  hojaFilas: document.querySelectorAll('ol.hoja li').length,
  hojaEstados: [...document.querySelectorAll('ol.hoja li')].slice(0, 4).map((li) => ({
    numero: li.querySelector('.hoja__numero')?.textContent?.trim(),
    casillas: [...li.querySelectorAll('.hoja__casilla')].map((c) => `${c.textContent.trim()}:${c.getAttribute('data-estado')}`),
  })),
}));
console.log('DESPUÉS:', JSON.stringify(despues, null, 2));

console.log('--- intento de ir a la pregunta 2 ---');
const objetivo = pagina.locator('[aria-label="Ir a la pregunta 2"]');
console.log('cuántos:', await objetivo.count(), 'visible:', await objetivo.first().isVisible().catch(() => 'error'));
try {
  await objetivo.first().click({ timeout: 5000 });
  await pagina.waitForTimeout(800);
  console.log('h1 tras ir a la 2:', await pagina.locator('h1').first().innerText().catch(() => '(sin h1)'));
} catch (error) {
  console.log('NO SE PUDO IR A LA 2:', String(error).split('\n')[0]);
}

await navegador.close();
