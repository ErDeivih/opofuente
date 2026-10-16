/**
 * El recorrido del alumno y del panel con **datos reales** (F34, §3 de `RECORRIDO-Y-ACABADO-2026-10`).
 *
 * Qué hace y qué no:
 *
 * - recorre los pasos del §3 **en el navegador**, como los haría una persona: pulsando lo que hay en
 *   pantalla, no llamando a la API por detrás;
 * - de cada paso guarda el PNG a **1280×800** y a **390×844** en `artifacts/recorrido/`, el tiempo que
 *   ha tardado la pantalla en quedar lista, los errores de consola y una foto del texto que se lee;
 * - **no juzga**: no hay aserciones que puedan dejar el recorrido a medias. Lo que no exista o falle se
 *   apunta en `filas.json` y se sigue con el paso siguiente. Es una herramienta de reconocimiento, no
 *   una puerta de calidad.
 *
 * Este modelo **no lee imágenes**: el PNG es para que lo mire el propietario. Lo que este guion puede
 * afirmar de lo que se ve es lo que saca del DOM (`evidenciaDeLaPantalla`), y eso es lo que va al
 * informe.
 *
 * Uso: `node artifacts/recorrido/herramientas/recorrido.mjs`
 */

import { mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { chromium } from 'playwright';

const AQUI = path.dirname(fileURLToPath(import.meta.url));
const RAIZ = path.resolve(AQUI, '..', '..', '..');
const SALIDA = path.join(RAIZ, 'artifacts', 'recorrido');
const WEB = process.env.OPOFUENTE_WEB_URL ?? 'http://127.0.0.1:4173';

const ANCHOS = [
  { ancho: 1280, alto: 800, etiqueta: 'escritorio' },
  { ancho: 390, alto: 844, etiqueta: 'movil' },
];

const filas = [];
let numero = 0;

const navegador = await chromium.launch();
const contexto = await navegador.newContext({ viewport: { width: 1280, height: 800 }, locale: 'es-ES' });
const pagina = await contexto.newPage();

let erroresConsola = [];
pagina.on('console', (m) => {
  if (m.type() === 'error') erroresConsola.push(m.text().slice(0, 300));
});
pagina.on('pageerror', (e) => erroresConsola.push(String(e).slice(0, 300)));

/**
 * Espera a que la pantalla esté "lista": sin red pendiente, con `main` a la vista y **sin esqueletos
 * ni textos de carga**. Lo último importa: medir el tiempo hasta que aparece el esqueleto diría que la
 * pantalla va rápida cuando lo que tarda es el contenido.
 */
async function esperarLista(msMax = 30_000) {
  await pagina.waitForLoadState('networkidle', { timeout: msMax }).catch(() => {});
  await pagina.locator('main').first().waitFor({ state: 'visible', timeout: msMax }).catch(() => {});
  const limite = Date.now() + msMax;
  for (;;) {
    const cargando = await pagina.evaluate(() => {
      const conEsqueleto = document.querySelector('.esqueleto, [data-testid^="esqueleto"]') !== null;
      const texto = (document.querySelector('main')?.textContent ?? '').replace(/\s+/g, ' ');
      const enCarga = /Cargando |Mirando |Abriendo |Preparando |Montando /.test(texto);
      return conEsqueleto || enCarga;
    });
    if (!cargando || Date.now() > limite) return;
    await pagina.waitForTimeout(120);
  }
}

/**
 * Lo que este guion puede afirmar de una pantalla sin ver el PNG: el texto de la interfaz y unas
 * cuantas cifras medidas en el DOM.
 */
async function evidenciaDeLaPantalla() {
  return pagina.evaluate(() => {
    const norm = (t) => (t ?? '').replace(/\s+/g, ' ').trim();
    const main = document.querySelector('main');
    const cuerpo = document.body;
    const carril = document.querySelector('.marco-alumno__carril, .carril, .panel__carril');
    return {
      url: location.pathname + location.search + location.hash,
      titulo: document.title,
      h1: norm(document.querySelector('h1')?.textContent),
      texto: norm(main?.textContent).slice(0, 3000),
      vacios: [...document.querySelectorAll('main p, main span, main li')]
        .map((n) => norm(n.textContent))
        .filter((t) =>
          /sin apuntes|todavía no|no hay|no queda|no se pudo|no tiene|0 preguntas|Sin empezar|Sin contestar/i.test(
            t,
          ),
        )
        .slice(0, 14),
      anchoDocumento: cuerpo.scrollWidth,
      altoDocumento: cuerpo.scrollHeight,
      altoCarril: carril === null ? null : Math.round(carril.getBoundingClientRect().height),
      anchoVentana: window.innerWidth,
      desbordes: [...document.querySelectorAll('main *')]
        .filter((n) => n.scrollWidth > n.clientWidth + 2 && n.clientWidth > 0)
        .slice(0, 8)
        .map(
          (n) =>
            `${n.tagName.toLowerCase()}.${String(n.className).slice(0, 40)} (${n.scrollWidth}>${n.clientWidth})`,
        ),
      numeros: (norm(main?.textContent).match(/-?\d+[.,]\d{2,}/g) ?? []).slice(0, 14),
      botones: [...document.querySelectorAll('main button')].map((b) => norm(b.textContent)).slice(0, 40),
      enlaces: [...document.querySelectorAll('main a')]
        .map((a) => norm(a.textContent))
        .slice(0, 40),
    };
  });
}

/** Retrata la pantalla tal como está, a los dos anchos, y deja la fila del informe. */
async function retratar(etiqueta, { ms, notas = [], accion = '' } = {}) {
  numero += 1;
  const id = `${String(numero).padStart(2, '0')}-${etiqueta}`;
  // `notas` puede venir ya calculada o como función: lo segundo hace falta cuando hay que mirar el
  // DOM **después** de haber llegado a la pantalla.
  const lista = typeof notas === 'function' ? await notas() : notas;
  const fila = { id, etiqueta, accion, ms: ms ?? null, notas: [...lista], capturas: [] };
  mkdirSync(SALIDA, { recursive: true });
  for (const { ancho, alto, etiqueta: nombre } of ANCHOS) {
    await pagina.setViewportSize({ width: ancho, height: alto });
    await pagina.waitForTimeout(150);
    const fichero = `${id}-${nombre}`;
    await pagina.screenshot({ path: path.join(SALIDA, `${fichero}.png`), fullPage: true });
    fila.capturas.push(`${fichero}.png`);
    const medida = await evidenciaDeLaPantalla();
    if (nombre === 'escritorio') {
      fila.evidencia = medida;
    } else {
      fila.evidenciaMovil = {
        anchoDocumento: medida.anchoDocumento,
        anchoVentana: medida.anchoVentana,
        desbordes: medida.desbordes,
        altoCarril: medida.altoCarril,
        altoDocumento: medida.altoDocumento,
        numeros: medida.numeros,
      };
    }
  }
  await pagina.setViewportSize({ width: 1280, height: 800 });
  fila.erroresConsola = [...erroresConsola];
  erroresConsola = [];
  filas.push(fila);
  console.log(
    `[${id}] ${fila.ms === null ? '' : `${String(fila.ms)} ms `}${fila.evidencia.h1} — ${fila.evidencia.url}`,
  );
  if (fila.notas.length) console.log(`        notas: ${fila.notas.join(' | ')}`);
  if (fila.erroresConsola.length)
    console.log(`        consola: ${fila.erroresConsola.slice(0, 2).join(' | ')}`);
  return fila;
}

/** Navega, mide y retrata. `notas` es una función: se evalúa **después** de cargar la pantalla. */
async function ir(etiqueta, ruta, opciones = {}) {
  erroresConsola = [];
  await pagina.setViewportSize({ width: 1280, height: 800 });
  const inicio = Date.now();
  await pagina.goto(`${WEB}${ruta}`, { waitUntil: 'domcontentloaded' });
  await esperarLista();
  const ms = Date.now() - inicio;
  const notas = opciones.notas === undefined ? [] : await opciones.notas();
  return retratar(etiqueta, { ms, accion: `GET ${ruta}`, notas });
}

/** Pulsa algo, espera y retrata. */
async function pulsar(etiqueta, localizador, opciones = {}) {
  erroresConsola = [];
  await pagina.setViewportSize({ width: 1280, height: 800 });
  const inicio = Date.now();
  const notas = [];
  try {
    await localizador.first().click({ timeout: 15_000 });
  } catch (error) {
    notas.push(`NO SE PUDO PULSAR: ${String(error).split('\n')[0].slice(0, 160)}`);
  }
  await esperarLista();
  const ms = Date.now() - inicio;
  if (opciones.notas !== undefined) notas.push(...(await opciones.notas()));
  return retratar(etiqueta, { ms, accion: `click ${etiqueta}`, notas });
}

/** El texto visible de un elemento, normalizado. */
async function texto(localizador, msMax = 10_000) {
  try {
    await localizador.first().waitFor({ state: 'visible', timeout: msMax });
    return (await localizador.first().innerText()).replace(/\s+/g, ' ').trim();
  } catch {
    return null;
  }
}

function diag(...partes) {
  return partes.filter((p) => p !== null && p !== undefined && p !== '').join(' · ');
}

/** Un paso que no se ha podido hacer, con su motivo por su nombre. */
async function sinPaso(etiqueta, motivo) {
  numero += 1;
  const id = `${String(numero).padStart(2, '0')}-${etiqueta}`;
  filas.push({
    id,
    etiqueta,
    accion: 'no se pudo hacer',
    notas: [motivo],
    capturas: [],
    evidencia: await evidenciaDeLaPantalla().catch(() => null),
    erroresConsola: [...erroresConsola],
  });
  erroresConsola = [];
  console.log(`[${id}] NO SE PUDO HACER: ${motivo}`);
}

/** Va a una pregunta del test por su número en la hoja de respuestas (es la única forma que hay). */
async function irAPregunta(posicion) {
  const destino = pagina.locator(`[aria-label="Ir a la pregunta ${String(posicion)}"]`);
  try {
    await destino.first().click({ timeout: 4_000 });
    return true;
  } catch {
    await pagina
      .locator('button', { hasText: /^Hoja$/ })
      .first()
      .click({ timeout: 3_000 })
      .catch(() => {});
    await pagina.waitForTimeout(200);
    try {
      await destino.first().click({ timeout: 4_000 });
      return true;
    } catch {
      return false;
    }
  }
}

/** La posición que anuncia la cabecera del test: `Pregunta 3 de 10`. */
async function posicionActual() {
  const t = await texto(pagina.locator('.test-cabecera__progreso'), 4_000);
  const m = t?.match(/Pregunta (\d+) de (\d+)/);
  return m ? { posicion: Number(m[1]), total: Number(m[2]) } : null;
}

/** Lo que dice la hoja de respuestas: por fila, el estado de cada casilla. */
async function leerHoja() {
  return pagina.evaluate(() =>
    [...document.querySelectorAll('ol.hoja li')].map((li) => ({
      posicion: Number(li.querySelector('.hoja__numero')?.textContent?.trim() ?? '0'),
      estados: Object.fromEntries(
        [...li.querySelectorAll('.hoja__casilla')].map((c) => [
          c.textContent.trim().toLowerCase(),
          c.getAttribute('data-estado'),
        ]),
      ),
    })),
  );
}

/** Contesta la pregunta que está a la vista. Devuelve lo que ha pasado, para el informe. */
async function contestarEnCurso({ indice = 0 } = {}) {
  const opciones = pagina.locator('.test-opciones button.test-opcion');
  const cuantas = await opciones.count();
  if (cuantas === 0) {
    const html = await pagina
      .locator('main')
      .first()
      .innerHTML()
      .catch(() => '(sin main)');
    return { nota: 'sin opciones en pantalla', html: html.slice(0, 400) };
  }
  const elegido = Math.min(indice, cuantas - 1);
  const letra = await texto(opciones.nth(elegido).locator('.test-opcion__letra'), 4_000);
  await opciones.nth(elegido).click({ timeout: 8_000 });
  await pagina.waitForTimeout(400);
  return { letra: letra?.toLowerCase() ?? null };
}

/** Contesta `n` preguntas seguidas, moviéndose con la hoja cuando el test no avanza solo. */
async function contestarN(n) {
  const hechas = [];
  for (let i = 1; i <= n; i += 1) {
    const antes = await posicionActual();
    if (antes === null) {
      hechas.push({ posicion: i, nota: 'la cabecera no dice por qué pregunta va' });
      break;
    }
    if (antes.posicion !== i) {
      if (!(await irAPregunta(i))) {
        hechas.push({ posicion: i, nota: 'no se pudo ir desde la hoja' });
        continue;
      }
      await pagina.waitForTimeout(200);
    }
    hechas.push({ posicion: i, ...(await contestarEnCurso({ indice: 0 })) });
  }
  return hechas;
}

// --------------------------------------------------------------------------- el recorrido

try {
  // ---------------------------------------------------------------- 1 · Inicio → Temario → IV.7
  await ir('01-inicio', '/', {
    notas: async () => [
      diag(
        '¿sale «Todavía no hay apuntes escritos de ningún tema»?',
        (await pagina.locator('text=Todavía no hay apuntes escritos').count()) > 0 ? 'SÍ' : 'no',
      ),
      diag('temas con apuntes en Inicio:', String(await pagina.locator('main .lista-temas a').count())),
      diag('tests recientes en Inicio:', String(await pagina.locator('main .lista-tests a').count())),
      diag('botón de test en curso:', String(await pagina.locator('main a[href^="/test/"]').count())),
    ],
  });

  await ir('02-temario', '/temario', {
    notas: async () => [
      diag('temas listados:', String(await pagina.locator('main a[href^="/temario/"]').count())),
    ],
  });

  await ir('03-tema-IV7', '/temario/IV.7', {
    notas: async () => [
      diag('apartados en el índice:', String(await pagina.locator('nav.apuntes__indice a').count())),
      diag('apartados en el cuerpo:', String(await pagina.locator('section.apartado').count())),
      diag('estado del tema:', await texto(pagina.locator('.tema__estado'))),
      diag('notas al margen:', String(await pagina.locator('aside.nota-margen').count())),
      diag('botones «Esto está mal»:', String(await pagina.locator('button', { hasText: 'Esto está mal' }).count())),
      diag(
        '¿«Practicar este apartado»?',
        (await pagina.locator('text=/Practicar este apartado/i').count()) > 0 ? 'sí' : 'NO',
      ),
      diag(
        '¿buscador dentro del tema?',
        (await pagina.locator('main input[type="search"]').count()) > 0 ? 'sí' : 'NO',
      ),
    ],
  });

  const apartados = pagina.locator('nav.apuntes__indice a');
  const cuantosApartados = await apartados.count();
  await pulsar('04-IV7-apartado-1', apartados.nth(0), {
    notas: async () => [diag('apartado 1 de', String(cuantosApartados)), diag('ancla:', new URL(pagina.url()).hash)],
  });
  await pulsar('05-IV7-apartado-2', apartados.nth(1), {
    notas: async () => [diag('ancla:', new URL(pagina.url()).hash)],
  });

  // Practicar: la pestaña «Preguntas» del tema (es la salida que existe).
  await pulsar(
    '06-IV7-practicar',
    pagina.locator('nav.pestanas a', { hasText: 'Preguntas' }),
    {
      notas: async () => [
        'El §3 pide un botón «Practicar este apartado»: lo que hay es la pestaña «Preguntas» del tema',
        diag('URL:', new URL(pagina.url()).pathname + new URL(pagina.url()).search),
      ],
    },
  );

  await pagina.locator('#cuenta-10').check({ timeout: 10_000 }).catch(() => {});
  await pagina.locator('#correccion-immediate').check({ timeout: 10_000 }).catch(() => {});
  await retratar('07-test-configurado', {
    ms: null,
    accion: 'marcar 10 preguntas · corrección al responder',
    notas: [diag('resumen:', await texto(pagina.locator('.resumen-test')))],
  });

  // ---------------------------------------------------------------- el test de 10
  erroresConsola = [];
  const inicioTest = Date.now();
  await pagina.locator('button', { hasText: 'Empezar el test' }).first().click({ timeout: 15_000 });
  await pagina.waitForURL(/\/test\//, { timeout: 30_000 }).catch(() => {});
  await esperarLista();
  const msArranque = Date.now() - inicioTest;
  const urlTest = pagina.url();

  const fallosBuscados = 3;
  const respuestas = [];
  let sinOpciones = null;
  // 1) Se contestan las diez con la primera opción. El test **avanza solo**, así que no hace falta
  //    tocar la hoja: lo que se comprueba es justo eso.
  let avanzoSolo = true;
  for (let posicion = 1; posicion <= 10; posicion += 1) {
    const antes = await posicionActual();
    if (antes === null) {
      respuestas.push({ posicion, nota: 'la cabecera no dice por qué pregunta va' });
      break;
    }
    if (antes.posicion !== posicion) {
      avanzoSolo = false;
      const fui = await irAPregunta(posicion);
      if (!fui) {
        respuestas.push({ posicion, nota: 'no se pudo ir a esta pregunta desde la hoja' });
        continue;
      }
      await pagina.waitForTimeout(200);
    }
    const resultado = await contestarEnCurso({ indice: 0 });
    if (resultado.html !== undefined) sinOpciones = resultado;
    respuestas.push({ posicion, ...resultado });
  }
  const hojaTrasContestar = await leerHoja();
  // 2) Y ahora se fallan tres a propósito: la hoja dice qué letra era la buena, así que se vuelve a
  //    esas filas y se marca otra. Se hace **con la hoja**, que es lo que hay para moverse.
  const seVanAFallar = [];
  for (const fila of hojaTrasContestar) {
    if (seVanAFallar.length >= fallosBuscados) break;
    if (Object.values(fila.estados).includes('fallada')) continue;
    seVanAFallar.push(fila.posicion);
  }
  const falladas = [];
  for (const posicion of seVanAFallar) {
    const fui = await irAPregunta(posicion);
    if (!fui) {
      falladas.push({ posicion, nota: 'no se pudo volver a la fila' });
      continue;
    }
    await pagina.waitForTimeout(250);
    const fila = (await leerHoja()).find((f) => f.posicion === posicion);
    const correcta = Object.entries(fila?.estados ?? {}).find(([, e]) => e === 'correcta')?.[0] ?? null;
    const letras = await pagina
      .locator('.test-opciones button.test-opcion .test-opcion__letra')
      .allInnerTexts();
    const indice = letras.findIndex((l) => l.trim().toLowerCase() !== correcta);
    const resultado = indice >= 0 ? await contestarEnCurso({ indice }) : { nota: 'no hay otra letra' };
    falladas.push({ posicion, correcta, ...resultado });
  }
  await pagina.setViewportSize({ width: 1280, height: 800 });
  await pagina.waitForTimeout(250);
  const hojaFinal = await leerHoja();
  await retratar('08-test-contestado', {
    ms: Date.now() - inicioTest,
    accion: 'contestar 10 (fallando 3 a propósito)',
    notas: [
      diag('arranque del test:', String(msArranque), 'ms'),
      diag('URL del test:', new URL(urlTest).pathname),
      diag('¿el test avanza solo al contestar?', avanzoSolo ? 'sí' : 'no, hay que moverse con la hoja'),
      diag('respuestas:', JSON.stringify(respuestas)),
      diag('filas que se han fallado a propósito:', JSON.stringify(falladas)),
      diag(
        'la hoja al final:',
        JSON.stringify(
          hojaFinal.map((f) => `${String(f.posicion)}:${Object.entries(f.estados).filter(([, e]) => e !== 'vacia').map(([l, e]) => `${l}=${String(e)}`).join(',')}`),
        ),
      ),
      diag(
        '¿cuántas falladas?',
        String(hojaFinal.filter((f) => Object.values(f.estados).includes('fallada')).length),
      ),
      ...(sinOpciones === null ? [] : [diag('SIN OPCIONES, HTML:', sinOpciones.html)]),
    ],
  });

  const inicioResultado = Date.now();
  await pagina.locator('button', { hasText: /^Terminar/ }).first().click({ timeout: 15_000 });
  await pagina.waitForURL(/\/resultado\//, { timeout: 30_000 }).catch(() => {});
  await esperarLista();
  const msResultado = Date.now() - inicioResultado;
  await retratar('09-resultado', {
    ms: msResultado,
    accion: 'pulsar Terminar',
    notas: async () => [
      diag('URL:', new URL(pagina.url()).pathname),
      diag('casillas de la hoja:', String(await pagina.locator('ol.hoja li').count())),
      diag('preguntas listadas:', String(await pagina.locator('main .resultado__preguntas li').count())),
      diag('enlaces «Ver en apuntes»:', String(await pagina.locator('main a', { hasText: 'Ver en apuntes' }).count())),
      diag('números con dos decimales:', JSON.stringify((await evidenciaDeLaPantalla()).numeros)),
    ],
  });

  // «Ver en apuntes» de una fallada
  const verEnApuntes = pagina.locator('main a', { hasText: 'Ver en apuntes' });
  const cuantosVerEnApuntes = await verEnApuntes.count();
  if (cuantosVerEnApuntes > 0) {
    await pulsar('10-ver-en-apuntes', verEnApuntes.nth(0), {
      notas: async () => {
        const estado = await pagina.evaluate(() => {
          const objetivo = location.hash === '' ? null : document.querySelector(location.hash);
          const caja = objetivo === null ? null : objetivo.getBoundingClientRect();
          return {
            scrollY: Math.round(window.scrollY),
            hash: location.hash,
            apartadoALaVista: caja === null ? null : caja.top > -50 && caja.top < window.innerHeight,
          };
        });
        return [diag('¿el apartado queda a la vista?', JSON.stringify(estado))];
      },
    });
  } else {
    await sinPaso('10-ver-en-apuntes', 'el resultado no ofrece ningún «Ver en apuntes»');
  }

  // ---------------------------------------------------------------- Fallos → Repasar
  await ir('11-fallos', '/fallos', {
    notas: async () => {
      const t = await texto(pagina.locator('main'));
      return [diag('cabecera:', t?.slice(0, 260))];
    },
  });
  const repasar = pagina
    .locator('main button, main a')
    .filter({ hasText: /Test con mis fallos|Solo los de/ });
  if ((await repasar.count()) > 0) {
    await pulsar('12-fallos-repasar', repasar.nth(0), {
      notas: async () => [
        diag('URL:', new URL(pagina.url()).pathname),
        diag('cabecera del test:', await texto(pagina.locator('.test-cabecera__progreso, .pagina__titulo'))),
      ],
    });
  } else {
    await sinPaso('12-fallos-repasar', 'no hay ningún botón de repaso en Fallos');
  }

  // ---------------------------------------------------------------- 2 · Temario → I.1
  await ir('13-tema-I1', '/temario/I.1', {
    notas: async () => [
      diag('apartados en el índice:', String(await pagina.locator('nav.apuntes__indice a').count())),
      diag('apartados en el cuerpo:', String(await pagina.locator('section.apartado').count())),
      diag(
        '¿buscador dentro del tema?',
        (await pagina.locator('main input[type="search"]').count()) > 0 ? 'sí' : 'NO',
      ),
      diag('¿modo repaso?', (await pagina.locator('text=/modo repaso/i').count()) > 0 ? 'sí' : 'NO'),
      diag('alto de la página:', String((await evidenciaDeLaPantalla()).altoDocumento), 'px'),
      diag('tiempo hasta lista:', 'medido arriba'),
    ],
  });
  const indiceI1 = pagina.locator('nav.apuntes__indice a');
  const cuantosI1 = await indiceI1.count();
  await pulsar('14-I1-indice-ultimo', indiceI1.nth(Math.max(0, cuantosI1 - 1)), {
    notas: async () => [diag('apartados del índice:', String(cuantosI1)), diag('ancla:', new URL(pagina.url()).hash)],
  });

  // ---------------------------------------------------------------- 3 · Simulacro
  await ir('15-simulacros', '/simulacros', {
    notas: async () => [
      diag('¿variante completa?', (await pagina.locator('#variante-full').count()) > 0 ? 'sí' : 'NO'),
      diag('¿supuesto III?', (await pagina.locator('#supuesto-III').count()) > 0 ? 'sí' : 'NO'),
      diag('¿supuesto IV?', (await pagina.locator('#supuesto-IV').count()) > 0 ? 'sí' : 'NO'),
    ],
  });
  await pagina.locator('#variante-full').check({ timeout: 10_000 }).catch(() => {});
  await pagina.locator('#supuesto-III').check({ timeout: 10_000 }).catch(() => {});
  await retratar('16-simulacro-supuesto-III', {
    ms: null,
    accion: 'elegir simulacro completo y supuesto III',
    notas: [
      diag('aviso:', (await texto(pagina.locator('.resultado__aviso')))?.slice(0, 260)),
      diag('partes:', await texto(pagina.locator('ul.simulacro__partes'))),
    ],
  });
  erroresConsola = [];
  const inicioSimulacro = Date.now();
  await pagina.locator('button', { hasText: 'Empezar el simulacro' }).first().click({ timeout: 15_000 });
  const cambioUrl = await pagina
    .waitForURL(/\/test\//, { timeout: 45_000 })
    .then(() => true)
    .catch(() => false);
  await esperarLista(45_000);
  await retratar('17-simulacro-empezado', {
    ms: Date.now() - inicioSimulacro,
    accion: 'empezar el simulacro',
    notas: async () => [
      diag('¿ha empezado?', cambioUrl ? 'sí' : 'NO'),
      ...(cambioUrl
        ? [
            diag('cabecera:', await texto(pagina.locator('.test-cabecera__progreso'))),
            diag(
              '¿enseña el reloj?',
              (await pagina.locator('main time, .test-cabecera__reloj').count()) > 0 ? 'sí' : 'NO',
            ),
            diag(
              '¿hay forma de abandonar?',
              (await pagina.locator('main button, main a').filter({ hasText: /abandon/i }).count()) > 0
                ? 'sí'
                : 'NO',
            ),
          ]
        : [diag('lo que dice la pantalla:', (await texto(pagina.locator('main')))?.slice(0, 400))]),
    ],
  });
  if (cambioUrl) {
    const cinco = await contestarN(5);
    await retratar('18-simulacro-5-contestadas', {
      ms: null,
      accion: 'contestar 5 del simulacro',
      notas: [
        diag('progreso:', await texto(pagina.locator('.test-cabecera__progreso'))),
        diag('respuestas:', JSON.stringify(cinco)),
        diag('hoja:', JSON.stringify((await leerHoja()).slice(0, 5))),
      ],
    });
    const inicioAbandono = Date.now();
    await pagina.goto(`${WEB}/simulacros`, { waitUntil: 'domcontentloaded' });
    await esperarLista();
    await retratar('19-simulacro-abandonado', {
      ms: Date.now() - inicioAbandono,
      accion: 'salir del simulacro sin terminar (no hay botón de abandonar)',
      notas: [
        'El §3 pide «abandonar»: la zona del alumno no ofrece esa acción, así que se sale por la dirección',
        diag('la sesión sigue en curso:', await texto(pagina.locator('main'))),
      ],
    });
  } else {
    await sinPaso('18-simulacro-5-contestadas', 'el simulacro no ha empezado: no hay preguntas que contestar');
    await sinPaso('19-simulacro-abandonado', 'no se ha podido abandonar lo que no ha empezado');
  }

  // ---------------------------------------------------------------- 4 · Examen oficial
  await ir('20-examenes', '/examenes', {
    notas: async () => [
      diag('exámenes listados:', String(await pagina.locator('main .examenes li').count())),
      diag(
        'sin fecha publicada:',
        String(await pagina.locator('text=Sin fecha publicada').count()),
      ),
      diag(
        '«no se puede hacer»:',
        String(await pagina.locator('text=/no se puede hacer/i').count()),
      ),
    ],
  });
  const filasExamen = pagina.locator('main .examenes li');
  const cuantasFilas = await filasExamen.count();
  let indiceInap = -1;
  for (let i = 0; i < cuantasFilas; i += 1) {
    const t = await texto(filasExamen.nth(i));
    if (t !== null && /INAP/.test(t) && /2025/.test(t) && /modelo A/.test(t)) {
      indiceInap = i;
      break;
    }
  }
  if (indiceInap >= 0) {
    const fila = filasExamen.nth(indiceInap);
    await retratar('21-examen-inap-2025-A', {
      ms: null,
      accion: 'localizar el INAP 2025 modelo A',
      notas: [diag('la fila dice:', (await texto(fila))?.slice(0, 320))],
    });
    const boton = fila.locator('button, a').filter({ hasText: /Hacer este examen|Hacerlo/ });
    if ((await boton.count()) > 0) {
      erroresConsola = [];
      const inicioExamen = Date.now();
      await boton.first().click({ timeout: 15_000 });
      const empezo = await pagina
        .waitForURL(/\/test\//, { timeout: 45_000 })
        .then(() => true)
        .catch(() => false);
      await esperarLista(45_000);
      await retratar('22-examen-inap-empezado', {
        ms: Date.now() - inicioExamen,
        accion: 'empezar el examen oficial',
        notas: async () => [
          diag('¿ha empezado?', empezo ? 'sí' : 'NO'),
          diag('cabecera:', await texto(pagina.locator('.test-cabecera__progreso'))),
          diag('título:', await texto(pagina.locator('.test-cabecera__titulo'))),
          ...(empezo
            ? []
            : [diag('lo que dice la pantalla:', (await texto(pagina.locator('main')))?.slice(0, 400))]),
        ],
      });
      if (empezo) {
        const tres = await contestarN(3);
        await retratar('23-examen-3-contestadas', {
          ms: null,
          accion: 'contestar 3 del examen',
          notas: [
            diag('progreso:', await texto(pagina.locator('.test-cabecera__progreso'))),
            diag('respuestas:', JSON.stringify(tres)),
          ],
        });
        erroresConsola = [];
        const inicioTerminar = Date.now();
        await pagina.locator('button', { hasText: /^Terminar/ }).first().click({ timeout: 15_000 });
        const termino = await pagina
          .waitForURL(/\/resultado\//, { timeout: 60_000 })
          .then(() => true)
          .catch(() => false);
        await esperarLista(60_000);
        await retratar('24-examen-terminado', {
          ms: Date.now() - inicioTerminar,
          accion: 'terminar el examen oficial',
          notas: async () => [
            diag('¿ha ido al resultado?', termino ? 'sí' : 'NO'),
            diag('URL:', new URL(pagina.url()).pathname),
            diag('cabecera:', (await texto(pagina.locator('main')))?.slice(0, 300)),
          ],
        });
      } else {
        await sinPaso('23-examen-3-contestadas', 'el examen no ha empezado');
        await sinPaso('24-examen-terminado', 'el examen no ha empezado');
      }
    } else {
      await sinPaso('22-examen-inap-empezado', 'el INAP 2025 modelo A no ofrece botón para hacerlo');
    }
  } else {
    await sinPaso('21-examen-inap-2025-A', 'no aparece ningún examen «INAP 2025 modelo A» en la lista');
  }

  // ---------------------------------------------------------------- 5 · Progreso
  await ir('25-progreso', '/progreso', {
    notas: async () => [
      diag('cabecera:', (await texto(pagina.locator('main')))?.slice(0, 220)),
      diag('temas con cifra:', String(await pagina.locator('main a[href^="/temario/"]').count())),
    ],
  });

  // ---------------------------------------------------------------- 6 · Panel
  await ir('26-panel-incidencias', '/admin/incidencias', {
    notas: async () => [
      diag('grupos por banco:', String(await pagina.locator('main li, main tr').count())),
      diag(
        'botones «Ver lo que tiene dentro»:',
        String(await pagina.locator('button', { hasText: 'Ver lo que tiene dentro' }).count()),
      ),
      diag('cabecera:', (await texto(pagina.locator('main')))?.slice(0, 220)),
    ],
  });
  const verDentro = pagina.locator('button', { hasText: 'Ver lo que tiene dentro' });
  if ((await verDentro.count()) > 0) {
    await pulsar('27-panel-banco-abierto', verDentro.nth(0), {
      notas: async () => [
        diag(
          'enlaces «Ver la pregunta en el banco»:',
          String(await pagina.locator('main a', { hasText: 'Ver la pregunta en el banco' }).count()),
        ),
      ],
    });
  } else {
    await sinPaso('27-panel-banco-abierto', 'no hay ningún botón «Ver lo que tiene dentro»');
  }
  const verPregunta = pagina.locator('main a', { hasText: 'Ver la pregunta en el banco' });
  if ((await verPregunta.count()) > 0) {
    await pulsar('28-panel-ficha-pregunta', verPregunta.nth(0), {
      notas: async () => [
        diag('URL:', new URL(pagina.url()).pathname + new URL(pagina.url()).search),
        diag('¿es la ficha?', (await pagina.locator('text=Ficha de la pregunta').count()) > 0 ? 'sí' : 'no'),
      ],
    });
    const radios = pagina.locator('input[name="respuesta-correcta"]');
    const cuantosRadios = await radios.count();
    await retratar('29-panel-ficha-acciones', {
      ms: null,
      accion: 'mirar las acciones de la ficha',
      notas: async () => [
        diag('opciones marcables:', String(cuantosRadios)),
        diag('botones:', JSON.stringify((await pagina.locator('main button').allInnerTexts()).slice(0, 12))),
        diag(
          '¿protegida?',
          (await pagina.locator('text=/oficial|protegid|no se puede/i').count()) > 0 ? 'sí' : 'no',
        ),
      ],
    });
    if (cuantosRadios > 0) {
      await radios.nth(0).check({ timeout: 10_000 }).catch(() => {});
      await pulsar('30-panel-marcar-correcta', pagina.locator('[aria-label="Guardar la respuesta correcta"]'), {
        notas: async () => [
          'se marca sobre la COPIA de la base, nunca sobre la real',
          diag('lo que dice después:', (await texto(pagina.locator('main')))?.slice(0, 300)),
        ],
      });
    } else {
      await sinPaso('30-panel-marcar-correcta', 'la ficha no ofrece marcar la respuesta correcta (banco protegido)');
    }
  } else {
    await sinPaso('28-panel-ficha-pregunta', 'no hay enlaces «Ver la pregunta en el banco» en la bandeja');
    await sinPaso('29-panel-ficha-acciones', 'no se ha abierto ninguna ficha');
    await sinPaso('30-panel-marcar-correcta', 'no se ha abierto ninguna ficha');
  }

  await ir('31-panel-apuntes', '/admin/apuntes', {
    notas: async () => [
      diag('filas de la tabla:', String(await pagina.locator('main tbody tr').count())),
      diag('cabecera:', (await texto(pagina.locator('main')))?.slice(0, 260)),
    ],
  });
  await ir('32-panel-apuntes-IV7', '/admin/apuntes/IV.7', {
    notas: async () => [
      diag('botones:', JSON.stringify((await pagina.locator('main button').allInnerTexts()).slice(0, 10))),
      diag('cabecera:', (await texto(pagina.locator('main')))?.slice(0, 260)),
    ],
  });
} catch (error) {
  console.error('EL RECORRIDO SE HA INTERRUMPIDO:', error);
  filas.push({
    id: 'interrupcion',
    error: String(error),
    evidencia: await evidenciaDeLaPantalla().catch(() => null),
  });
} finally {
  mkdirSync(SALIDA, { recursive: true });
  writeFileSync(path.join(SALIDA, 'filas.json'), JSON.stringify(filas, null, 2), 'utf8');
  await navegador.close();
  console.log(`\n${filas.length} pasos · filas.json escrito en ${SALIDA}`);
}
