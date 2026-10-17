import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';

import type { StudentRun, StudentSheetRow } from '../../src/api/studentTests';
import { AnswerSheet } from '../../src/features/study/AnswerSheet';
import { StudentTestRunner } from '../../src/features/study/StudentTestRunner';
import { renderWithProviders, stubApi, type StubbedRoute } from './testUtils';

/** La URL de una llamada simulada, sin depender de su forma (`string`, `URL` o `Request`). */
function urlDe(url: RequestInfo | URL): string {
  if (typeof url === 'string') {
    return url;
  }
  return url instanceof URL ? url.href : url.url;
}

/** El cuerpo que se mandó en una llamada, ya leído como objeto. */
function cuerpoDe(
  llamada: [input: RequestInfo | URL, init?: RequestInit | undefined] | undefined,
): unknown {
  const cuerpo = llamada?.[1]?.body;
  if (typeof cuerpo !== 'string') {
    throw new Error('la llamada no llevaba cuerpo de texto');
  }
  return JSON.parse(cuerpo) as unknown;
}

/**
 * El test en curso con su hoja de respuestas (diseño v0).
 *
 * Lo que se comprueba aquí es lo que no se puede ver en una captura: que la hoja pinte el estado de
 * cada fila, que el teclado conteste, y —lo más importante— que la solución **no** se enseñe cuando
 * el modo corrige al final y el test no ha terminado. Esa última es la regla que impide filtrar el
 * examen, y una pantalla puede romperla sin que ninguna captura lo delate.
 */

const FILAS: StudentSheetRow[] = [
  {
    position: 1,
    answered: true,
    chosen: ['b'],
    confidence: null,
    outcome: 'correct',
    correct: ['b'],
  },
  {
    position: 2,
    answered: true,
    chosen: ['a'],
    confidence: 'low',
    outcome: 'wrong',
    correct: ['b'],
  },
  { position: 3, answered: false, chosen: [], confidence: null, outcome: null, correct: [] },
];

/** La hoja **sin corregir**: solo lo que se marcó y si se marcó con poca confianza. */
const FILAS_SIN_CORREGIR: StudentSheetRow[] = FILAS.map((fila) => ({
  ...fila,
  outcome: null,
  correct: [],
}));

function runFixture(overrides: Partial<StudentRun> = {}): StudentRun {
  return {
    session: {
      id: 'ses-1',
      mode: 'practice',
      status: 'running',
      title: 'Test · 3 preguntas',
      total_questions: 3,
      answered_questions: 2,
      time_limit_minutes: null,
      started_at: '2026-10-11T09:00:00Z',
      // La hora del servidor, del **mismo reloj** que `started_at`: aquí es la del arranque, así que
      // el test acaba de empezar. Cada prueba que quiera un transcurrido concreto mueve las dos.
      server_now: '2026-10-11T09:00:00Z',
      finished_at: null,
      created_at: '2026-10-11T08:59:00Z',
      result: null,
      practical_case_origin: null,
    },
    total: 3,
    answered: 2,
    pending: 1,
    finished: false,
    questions_in_review: 0,
    questions_derived: 0,
    position: 3,
    question: {
      position: 3,
      is_reserve: false,
      in_review: false,
      derived_key: false,
      stem: '¿Cuántas capas tiene el modelo OSI?',
      question_type: 'single_choice',
      options: [
        { key: 'a', text: 'Cuatro' },
        { key: 'b', text: 'Siete' },
      ],
      answered: false,
      chosen: [],
      confidence: null,
      correction: null,
    },
    sheet: FILAS,
    ...overrides,
  };
}

function rutas(run: StudentRun): Record<string, StubbedRoute> {
  return {
    'GET /api/v1/student/sessions/ses-1': { body: run },
    'POST /api/v1/student/sessions/ses-1/answers': { body: run },
    'POST /api/v1/student/sessions/ses-1/abandon': {
      body: {
        session_id: 'ses-1',
        action: 'abandoned',
        detail: 'tus respuestas se conservan para repasar, pero este test no cuenta como hecho',
      },
    },
    'POST /api/v1/student/sessions/ses-1/finish': {
      body: {
        session: { ...run.session, status: 'finished' },
        parts: [
          {
            part_code: 'primera_parte',
            part_name: 'Primera parte: cuestionario de conocimientos',
            kind: 'estimated',
            correct: 1,
            wrong: 1,
            blank: 1,
            score: '5/6',
            score_decimal: '0.8333',
            score_max: 50,
            pass_score: 25,
            passed: null,
            verdict_note: 'La estimación no llega al mínimo publicado, y no es la calificación.',
          },
        ],
        total: {
          part_code: null,
          part_name: null,
          kind: 'estimated',
          correct: 1,
          wrong: 1,
          blank: 1,
          score: '5/6',
          score_decimal: '0.8333',
          score_max: null,
          pass_score: null,
          passed: null,
          verdict_note: null,
        },
        official_available: false,
        official_note: 'La calificación oficial 0-50 no está importada.',
      },
    },
  };
}

