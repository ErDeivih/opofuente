/**
 * El acabado del resultado (§2.3 y §2.4 del cierre del objetivo), tal como lo vio el propietario.
 *
 * Lo que se comprueba es lo que él escribió, no una interpretación:
 *
 * 1. la nota es **una línea** —«Puntuación directa: 0,33 sobre 50 (estimada)»— y las notas van en
 *    español, con coma y dos decimales. Desde F38 (§3.5) esta forma es la de un **examen**: en un test
 *    de práctica la línea dice los netos con penalización y no lleva banda
 *    (`resultadoPracticaYExamen.test.tsx`);
 * 2. los párrafos sobre baremos y mínimos **siguen ahí, pero plegados** (no se borran) y se despliegan
 *    con «¿Por qué estimada?»: por defecto no hay ningún párrafo explicativo a la vista;
 * 3. el resultado **usa la hoja de respuestas** del diseño v0 —casillas A–D por pregunta, verde la
 *    correcta y rojo la fallada— y pulsar un número baja a esa pregunta;
 * 4. debajo de cada fallada hay **«Ver en apuntes»**, y lleva al **apartado** que contesta esa
 *    pregunta (`/temario/IV.7#udp`), no a la portada del tema.
 */

import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';

import type { StudentSessionResult } from '../../src/api/studentTests';
import { ResultPage } from '../../src/pages/student/ResultPage';
import { resultadoDeSimulacroFixture, sessionResultFixture } from './studentFixtures';
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

/** Los fallos de una pregunta: la lista de sus opciones, no la de preguntas. */
function opcionesDe(pregunta: HTMLElement): HTMLElement[] {
  return Array.from(pregunta.querySelectorAll<HTMLElement>(':scope > .resultado__opciones > li'));
}

/** Los elementos a los que la pantalla ha bajado con `scrollIntoView`. */
const desplazados: Element[] = [];

beforeEach(() => {
  // `scrollIntoView` no existe en jsdom; la pantalla lo usa para bajar a la pregunta pulsada. Se anota
  // **sobre qué elemento** se llama, que es lo que distingue «baja a la 3» de «baja a alguna».
  desplazados.length = 0;
  Element.prototype.scrollIntoView = vi.fn(function (this: Element) {
    desplazados.push(this);
  });
});

describe('el resultado: la nota en una línea', () => {
  it('escribe «Puntuación directa: 0,33 sobre 50 (estimada)» y ninguna cifra con punto', async () => {
    // F38: la banda del examen se enseña en un examen. El caso de esta prueba es un simulacro; en un
    // test de práctica la línea dice «Netos con penalización» y no lleva escala.
    montar(resultadoDeSimulacroFixture);

    const linea = await screen.findByText(/^Puntuación directa:/);
    expect(linea.textContent?.replace(/\s+/g, ' ').trim()).toBe(
      'Puntuación directa: 0,33 sobre 50 (estimada)',
    );
  });

  it('no deja ningún número con punto y dos o más decimales a la vista', async () => {
    montar(resultadoDeSimulacroFixture);

    await screen.findByText(/^Puntuación directa:/);
    // Se mira la pantalla **entera**, plegado incluido: desde el arreglo del servidor, la prosa que
    // compone el dominio también va en español (`0,33 sobre 50 ... (25)`), así que ya no queda ningún
    // rincón de esta pantalla —tampoco el que se despliega— con el punto del decimal.
    const pantalla = document.body.textContent ?? '';
    expect(pantalla).not.toMatch(/\d\.\d{2,}/);
  });
});

describe('el resultado: la explicación, plegada', () => {
  it('no enseña ningún párrafo sobre baremos y mínimos por defecto', async () => {
    montar(resultadoDeSimulacroFixture);

    const explicacion = await screen.findByText(/no es la calificación oficial/i);
    expect(explicacion).not.toBeVisible();
    // Los dos párrafos que explicaban los baremos están dentro del pliegue, y ninguno a la vista.
    for (const parrafo of screen.getAllByText(/los baremos que fija la Comisión de Selección/i)) {
      expect(parrafo).not.toBeVisible();
    }
  });

  it('«¿Por qué estimada?» despliega la explicación, que no se ha borrado', async () => {
    const usuario = userEvent.setup();
    montar(resultadoDeSimulacroFixture);

    const boton = await screen.findByRole('button', { name: /por qué estimada/i });
    expect(boton).toHaveAttribute('aria-expanded', 'false');

    await usuario.click(boton);

    expect(boton).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByText(/no es la calificación oficial/i)).toBeVisible();
  });
});

