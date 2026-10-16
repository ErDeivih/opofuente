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
 * El ciclo de contestar, como **una sola máquina de estados** (§3.2 del encargo F36).
 *
 * Los defectos 5, 6 y 8 del recorrido se ven aquí, donde no llega una captura: cuántas veces se pide
 * el arranque, si la hoja lleva a la fila que se pulsa, si las flechas existen y si cambiar una
 * respuesta mueve al alumno de la pregunta que está corrigiendo.
 */
describe('el ciclo de contestar', () => {
  /** Las direcciones de las llamadas de la simulación, para poder contarlas y mirarlas. */
  function direcciones(fetchMock: ReturnType<typeof stubApi>, fragmento: string): string[] {
    return fetchMock.mock.calls
      .map(([url]) => urlDe(url))
      .filter((direccion) => direccion.includes(fragmento));
  }

  /**
   * Las filas que se han pedido de verdad (`GET …?position=N`).
   *
   * Es la medida de la navegación: si la hoja funciona, cada fila que se pulsa deja su petición; y si
   * el alumno se queda donde está al cambiar una respuesta, no hay petición ninguna.
   */
  function filasPedidas(fetchMock: ReturnType<typeof stubApi>): number[] {
    return direcciones(fetchMock, '/student/sessions/')
      .filter((direccion) => !direccion.includes('/answers') && !direccion.includes('/finish'))
      .map((direccion) => {
        const encontrado = /[?&]position=(\d+)/.exec(direccion);
        return encontrado === null ? -1 : Number(encontrado[1]);
      })
      .filter((posicion) => posicion > 0);
  }

  /** La hoja de un test de tres preguntas: la 1 y la 2 contestadas, la 3 pendiente. */
  const HOJA: StudentSheetRow[] = FILAS;

  /**
   * El test como lo sirve el servidor **en una fila concreta**.
   *
   * La simulación tiene que contestar por posición —y no devolver siempre lo mismo— porque si no,
   * moverse por la hoja no cambiaría nada en pantalla y la prueba no comprobaría la navegación.
   */
  function runEnFila(posicion: number, filas: StudentSheetRow[] = HOJA): StudentRun {
    const fila = filas.find((candidata) => candidata.position === posicion) ?? filas[0]!;
    const base = runFixture();
    return {
      ...base,
      position: posicion,
      question: {
        position: posicion,
        is_reserve: false,
        in_review: false,
        derived_key: false,
        stem: `¿Cuántas capas tiene el modelo OSI? (pregunta ${String(posicion)})`,
        question_type: 'single_choice',
        options: [
          { key: 'a', text: 'Cuatro' },
          { key: 'b', text: 'Siete' },
        ],
        answered: fila.answered,
        chosen: fila.chosen,
        confidence: fila.confidence,
        correction:
          fila.outcome === null
            ? null
            : { outcome: fila.outcome, correct: fila.correct, reason: null },
      },
      sheet: filas,
    };
  }

  /** Pinta el test con una simulación que contesta por fila y devuelve su simulador de `fetch`. */
  function pintarConHoja(filas: StudentSheetRow[], inicial: number, respuestas?: StudentRun) {
    const rutas: Record<string, StubbedRoute> = {};
    for (const fila of filas) {
      rutas[`GET /api/v1/student/sessions/ses-1?position=${String(fila.position)}`] = {
        body: runEnFila(fila.position, filas),
      };
    }
    rutas['GET /api/v1/student/sessions/ses-1'] = { body: runEnFila(inicial, filas) };
    rutas['POST /api/v1/student/sessions/ses-1/answers'] = {
      body: respuestas ?? runEnFila(inicial, filas),
    };
    const fetchMock = stubApi(rutas);
    renderWithProviders(
      <Routes>
        <Route path="/test/:id" element={<StudentTestRunner />} />
      </Routes>,
      { route: '/test/ses-1' },
    );
    return fetchMock;
  }

  it('arranca el test con **un solo** `POST /start`, aunque la pantalla se repinte', async () => {
    const borrador = runFixture({ session: { ...runFixture().session, status: 'draft' } });
    const enMarcha = runFixture();
    // Las rutas de la sesión en marcha van **primero** y la lectura del borrador las pisa después: al
    // revés, el objeto literal se quedaría con la última y no habría borrador que arrancar.
    //
    // El arranque tarda 20 ms a propósito: es el hueco de una ida y vuelta de verdad, y es justo
    // durante ese hueco cuando la pantalla se repinta y el efecto se volvía a disparar. Con la
    // respuesta inmediata ese hueco no existe y la prueba pasaría sin demostrar nada.
    const fetchMock = stubApi({
      ...rutas(enMarcha),
      'GET /api/v1/student/sessions/ses-1': { body: borrador, demoraMs: 5 },
      'POST /api/v1/student/sessions/ses-1/start': { body: enMarcha, demoraMs: 20 },
    });
    renderWithProviders(
      <Routes>
        <Route path="/test/:id" element={<StudentTestRunner />} />
      </Routes>,
      { route: '/test/ses-1' },
    );

    await screen.findByText('¿Cuántas capas tiene el modelo OSI?');
    await waitFor(() => {
      expect(direcciones(fetchMock, '/start')).toHaveLength(1);
    });
    // Y sigue siendo uno cuando la pantalla ya se ha asentado: el fallo era que el efecto se volvía a
    // disparar en cada render, así que mirar la primera llamada no bastaba.
    await new Promise((seguir) => {
      setTimeout(seguir, 30);
    });
    expect(direcciones(fetchMock, '/start')).toHaveLength(1);
  });

  it('el número de una fila de la hoja abre esa pregunta', async () => {
    const usuario = userEvent.setup();
    const fetchMock = pintarConHoja(HOJA, 3);
    await screen.findByText(/pregunta 3/);

    await usuario.click(screen.getByRole('button', { name: 'Ir a la pregunta 1' }));

    await waitFor(() => {
      expect(filasPedidas(fetchMock)).toContain(1);
    });
    expect(await screen.findByText(/pregunta 1/)).toBeInTheDocument();
  });

  it('las flechas `←` y `→` recorren la hoja', async () => {
    const usuario = userEvent.setup();
    const fetchMock = pintarConHoja(HOJA, 3);
    await screen.findByText(/pregunta 3/);
    expect(filasPedidas(fetchMock)).toEqual([]);

    await usuario.keyboard('{ArrowLeft}');
    await waitFor(() => {
      expect(filasPedidas(fetchMock)).toContain(2);
    });
    // La pregunta anterior se pide y se pinta: la flecha no se queda en un `preventDefault`.
    expect(await screen.findByText(/pregunta 2/)).toBeInTheDocument();

    await usuario.keyboard('{ArrowRight}');
    await waitFor(() => {
      expect(filasPedidas(fetchMock)).toContain(3);
    });
    // Y por la derecha no se sale del test: la 4 no existe en uno de tres.
    expect(filasPedidas(fetchMock)).not.toContain(4);
  });

  it('cambiar la respuesta no mueve al alumno de la pregunta que está corrigiendo', async () => {
    const usuario = userEvent.setup();
    // La pregunta 2 ya está contestada: es el caso del defecto 5 —volver y cambiar—.
    const fetchMock = pintarConHoja(HOJA, 2);
    await screen.findByText(/pregunta 2/);

    await usuario.click(screen.getByRole('button', { name: /Siete/ }));

    await waitFor(() => {
      expect(direcciones(fetchMock, '/answers')).toHaveLength(1);
    });
    // Ni se pide otra fila ni se salta a la primera sin contestar: sigue donde estaba.
    expect(filasPedidas(fetchMock)).toEqual([]);
    expect(screen.getByText(/pregunta 2/)).toBeInTheDocument();
  });

  it('contestar una pregunta nueva sí avanza a la primera sin contestar', async () => {
    const usuario = userEvent.setup();
    const sinContestar: StudentSheetRow[] = [
      { position: 1, answered: false, chosen: [], confidence: null, outcome: null, correct: [] },
      { position: 2, answered: false, chosen: [], confidence: null, outcome: null, correct: [] },
      { position: 3, answered: false, chosen: [], confidence: null, outcome: null, correct: [] },
    ];
    // Lo que devuelve el servidor al contestar: la fila contestada, con la hoja ya marcada.
    const contestada = runEnFila(1, [
      {
        position: 1,
        answered: true,
        chosen: ['a'],
        confidence: null,
        outcome: 'correct',
        correct: ['a'],
      },
      sinContestar[1]!,
      sinContestar[2]!,
    ]);
    const fetchMock = pintarConHoja(sinContestar, 1, contestada);
    await screen.findByText(/pregunta 1/);

    await usuario.click(screen.getByRole('button', { name: /Cuatro/ }));

    await waitFor(() => {
      expect(filasPedidas(fetchMock)).toContain(2);
    });
  });
});
