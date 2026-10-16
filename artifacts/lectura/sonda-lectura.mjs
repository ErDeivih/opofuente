/**
 * Sonda de lectura (F35): mide la pantalla de apuntes y volcado de su texto.
 *
 * No es una prueba: es la herramienta con la que se mide «antes» y «después». Devuelve, por cada
 * ruta y ancho, la geometría que el encargo pide y —cuando se le pide— el texto visible de la
 * pantalla, para poder leer qué párrafos explicativos hay sin depender de mirar el PNG.
 *
 * Uso: node sonda-lectura.mjs [--salida <dir>] [--texto]
 */

import { mkdirSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import path from 'node:path';

// La sonda vive fuera del arbol (es scratch), asi que resuelve Playwright desde el arbol que si lo
// tiene instalado: `require` con la raiz de `apps/web` como base.
const require = createRequire('F:/temp-opofuente/opofuente-lectura/apps/web/package.json');
const { chromium } = require('@playwright/test');

const BASE = 'http://127.0.0.1:4173';
const ANCHOS = [
  { ancho: 1280, alto: 800, etiqueta: 'escritorio' },
  { ancho: 390, alto: 844, etiqueta: 'movil' },
];
const RUTAS = [
  { ruta: '/temario/IV.7', nombre: 'tema-IV-7' },
  { ruta: '/temario/I.1', nombre: 'tema-I-1' },
  { ruta: '/temario/IV.7#osi-capas', nombre: 'tema-IV-7-ancla-desnuda' },
  { ruta: '/temario/IV.7#apartado-osi-capas', nombre: 'tema-IV-7-ancla' },
];

function argumento(nombre) {
  const indice = process.argv.indexOf(nombre);
  return indice < 0 ? null : (process.argv[indice + 1] ?? null);
}

const SALIDA = argumento('--salida');
const CON_TEXTO = process.argv.includes('--texto');

async function medir(page) {
  return page.evaluate(() => {
    const redondo = (valor) => Math.round(valor);
    const caja = (selector) => {
      const elemento = document.querySelector(selector);
      if (elemento === null) return null;
      const rect = elemento.getBoundingClientRect();
      return { ancho: redondo(rect.width), alto: redondo(rect.height) };
    };
    const marco = document.querySelector('.apuntes__tabla-marco');
    return {
      altoDocumento: document.documentElement.scrollHeight,
      anchoDocumento: document.documentElement.scrollWidth,
      anchoVentana: window.innerWidth,
      altoVentana: window.innerHeight,
      scrollY: redondo(window.scrollY),
      columnaTexto: caja('.apartado__cuerpo'),
      indice: caja('.apuntes__indice'),
      indiceScroll: (() => {
        const interior = document.querySelector('.apuntes__indice');
        if (interior === null) return null;
        return {
          alto: redondo(interior.getBoundingClientRect().height),
          desplazable: interior.scrollHeight - interior.clientHeight,
          posicion: getComputedStyle(interior).position,
          desbordaVentana: redondo(interior.getBoundingClientRect().bottom) > window.innerHeight,
        };
      })(),
      apartadosServidos: document.querySelectorAll('.apartado').length,
      apartadosEnIndice: document.querySelectorAll('.apuntes__indice-lista a').length,
      capitulosEnIndice: document.querySelectorAll('.apuntes__indice-capitulo').length,
      tablaDesborda: marco === null ? null : marco.scrollWidth - marco.clientWidth,
      tablas: document.querySelectorAll('.apuntes__tabla').length,
      parrafos: document.querySelectorAll('.apuntes__prosa p').length,
      detalle: [...document.querySelectorAll('.apartado')].slice(0, 3).map((apartado) => ({
        id: apartado.id,
        top: redondo(apartado.getBoundingClientRect().top),
      })),
    };
  });
}

/** El apartado al que apunta el ancla, y si está a la vista. */
async function medirAncla(page, ancla) {
  return page.evaluate((buscado) => {
    const elemento = document.getElementById(buscado);
    if (elemento === null) {
      return { encontrado: false, offsetTop: null, scrollY: Math.round(window.scrollY) };
    }
    const rect = elemento.getBoundingClientRect();
    return {
      encontrado: true,
      scrollY: Math.round(window.scrollY),
      offsetTop: Math.round(rect.top + window.scrollY),
      topEnVentana: Math.round(rect.top),
      aLaVista: rect.top >= -8 && rect.top < window.innerHeight,
    };
  }, ancla);
}

const navegador = await chromium.launch();
const informe = [];
try {
  for (const { ancho, alto, etiqueta } of ANCHOS) {
    const contexto = await navegador.newContext({ viewport: { width: ancho, height: alto } });
    const page = await contexto.newPage();
    const errores = [];
    page.on('console', (mensaje) => {
      if (mensaje.type() === 'error') errores.push(mensaje.text());
    });
    page.on('pageerror', (error) => errores.push(String(error)));

    for (const { ruta, nombre } of RUTAS) {
      if (ancho === 390 && !['tema-IV-7', 'tema-I-1'].includes(nombre)) continue;
      await page.goto(`${BASE}${ruta}`, { waitUntil: 'networkidle' });
      await page.waitForTimeout(2500);
      const medidas = await medir(page);
      const ancla = ruta.includes('#') ? await medirAncla(page, ruta.split('#')[1]) : null;
      const fila = { ruta, ancho, etiqueta, url: page.url(), ...medidas, ancla, errores: [...errores] };
      if (CON_TEXTO) {
        fila.texto = await page.evaluate(() => {
          const copia = document.body.cloneNode(true);
          for (const nodo of Array.from(copia.querySelectorAll('[data-contenido]'))) nodo.remove();
          return (copia.innerText || '').replace(/\n{2,}/g, '\n').slice(0, 4000);
        });
      }
      informe.push(fila);
      if (SALIDA) {
        mkdirSync(SALIDA, { recursive: true });
        await page.screenshot({
          path: path.join(SALIDA, `${nombre}-${etiqueta}.png`),
          fullPage: false,
        });
      }
    }
    await contexto.close();
  }
} finally {
  await navegador.close();
}

const destino = argumento('--json');
if (destino) writeFileSync(destino, JSON.stringify(informe, null, 2));
console.log(JSON.stringify(informe, null, 2));
