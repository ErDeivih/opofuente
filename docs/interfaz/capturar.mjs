#!/usr/bin/env node
/**
 * Captura todas las pantallas de OpoFuente para la revisión de interfaz externa de 2026-11.
 *
 * No forma parte de la aplicación ni de las puertas: es una herramienta de documentación. Vive en
 * `docs/interfaz/` y solo escribe en `docs/capturas/revision-2026-11/` y en
 * `docs/interfaz/.captura-<modo>.json` (JSON de trabajo que `generar-textos.mjs` convierte en el
 * anexo de textos).
 *
 * Uso (con la API y el preview ya levantados):
 *
 *   node docs/interfaz/capturar.mjs --modo=datos
 *   node docs/interfaz/capturar.mjs --modo=vacio
 *
 * Variables:
 *   CAPTURA_BASE  URL del preview de la web (por defecto http://127.0.0.1:4173)
 *   CAPTURA_API   URL de la API           (por defecto http://127.0.0.1:8765)
 *
 * El modo `datos` espera la API apuntando a `.e2e-data` (datos sintéticos de la suite E2E). El modo
 * `vacio` espera una API recién migrada y sembrada, sin material, preguntas ni sesiones; en ese modo
 * solo se capturan las pantallas que tienen estado vacío propio.
 *
 * Los ids reales NO están escritos a mano: se piden a la API antes de navegar.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { chromium, request as playwrightRequest } from '@playwright/test';

const aqui = path.dirname(fileURLToPath(import.meta.url));
const raiz = path.resolve(aqui, '..', '..');

const BASE = process.env.CAPTURA_BASE ?? 'http://127.0.0.1:4173';
const API = process.env.CAPTURA_API ?? 'http://127.0.0.1:8765';

const argModo = process.argv.find((arg) => arg.startsWith('--modo='));
const modo = (argModo?.split('=')[1] ?? process.env.CAPTURA_MODO ?? 'datos').trim();

const DIR_CAPTURAS = path.join(raiz, 'docs', 'capturas', 'revision-2026-11');
const JSON_SALIDA = path.join(aqui, `.captura-${modo}.json`);
const SUFIJO = modo === 'vacio' ? '-vacio' : '';

const VIEWPORTS = [
  { ancho: 1280, alto: 900, etiqueta: '1280' },
  { ancho: 390, alto: 844, etiqueta: '390' },
];

/** Rutas estáticas que existen en `apps/web/src/app/routes.tsx` (para la comprobación de enlaces). */
const RUTAS_CONOCIDAS = [
  '/',
  '/temario',
  '/programa',
  '/bandeja',
  '/biblioteca',
  '/preguntas',
  '/estudiar',
  '/errores',
  '/cambios',
  '/ajustes',
  '/revision',
  '/buscar',
];

// ---------------------------------------------------------------------------------------------
// Utilidades
// ---------------------------------------------------------------------------------------------

async function apiJson(ruta) {
  const respuesta = await fetch(`${API}${ruta}`, { headers: { Accept: 'application/json' } });
  if (!respuesta.ok) {
    throw new Error(`La API respondió ${respuesta.status} en ${ruta}`);
  }
  return respuesta.json();
}

