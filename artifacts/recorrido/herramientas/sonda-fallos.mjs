/** Sonda mínima (F34): el botón «Test con mis fallos», con consola y red a la vista. */

import { chromium } from 'playwright';

const WEB = 'http://127.0.0.1:4173';

const navegador = await chromium.launch();
const pagina = await (await navegador.newContext({ viewport: { width: 1280, height: 800 } })).newPage();

pagina.on('console', (m) => console.log('CONSOLA', m.type(), m.text().slice(0, 200)));
pagina.on('pageerror', (e) => console.log('PAGEERROR', String(e).slice(0, 300)));
pagina.on('request', (r) => {
  if (r.url().includes('/api/v1')) console.log('PETICIÓN', r.method(), r.url().split('/api/v1')[1]);
});
pagina.on('response', async (r) => {
  if (r.url().includes('/student/tests')) {
    console.log('RESPUESTA', r.status(), (await r.text().catch(() => '')).slice(0, 200));
  }
});

await pagina.goto(`${WEB}/fallos`, { waitUntil: 'networkidle' });
await pagina.waitForTimeout(1500);

const info = await pagina.evaluate(() => {
  const botones = [...document.querySelectorAll('main button, main a')]
    .filter((b) => /Test con mis fallos|Solo los de/.test(b.textContent ?? ''))
    .map((b) => ({
      etiqueta: b.tagName.toLowerCase(),
      texto: b.textContent.trim().slice(0, 40),
      deshabilitado: b.disabled ?? null,
      clase: b.className,
    }));
  return { botones, url: location.pathname };
});
console.log('BOTONES:', JSON.stringify(info, null, 2));

const boton = pagina.locator('main button').filter({ hasText: 'Test con mis fallos' });
console.log('botones que dicen «Test con mis fallos»:', await boton.count());
console.log('¿habilitado?', await boton.first().isEnabled());

await boton.first().click({ timeout: 10_000 });
console.log('pulsado. URL:', pagina.url());
for (const espera of [1000, 3000, 8000, 20000]) {
  await pagina.waitForTimeout(espera === 1000 ? 1000 : espera - 1000);
  console.log(`  +${espera / 1000}s URL:`, pagina.url());
}
console.log(
  'texto de la pantalla:',
  (await pagina.locator('main').first().innerText()).replace(/\s+/g, ' ').slice(-500),
);

await navegador.close();