function pintarElTest(run: StudentRun) {
  const fetchMock = stubApi(rutas(run));
  renderWithProviders(
    <Routes>
      <Route path="/test/:id" element={<StudentTestRunner />} />
    </Routes>,
    { route: '/test/ses-1' },
  );
  return fetchMock;
}

describe('la hoja de respuestas', () => {
  it('pinta una fila por pregunta y marca la actual, la respondida y la dudosa', () => {
    renderWithProviders(<AnswerSheet filas={FILAS_SIN_CORREGIR} actual={3} letras={['a', 'b']} />);

    const filas = screen.getAllByRole('listitem');
    expect(filas).toHaveLength(3);
    expect(filas[2]).toHaveAttribute('data-actual', 'si');
    // La respondida se marca en azul; la dudosa (posición 2) lleva su estado propio.
    expect(within(filas[0]!).getAllByLabelText('Fila 1, opción B')[0]).toHaveAttribute(
      'data-estado',
      'marcada',
    );
    expect(within(filas[1]!).getAllByLabelText('Fila 2, opción A')[0]).toHaveAttribute(
      'data-estado',
      'dudosa',
    );
  });

  it('en una hoja corregida marca la casilla correcta y la fallada, como la plantilla', () => {
    renderWithProviders(<AnswerSheet filas={FILAS} actual={null} letras={['a', 'b']} />);

    const fila1 = screen.getAllByRole('listitem')[0]!;
    const fila2 = screen.getAllByRole('listitem')[1]!;
    expect(within(fila1).getAllByLabelText('Fila 1, opción B')[0]).toHaveAttribute(
      'data-estado',
      'correcta',
    );
    expect(within(fila2).getAllByLabelText('Fila 2, opción A')[0]).toHaveAttribute(
      'data-estado',
      'fallada',
    );
    expect(within(fila2).getAllByLabelText('Fila 2, opción B')[0]).toHaveAttribute(
      'data-estado',
      'correcta',
    );
  });
});

describe('el test en curso', () => {
  it('responde con el teclado: `B` y `2` mandan la misma respuesta por la posición de la hoja', async () => {
    const usuario = userEvent.setup();
    const fetchMock = pintarElTest(runFixture());

    await screen.findByText('¿Cuántas capas tiene el modelo OSI?');
    await usuario.keyboard('b');

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/student/sessions/ses-1/answers'),
        expect.objectContaining({ method: 'POST' }),
      );
    });
    const llamada = fetchMock.mock.calls.find(([url]) => urlDe(url).includes('/answers'));
    expect(cuerpoDe(llamada)).toEqual({
      position: 3,
      chosen: ['b'],
      elapsed_ms: 0,
      confidence: null,
    });

    // Y `M` la marca como dudosa, que es lo que llena el contorno ámbar de la hoja.
    await usuario.keyboard('m');
    await waitFor(() => {
      const ultima = fetchMock.mock.calls
        .filter(([url]) => urlDe(url).includes('/answers'))
        .at(-1);
      expect(cuerpoDe(ultima)).toMatchObject({ confidence: 'low' });
    });
  });

  it('con corrección al final y el test sin terminar no se enseña la solución', async () => {
    pintarElTest(runFixture());

    await screen.findByText('¿Cuántas capas tiene el modelo OSI?');
    // El enunciado y las opciones están, pero ninguna dice cuál es la correcta.
    expect(screen.queryByText('Correcta')).not.toBeInTheDocument();
    expect(screen.getByText(/se ve al terminar/)).toBeInTheDocument();
  });

  it('con corrección inmediata y la pregunta respondida sí se enseña lo que manda el servidor', async () => {
    const corregida = runFixture({
      question: {
        position: 3,
        is_reserve: false,
        in_review: false,
      derived_key: false,
        stem: '¿Cuántas capas tiene el modelo OSI?',
        question_type: 'single_choice',
        options: [
          { key: 'a', text: 'Cuatro' },
          { key: 'b', text: 'Siete' },
        ],
        answered: true,
        chosen: ['a'],
        confidence: null,
        correction: { outcome: 'wrong', correct: ['b'], reason: null },
      },
    });
    pintarElTest(corregida);

    await screen.findByText('¿Cuántas capas tiene el modelo OSI?');
    expect(screen.getByText('Tu respuesta')).toBeInTheDocument();
    expect(screen.getByText('Correcta')).toBeInTheDocument();
    expect(screen.queryByText('La corrección de este test se ve al terminar.')).not.toBeInTheDocument();
  });
});