function dormir(ms) {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

/**
 * Espera a que la pantalla se asiente: sin estados de carga visibles, sin red en curso y con las
 * fuentes listas. Los tiempos son topes, no esperas fijas: en cuanto la página está quieta se sigue.
 */
async function asentar(page) {
  const limite = Date.now() + 12_000;
  while (Date.now() < limite) {
    const cargando = await page.locator('.loading').count();
    if (cargando === 0) {
      break;
    }
    await dormir(120);
  }
  try {
    await page.waitForLoadState('networkidle', { timeout: 6_000 });
  } catch {
    // Una pantalla con reintentos periódicos nunca llega a "idle": se sigue con lo que hay.
  }
  await page.evaluate(() => document.fonts.ready.then(() => true));
  await dormir(300);
}

/** Mide el desborde horizontal real de la página y los elementos que se salen sin estar recortados. */
async function medirDesborde(page) {
  return page.evaluate(() => {
    const vw = window.innerWidth;
    const doc = document.documentElement;

    function recortadoPorAncestro(el) {
      for (let p = el.parentElement; p !== null; p = p.parentElement) {
        const estilo = getComputedStyle(p);
        if (estilo.overflowX !== 'visible') {
          return true;
        }
      }
      return false;
    }

    const culpables = [];
    if (doc.scrollWidth > doc.clientWidth) {
      for (const el of document.querySelectorAll('body *')) {
        const r = el.getBoundingClientRect();
        if (r.width <= 0 || r.right <= vw + 1) {
          continue;
        }
        if (recortadoPorAncestro(el)) {
          continue;
        }
        culpables.push({
          etiqueta: el.tagName.toLowerCase(),
          clase: typeof el.className === 'string' ? el.className.slice(0, 80) : null,
          derecha: Math.round(r.right),
          ancho: Math.round(r.width),
          texto: (el.textContent ?? '').trim().slice(0, 70),
        });
      }
    }

    return {
      anchoViewport: vw,
      scrollWidth: doc.scrollWidth,
      clientWidth: doc.clientWidth,
      scrollWidthBody: document.body.scrollWidth,
      desborda: doc.scrollWidth > doc.clientWidth,
      culpables: culpables.slice(0, 12),
      totalCulpables: culpables.length,
    };
  });
}

/** Datos técnicos y textos de la pantalla en el estado en que se captura. */
async function leerPantalla(page) {
  return page.evaluate(() => {
    const main = document.querySelector('main');
    const texto = (el) => (el === null ? '' : (el.innerText ?? '').trim());
    return {
      tituloPestana: document.title,
      h1: [...document.querySelectorAll('main h1, header h1')].map((h) => h.innerText.trim()),
      encabezados: [...document.querySelectorAll('main h1, main h2, main h3')].map((h) => ({
        nivel: h.tagName.toLowerCase(),
        texto: h.innerText.trim(),
      })),
      pestanas: [...document.querySelectorAll('main [role="tab"]')].map((t) => ({
        texto: t.innerText.trim(),
        seleccionada: t.getAttribute('aria-selected') === 'true',
      })),
      main: texto(main),
      cabecera: texto(document.querySelector('.app__header')),
      navegacion: [...document.querySelectorAll('.app__nav a')].map((a) => ({
        texto: a.innerText.trim().replace(/\s+/g, ' '),
        href: a.getAttribute('href'),
        actual: a.classList.contains('nav__link--active'),
      })),
      estados: {
        vacio: document.querySelectorAll('.empty').length,
        cargando: document.querySelectorAll('.loading').length,
        error: document.querySelectorAll('.error-state').length,
        avisos: document.querySelectorAll('.notice, .status-summary').length,
      },
      enlaces: [...document.querySelectorAll('main a[href]')].map((a) => ({
        texto: a.innerText.trim().replace(/\s+/g, ' ').slice(0, 90),
        href: a.getAttribute('href'),
      })),
      botones: [...document.querySelectorAll('main button, main a.button')]
        .map((b) => ({ texto: b.innerText.trim().replace(/\s+/g, ' ').slice(0, 90), deshabilitado: b.disabled === true }))
        .filter((b) => b.texto !== ''),
    };
  });
}

/** Abre `ruta` en una pestaña limpia y devuelve lo observado (sin capturar imagen). */
async function visitar(contexto, ruta, opciones = {}) {
  const page = await contexto.newPage();
  const consola = [];
  const fallosRed = [];
  const respuestasMalas = [];
  page.on('console', (mensaje) => {
    if (mensaje.type() === 'error') {
      consola.push({ tipo: 'console.error', texto: mensaje.text().slice(0, 500) });
    }
  });
  page.on('pageerror', (error) => {
    consola.push({ tipo: 'pageerror', texto: String(error.message).slice(0, 500) });
  });
  page.on('requestfailed', (peticion) => {
    fallosRed.push({ url: peticion.url().slice(0, 300), error: peticion.failure()?.errorText ?? '' });
  });
  page.on('response', (respuesta) => {
    if (respuesta.status() >= 400) {
      respuestasMalas.push({ url: respuesta.url().slice(0, 300), estado: respuesta.status() });
    }
  });

  let respuesta = null;
  try {
    respuesta = await page.goto(`${BASE}${ruta}`, { waitUntil: 'load', timeout: 30_000 });
  } catch (error) {
    consola.push({ tipo: 'navegacion', texto: String(error.message).slice(0, 500) });
  }
  if (opciones.preparar !== undefined) {
    try {
      await opciones.preparar(page);
    } catch (error) {
      consola.push({ tipo: 'preparacion', texto: String(error.message).slice(0, 500) });
    }
  }
  await asentar(page);

  return { page, respuesta, consola, fallosRed, respuestasMalas };
}

// ---------------------------------------------------------------------------------------------
// Resolución de ids reales por la API
// ---------------------------------------------------------------------------------------------

async function resolverIds() {
  const ids = { documentoId: null, nodeId: null, nodoConvocatoriaId: null, convocatoriaId: null, setId: null, preguntaId: null };
  if (modo === 'vacio') {
    return ids;
  }

  // Documento con varias versiones: el primero que devuelve la biblioteca.
  const documentos = await apiJson('/api/v1/documents?limit=10');
  const documento =
    documentos.documents.find((d) => (d.version_count ?? 0) > 1) ?? documentos.documents[0] ?? null;
  ids.documentoId = documento?.id ?? null;

  // Nodo del temario con preguntas y material: sale de las asignaciones ya aceptadas, no a mano.
  const mappings = await apiJson('/api/v1/mappings?limit=300');
  const conPreguntas = mappings.filter((m) => m.subject_type === 'question_version');
  const candidato = conPreguntas.find((m) => m.node_depth >= 1) ?? conPreguntas[0] ?? null;
  ids.nodeId = candidato?.node_id ?? null;

  // Nodo que aparece en alguna convocatoria publicada: sirve para la ficha con `?convocatoria=`.
  const curricula = await apiJson('/api/v1/curricula');
  const comun = curricula.find((c) => c.kind === 'common') ?? null;
  if (comun !== null) {
    const detalle = await apiJson(`/api/v1/curricula/${comun.code}`);
    const tema = detalle.nodes.flatMap((bloque) => bloque.children ?? [])[0] ?? null;
    if (tema !== null) {
      const detalleTema = await apiJson(`/api/v1/curriculum-nodes/${tema.id}`);
      const aparicion =
        detalleTema.appears_in.find((a) => a.convocation_status !== 'draft') ?? null;
      if (aparicion !== null) {
        ids.nodoConvocatoriaId = tema.id;
        ids.convocatoriaId = aparicion.convocation_id;
      }
    }
  }

  // Conjunto de preguntas más grande y su primera pregunta.
  const conjuntos = await apiJson('/api/v1/question-sets?limit=100');
  const conjunto =
    [...conjuntos.sets].sort((a, b) => (b.question_count ?? 0) - (a.question_count ?? 0))[0] ?? null;
  ids.setId = conjunto?.id ?? null;
  if (ids.setId !== null) {
    const preguntas = await apiJson(`/api/v1/question-sets/${ids.setId}/questions?limit=50`);
    ids.preguntaId = preguntas.questions[0]?.id ?? null;
  }

  return ids;
}

// ---------------------------------------------------------------------------------------------
// Definición de pantallas
// ---------------------------------------------------------------------------------------------

function definirPantallas(ids) {
  const temas = [
    {
      nombre: 'inicio',
      ruta: '/',
      descripcion: 'Inicio: siguiente tarea, acciones necesarias, estado del programa, actividad.',
    },
    { nombre: 'bandeja', ruta: '/bandeja', descripcion: 'Bandeja: entrada de material e inventario.' },
    { nombre: 'temario', ruta: '/temario', descripcion: 'Temario: árbol de bloques y temas.' },
    { nombre: 'programa', ruta: '/programa', descripcion: 'Programa: árbol oficial de la convocatoria activa.' },
    { nombre: 'biblioteca', ruta: '/biblioteca', descripcion: 'Biblioteca: documentos, filtros y colecciones.' },
    { nombre: 'preguntas', ruta: '/preguntas', descripcion: 'Preguntas: banco, importación y plantillas.' },
    { nombre: 'estudiar', ruta: '/estudiar', descripcion: 'Estudiar: preparación, sesión en marcha y resultado.' },
    { nombre: 'errores', ruta: '/errores', descripcion: 'Errores: cola de repaso y conceptos.' },
    { nombre: 'cambios', ruta: '/cambios', descripcion: 'Cambios: diff de versiones y derivados por revisar.' },
    { nombre: 'revision', ruta: '/revision', descripcion: 'Revisión: propuestas de clasificación.' },
    { nombre: 'buscar', ruta: '/buscar?q=plazo', descripcion: 'Buscar y preguntar: resultados y respuesta del corpus.' },
    { nombre: 'ajustes', ruta: '/ajustes', descripcion: 'Ajustes: datos, capacidades, copias, diagnóstico.' },
    { nombre: 'no-encontrada', ruta: '/seccion-que-no-existe', descripcion: '404.' },
  ];

  if (modo === 'vacio') {
    // Las ocho pantallas del encargo, más el temario (la siembra de perfiles deja el temario común
    // pero ningún material ni pregunta) y la revisión, que en vacío no tiene propuestas.
    const vacias = [
      'inicio',
      'bandeja',
      'temario',
      'biblioteca',
      'preguntas',
      'estudiar',
      'errores',
      'cambios',
      'ajustes',
      'revision',
    ];
    return temas.filter((tema) => vacias.includes(tema.nombre));
  }

  const conIds = [];

  if (ids.nodeId !== null) {
    conIds.push({
      nombre: 'temario-tema',
      ruta: `/temario/${ids.nodeId}`,
      descripcion: 'Ficha del tema: apuntes, material, preguntas y convocatorias.',
    });
    conIds.push({
      nombre: 'temario-tema-practicar',
      ruta: `/temario/${ids.nodeId}/practicar`,
      descripcion: 'Práctica libre del bloque: preguntas del bloque y arranque de sesión.',
    });
    if (ids.convocatoriaId !== null) {
      conIds.push({
        nombre: 'temario-tema-convocatoria',
        ruta: `/temario/${ids.nodoConvocatoriaId ?? ids.nodeId}?convocatoria=${ids.convocatoriaId}`,
        descripcion: 'Ficha del tema con las particularidades de una convocatoria.',
      });
    }
  }

  if (ids.documentoId !== null) {
    conIds.push({
      nombre: 'biblioteca-documento',
      ruta: `/biblioteca?documento=${ids.documentoId}`,
      descripcion: 'Ficha del documento abierta (pestaña Lector).',
    });
    conIds.push({
      nombre: 'biblioteca-documento-versiones',
      ruta: `/biblioteca?documento=${ids.documentoId}`,
      descripcion: 'Ficha del documento, pestaña «Versiones y diff».',
      preparar: async (page) => {
        await page.getByRole('tab', { name: 'Versiones y diff' }).click();
        await dormir(400);
      },
    });
  }

  if (ids.setId !== null && ids.preguntaId !== null) {
    conIds.push({
      nombre: 'preguntas-conjunto',
      ruta: `/preguntas?conjunto=${ids.setId}&pregunta=${ids.preguntaId}`,
      descripcion: 'Banco con un conjunto y una pregunta abiertos.',
    });
    conIds.push({
      nombre: 'preguntas-plantillas',
      ruta: '/preguntas',
      descripcion: 'Pestaña «Plantillas» del banco de preguntas.',
      preparar: async (page) => {
        await page.getByRole('tab', { name: 'Plantillas' }).click();
        await dormir(400);
      },
    });
  }

  // Orden de revisión: primero el recorrido del producto y luego las fichas con ids.
  return [...temas, ...conIds];
}

// ---------------------------------------------------------------------------------------------
// Captura
// ---------------------------------------------------------------------------------------------

async function capturar(contexto, viewport, pantalla) {
  const { page, respuesta, consola, fallosRed, respuestasMalas } = await visitar(contexto, pantalla.ruta, pantalla);
  const textos = await leerPantalla(page);
  const desborde = await medirDesborde(page);
  const nombreFichero = `${pantalla.nombre}${SUFIJO}-${viewport.etiqueta}.png`;
  await page.screenshot({
    path: path.join(DIR_CAPTURAS, nombreFichero),
    fullPage: true,
    animations: 'disabled',
  });
  const alto = await page.evaluate(() => document.documentElement.scrollHeight);
  const resultado = {
    pantalla: pantalla.nombre,
    ruta: pantalla.ruta,
    descripcion: pantalla.descripcion,
    viewport: { ancho: viewport.ancho, alto: viewport.alto },
    captura: nombreFichero,
    estadoHttp: respuesta?.status() ?? null,
    altoPagina: alto,
    textos,
    desborde,
    consola,
    fallosRed,
    respuestasMalas,
    cuando: new Date().toISOString(),
  };
  await page.close();
  return resultado;
}

/** Estado de carga: se retrasa la respuesta de la API para fotografiar el «cargando». */
async function capturarCargando(browser, pantalla) {
  const contexto = await browser.newContext({ viewport: { width: 1280, height: 900 }, locale: 'es-ES' });
  await contexto.route('**/api/v1/**', async (ruta) => {
    await dormir(2500);
    await ruta.continue();
  });
  const page = await contexto.newPage();
  await page.goto(`${BASE}${pantalla.ruta}`, { waitUntil: 'domcontentloaded', timeout: 30_000 });
  await page.waitForSelector('main', { timeout: 10_000 });
  await dormir(700);
  const textos = await leerPantalla(page);
  await page.screenshot({ path: path.join(DIR_CAPTURAS, `${pantalla.nombre}-cargando-1280.png`), fullPage: true });
  await page.close();
  await contexto.close();
  return {
    pantalla: `${pantalla.nombre}-cargando`,
    ruta: pantalla.ruta,
    descripcion: 'Estado de carga (respuestas de la API retrasadas 2,5 s).',
    viewport: { ancho: 1280, alto: 900 },
    captura: `${pantalla.nombre}-cargando-1280.png`,
    altoPagina: 900,
    textos,
    desborde: null,
    consola: [],
    fallosRed: [],
    cuando: new Date().toISOString(),
  };
}

/** Estado de error: se fuerza un 500 en la API para ver qué enseña la pantalla. */
async function capturarError(browser, pantalla) {
  const contexto = await browser.newContext({ viewport: { width: 1280, height: 900 }, locale: 'es-ES' });
  await contexto.route('**/api/v1/**', async (ruta) => {
    await ruta.fulfill({ status: 500, contentType: 'application/problem+json', body: JSON.stringify({ type: 'about:blank', title: 'Fallo forzado', status: 500, detail: 'Fallo forzado para la captura', code: 'forced_failure', correlation_id: 'captura' }) });
  });
  const page = await contexto.newPage();
  await page.goto(`${BASE}${pantalla.ruta}`, { waitUntil: 'load', timeout: 30_000 });
  await dormir(1500);
  const textos = await leerPantalla(page);
  await page.screenshot({ path: path.join(DIR_CAPTURAS, `${pantalla.nombre}-error-1280.png`), fullPage: true });
  await page.close();
  await contexto.close();
  return {
    pantalla: `${pantalla.nombre}-error`,
    ruta: pantalla.ruta,
    descripcion: 'Estado de error (la API responde 500 a todo).',
    viewport: { ancho: 1280, alto: 900 },
    captura: `${pantalla.nombre}-error-1280.png`,
    altoPagina: 900,
    textos,
    desborde: null,
    consola: [],
    fallosRed: [],
    cuando: new Date().toISOString(),
  };
}

// ---------------------------------------------------------------------------------------------
// Comprobación de enlaces
// ---------------------------------------------------------------------------------------------

function patrónDeRuta(href) {
  const ruta = href.split('?')[0];
  if (RUTAS_CONOCIDAS.includes(ruta)) {
    return ruta;
  }
  if (/^\/temario\/[^/]+\/practicar$/.test(ruta)) {
    return '/temario/:nodeId/practicar';
  }
  if (/^\/temario\/[^/]+$/.test(ruta)) {
    return '/temario/:nodeId';
  }
  return null;
}

async function comprobarEnlaces(browser, resultados) {
  const internos = new Map();
  const externos = new Map();

  for (const resultado of resultados) {
    if (resultado.textos === undefined) {
      continue;
    }
    for (const enlace of resultado.textos.enlaces) {
      const href = enlace.href;
      if (href === null) {
        continue;
      }
      if (href.startsWith('#') || href.startsWith('mailto:') || href.startsWith('blob:')) {
        continue;
      }
      if (href.startsWith('http') && !href.startsWith(BASE)) {
        externos.set(href, enlace.texto);
        continue;
      }
      const ruta = href.startsWith(BASE) ? href.slice(BASE.length) : href;
      if (!internos.has(ruta)) {
        internos.set(ruta, { ruta, textos: new Set(), pantallas: new Set() });
      }
      const entrada = internos.get(ruta);
      entrada.textos.add(enlace.texto);
      entrada.pantallas.add(resultado.pantalla);
    }
  }

  // Contexto de peticiones propio (independiente del navegador: el del navegador se cerraría con
  // el contexto y dejaría a medias la comprobación de entidades).
  const request = await playwrightRequest.newContext({ timeout: 20_000 });
  const revisados = [];
  for (const [ruta, entrada] of internos) {
    let estadoHttp = null;
    let error = null;
    try {
      const respuesta = await request.get(`${BASE}${ruta.split('#')[0]}`);
      estadoHttp = respuesta.status();
    } catch (fallo) {
      error = String(fallo.message).slice(0, 200);
    }
    revisados.push({
      ruta,
      estadoHttp,
      error,
      patron: patrónDeRuta(ruta),
      textos: [...entrada.textos],
      pantallas: [...entrada.pantallas],
    });
  }

  // Entidades referenciadas por la dirección: se comprueban contra la API, no contra el HTML.
  const entidades = [];
  const parametros = new Map([
    ['documento', (id) => `/api/v1/documents/${id}`],
    ['conjunto', (id) => `/api/v1/question-sets/${id}`],
    ['pregunta', (id) => `/api/v1/questions/${id}`],
    ['convocatoria', (id) => `/api/v1/convocations/${id}`],
  ]);
  const yaComprobadas = new Set();
  for (const ruta of internos.keys()) {
    const [camino, consulta] = ruta.split('?');
    if (consulta === undefined) {
      const tema = camino.match(/^\/temario\/([0-9a-f-]{36})/);
      if (tema !== null && !yaComprobadas.has(`nodo:${tema[1]}`)) {
        yaComprobadas.add(`nodo:${tema[1]}`);
        const respuesta = await request.get(`${API}/api/v1/curriculum-nodes/${tema[1]}`);
        entidades.push({ referencia: `nodo ${tema[1]}`, desde: ruta, estadoHttp: respuesta.status() });
      }
      continue;
    }
    for (const [clave, valor] of new URLSearchParams(consulta)) {
      const constructor = parametros.get(clave);
      if (constructor === undefined) {
        continue;
      }
      const marca = `${clave}:${valor}`;
      if (yaComprobadas.has(marca)) {
        continue;
      }
      yaComprobadas.add(marca);
      const respuesta = await request.get(`${API}${constructor(valor)}`);
      entidades.push({ referencia: `${clave} ${valor}`, desde: ruta, estadoHttp: respuesta.status() });
    }
  }

  const externosLista = [...externos.entries()].map(([href, texto]) => ({ href, texto }));
  await request.dispose();
  return {
    internos: revisados,
    externos: externosLista,
    entidades,
    noRevisados: 'Los enlaces externos (http/https fuera del preview) no se han pedido: la revisión los enumera pero no los descarga.',
  };
}

// ---------------------------------------------------------------------------------------------
// Programa principal
// ---------------------------------------------------------------------------------------------

async function main() {
  await fs.mkdir(DIR_CAPTURAS, { recursive: true });

  // Comprueba que la API responde antes de nada: si no, todas las capturas saldrían con errores.
  const salud = await apiJson('/api/v1/health/ready').catch((error) => ({ error: String(error.message) }));
  if (salud.error !== undefined) {
    throw new Error(`La API no responde en ${API}: ${salud.error}`);
  }

  const ids = await resolverIds();
  const pantallas = definirPantallas(ids);
  console.log(`Modo ${modo}: ${pantallas.length} pantallas × ${VIEWPORTS.length} anchos`);
  console.log('Ids resueltos:', ids);

  const browser = await chromium.launch({ headless: true });
  const resultados = [];
  try {
    for (const viewport of VIEWPORTS) {
      const contexto = await browser.newContext({
        viewport: { width: viewport.ancho, height: viewport.alto },
        deviceScaleFactor: 1,
        locale: 'es-ES',
        colorScheme: 'light',
      });
      for (const pantalla of pantallas) {
        try {
          const resultado = await capturar(contexto, viewport, pantalla);
          resultados.push(resultado);
          console.log(`  ok ${resultado.captura} (${resultado.altoPagina}px de alto)`);
        } catch (error) {
          resultados.push({
            pantalla: pantalla.nombre,
            ruta: pantalla.ruta,
            descripcion: pantalla.descripcion,
            viewport: { ancho: viewport.ancho, alto: viewport.alto },
            captura: null,
            error: String(error.message).slice(0, 500),
          });
          console.log(`  FALLO ${pantalla.nombre} @${viewport.etiqueta}: ${String(error.message).slice(0, 200)}`);
        }
      }
      await contexto.close();
    }

    // Estados de apoyo, solo a 1280: carga y error de las dos pantallas donde más se ven.
    for (const pantalla of modo === 'vacio' ? [] : [{ nombre: 'inicio', ruta: '/' }, { nombre: 'preguntas', ruta: '/preguntas' }]) {
      for (const constructor of [capturarCargando, capturarError]) {
        try {
          const resultado = await constructor(browser, pantalla);
          resultados.push(resultado);
          console.log(`  ok ${resultado.captura}`);
        } catch (error) {
          console.log(`  FALLO estado de ${pantalla.nombre}: ${String(error.message).slice(0, 200)}`);
        }
      }
    }

    const enlaces = await comprobarEnlaces(browser, resultados);
    const informe = {
      generado: new Date().toISOString(),
      modo,
      base: BASE,
      api: API,
      directorio: 'docs/capturas/revision-2026-11',
      ids,
      pantallas: resultados,
      enlaces,
    };
    await fs.writeFile(JSON_SALIDA, `${JSON.stringify(informe, null, 2)}\n`, 'utf8');
    console.log(`\nInforme de captura: ${JSON_SALIDA}`);
    console.log(`Capturas: ${resultados.filter((r) => r.captura !== null).length} de ${resultados.length} intentos`);
    const fallidas = resultados.filter((r) => r.captura === null);
    if (fallidas.length > 0) {
      console.log('Pantallas fallidas:', fallidas.map((r) => r.pantalla).join(', '));
    }
  } finally {
    await browser.close();
  }
}

await main();
