#!/usr/bin/env node
/**
 * Convierte los JSON de `capturar.mjs` en el anexo de textos visibles por pantalla.
 *
 * Uso: node docs/interfaz/generar-textos.mjs
 *
 * Lee `docs/interfaz/.captura-datos.json` y `docs/interfaz/.captura-vacio.json` (los produce
 * `capturar.mjs`) y escribe `docs/interfaz/TEXTOS-PANTALLAS-2026-11.md`. Es determinista: el mismo
 * JSON produce el mismo Markdown.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const aqui = path.dirname(fileURLToPath(import.meta.url));
const salida = path.join(aqui, 'TEXTOS-PANTALLAS-2026-11.md');

async function leerJson(nombre) {
  try {
    return JSON.parse(await fs.readFile(path.join(aqui, nombre), 'utf8'));
  } catch {
    return null;
  }
}

function bloqueTexto(texto) {
  if (texto.trim() === '') {
    return '_(sin texto visible)_';
  }
  // Los bloques de código del Markdown usan ``` y el innerText no contiene backticks, pero se
  // protege por si algún texto los trae.
  const contenido = texto.replaceAll('```', "'''");
  return ['```text', contenido, '```'].join('\n');
}

function describirPantallas(informe, titulo, nota) {
  const lineas = [`## ${titulo}`, '', nota, ''];
  if (informe === null) {
    return [...lineas, '_No se encontró el informe de captura correspondiente._', ''];
  }
  for (const pantalla of informe.pantallas) {
    // Solo el volcado a 1280: el texto de la pantalla no cambia con el ancho (solo refluye). Las
    // capturas a 390 están en el inventario y en el directorio de imágenes.
    if (pantalla.textos === undefined || pantalla.viewport.ancho !== 1280) {
      continue;
    }
    lineas.push(
      `### ${pantalla.pantalla} — \`${pantalla.ruta}\``,
      '',
      `- **Captura**: [${pantalla.captura}](../capturas/revision-2026-11/${pantalla.captura}) (${pantalla.viewport.ancho}×${pantalla.viewport.alto}, ${pantalla.altoPagina} px de alto)`,
      `- **Título de la pestaña**: ${pantalla.textos.tituloPestana}`,
      `- **H1**: ${pantalla.textos.h1.length === 0 ? '_(ninguno)_' : pantalla.textos.h1.map((h) => `«${h}»`).join(' · ')}`,
      `- **Encabezados**: ${pantalla.textos.encabezados.map((h) => h.texto).join(' · ') || '_(ninguno)_'}`,
      `- **Estados**: vacío ${pantalla.textos.estados.vacio}, cargando ${pantalla.textos.estados.cargando}, error ${pantalla.textos.estados.error}, avisos ${pantalla.textos.estados.avisos}`,
      '',
      'Texto visible de `main` (innerText tal cual):',
      '',
      bloqueTexto(pantalla.textos.main),
      '',
    );
  }
  return lineas;
}

const datos = await leerJson('.captura-datos.json');
const vacio = await leerJson('.captura-vacio.json');

const lineas = [
  '# Textos visibles por pantalla (OpoFuente, 2026-11)',
  '',
  'Anexo del [inventario de pantallas](./INVENTARIO-PANTALLAS-2026-11.md). Es el volcado literal del',
  '`innerText` que se ve en cada pantalla, capturado con Playwright el mismo día que las imágenes.',
  'Sirve para juzgar el copy: lo que el revisor externo lea aquí es exactamente lo que aparece en la',
  'pantalla, sin reconstruir ni corregir tildes.',
  '',
  '> **Los datos son sintéticos** (los de la suite E2E). Por eso hay textos sin tildes, títulos como',
  '> «Apuntes sinteticos E2E-08 mw8f42ou» y contenidos de relleno: no son defectos de copy de la',
  '> interfaz. Los textos de la interfaz —etiquetas, avisos, botones, estados vacíos— sí son los',
  '> reales.',
  '',
  'Generado con `node docs/interfaz/generar-textos.mjs` a partir de `.captura-datos.json` y',
  '`.captura-vacio.json`.',
  '',
  '## Índice',
  '',
];

if (datos !== null) {
  for (const pantalla of datos.pantallas) {
    if (pantalla.textos !== undefined && pantalla.viewport.ancho === 1280) {
      lineas.push(`- **${pantalla.pantalla}** — \`${pantalla.ruta}\``);
    }
  }
}
lineas.push('');

lineas.push(
  ...describirPantallas(
    datos,
    'Con datos (directorio sintético `.e2e-data`)',
    'Volcado a 1280 px de ancho. A 390 px el contenido es el mismo salvo el reflujo de la navegación y las tablas (que pasan a bloques); los textos que cambian con el ancho se señalan en el inventario.',
  ),
  '',
);

lineas.push(
  ...describirPantallas(
    vacio,
    'Estados vacíos (directorio temporal recién migrado y sembrado)',
    'Directorio de datos sin material, sin preguntas, sin sesiones, sin propuestas y sin cambios. Solo la siembra de perfiles (oposiciones, convocatorias y temario común) está puesta.',
  ),
  '',
);

await fs.writeFile(salida, lineas.join('\n'), 'utf8');
console.log(`Escrito ${salida}`);
