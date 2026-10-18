/**
 * F38: el resultado del alumno, con las tres cosas que el propietario vio (§3.5 del encargo).
 *
 * 1. **la hoja de respuestas sale rota en el Resultado**: las letras casi no se ven y no tienen color,
 *    aunque en el test en curso se pintan bien. El color se mide de verdad —el `background-color` y el
 *    `color` computados de cada casilla, por su `data-estado`— y se compara con el mismo casillero de la
 *    pantalla del test: lo que él dijo es que **se ven distintas**, así que la prueba lo compara;
 * 2. **un test de práctica no se puntúa como un examen**: dice aciertos, fallos, porcentaje y «netos con
 *    penalización», y la puntuación sobre 50 con su mínimo **solo** en simulacros y exámenes oficiales;
 * 3. **la puntuación directa nunca por debajo de 0,00 en pantalla**, con la cifra exacta dentro del
 *    pliegue.
 *
 * Y la regla general que es el suelo de las tres: **ningún párrafo explicativo visible por defecto** en
 * la zona del alumno.
 */

import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';

import type { StudentSessionResult } from '../../src/api/studentTests';
import { ResultPage } from '../../src/pages/student/ResultPage';
import {
  resultadoDePracticaDeDiezFixture,
  resultadoDeSimulacroFixture,
  resultadoNegativoFixture,
  sessionResultFixture,
} from './studentFixtures';
import { renderWithProviders, stubApi } from './testUtils';

function montar(resultado: StudentSessionResult = sessionResultFixture) {
  stubApi({
    '/api/v1/student/sessions/ses-9/result': { body: resultado, status: 200 },
    'POST /api/v1/student/tests': { body: { ...resultado.session, id: 'ses-10' }, status: 201 },
  });
  renderWithProviders(
    <Routes>
      <Route path="/resultado/:id" element={<ResultPage />} />
    </Routes>,
    { route: '/resultado/ses-9' },
  );
}

/** El texto de un párrafo, con los espacios colapsados: la pantalla parte las líneas donde quiere. */
function textoDe(elemento: Element | null): string {
  return (elemento?.textContent ?? '').replace(/\s+/g, ' ').trim();
}

/** La línea de la puntuación: la que el propietario leyó como «6,00 sobre 50 · mínimo 25». */
async function lineaDeLaNota(): Promise<string> {
  return textoDe(await screen.findByText(/^(Netos con penalización|Puntuación directa):/));
}

/**
 * Las cifras exactas del pliegue. Se buscan por su elemento —el `strong` de cada aviso marcado como
 * exacto— y no por el texto: la frase y la cifra comparten nodo de texto, y `getByText` las encontraría
 * dos veces. La marca es la clase, porque el aviso del servidor también lleva negritas.
 */
function cifrasExactas(): HTMLElement[] {
  return Array.from(document.querySelectorAll<HTMLElement>('.resultado__exacta strong'));
}

