/**
 * Capturas de todas las pantallas, con su informe (F0 del rediseño).
 *
 * Para qué sirve: quien construye la interfaz tiene que **verla**. Este guion recorre cada ruta de la
 * aplicación a dos anchos (escritorio 1280×800 y móvil 390×844), guarda el PNG en
 * `artifacts/screens/` y escribe `artifacts/screens/report.md` con lo que ha visto en cada una: lo que
 * tarda en quedar lista, los errores de consola, las violaciones de accesibilidad que detecta axe y las
 * **palabras prohibidas** de la zona del alumno (`tests/palabrasProhibidas.ts`).
 *
 * No es una prueba de las puertas: es una herramienta. Las puertas corren `npm run e2e`, que solo mira
 * `tests/e2e`; esto vive en `tests/screens` y se lanza a mano con `npm run screens` (o se pide desde el
 * informe de una entrega).
 *
 * En F0 las palabras prohibidas se **informan**, no bloquean: primero hay que ver cuántas salen.
 *
 * El **test en curso** necesita una sesión de verdad para poder retratarse: esta herramienta la monta
 * por la API del alumno (un conjunto, sus preguntas, su plantilla activa y su tema) antes de entrar.
 * No se inventa la pantalla con datos falsos: si la API no está, la captura sale con su estado y se
 * dice en el informe.
 */

import { mkdirSync } from 'node:fs';
import path from 'node:path';

import AxeBuilder from '@axe-core/playwright';
import { expect, test, type Page } from '@playwright/test';

import { revisarPantalla } from '../palabrasProhibidas';
import { escribirInforme, guardarFila, nombreDeFichero } from './informe';

const SALIDA = path.resolve(process.cwd(), '..', '..', 'artifacts', 'screens');

/** Dónde escucha la API local en esta herramienta (la misma dirección que usa la web). */
const API = process.env.OPOFUENTE_API_URL ?? 'http://127.0.0.1:8765';

/** El origen con el que se firman las escrituras, como en el navegador. */
const ORIGEN = 'http://127.0.0.1:4173';

// El informe se escribe **después** de la última captura de este proceso. Si una captura se pasa de
// tiempo, Playwright reinicia el proceso y este `afterAll` vuelve a correr: cada fila ya está en
// disco, así que el informe sale completo igualmente.
test.afterAll(() => {
  escribirInforme();
});

/** Las rutas que se visitan, con el nombre con el que se guarda cada captura. */
const RUTAS: readonly { ruta: string; nombre: string }[] = [
  { ruta: '/', nombre: 'inicio' },
  { ruta: '/programa', nombre: 'programa' },
  { ruta: '/estudiar', nombre: 'estudiar' },
  { ruta: '/preguntas', nombre: 'preguntas' },
  { ruta: '/biblioteca', nombre: 'biblioteca' },
  { ruta: '/bandeja', nombre: 'bandeja' },
  { ruta: '/revision', nombre: 'revision' },
  { ruta: '/cambios', nombre: 'cambios' },
  { ruta: '/errores', nombre: 'errores' },
  { ruta: '/buscar?q=constitucion', nombre: 'buscar' },
  { ruta: '/ajustes', nombre: 'ajustes' },
  { ruta: '/admin/ui', nombre: 'admin-ui' },
];

const ANCHOS: readonly { ancho: number; alto: number; etiqueta: string }[] = [
  { ancho: 1280, alto: 800, etiqueta: 'escritorio' },
  { ancho: 390, alto: 844, etiqueta: 'movil' },
];

/** Visita una ruta, la retrata y guarda su fila del informe.
 *
 * `fichero` es el nombre con el que se guarda el PNG: para una ruta con identificador dentro
 * (`/test/<uuid>`) no se puede usar la ruta, o cada captura tendría un nombre distinto y el informe
 * dejaría de poder compararse con el de ayer.
 */
async function retratar(
  page: Page,
  ruta: string,
  fichero: string,
  ancho: number,
  alto: number,
  etiqueta: string,
): Promise<void> {
  const errores: string[] = [];
  page.on('console', (mensaje) => {
    if (mensaje.type() === 'error') {
      errores.push(mensaje.text());
    }
  });
  page.on('pageerror', (error) => errores.push(String(error)));

  await page.setViewportSize({ width: ancho, height: alto });
  const inicio = Date.now();
  await page.goto(ruta, { waitUntil: 'networkidle' });
  const ms = Date.now() - inicio;

  await expect(page.locator('main')).toBeVisible();
  mkdirSync(SALIDA, { recursive: true });
  const nombreFichero = nombreDeFichero(fichero, etiqueta);
  await page.screenshot({
    path: path.join(SALIDA, `${nombreFichero}.png`),
    fullPage: true,
  });

  const analisis = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
    .analyze();
  // Dos textos, porque son dos comprobaciones: el de la **interfaz** (todo menos lo que va dentro
  // de un contenedor `data-contenido`: enunciados, opciones, apuntes, títulos de tema) y el de
  // **toda** la pantalla. La jerga solo se busca en el primero; las rutas y los bancos, en los dos.
  const { interfaz, todo } = await page.evaluate(() => {
    const copia = document.body.cloneNode(true) as HTMLElement;
    for (const nodo of Array.from(copia.querySelectorAll('[data-contenido]'))) {
      nodo.remove();
    }
    return {
      interfaz: copia.innerText || copia.textContent || '',
      todo: document.body.innerText,
    };
  });

  guardarFila({
    ruta,
    ancho: `${ancho}×${alto}`,
    ms,
    errores,
    violaciones: analisis.violations.map((violacion) => violacion.id),
    prohibidas: revisarPantalla(interfaz, todo),
    fichero: nombreFichero,
  });
}

