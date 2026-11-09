// Capturas "después" de la corrección de interfaz (9/11/2026, noche).
//
// Requiere la API en 127.0.0.1:8765 apuntando a `.e2e-data` y el preview de la web en 4173
// (`npm run preview --workspace @opofuente/web -- --port 4173 --strictPort`). No arranca servidores.
//
// Uso: node docs/interfaz/capturar-despues.mjs

import { mkdir } from 'node:fs/promises';
import path from 'node:path';

import { chromium } from '@playwright/test';

const BASE = process.env.CAPTURA_BASE ?? 'http://127.0.0.1:4173';
const API = process.env.CAPTURA_API ?? 'http://127.0.0.1:8765';
const AQUI = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1'));
const SALIDA = path.join(AQUI, '..', 'capturas', 'despues-2026-11');

const PANTALLAS = [
  { nombre: 'inicio', ruta: '/' },
  { nombre: 'estudiar', ruta: '/estudiar' },
  { nombre: 'buscar', ruta: '/buscar?q=plazo' },
  { nombre: 'revision', ruta: '/revision' },
  { nombre: 'cambios', ruta: '/cambios' },
];

await mkdir(SALIDA, { recursive: true });
const navegador = await chromium.launch();
const contexto = await navegador.newContext({
  viewport: { width: 1280, height: 900 },
  locale: 'es-ES',
});
const pagina = await contexto.newPage();

async function captura(ruta, nombre, ancho) {
  await pagina.setViewportSize({ width: ancho, height: ancho === 390 ? 844 : 900 });
  await pagina.goto(`${BASE}${ruta}`, { waitUntil: 'networkidle' });
  await pagina.waitForSelector('h1', { timeout: 15_000 });
  await pagina.screenshot({
    path: path.join(SALIDA, `${nombre}-${ancho}.png`),
    fullPage: true,
  });
  const texto = await pagina.locator('body').innerText();
  return texto;
}

// Un conjunto real del corpus sintético para que la pantalla de preguntas no salga vacía.
const conjuntos = await (await fetch(`${API}/api/v1/question-sets`)).json();
const conjunto = conjuntos.sets?.[0];
if (conjunto) {
  PANTALLAS.push({ nombre: 'preguntas', ruta: `/preguntas?conjunto=${conjunto.id}` });
}

for (const pantalla of PANTALLAS) {
  const texto = await captura(pantalla.ruta, pantalla.nombre, 1280);
  if (pantalla.nombre === 'buscar') {
    const jerga = ['T', 'rev-', 'corpus 18'].filter((marca) => texto.includes(marca));
    if (texto.includes('recuperación léxica')) {
      console.log('OK buscar: estrategia traducida a «léxica»');
    } else {
      console.log('AVISO buscar: no se encontró «recuperación léxica»');
    }
    if (jerga.length > 0) {
      console.log(`AVISO buscar: quedan marcas técnicas: ${jerga.join(', ')}`);
    }
  }
  if (pantalla.nombre === 'inicio' && /2026-11-08T/.test(texto)) {
    console.log('AVISO inicio: todavía hay una fecha ISO con T');
  }
  await captura(pantalla.ruta, pantalla.nombre, 390);
}

await navegador.close();
console.log(`Capturas en ${SALIDA}`);
