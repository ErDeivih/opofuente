/**
 * Sonda de comprobación (F34): los cuatro hallazgos del recorrido que hay que medir antes de
 * escribirlos.
 *
 * 1. ¿Qué pasa si el alumno cambia de respuesta en la misma pregunta?
 * 2. El botón «Test con mis fallos»: ¿monta el test y navega?
 * 3. `POST /student/mock-exams`: ¿cuánto tarda de verdad?
 * 4. `/admin/apuntes`: ¿la tabla sale vacía?
 * 5. El índice de I.1: ¿se puede pulsar su último apartado?
 * 6. «Ver en apuntes»: ¿deja el apartado a la vista?
 */

import { chromium } from 'playwright';

const API = 'http://127.0.0.1:8765/api/v1';
const WEB = 'http://127.0.0.1:4173';
const cabecera = { origin: WEB, 'content-type': 'application/json' };

const navegador = await chromium.launch();
const contexto = await navegador.newContext({ viewport: { width: 1280, height: 800 }, locale: 'es-ES' });
const pagina = await contexto.newPage();

// ---------------------------------------------------------------- 1 · cambiar de respuesta
console.log('=== 1 · cambiar de respuesta en la misma pregunta ===');
const sesion = await fetch(`${API}/student/tests`, {
  method: 'POST',
  headers: cabecera,
  body: JSON.stringify({ nodes: ['IV.7'], count: 10, filter: 'all', feedback: 'immediate', timed: false }),
}).then((r) => r.json());
console.log('sesión:', sesion.id);
await pagina.goto(`${WEB}/test/${sesion.id}`, { waitUntil: 'networkidle' });
await pagina.waitForTimeout(1200);
const primera = pagina.locator('.test-opciones button.test-opcion').nth(0);
await primera.click();
await pagina.waitForTimeout(800);
console.log('pregunta tras contestar:', await pagina.locator('.test-cabecera__progreso').innerText());
// Se vuelve a la fila 1 con la hoja (no hace nada, pero se intenta como haría un alumno) y se
// contesta otra vez a la MISMA pregunta por su API: es lo que hace el botón si el alumno cambia.
const antes = await pagina.locator('.test-cabecera__progreso').innerText();
const respuestaCambio = await fetch(`${API}/student/sessions/${sesion.id}/answers`, {
  method: 'POST',
  headers: cabecera,
  body: JSON.stringify({ position: 1, chosen: ['b'], elapsed_ms: 0, confidence: null }),
});
console.log('¿se puede volver a contestar la 1?', respuestaCambio.status, (await respuestaCambio.text()).slice(0, 200));

// ---------------------------------------------------------------- 5 · el índice de I.1
console.log('\n=== 5 · el índice de I.1 ===');
await pagina.goto(`${WEB}/temario/I.1`, { waitUntil: 'networkidle' });
await pagina.waitForTimeout(1500);
const infoIndice = await pagina.evaluate(() => {
  const nav = document.querySelector('nav.apuntes__indice');
  const enlaces = [...nav.querySelectorAll('a')];
  const ultimo = enlaces[enlaces.length - 1];
  const caja = ultimo.getBoundingClientRect();
  const estilo = getComputedStyle(nav);
  return {
    enlaces: enlaces.length,
    ultimoTexto: ultimo.textContent.trim().slice(0, 50),
    ultimoCaja: { top: Math.round(caja.top), alto: Math.round(caja.height) },
    navAlto: Math.round(nav.getBoundingClientRect().height),
    navOverflow: estilo.overflowY,
    navPosicion: estilo.position,
    ventanaAlto: window.innerHeight,
  };
});
console.log(JSON.stringify(infoIndice, null, 2));
try {
  await pagina.locator('nav.apuntes__indice a').last().click({ timeout: 6000 });
  await pagina.waitForTimeout(800);
  console.log('pulsado el último: OK, hash =', await pagina.evaluate(() => location.hash));
} catch (error) {
  console.log('pulsar el último FALLA:', String(error).split('\n').slice(0, 3).join(' | '));
}

// ---------------------------------------------------------------- 6 · Ver en apuntes
console.log('\n=== 6 · «Ver en apuntes» ===');
const finalizada = await fetch(`${API}/student/tests`, {
  method: 'POST',
  headers: cabecera,
  body: JSON.stringify({ nodes: ['IV.7'], count: 5, filter: 'all', feedback: 'immediate', timed: false }),
}).then((r) => r.json());
for (let i = 1; i <= 5; i += 1) {
  await fetch(`${API}/student/sessions/${finalizada.id}/start`, { method: 'POST', headers: cabecera });
  await fetch(`${API}/student/sessions/${finalizada.id}/answers`, {
    method: 'POST',
    headers: cabecera,
    body: JSON.stringify({ position: i, chosen: ['a'], elapsed_ms: 0, confidence: null }),
  });
}
await fetch(`${API}/student/sessions/${finalizada.id}/finish`, { method: 'POST', headers: cabecera });
await pagina.goto(`${WEB}/resultado/${finalizada.id}`, { waitUntil: 'networkidle' });
await pagina.waitForTimeout(1200);
const enlaces = pagina.locator('main a', { hasText: 'Ver en apuntes' });
console.log('enlaces «Ver en apuntes»:', await enlaces.count());
if ((await enlaces.count()) > 0) {
  const destino = await enlaces.first().getAttribute('href');
  await enlaces.first().click();
  await pagina.waitForTimeout(1800);
  const donde = await pagina.evaluate((href) => {
    const ancla = decodeURIComponent((href ?? '').split('#')[1] ?? '');
    const directo = document.getElementById(ancla);
    const conPrefijo = document.getElementById(`apartado-${ancla}`);
    const visible = (el) => {
      if (el === null) return null;
      const r = el.getBoundingClientRect();
      return { top: Math.round(r.top), aLaVista: r.top > -50 && r.top < window.innerHeight };
    };
    return {
      href,
      ancla,
      existeDirecto: directo !== null,
      existeConPrefijo: conPrefijo !== null,
      cajaConPrefijo: visible(conPrefijo),
      scrollY: Math.round(window.scrollY),
    };
  }, destino);
  console.log(JSON.stringify(donde, null, 2));
}

// ---------------------------------------------------------------- 4 · /admin/apuntes
console.log('\n=== 4 · /admin/apuntes ===');
await pagina.goto(`${WEB}/admin/apuntes`, { waitUntil: 'networkidle' });
await pagina.waitForTimeout(2500);
const apuntes = await pagina.evaluate(() => ({
  tablas: document.querySelectorAll('main table').length,
  filasTbody: document.querySelectorAll('main tbody tr').length,
  filasLi: document.querySelectorAll('main li').length,
  texto: (document.querySelector('main')?.textContent ?? '').replace(/\s+/g, ' ').slice(0, 500),
  esqueleto: document.querySelectorAll('.esqueleto').length,
  error: document.querySelectorAll('[role="alert"], .error').length,
}));
console.log(JSON.stringify(apuntes, null, 2));

await navegador.close();