for (const { ruta, nombre } of RUTAS) {
  for (const { ancho, alto, etiqueta } of ANCHOS) {
    test(`${nombre} a ${ancho} px`, async ({ page }) => {
      await retratar(page, ruta, ruta, ancho, alto, etiqueta);
    });
  }
}

/**
 * El test en curso, con datos de verdad.
 *
 * Se monta por la API del alumno —la misma que usa la pantalla— porque una captura de esta pantalla
 * sin sesión no enseña nada: es la hoja de respuestas lo que hay que ver. Si algo falla, la captura
 * se hace igual (con el estado de error de la pantalla) y el fallo se ve en el informe.
 */
for (const { ancho, alto, etiqueta } of ANCHOS) {
  test(`test-en-curso a ${ancho} px`, async ({ page }) => {
    const sesion = await montarTestDeAlumno();
    await retratar(page, `/test/${sesion}`, '/test-en-curso', ancho, alto, etiqueta);
  });
}

/** Monta un test de tres preguntas de un tema y lo deja empezado: devuelve su identificador. */
async function montarTestDeAlumno(): Promise<string> {
  const cabeceras = { 'Content-Type': 'application/json', Origin: ORIGEN };
  const leer = async <T>(respuesta: Response): Promise<T> => {
    if (!respuesta.ok) {
      throw new Error(`la API respondió ${respuesta.status} al montar el test`);
    }
    return (await respuesta.json()) as T;
  };

  const oposiciones = await leer<{ id: string; active: boolean; active_convocation: { id: string } | null }[]>(
    await fetch(`${API}/api/v1/oppositions`),
  );
  const activa = oposiciones.find((oposicion) => oposicion.active);
  if (activa?.active_convocation == null) {
    throw new Error('no hay oposición activa con convocatoria: no se puede montar el test');
  }

  const conjunto = await leer<{ id: string }>(
    await fetch(`${API}/api/v1/question-sets`, {
      method: 'POST',
      headers: cabeceras,
      body: JSON.stringify({
        title: `Capturas ${String(Date.now())}`,
        opposition_id: activa.id,
        set_type: 'private_bank',
        convocation_version_id: activa.active_convocation.id,
      }),
    }),
  );

  const texto = [
    '1. El modelo TCP/IP tiene cuatro capas.',
    'a) Verdadero',
    'b) Falso',
    'Respuesta correcta: a',
    '2. La sede electronica se regula en la Ley 39/2015.',
    'a) Verdadero',
    'b) Falso',
    'Respuesta correcta: a',
    '3. El Esquema Nacional de Seguridad se regula en el Real Decreto 311/2022.',
    'a) Verdadero',
    'b) Falso',
    'Respuesta correcta: a',
    '',
  ].join('\n');
  await leer<unknown>(
    await fetch(`${API}/api/v1/question-sets/${conjunto.id}/parse`, {
      method: 'POST',
      headers: cabeceras,
      body: JSON.stringify({ kind: 'questions', text: texto }),
    }),
  );

  const claves = await leer<{ id: string }[]>(
    await fetch(`${API}/api/v1/question-sets/${conjunto.id}/answer-keys`),
  );
  const clave = claves[0];
  if (clave === undefined) {
    throw new Error('el conjunto no trae plantilla: sin ella no hay test que retratar');
  }
  await leer<unknown>(
    await fetch(`${API}/api/v1/question-sets/${conjunto.id}/answer-keys/${clave.id}/activate`, {
      method: 'POST',
      headers: cabeceras,
    }),
  );

  const programa = await leer<{ nodes: NodoPrograma[] }>(
    await fetch(`${API}/api/v1/convocations/${activa.active_convocation.id}/curriculum`),
  );
  const tema = aplanar(programa.nodes).find((nodo) => nodo.path === 'IV.1');
  if (tema === undefined) {
    throw new Error('el programa no tiene el tema IV.1: no se puede catalogar el test');
  }
  const preguntas = await leer<{ questions: { id: string }[] }>(
    await fetch(`${API}/api/v1/questions?set_id=${conjunto.id}&limit=10`),
  );
  for (const pregunta of preguntas.questions) {
    await leer<unknown>(
      await fetch(`${API}/api/v1/questions/${pregunta.id}/topics`, {
        method: 'POST',
        headers: cabeceras,
        body: JSON.stringify({ curriculum_node_id: tema.id }),
      }),
    );
  }

  const sesion = await leer<{ id: string }>(
    await fetch(`${API}/api/v1/student/tests`, {
      method: 'POST',
      headers: cabeceras,
      body: JSON.stringify({ nodes: ['IV.1'], count: 3, filter: 'all', feedback: 'immediate' }),
    }),
  );
  await leer<unknown>(
    await fetch(`${API}/api/v1/student/sessions/${sesion.id}/start`, {
      method: 'POST',
      headers: cabeceras,
    }),
  );
  // Y una respuesta marcada como dudosa, para que la captura enseñe la casilla ámbar y la corrección.
  await leer<unknown>(
    await fetch(`${API}/api/v1/student/sessions/${sesion.id}/answers`, {
      method: 'POST',
      headers: cabeceras,
      body: JSON.stringify({ position: 1, chosen: ['a'], elapsed_ms: 2400, confidence: 'low' }),
    }),
  );
  return sesion.id;
}

interface NodoPrograma {
  id: string;
  path: string;
  children?: NodoPrograma[];
}

function aplanar(nodos: NodoPrograma[]): NodoPrograma[] {
  return nodos.flatMap((nodo) => [nodo, ...aplanar(nodo.children ?? [])]);
}
