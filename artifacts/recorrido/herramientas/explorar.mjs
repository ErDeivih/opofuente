/**
 * Reconocimiento de la interfaz (F34): qué enseña cada pantalla, en texto.
 *
 * Este modelo **no ve imágenes**, así que el recorrido no puede describirse mirando los PNG: se
 * describe leyendo el DOM (texto, etiquetas, roles) y midiendo la geometría. El PNG queda para que lo
 * mire el propietario. Esta herramienta es la mitad que sí puedo leer.
 */

import { chromium } from 'playwright';

const BASE = process.env.OPOFUENTE_WEB_URL ?? 'http://127.0.0.1:4173';

const RUTAS = [
  '/',
  '/temario',
  '/temario/IV.7',
  '/temario/I.1',
  '/simulacros',
  '/examenes',
  '/fallos',
  '/progreso',
  '/admin/incidencias',
  '/admin/apuntes',
  '/tests',
];

const navegador = await chromium.launch();
const contexto = await navegador.newContext({ viewport: { width: 1280, height: 800 }, locale: 'es-ES' });
const pagina = await contexto.newPage();
const errores = [];
pagina.on('console', (m) => {
  if (m.type() === 'error') errores.push(m.text());
});
pagina.on('pageerror', (e) => errores.push(String(e)));

for (const ruta of RUTAS) {
  errores.length = 0;
  const inicio = Date.now();
  await pagina.goto(`${BASE}${ruta}`, { waitUntil: 'networkidle' });
  const ms = Date.now() - inicio;
  const datos = await pagina.evaluate(() => {
    const norm = (t) => (t ?? '').replace(/\s+/g, ' ').trim();
    const main = document.querySelector('main');
    const botones = [...document.querySelectorAll('main button')].map((b) => norm(b.textContent));
    const enlaces = [...document.querySelectorAll('main a')].map((a) => norm(a.textContent));
    const titulos = [...document.querySelectorAll('main h1, main h2, main h3')].map((h) => norm(h.textContent));
    const entradas = [...document.querySelectorAll('main input, main select, main textarea')].map(
      (i) => `${i.tagName.toLowerCase()}[${i.type ?? ''}] name=${i.name ?? ''} id=${i.id ?? ''} placeholder=${i.placeholder ?? ''}`,
    );
    return {
      titulo: document.title,
      h1: norm(document.querySelector('h1')?.textContent),
      titulos,
      botones,
      enlaces,
      entradas,
      texto: norm(main?.textContent).slice(0, 1400),
    };
  });
  console.log('='.repeat(100));
  console.log(`RUTA ${ruta}  (${ms} ms)`);
  console.log('h1:', datos.h1);
  console.log('TITULOS:', JSON.stringify(datos.titulos));
  console.log('BOTONES:', JSON.stringify(datos.botones));
  console.log('ENLACES:', JSON.stringify(datos.enlaces.slice(0, 60)));
  console.log('ENTRADAS:', JSON.stringify(datos.entradas));
  console.log('TEXTO:', datos.texto);
  if (errores.length) console.log('ERRORES CONSOLA:', JSON.stringify(errores.slice(0, 5)));
}

await navegador.close();
