import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

import { expect, test, type Page } from '@playwright/test';

/**
 * E2E: pasar el material de la bandeja a la biblioteca.
 *
 * Este recorrido comprueba **el paso que faltaba**: hasta ahora se podía inventariar, importar y
 * clasificar material, y la biblioteca seguía vacía porque promocionar solo existía en la API. Lo que
 * se verifica aquí, contra la API real y en el directorio de datos de la suite (nunca el del
 * propietario), es:
 *
 * 1. que el material importado **se puede pasar a la biblioteca desde la pantalla**, en lote;
 * 2. que al pasar **no se acepta nada**: la versión queda candidata, con el aviso a la vista y sin
 *    que la aplicación la dé por buena (ADR-009);
 * 3. que repetirlo **no duplica** documentos (la promoción es idempotente).
 *
 * La bandeja de origen es sintética y vive en el directorio temporal del sistema, como en el resto de
 * la suite: no se apunta a ficheros reales.
 */

let raiz = '';
let sufijo = '';
let nombreConTexto = '';

/**
 * PDF válido de una página con las líneas que se le pasen (sin líneas, sin texto).
 */
function pdfDeUnaPagina(lineas: string[]): Buffer {
  const escape = (texto: string) =>
    texto.replace(/\\/g, '\\\\').replace(/\(/g, '\\(').replace(/\)/g, '\\)');
  const flujo =
    lineas.length === 0
      ? ''
      : ['BT /F1 12 Tf 60 780 Td 16 TL', ...lineas.map((l) => `(${escape(l)}) Tj T*`), 'ET'].join('\n');

  const objetos: string[] = [
    '<< /Type /Catalog /Pages 2 0 R >>',
    '<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
    '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>',
    `<< /Length ${Buffer.byteLength(flujo, 'latin1')} >>\nstream\n${flujo}\nendstream`,
    '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>',
  ];

  const partes: string[] = ['%PDF-1.4\n'];
  const desplazamientos: number[] = [];
  let posicion = Buffer.byteLength(partes[0] ?? '', 'latin1');
  objetos.forEach((cuerpo, indice) => {
    desplazamientos.push(posicion);
    const texto = `${indice + 1} 0 obj\n${cuerpo}\nendobj\n`;
    partes.push(texto);
    posicion += Buffer.byteLength(texto, 'latin1');
  });
  const entradas = desplazamientos
    .map((desplazamiento) => `${String(desplazamiento).padStart(10, '0')} 00000 n \n`)
    .join('');
  partes.push(
    `xref\n0 ${objetos.length + 1}\n0000000000 65535 f \n${entradas}` +
      `trailer\n<< /Size ${objetos.length + 1} /Root 1 0 R >>\nstartxref\n${posicion}\n%%EOF\n`,
  );
  return Buffer.from(partes.join(''), 'latin1');
}

test.beforeAll(() => {
  raiz = fs.mkdtempSync(path.join(os.tmpdir(), 'opofuente-promote-'));
  // El directorio de datos de la suite **persiste** entre corridas (y hace bien: es su base). Por eso
  // cada corrida trae material **propio**, con su marca en el nombre y en el texto: si no, la segunda
  // corrida encontraría el documento ya promocionado de la anterior y la prueba diría «ya estaba»
  // donde esperaba «nuevo», midiendo el estado del disco en lugar del comportamiento.
  sufijo = `${Date.now().toString(36)}-${Math.floor(Math.random() * 1e6).toString(36)}`;
  nombreConTexto = `tema ${sufijo} - constitucion.pdf`;
  const bandeja = path.join(raiz, 'material');
  fs.mkdirSync(bandeja, { recursive: true });
  // Uno con texto y otro sin él: el que no tiene texto (un escaneo) no debe venir marcado solo.
  fs.writeFileSync(
    path.join(bandeja, nombreConTexto),
    pdfDeUnaPagina([
      'Tema 1. La Constitucion Espanola de 1978.',
      'Espana se constituye en un Estado social y democratico de Derecho.',
      `Marcador de esta corrida: ${sufijo}.`,
    ]),
  );
  fs.writeFileSync(path.join(bandeja, `escaneo sin texto ${sufijo}.pdf`), pdfDeUnaPagina([]));
});

test.afterAll(() => {
  fs.rmSync(raiz, { recursive: true, force: true });
});