describe('F38 · un test de práctica no se puntúa como un examen', () => {
  it('el test de 10 del propietario dice sus cifras, y no la banda del examen', async () => {
    montar(resultadoDePracticaDeDiezFixture);

    // Lo que decía antes del arreglo, medido con esta misma prueba sobre el código de `main`:
    // «Puntuación directa: 6,00 sobre 50 (estimada)» y, en el desglose por parte,
    // «6,00 sobre 50 · mínimo 25». Ahora:
    expect(textoDe(await screen.findByText(/6 aciertos/))).toBe(
      '6 aciertos · 0 fallos · 4 en blanco · 60 % de acierto',
    );
    expect(await lineaDeLaNota()).toBe('Netos con penalización: 6,00');
    const pantalla = textoDe(document.body);
    expect(pantalla).not.toMatch(/sobre 50/);
    expect(pantalla).not.toMatch(/mínimo 25/);
  });

  it('dice aciertos, fallos, porcentaje y «netos con penalización»', async () => {
    montar();

    // 1 acierto, 2 fallos y 0 en blanco de 3 corregidas → 33 % de acierto.
    const cifras = await screen.findByText(/1 acierto/);
    expect(textoDe(cifras)).toBe('1 acierto · 2 fallos · 0 en blanco · 33 % de acierto');
    // Netos con penalización: 1 acierto − 2 fallos × 1/3 = 1/3 → «0,33», en español.
    expect(await lineaDeLaNota()).toBe('Netos con penalización: 0,33');
  });

  it('no enseña la banda del examen ni su mínimo, porque una práctica no los tiene', async () => {
    montar();

    await lineaDeLaNota();
    const pantalla = textoDe(document.body);
    // La banda viaja en la respuesta (50 y 25 son el dato declarado de la convocatoria) y la pantalla
    // **no la enseña** fuera de un examen, ni la llama «estimada».
    expect(pantalla).not.toMatch(/sobre 50/);
    expect(pantalla).not.toMatch(/mínimo 25/);
    expect(pantalla).not.toMatch(/estimada/);
    expect(pantalla).not.toMatch(/Puntuación directa/);
    // Y sin banda no hay desglose por parte que enseñar: una práctica es una sola parte.
    expect(screen.queryByRole('list', { name: /nota por parte/i })).toBeNull();
  });

  it('el porcentaje avisa cuando no hay nada que medir, en vez de inventar un cero', async () => {
    montar({
      ...sessionResultFixture,
      total: { ...sessionResultFixture.total, correct: 0, wrong: 0, blank: 0 },
    });

    const cifras = await screen.findByText(/0 aciertos/);
    // Sin preguntas presentadas no hay porcentaje que dar: la frase se queda en los tres recuentos.
    expect(textoDe(cifras)).toBe('0 aciertos · 0 fallos · 0 en blanco');
  });
});

describe('F38 · un simulacro sí enseña la puntuación sobre 50 con su mínimo', () => {
  it('dice la puntuación directa sobre 50, su mínimo y el desglose por parte', async () => {
    montar(resultadoDeSimulacroFixture);

    expect(await lineaDeLaNota()).toBe('Puntuación directa: 0,33 sobre 50 (estimada)');

    const partes = await screen.findByRole('list', { name: /nota por parte/i });
    const filas = within(partes).getAllByRole('listitem');
    expect(filas).toHaveLength(1);
    expect(textoDe(filas[0]!)).toContain('0,33 sobre 50 · mínimo 25');
  });
});

describe('F38 · la puntuación directa nunca por debajo de 0,00 en pantalla', () => {
  it('enseña 0,00 en la línea y deja la cifra exacta dentro del pliegue', async () => {
    montar(resultadoNegativoFixture);

    // La línea visible: 0 aciertos, 1 fallo, penalización de un tercio → -0,33 de netos, que en
    // pantalla no baja de cero.
    expect(await lineaDeLaNota()).toBe('Netos con penalización: 0,00');

    // La cifra exacta no se pierde: está en el pliegue, y el pliegue no se ve por defecto.
    const exactas = cifrasExactas();
    expect(exactas.map((cifra) => cifra.textContent)).toEqual(['-0,33']);
    expect(exactas[0]!).not.toBeVisible();
  });

  it('el pliegue se llama «¿Por qué 0,00?» y al abrirlo aparece la cifra exacta', async () => {
    const usuario = userEvent.setup();
    montar(resultadoNegativoFixture);

    const boton = await screen.findByRole('button', { name: /por qué 0,00/i });
    expect(boton).toHaveAttribute('aria-expanded', 'false');

    await usuario.click(boton);

    expect(boton).toHaveAttribute('aria-expanded', 'true');
    expect(cifrasExactas()[0]!).toBeVisible();
  });

  it('en un simulacro la cifra exacta vive en «¿Por qué estimada?», que ya existía', async () => {
    montar({
      ...resultadoDeSimulacroFixture,
      parts: [{ ...resultadoDeSimulacroFixture.parts[0]!, score: '-1/6' }],
      total: { ...resultadoDeSimulacroFixture.total, score: '-1/6' },
    });

    // La línea del total sigue sin bajar de cero…
    expect(await lineaDeLaNota()).toBe('Puntuación directa: 0,00 sobre 50 (estimada)');
    // …la de la parte tampoco…
    const partes = await screen.findByRole('list', { name: /nota por parte/i });
    expect(textoDe(within(partes).getAllByRole('listitem')[0]!)).toContain('0,00 sobre 50');
    // …y las dos cifras exactas están dentro del pliegue, que aquí se llama «¿Por qué estimada?» y no
    // se ve por defecto.
    const boton = await screen.findByRole('button', { name: /por qué estimada/i });
    expect(boton).toHaveAttribute('aria-expanded', 'false');
    expect(cifrasExactas().map((cifra) => cifra.textContent)).toEqual(['-0,17', '-0,17']);
    for (const cifra of cifrasExactas()) {
      expect(cifra).not.toBeVisible();
    }
  });
});

