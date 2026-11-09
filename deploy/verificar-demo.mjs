// Verificación de la demo desplegada (o del contenedor local): carga el temario, el banco y el tema
// completo, y **termina una práctica sin cuenta** usando solo la API pública. Deja capturas.
//
// Uso:
//   node deploy/verificar-demo.mjs http://127.0.0.1:8099
//   BASE_URL=https://<url> node deploy/verificar-demo.mjs
//
// No escribe material ni toca administración: la sesión de práctica se crea en la base efímera de
// la demo y se queda ahí. Sale con código 1 si una comprobación falla.

import { mkdir } from 'node:fs/promises';
import path from 'node:path';

import { chromium, request } from '@playwright/test';

const BASE = (process.env.BASE_URL ?? process.argv[2] ?? '').replace(/\/+$/, '');
if (!BASE) {
  console.error('Falta BASE_URL (o el primer argumento).');
  process.exit(2);
}

const OUT_DIR = process.env.OUT_DIR ?? path.join(process.cwd(), 'docs', 'capturas', 'deploy-local');

const checks = [];
function check(name, ok, detail = '') {
  checks.push({ name, ok });
  console.log(`${ok ? 'OK  ' : 'FALLO'} ${name}${detail ? ` — ${detail}` : ''}`);
}

await mkdir(OUT_DIR, { recursive: true });

// --- 1. API pública: lectura, ficha del tema y una práctica completa sin cuenta ------------------
const api = await request.newContext({
  baseURL: BASE,
  extraHTTPHeaders: { Origin: BASE, Accept: 'application/json' },
  timeout: 30_000,
});

const curriculas = await api.get('/api/v1/curricula');
check('GET /api/v1/curricula responde 200', curriculas.status() === 200, String(curriculas.status()));
const comun = (await curriculas.json()).find(
  (item) => item.kind === 'common' && item.active_version !== null,
);
check('el temario común está activo', comun !== undefined, comun?.code ?? '');

const detalle = await api.get(`/api/v1/curricula/${comun?.code ?? ''}`);
const arbol = await detalle.json();
check('el temario común tiene 5 bloques y 40 temas', arbol.nodes?.length === 5, `${arbol.nodes?.length ?? 0} bloques`);

function temas(nodos) {
  const salida = [];
  for (const nodo of nodos ?? []) {
    if (nodo.node_type === 'topic') salida.push(nodo);
    salida.push(...temas(nodo.children));
  }
  return salida;
}
const listaTemas = temas(arbol.nodes);
check('hay 40 temas en el árbol', listaTemas.length === 40, `${listaTemas.length}`);
const temaI1 = listaTemas.find((nodo) => nodo.path === 'I.1');
check('existe el tema I.1', temaI1 !== undefined, temaI1?.id ?? '');

const ficha = await api.get(`/api/v1/curriculum-nodes/${temaI1?.id ?? ''}`);
const fichaJson = await ficha.json();
const apuntes = fichaJson.node?.description ?? '';
check(
  'la ficha del tema I.1 tiene apuntes de verdad',
  typeof apuntes === 'string' && apuntes.length > 1000,
  `${apuntes.length} caracteres`,
);

const conjuntos = await api.get('/api/v1/question-sets');
const listaConjuntos = (await conjuntos.json()).sets ?? [];
const practica = listaConjuntos.find((set) => String(set.title).includes('Tema I.1'));
check('existe la práctica del tema I.1', practica !== undefined, practica?.title ?? '');

const oposiciones = await (await api.get('/api/v1/oppositions')).json();
const activa = oposiciones.find((oposicion) => oposicion.active);
const convocatoria = activa?.active_convocation?.id;
check('hay oposición activa para la práctica', activa !== undefined && convocatoria !== undefined);