describe('el resultado: la hoja de respuestas', () => {
  it('pinta la hoja corregida, con la correcta en verde y la fallada en rojo', async () => {
    montar();

    const hoja = await screen.findByRole('list', { name: /hoja de respuestas/i });
    const filas = Array.from(hoja.querySelectorAll<HTMLElement>(':scope > li'));
    expect(filas).toHaveLength(4);

    // Fila 1: se marcó la b y la correcta era la a. La a sale `correcta` y la b, `fallada`.
    const primera = filas[0]!;
    expect(primera.querySelector('[data-estado="correcta"]')?.textContent).toBe('A');
    expect(primera.querySelector('[data-estado="fallada"]')?.textContent).toBe('B');

    // Fila 2: acertada. No hay ninguna casilla fallada en esa fila.
    const segunda = filas[1]!;
    expect(segunda.querySelector('[data-estado="correcta"]')?.textContent).toBe('A');
    expect(segunda.querySelector('[data-estado="fallada"]')).toBeNull();
  });

  it('pulsar un número de la hoja baja a esa pregunta', async () => {
    const usuario = userEvent.setup();
    montar();

    await screen.findByRole('list', { name: /hoja de respuestas/i });
    await usuario.click(screen.getByRole('button', { name: /ir a la pregunta 3/i }));

    const pregunta = document.getElementById('pregunta-3');
    expect(pregunta).not.toBeNull();
    // Se comprueba **sobre qué elemento** se llamó, no solo que se llamara: la hoja tiene que bajar a
    // la pregunta 3 y no a la primera.
    expect(desplazados).toContain(pregunta);
  });
});

describe('el resultado: «Ver en apuntes»', () => {
  it('lleva al apartado que contesta la pregunta, con su capítulo y su párrafo', async () => {
    montar();

    const lista = await screen.findByRole('list', { name: /pregunta a pregunta/i });
    const preguntas = Array.from(lista.querySelectorAll<HTMLElement>(':scope > li'));

    // Desde que los apuntes se leen por epígrafes oficiales (F35, §3.1), el enlace lleva **el
    // capítulo y el párrafo**, y el `#` con el prefijo `apartado-`, que es el `id` de la página. Las
    // tres cosas hacían falta: con `#tcpip-arquitectura` a secas el enlace no bajaba a ninguna parte
    // (medido: `scrollY = 0` con el apartado a 10.288 px).
    const enlace = within(preguntas[0]!).getByRole('link', { name: /ver en apuntes/i });
    expect(enlace).toHaveAttribute(
      'href',
      '/temario/IV.7?capitulo=IV.7.1#apartado-tcpip-arquitectura',
    );

    // La tercera pregunta trae dos temas; el apartado dice cuál de los dos explica el fallo, y su
    // capítulo (`IV.7.2`) es uno que **no** se sirve por defecto: sin él, el párrafo no estaría en la
    // página.
    expect(within(preguntas[2]!).getByRole('link', { name: /ver en apuntes/i })).toHaveAttribute(
      'href',
      '/temario/IV.7?capitulo=IV.7.2#apartado-udp',
    );
  });

  it('solo sale bajo las falladas: una acertada no manda a repasar nada', async () => {
    montar();

    const lista = await screen.findByRole('list', { name: /pregunta a pregunta/i });
    const preguntas = Array.from(lista.querySelectorAll<HTMLElement>(':scope > li'));

    // La 2 es la acertada y la 4 la que la plantilla no corrige: ni una ni otra ofrecen repaso.
    expect(within(preguntas[1]!).queryByRole('link', { name: /ver en apuntes/i })).toBeNull();
    expect(within(preguntas[3]!).queryByRole('link', { name: /ver en apuntes/i })).toBeNull();
  });
});

describe('el resultado: las casillas de cada pregunta', () => {
  it('marca la correcta y la fallada con la misma señal que la hoja', async () => {
    montar();

    const lista = await screen.findByRole('list', { name: /pregunta a pregunta/i });
    const preguntas = Array.from(lista.querySelectorAll<HTMLElement>(':scope > li'));
    const opciones = opcionesDe(preguntas[0]!);

    expect(opciones[0]!).toHaveClass('resultado__opcion--correcta');
    expect(opciones[1]!).toHaveClass('resultado__opcion--fallada');
    // Y la letra de cada opción va delante, como en la hoja.
    expect(opciones[0]!.textContent).toContain('A');
  });
});
