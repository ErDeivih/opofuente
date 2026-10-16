/**
 * «Ver en apuntes», medido de punta a punta (F35).
 *
 * Monta un test terminado de IV.7 con las preguntas **falladas** —salen del banco real, que es lo que
 * hace la aplicación— y deja sus dos apartados apuntando a dos apartados reales del tema: uno del
 * primer capítulo (`IV.7.1`) y otro del segundo (`IV.7.2`). Después abre el Resultado, pulsa cada
 * «Ver en apuntes» y mide la dirección a la que lleva, el `scrollY` al llegar y si el apartado queda
 * a la vista.
 *
 * Por qué se reescribe el anclaje: el resultado resuelve «Ver en apuntes» de la comprobación del
 * motor (`question_note_anchors`), que es del propietario y apunta a los apartados que le tocaron. Lo
 * que se mide aquí es el **comportamiento del enlace**, y para eso hacen falta dos apartados
 * concretos —uno del primer capítulo y otro del segundo—. Se reescribe sobre la **copia de trabajo**
 * (`f35-datos`), no sobre la base real.
 *
 * Uso: node sonda-ver-en-apuntes.mjs [--salida <dir>] [--json <fichero>]
 */

import { mkdirSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import path from 'node:path';

const require = createRequire('F:/temp-opofuente/opofuente-lectura/apps/web/package.json');
const { chromium } = require('@playwright/test');
const { DatabaseSync } = require('node:sqlite');

const API = 'http://127.0.0.1:8765';
const BASE = 'http://127.0.0.1:4173';
const ORIGEN = 'http://127.0.0.1:4173';
const COPIA = 'F:/temp-opofuente/f35-datos/opofuente.sqlite3';
/** Los dos apartados reales que se miden: uno de cada capítulo de IV.7. */
const ANCLAS = ['osi-capas', 'puertos'];

function argumento(nombre) {
  const indice = process.argv.indexOf(nombre);
  return indice < 0 ? null : (process.argv[indice + 1] ?? null);
}

const SALIDA = argumento('--salida');
const CABECERAS = { 'Content-Type': 'application/json', Origin: ORIGEN };

async function leer(respuesta) {
  if (!respuesta.ok) {
    throw new Error(`la API respondio ${respuesta.status}: ${await respuesta.text()}`);
  }
  return respuesta.json();
}

/** Los apartados reales de IV.7 por su ancla: `{anchor: {section_id, node_id, epigraph_code}}`. */
function apartadosReales(anclas) {
  const base = new DatabaseSync(COPIA, { readOnly: true });
  try {
    const salida = {};
    for (const ancla of anclas) {
      const fila = base
        .prepare(
          'SELECT s.id AS section_id, s.curriculum_node_id AS node_id, s.anchor, ' +
            's.epigraph_code, s.title ' +
            'FROM topic_note_sections s JOIN curriculum_nodes n ON n.id = s.curriculum_node_id ' +
            "WHERE n.path = 'IV.7' AND s.anchor = ?",
        )
        .get(ancla);
      if (fila === undefined) throw new Error(`IV.7 no tiene el apartado ${ancla}`);
      salida[ancla] = fila;
    }
    return salida;
  } finally {
    base.close();
  }
}

/** Apunta el anclaje de una pregunta del intento a un apartado concreto (sobre la copia). */
function reanclar(pregunta, apartado) {
  const base = new DatabaseSync(COPIA);
  try {
    const cambiadas = base
      .prepare(
        'UPDATE question_note_anchors SET curriculum_node_id = ?, section_id = ?, anchor = ?, ' +
          "result = 'covered', key_status = 'active' WHERE question_version_id = ?",
      )
      .run(apartado.node_id, apartado.section_id, apartado.anchor, pregunta);
    return Number(cambiadas.changes);
  } finally {
    base.close();
  }
}

async function sembrar() {
  const oposiciones = await leer(await fetch(`${API}/api/v1/oppositions`));
  const activa = oposiciones.find((oposicion) => oposicion.active);
  if (activa?.active_convocation == null) throw new Error('no hay oposicion activa');

  const apartados = apartadosReales(ANCLAS);

  const sesion = await leer(
    await fetch(`${API}/api/v1/student/tests`, {
      method: 'POST',
      headers: CABECERAS,
      body: JSON.stringify({
        nodes: ['IV.7'],
        count: ANCLAS.length,
        filter: 'all',
        feedback: 'immediate',
      }),
    }),
  );
  await leer(
    await fetch(`${API}/api/v1/student/sessions/${sesion.id}/start`, {
      method: 'POST',
      headers: CABECERAS,
    }),
  );

  const base = new DatabaseSync(COPIA, { readOnly: true });
  let preguntas;
  try {
    preguntas = base
      .prepare(
        'SELECT position, question_version_id, correct_option_keys_json FROM session_questions ' +
          'WHERE session_id = ? ORDER BY position',
      )
      .all(sesion.id);
  } finally {
    base.close();
  }

  const reancladas = [];
  for (const [indice, pregunta] of preguntas.entries()) {
    const ancla = ANCLAS[indice % ANCLAS.length];
    reancladas.push({ position: pregunta.position, ancla, filas: reanclar(pregunta.question_version_id, apartados[ancla]) });
  }

  // Se contesta **mal** a propósito: «Ver en apuntes» solo sale bajo las falladas.
  for (const pregunta of preguntas) {
    const correcta = JSON.parse(pregunta.correct_option_keys_json ?? '[]');
    const elegida = correcta.includes('a') ? ['b'] : ['a'];
    await leer(
      await fetch(`${API}/api/v1/student/sessions/${sesion.id}/answers`, {
        method: 'POST',
        headers: CABECERAS,
        body: JSON.stringify({
          position: pregunta.position,
          chosen: elegida,
          elapsed_ms: 1500,
        }),
      }),
    );
  }
  await leer(
    await fetch(`${API}/api/v1/student/sessions/${sesion.id}/finish`, {
      method: 'POST',
      headers: CABECERAS,
    }),
  );
  return { sesion: sesion.id, reancladas, apartados };
}

const sembrado = await sembrar();
const navegador = await chromium.launch();
const informe = [];
try {
  for (const { ancho, alto, etiqueta } of [
    { ancho: 1280, alto: 800, etiqueta: 'escritorio' },
    { ancho: 390, alto: 844, etiqueta: 'movil' },
  ]) {
    const contexto = await navegador.newContext({ viewport: { width: ancho, height: alto } });
    const page = await contexto.newPage();
    const errores = [];
    page.on('console', (mensaje) => {
      if (mensaje.type() === 'error') errores.push(mensaje.text());
    });
    page.on('pageerror', (error) => errores.push(String(error)));

    await page.goto(`${BASE}/resultado/${sembrado.sesion}`, { waitUntil: 'networkidle' });
    if (SALIDA) {
      mkdirSync(SALIDA, { recursive: true });
      await page.screenshot({
        path: path.join(SALIDA, `resultado-antes-de-pulsar-${etiqueta}.png`),
        fullPage: false,
      });
    }

    const enlaces = page.getByRole('link', { name: /ver en apuntes/i });
    const cuantos = await enlaces.count();
    for (let indice = 0; indice < cuantos; indice += 1) {
      const ancla = ANCLAS[indice % ANCLAS.length];
      const href = await enlaces.nth(indice).getAttribute('href');
      await enlaces.nth(indice).click();
      await page.waitForTimeout(3500);
      const medido = await page.evaluate((buscado) => {
        const apartado = document.getElementById(buscado);
        const rect = apartado === null ? null : apartado.getBoundingClientRect();
        return {
          scrollY: Math.round(window.scrollY),
          encontradoEnLaPagina: apartado !== null,
          offsetTop: rect === null ? null : Math.round(rect.top + window.scrollY),
          topEnVentana: rect === null ? null : Math.round(rect.top),
          aLaVista: rect !== null && rect.top >= -8 && rect.top < window.innerHeight,
          altoDocumento: document.documentElement.scrollHeight,
        };
      }, `apartado-${ancla}`);
      informe.push({
        ancho,
        etiqueta,
        pregunta: indice + 1,
        ancla,
        capituloDelAncla: sembrado.apartados[ancla].epigraph_code,
        hrefDelEnlace: href,
        urlTrasPulsar: page.url(),
        ...medido,
        errores: [...errores],
      });
      if (SALIDA) {
        await page.screenshot({
          path: path.join(SALIDA, `ver-en-apuntes-${ancla}-${etiqueta}.png`),
          fullPage: false,
        });
      }
      await page.goto(`${BASE}/resultado/${sembrado.sesion}`, { waitUntil: 'networkidle' });
    }
    await contexto.close();
  }
} finally {
  await navegador.close();
}

const destino = argumento('--json');
if (destino) writeFileSync(destino, JSON.stringify({ sembrado, informe }, null, 2));
console.log(JSON.stringify({ sesion: sembrado.sesion, reancladas: sembrado.reancladas, informe }, null, 2));