/**
 * El reloj visible y «Abandonar» (§3.4), que es lo que hoy no existía: el examen oficial no enseñaba
 * el tiempo y no se podía salir de él.
 */
describe('el reloj y abandonar el test', () => {
  it('enseña el tiempo que queda y el que llevas en un test con límite', async () => {
    // El servidor responde diez minutos después de arrancar, con 120 de límite: quedan 110.
    const conReloj = runFixture({
      session: {
        ...runFixture().session,
        time_limit_minutes: 120,
        started_at: '2026-10-16T10:00:00Z',
        server_now: '2026-10-16T10:10:00Z',
      },
    });
    pintarElTest(conReloj);

    // El bloque del reloj lleva las dos cifras: lo que queda y lo que llevas.
    await screen.findByText(/Quedan/);
    const reloj = document.querySelector('.test-reloj');
    expect(reloj).not.toBeNull();
    expect(reloj).toHaveTextContent('Quedan 1:50:00');
    expect(reloj).toHaveTextContent('Llevas 10:00');
  });

  it('no enseña reloj cuando el test no lleva tiempo', async () => {
    pintarElTest(runFixture());

    await screen.findByText('¿Cuántas capas tiene el modelo OSI?');
    expect(screen.queryByText(/Quedan/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Llevas/)).not.toBeInTheDocument();
  });

  it('abandonar pide confirmación, avisa de lo que se pierde y dice qué ha quedado', async () => {
    const usuario = userEvent.setup();
    const confirmacion = vi.spyOn(window, 'confirm').mockReturnValue(true);
    const fetchMock = pintarElTest(runFixture());
    await screen.findByText('¿Cuántas capas tiene el modelo OSI?');

    await usuario.click(screen.getByRole('button', { name: 'Abandonar' }));

    // La confirmación dice **cuántas** llevas y qué pasa con ellas: es la decisión, escrita.
    expect(confirmacion).toHaveBeenCalledWith(expect.stringContaining('2 de 3 contestadas'));
    expect(confirmacion).toHaveBeenCalledWith(expect.stringContaining('se conservan para repasar'));
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/student/sessions/ses-1/abandon'),
        expect.objectContaining({ method: 'POST' }),
      );
    });
    expect(await screen.findByText(/no cuenta como hecho/)).toBeInTheDocument();
    confirmacion.mockRestore();
  });

  it('si no se confirma, no se abandona nada', async () => {
    const usuario = userEvent.setup();
    const confirmacion = vi.spyOn(window, 'confirm').mockReturnValue(false);
    const fetchMock = pintarElTest(runFixture());
    await screen.findByText('¿Cuántas capas tiene el modelo OSI?');

    await usuario.click(screen.getByRole('button', { name: 'Abandonar' }));

    expect(
      fetchMock.mock.calls.some(([url]) => urlDe(url).includes('/abandon')),
    ).toBe(false);
    confirmacion.mockRestore();
  });

  it('un test abandonado no se puede contestar, lo dice y ofrece salir', async () => {
    const abandonado = runFixture({
      session: { ...runFixture().session, status: 'abandoned' },
    });
    pintarElTest(abandonado);

    await screen.findByText('¿Cuántas capas tiene el modelo OSI?');
    // Abandonar y volver a entrar funciona: la pantalla abre, dice qué es y no deja contestar.
    expect(screen.getByRole('status')).toHaveTextContent(/no cuenta como test hecho/i);
    expect(screen.getByRole('button', { name: 'Ir a la pregunta 1' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Salir' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Terminar' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Abandonar' })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Siete/ })).toBeDisabled();
    expect(screen.getByText(/no admite respuestas/)).toBeInTheDocument();
  });
});