async function inventariarEImportar(page: Page, carpeta: string) {
  await page.goto('/bandeja');
  await page.getByLabel(/Carpeta a inventariar/).fill(carpeta);
  await page.getByRole('button', { name: 'Inventariar (solo lectura)' }).click();
  await expect(page.getByRole('heading', { name: 'Vista previa del inventario' })).toBeVisible();
  await page.getByRole('button', { name: 'Importar una copia' }).click();

  const importacion = page.getByRole('region', { name: 'Importación' });
  await expect(importacion.getByText(/terminado|fallido/)).toBeVisible({ timeout: 60_000 });
}

test('E2E-20 biblioteca: el material de la bandeja se pasa a la biblioteca desde la pantalla, y sin aceptar', async ({
  page,
}) => {
  await inventariarEImportar(page, path.join(raiz, 'material'));

  const panel = page.getByRole('region', { name: 'Pasar a la biblioteca' });
  await expect(panel).toBeVisible();

  // Los dos artefactos están a la vista, y solo viene marcado el que tiene texto.
  const casillaTexto = panel.getByLabel(new RegExp(`Pasar a la biblioteca: .*tema ${sufijo} - constitucion`));
  await expect(casillaTexto).toBeVisible();
  await expect(casillaTexto).toBeChecked();
  await expect(panel.getByRole('button', { name: 'Pasar a la biblioteca (1)' })).toBeEnabled();

  // Al pedir ver los que no tienen texto, el escaneo aparece **desmarcado**: lo decide una persona.
  await panel.getByLabel(/Enseñar solo los que tienen texto/).click();
  const escaneo = panel.getByLabel(new RegExp(`Pasar a la biblioteca: .*escaneo sin texto ${sufijo}`));
  await expect(escaneo).toBeVisible();
  await expect(escaneo).not.toBeChecked();
  await panel.getByLabel(/Enseñar solo los que tienen texto/).click();

  await panel.getByRole('button', { name: 'Pasar a la biblioteca (1)' }).click();
  await expect(page.getByText(/1 documento\(s\) nuevo\(s\)/)).toBeVisible({ timeout: 30_000 });

  // Y lo promocionado entra de verdad: está en la biblioteca, y **sin aceptar**.
  await page.goto('/biblioteca');
  const tabla = page.getByRole('table', { name: /documentos en la biblioteca/ });
  const fila = tabla.getByRole('row').filter({ hasText: `tema ${sufijo} - constitucion` });
  await expect(fila).toBeVisible();
  await expect(fila.getByText('propuesta de cambio, sin aceptar')).toBeVisible();

  // El siguiente paso —aceptar— está ahí y no lo ha dado nadie: es de una persona.
  await fila.getByRole('button', { name: /Abrir la ficha/ }).click();
  await expect(
    page.getByRole('region', { name: /La versión activa es una propuesta de cambio/ }),
  ).toBeVisible();
  await page.getByRole('tab', { name: 'Versiones y diff' }).click();
  await expect(page.getByRole('button', { name: /^Aceptar la versión/ })).toBeVisible();
});

test('E2E-20 biblioteca: volver a pasar el mismo material no duplica documentos', async ({ page }) => {
  // Se reabre **el mismo lote** desde el historial: es la forma de repetir la promoción sobre el
  // mismo artefacto, que es lo que la idempotencia del servidor promete resolver.
  await page.goto('/bandeja');
  const historial = page.getByRole('region', { name: 'Lotes recientes' });
  await historial.getByRole('button', { name: /import/ }).first().click();
  await expect(page.getByRole('heading', { name: 'Pasar a la biblioteca' })).toBeVisible();

  const panel = page.getByRole('region', { name: 'Pasar a la biblioteca' });
  const casilla = panel.getByLabel(new RegExp(`Pasar a la biblioteca: .*tema ${sufijo} - constitucion`));
  await expect(casilla).toBeVisible();

  // Tras promocionar, la selección se queda vacía para no invitar a repetirlo sin querer: hay que
  // volver a marcarlo, que es exactamente lo que hace alguien que repite la operación a propósito.
  if (!(await casilla.isChecked())) {
    await casilla.check();
  }
  await panel.getByRole('button', { name: /Pasar a la biblioteca \(\d+\)/ }).click();
  await expect(page.getByText(/ya estaban en la biblioteca/)).toBeVisible({ timeout: 30_000 });

  // Y en la biblioteca sigue habiendo **un** documento con ese título, no dos.
  await page.goto('/biblioteca');
  const tabla = page.getByRole('table', { name: /documentos en la biblioteca/ });
  await expect(
    tabla.getByRole('row').filter({ hasText: `tema ${sufijo} - constitucion` }),
  ).toHaveCount(1);
});