let practicaCompletada = false;
let resultadoPractica = null;
if (practica !== undefined && activa !== undefined && convocatoria !== undefined) {
  const creada = await api.post('/api/v1/study-sessions', {
    data: {
      opposition_id: activa.id,
      mode: 'practice',
      sources: [
        {
          question_set_id: practica.id,
          part_code: 'primera_parte',
          count: 10,
          include_reserves: false,
        },
      ],
      convocation_version_id: convocatoria,
      feedback: 'immediate',
      shuffle: false,
    },
  });
  const sesion = await creada.json();
  if (creada.status() === 201) {
    await api.post(`/api/v1/study-sessions/${sesion.id}/start`);
    for (let i = 0; i < 12; i += 1) {
      const actual = await api.get(`/api/v1/study-sessions/${sesion.id}/current-question`);
      if (actual.status() !== 200) break;
      const cuerpo = await actual.json();
      if (!cuerpo.question) break;
      const respuesta = await api.post(`/api/v1/study-sessions/${sesion.id}/answers`, {
        data: {
          question_version_id: cuerpo.question.question_version_id,
          chosen_option_keys: ['a'],
          elapsed_ms: 1200,
          confidence: 'high',
        },
      });
      if (respuesta.status() >= 400) break;
    }
    await api.post(`/api/v1/study-sessions/${sesion.id}/finish`);
    const resultado = await api.get(`/api/v1/study-sessions/${sesion.id}/result`);
    practicaCompletada = resultado.status() === 200;
    resultadoPractica = resultado.status();
  }
  check('la práctica se crea sin cuenta', creada.status() === 201, `${creada.status()}`);
}
check('la práctica se puede terminar sin cuenta', practicaCompletada, `result ${resultadoPractica}`);

const admin = await api.post('/api/v1/backups', { data: {} });
check('la administración sigue protegida (sin credenciales)', admin.status() === 401, `${admin.status()}`);

// --- 2. Navegador: portada, temario, banco y ficha del tema -------------------------------------
const browser = await chromium.launch();
const context = await browser.newContext({
  viewport: { width: 1280, height: 900 },
  locale: 'es-ES',
});
const page = await context.newPage();
const consoleErrors = [];
const failedResponses = [];
const CONSOLE_KNOWN = [/frame-ancestors/i, /Failed to load resource/i];
const RESPONSE_KNOWN = [/\/favicon\.ico$/];
page.on('console', (message) => {
  if (message.type() === 'error' && !CONSOLE_KNOWN.some((patron) => patron.test(message.text()))) {
    consoleErrors.push(message.text());
  }
});
page.on('pageerror', (error) => consoleErrors.push(String(error)));
page.on('response', (response) => {
  if (response.status() >= 400 && !RESPONSE_KNOWN.some((patron) => patron.test(response.url()))) {
    failedResponses.push(`${response.status()} ${response.url()}`);
  }
});

async function captura(ruta, nombre, ancho = 1280) {
  await page.setViewportSize({ width: ancho, height: ancho === 390 ? 844 : 900 });
  await page.goto(`${BASE}${ruta}`, { waitUntil: 'networkidle' });
  await page.waitForSelector('h1', { timeout: 20_000 });
  const texto = await page.locator('body').innerText();
  await page.screenshot({ path: path.join(OUT_DIR, `${nombre}-${ancho}.png`), fullPage: true });
  return texto;
}

const inicio = await captura('/', 'inicio');
check('la portada carga con su H1', /Inicio/.test(inicio));

const temario = await captura('/temario', 'temario');
check('la pantalla del temario enseña 5 bloques y 40 temas', /5 bloques/.test(temario) && /40 temas/.test(temario));
await captura('/temario', 'temario', 390);

const pregunta = await captura('/preguntas', 'preguntas');
check('el banco de preguntas carga los conjuntos', /Preguntas/.test(pregunta));

const fichaTexto = await captura(`/temario/${temaI1?.id ?? ''}`, 'tema-i1');
check(
  'la ficha del tema enseña sus apuntes',
  /Constitución Española de 1978/.test(fichaTexto) && /reforma/i.test(fichaTexto),
);
await captura(`/temario/${temaI1?.id ?? ''}`, 'tema-i1', 390);

check('sin respuestas 4xx/5xx inesperadas', failedResponses.length === 0, failedResponses.slice(0, 3).join(' | '));
check('sin errores de consola', consoleErrors.length === 0, consoleErrors.slice(0, 3).join(' | '));

await browser.close();
await api.dispose();

const fallos = checks.filter((item) => !item.ok);
console.log(`\n${checks.length - fallos.length}/${checks.length} comprobaciones correctas. Capturas en ${OUT_DIR}`);
process.exit(fallos.length === 0 ? 0 : 1);