describe('F38 · la hoja de respuestas, que es del propietario', () => {
  it('no lleva encima la frase explicativa: fuera de la vista por defecto', async () => {
    montar();

    await screen.findByRole('list', { name: /hoja de respuestas/i });
    expect(screen.queryByText(/Cada casilla dice lo que pasó/i)).toBeNull();
  });

  it('pinta las dos casillas corregidas con su estado, que es lo que el color tiene que seguir', async () => {
    montar();

    const hoja = await screen.findByRole('list', { name: /hoja de respuestas/i });
    expect(hoja.querySelector('[data-estado="correcta"]')?.textContent).toBe('A');
    expect(hoja.querySelector('[data-estado="fallada"]')?.textContent).toBe('B');
  });
});

describe('F38 · ningún párrafo explicativo a la vista en el resultado', () => {
  it('los avisos del servidor están plegados y no a la vista', async () => {
    montar(resultadoDeSimulacroFixture);

    await lineaDeLaNota();
    const avisos = document.querySelectorAll('.resultado__aviso');
    expect(avisos.length).toBeGreaterThan(0);
    for (const aviso of Array.from(avisos)) {
      expect(aviso).not.toBeVisible();
    }
  });
});

/**
 * Y la causa del color, medida donde se puede medir sin navegador: **los tokens de la hoja se
 * declaran en un sitio que las dos pantallas ven**.
 *
 * La hoja de respuestas (`.hoja__casilla--*`) toma sus colores de `--hoja-*`. Mientras esos tokens
 * vivieron dentro de `.test-marco` —el marco del test en curso—, en el Resultado no existían: una
 * `var()` sin valor deja la declaración inválida, el fondo se queda en `transparent` y el color de la
 * letra se queda en `--sobre-acento` (**blanco sobre blanco**: «las letras casi no se ven»). Esta
 * prueba lee la hoja de estilos y exige que la declaración esté en `:root`, que es el único sitio del
 * que las dos pantallas heredan. El navegador lo mide `tests/e2e/resultado.spec.ts`.
 */
describe('F38 · los tokens de la hoja los ven las dos pantallas', () => {
  const aqui = path.dirname(fileURLToPath(import.meta.url));
  const global = readFileSync(
    path.resolve(aqui, '..', '..', 'src', 'styles', 'global.css'),
    'utf8',
  );

  /** El selector del bloque donde se declara un token, con los comentarios fuera. */
  function selectorDe(css: string, token: string): string {
    // Los comentarios se quitan antes de mirar: este fichero explica mucho, y un `{` dentro de una
    // explicación no es el de un bloque.
    const limpio = css.replace(/\/\*[\s\S]*?\*\//g, '');
    const indice = limpio.indexOf(`${token}:`);
    expect(indice, `${token} no se declara en global.css`).toBeGreaterThan(-1);
    const llave = limpio.lastIndexOf('{', indice);
    const cierre = limpio.lastIndexOf('}', llave);
    return limpio.slice(cierre + 1, llave).trim();
  }

  it('declara los cuatro tokens de estado en :root y no dentro del marco del test', () => {
    for (const token of [
      '--hoja-acierto',
      '--hoja-fallo',
      '--hoja-azul',
      '--hoja-tinta-suave',
    ]) {
      expect(selectorDe(global, token), `el ámbito de ${token}`).toBe(':root');
    }
  });
});
