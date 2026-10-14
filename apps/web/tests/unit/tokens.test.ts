/**
 * Los tokens del diseño viven en **un solo sitio** (F13, §3.7 del objetivo).
 *
 * La regla es la del encargo: color, tipografía, espaciado, radios, sombras y estados en un fichero
 * único, y las pantallas tomándolos de ahí. Una hoja de estilos que vuelve a escribir `#2347C5` a
 * mano es exactamente lo que hace que la aplicación se desvíe del diseño sin que nadie lo note: el
 * día que el azul cambie, cambiará en todas partes menos en ese rincón.
 *
 * Por eso esta prueba no mira un componente: lee los ficheros de estilo y comprueba dos cosas.
 *
 * 1. **los valores del diseño están, con su nombre y su valor exactos** (los del §1 del documento de
 *    diseño: papel, hoja, tinta, el azul de hoja óptica, acierto, fallo, dudosa, las dos familias
 *    tipográficas, la escala y los radios);
 * 2. **ninguna otra hoja declara un color propio**: `ui.css` y `global.css` los toman de los tokens.
 *    Si alguien necesita un color nuevo, su sitio es `tokens.css`.
 */

import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { describe, expect, it } from 'vitest';

const aqui = path.dirname(fileURLToPath(import.meta.url));
const estilos = path.resolve(aqui, '..', '..', 'src', 'styles');
const componentes = path.resolve(aqui, '..', '..', 'src', 'ui');

function leer(nombre: string): string {
  return readFileSync(path.join(estilos, nombre), 'utf8');
}

/** El valor de un token, tal cual está declarado (`--papel: #f4f6f9;`). */
function token(css: string, nombre: string): string | null {
  const encontrado = new RegExp(`${nombre}\\s*:\\s*([^;]+);`).exec(css);
  return encontrado?.[1]?.trim() ?? null;
}

describe('los tokens del diseño', () => {
  const tokens = leer('tokens.css');

  it('declara la paleta del diseño con sus valores exactos', () => {
    const paleta: Record<string, string> = {
      '--papel': '#f4f6f9',
      '--hoja': '#ffffff',
      '--tinta': '#18202b',
      '--tinta-suave': '#5a6472',
      '--linea': '#d5dce6',
      '--linea-suave': '#e4e9f0',
      '--azul': '#2347c5',
      '--azul-suave': '#e7ecfb',
      '--acierto': '#15734a',
      '--acierto-suave': '#e3f2ea',
      '--fallo': '#b42318',
      '--fallo-suave': '#fbe8e6',
      '--dudosa': '#9a6200',
      '--dudosa-suave': '#fbf0d9',
    };
    for (const [nombre, valor] of Object.entries(paleta)) {
      expect(token(tokens, nombre), `${nombre} no está en tokens.css`).toBe(valor);
    }
  });

  it('declara la tipografía, la escala, los espaciados y los radios', () => {
    expect(token(tokens, '--fuente-interfaz')).toContain('Atkinson Hyperlegible Next');
    expect(token(tokens, '--fuente-apuntes')).toContain('Source Serif 4');

    const escala: Record<string, string> = {
      '--t-sm': '0.875rem', // 14
      '--t-cuerpo': '1.0625rem', // 17
      '--t-enunciado': '1.25rem', // 20
      '--t-titulo': '1.5rem', // 24
      '--t-portada': '2rem', // 32
    };
    for (const [nombre, valor] of Object.entries(escala)) {
      expect(token(tokens, nombre), `${nombre} no está en tokens.css`).toBe(valor);
    }

    for (const nombre of ['--s1', '--s2', '--s3', '--s4', '--s5', '--s6', '--s7']) {
      expect(token(tokens, nombre), `${nombre} no está en tokens.css`).not.toBeNull();
    }
    for (const nombre of ['--radio-sm', '--radio', '--radio-pildora']) {
      expect(token(tokens, nombre), `${nombre} no está en tokens.css`).not.toBeNull();
    }

    // La sombra del diseño: solo para lo que de verdad se superpone.
    expect(token(tokens, '--sombra-superpuesta')).toBe('0 4px 16px rgba(24, 32, 43, 0.1)');
    // Y el estado de foco, que es el que hace visible el teclado.
    expect(token(tokens, '--foco')).toContain('var(--azul)');
    expect(token(tokens, '--medida-apuntes')).toBe('68ch');
  });

  it('ninguna otra hoja de estilos declara un color propio', () => {
    const hojas: [string, string][] = [
      ['global.css', leer('global.css')],
      // `ui.css` vive junto a los componentes, no en `styles/`.
      ['ui.css', readFileSync(path.join(componentes, 'ui.css'), 'utf8')],
    ];
    for (const [nombre, css] of hojas) {
      const colores = [...css.matchAll(/#[0-9a-fA-F]{3,8}\b/g)].map((encontrado) => encontrado[0]);
      expect(colores, `${nombre} vuelve a escribir colores a mano: ${colores.join(', ')}`).toEqual(
        [],
      );
      const rgb = [...css.matchAll(/rgba?\([^)]*\)/g)].map((encontrado) => encontrado[0]);
      expect(rgb, `${nombre} vuelve a escribir colores a mano: ${rgb.join(', ')}`).toEqual([]);
    }
  });

  it('las fuentes del diseño se cargan desde el paquete que las autoaloja', () => {
    const main = readFileSync(path.resolve(estilos, '..', 'main.tsx'), 'utf8');
    expect(main).toContain('@fontsource/atkinson-hyperlegible-next');
    expect(main).toContain('@fontsource-variable/source-serif-4');
    // La CSP del proyecto no deja cargar fuentes de fuera: nada de enlaces a Google Fonts.
    expect(main).not.toContain('fonts.googleapis.com');
  });
});
