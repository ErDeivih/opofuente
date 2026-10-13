import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';

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
      finished_at: null,
      created_at: '2026-10-11T08:59:00Z',
      result: null,
      practical_case_origin: null,
    },
    total: 3,
    answered: 2,
    pending: 1,
    finished: false,
    keys_in_review: 0,
    position: 3,
    question: {
      position: 3,
      is_reserve: false,
      key_in_review: false,
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
        key_in_review: false,
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
