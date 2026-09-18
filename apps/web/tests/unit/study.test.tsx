import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import type {
  CurrentQuestion,
  SessionResult,
  SessionReview,
  StudySession,
} from '../../src/api/study';
import type { ConvocationDetail } from '../../src/api/profiles';
import type { QuestionSet } from '../../src/api/questions';
import { AppShell } from '../../src/app/AppShell';
import { StudyPage } from '../../src/pages/StudyPage';
import { renderWithProviders, stubApi, type StubbedRoute } from './testUtils';

/**
 * Pantalla Estudiar (S07) desde el comportamiento real: qué se puede configurar, qué se ve de una
 * pregunta, qué aparece al corregir y qué dice el resultado.
 *
 * Las respuestas imitan el contrato real, incluidos los 409 con su motivo y la ausencia de solución
 * mientras no se pueda enseñar.
 */

const SESION: StudySession = {
  id: 'ses-1',
  mode: 'practice',
  status: 'running',
  feedback: 'immediate',
  opposition_id: 'op-1',
  convocation_version_id: 'conv-tai',
  question_set_id: 'set-1',
  answer_key_version_id: 'key-1',
  key_label: 'Primera parte: cuestionario de conocimientos: plantilla v1',
  configuration: {
    mode: 'practice',
    feedback: 'immediate',
    time_limit_minutes: null,
    shuffle: false,
    sources: [
      {
        question_set_id: 'set-1',
        part_code: 'primera_parte',
        count: 3,
        include_reserves: false,
      },
    ],
  },
  time_limit_minutes: null,
  total_questions: 3,
  answered_questions: 0,
  started_at: '2026-09-17T12:00:00Z',
  finished_at: null,
  created_at: '2026-09-17T12:00:00Z',
  result: null,
};

const PREGUNTA = {
  session_question_id: 'sq-1',
  question_version_id: 'q-1',
  stable_key: 'q001',
  position: 1,
  part_code: 'primera_parte',
  is_reserve: false,
  reserve_order: null,
  stem: 'La Constitucion espanola se aprobo en:',
  question_type: 'single_choice',
  origin_type: 'private',
  options: [
    { id: 'o-1', stable_key: 'a', label: 'A', text: '1976', position: 1 },
    { id: 'o-2', stable_key: 'b', label: 'B', text: '1978', position: 2 },
  ],
  answered: false,
  chosen_option_keys: [],
  elapsed_ms: null,
  confidence: null,
  correction: null,
} satisfies NonNullable<CurrentQuestion['question']>;

const ACTUAL: CurrentQuestion = {
  session: SESION,
  question: PREGUNTA,
  answered: 0,
  total: 3,
  pending: 3,
  finished: false,
};

const CORRECCION = {
  outcome: 'wrong' as const,
  correct_option_keys: ['b'],
  score: { numerator: -1, denominator: 3, fraction: '-1/3', decimal: '-0.3333' },
  reason: null,
  explanation: null,
  evidence: [],
};

const RESULTADO: SessionResult = {
  session_id: 'ses-1',
  mode: 'practice',
  answer_key_version_id: 'key-1',
  key_label: 'Primera parte: cuestionario de conocimientos: plantilla v1',
  parts: [
    {
      part_code: 'primera_parte',
      part_name: 'Primera parte: cuestionario de conocimientos',
      ordinary_items: 80,
      score_min: 0,
      score_max: 50,
      pass_score: 25,
      penalty: { numerator: 1, denominator: 3, fraction: '1/3', decimal: '0.3333' },
      correct: 2,
      wrong: 1,
      blank: 1,
      annulled: 0,
      excluded: 0,
      conflicting: 0,
      reserves_used: 0,
      unused_reserves: 0,
      score: { numerator: 5, denominator: 3, fraction: '5/3', decimal: '1.6667' },
      official_available: false,
    },
  ],
  total: {
    part_code: null,
    part_name: null,
    ordinary_items: null,
    score_min: null,
    score_max: null,
    pass_score: null,
    penalty: { numerator: 1, denominator: 3, fraction: '1/3', decimal: '0.3333' },
    correct: 2,
    wrong: 1,
    blank: 1,
    annulled: 0,
    excluded: 0,
    conflicting: 0,
    reserves_used: 0,
    unused_reserves: 0,
    score: { numerator: 5, denominator: 3, fraction: '5/3', decimal: '1.6667' },
    official_available: false,
  },
  substitutions: [],
  unfinished: 1,
  official_available: false,
  official_note:
    'La calificación oficial 0-50 resulta de transformar la puntuación directa con los baremos que fija la Comisión de Selección, y esa tabla no está importada: se muestra la puntuación directa y no se declara aprobado ni suspenso.',
  calculated_at: '2026-09-17T12:30:00Z',
};

const REVISION: SessionReview = {
  session: { ...SESION, status: 'finished', finished_at: '2026-09-17T12:30:00Z' },
  entries: [
    { ...PREGUNTA, answered: true, chosen_option_keys: ['a'], correction: CORRECCION },
  ],
  partial: false,
  note: null,
  pending: 0,
  unanswered: 1,
};

const CONJUNTO: QuestionSet = {
  id: 'set-1',
  title: 'Examen de prueba',
  set_type: 'private_bank',
  status: 'draft',
  opposition_id: 'op-1',
  convocation_version_id: 'conv-tai',
  model_code: null,
  held_at: null,
  source_document_version_id: null,
  created_at: '2026-09-17T10:00:00Z',
  question_count: 30,
  reserve_count: 2,
  incomplete_count: 0,
  key_count: 1,
  active_key_id: 'key-1',
  is_official: false,
};

const CONVOCATORIA: ConvocationDetail = {
  id: 'conv-tai',
  code: 'tai-age-2025',
  title: 'Convocatoria de prueba',
  official_url: 'https://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-26262',
  published_at: '2025-12-22',
  exam_date: null,
  status: 'active',
  source_reference: 'BOE-A-2025-26262 · ANEXO V',
  opposition_id: 'op-1',
  opposition_code: 'tai-age',
  opposition_name: 'Técnicos Auxiliares de Informática',
  parts: [
    {
      code: 'ejercicio_unico',
      name: 'Ejercicio único',
      kind: 'group',
      format: null,
      position: 1,
      parent_code: null,
      ordinary_items: null,
      reserve_items: null,
      options_per_question: null,
      score_min: 0,
      score_max: 100,
      pass_score: null,
      wrong_penalty_fraction: null,
      fail_if_errors_gte: null,
      time_minutes: 120,
      structure_note: null,
      notes: null,
      evidence_quote: 'El proceso de selección estará formado por un ejercicio único',
    },
    {
      code: 'primera_parte',
      name: 'Primera parte: cuestionario de conocimientos',
      kind: 'test',
      format: 'single_choice',
      position: 1,
      parent_code: 'ejercicio_unico',
      ordinary_items: 80,
      reserve_items: 5,
      options_per_question: null,
      score_min: 0,
      score_max: 50,
      pass_score: 25,
      wrong_penalty_fraction: 0.3333333333,
      fail_if_errors_gte: null,
      time_minutes: null,
      structure_note: null,
      notes: null,
      evidence_quote: 'Primera parte: consistirá en contestar por escrito un cuestionario',
    },
    {
      code: 'ortografia',
      name: 'Ortografía',
      kind: 'test',
      format: 'multi_mark_error',
      position: 2,
      parent_code: 'ejercicio_unico',
      ordinary_items: 20,
      reserve_items: 4,
      options_per_question: null,
      score_min: null,
      score_max: null,
      pass_score: null,
      wrong_penalty_fraction: null,
      fail_if_errors_gte: 6,
      time_minutes: null,
      structure_note: null,
      notes: null,
      evidence_quote: 'se valorará la ortografía',
    },
  ],
  rules: [],
};

function stubEstudio(overrides: Record<string, StubbedRoute> = {}) {
  return stubApi({
    '/api/v1/oppositions': {
      body: [
        {
          id: 'op-1',
          code: 'tai-age',
          name: 'Técnicos Auxiliares de Informática',
          description: null,
          active: true,
          active_convocation: {
            id: 'conv-tai',
            code: 'tai-age-2025',
            published_at: '2025-12-22',
            status: 'active',
          },
        },
      ],
    },
    '/api/v1/convocations/conv-tai': { body: CONVOCATORIA },
    '/api/v1/question-sets?limit=100&offset=0&opposition_id=op-1': {
      body: { sets: [CONJUNTO], total: 1, limit: 100, offset: 0 },
    },
    // Por defecto **no hay sesiones**: así la pantalla abre en la configuración. Las pruebas que
    // necesitan una sesión en marcha o terminada lo dicen con su propia respuesta.
    '/api/v1/study-sessions?limit=50&offset=0&opposition_id=op-1': {
      body: { sessions: [], total: 0, limit: 50, offset: 0 },
    },
    '/api/v1/study-sessions/ses-1/current-question': { body: ACTUAL },
    ...overrides,
  });
}

/** La lista de sesiones con una sesión en el estado que pida la prueba. */
function conSesion(sesion: StudySession): StubbedRoute {
  return {
    body: { sessions: [sesion], total: 1, limit: 50, offset: 0 },
  };
}

function renderEstudiar() {
  return renderWithProviders(
    <AppShell>
      <StudyPage />
    </AppShell>,
    { route: '/estudiar' },
  );
}

/** El cuerpo JSON de la primera petición que contenga el fragmento (y el método, si se pide). */
function cuerpoJson(
  fetchMock: ReturnType<typeof stubEstudio>,
  fragmento: string,
  metodo?: string,
): Record<string, unknown> {
  const llamada = fetchMock.mock.calls.find(
    (call) =>
      typeof call[0] === 'string' &&
      call[0].includes(fragmento) &&
      (metodo === undefined || call[1]?.method === metodo),
  );
  const body = llamada?.[1]?.body;
  if (typeof body !== 'string') {
    throw new Error(`la petición a ${fragmento} no llevaba cuerpo JSON`);
  }
  return JSON.parse(body) as Record<string, unknown>;
}

describe('estudiar: configuración', () => {
  it('ofrece solo las partes que el servidor sabe corregir y dice por qué las demás no', async () => {
    stubEstudio();
    renderEstudiar();

    const select = await screen.findByLabelText('Parte del examen');
    // La lista de partes llega con la convocatoria: se espera a que esté, no a que exista el select.
    await within(select).findByRole('option', { name: /Primera parte/ });
    expect(within(select).getByRole('option', { name: /Primera parte/ })).toBeInTheDocument();
    expect(within(select).queryByRole('option', { name: /Ortografía/ })).not.toBeInTheDocument();
    expect(within(select).queryByRole('option', { name: /Ejercicio único/ })).not.toBeInTheDocument();

    await userEvent.click(screen.getByText('Partes que todavía no se pueden practicar'));
    expect(screen.getByText(/Ortografía: se corrige como «multi_mark_error»/)).toBeInTheDocument();
    expect(screen.getByText(/Ejercicio único: agrupa partes/)).toBeInTheDocument();
  });

  it('no deja empezar sin conjunto elegido y avisa si el conjunto no tiene clave activa', async () => {
    stubEstudio({
      '/api/v1/question-sets?limit=100&offset=0&opposition_id=op-1': {
        body: {
          sets: [{ ...CONJUNTO, active_key_id: null }],
          total: 1,
          limit: 100,
          offset: 0,
        },
      },
    });
    renderEstudiar();

    await screen.findByRole('option', { name: /Examen de prueba/ });
    await userEvent.selectOptions(screen.getByLabelText('Conjunto de preguntas'), 'set-1');

    expect(screen.getByText(/sin clave activa: no se puede corregir/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Crear y empezar la sesión' })).toBeDisabled();
  });

  it('crea la sesión con el modo, la parte y el número de preguntas elegidos', async () => {
    const fetchMock = stubEstudio({
      '/api/v1/study-sessions': { body: { ...SESION, status: 'draft' }, status: 201 },
      '/api/v1/study-sessions/ses-1/start': { body: SESION },
    });
    renderEstudiar();

    await screen.findByRole('option', { name: /Examen de prueba/ });
    await userEvent.selectOptions(screen.getByLabelText('Conjunto de preguntas'), 'set-1');
    await userEvent.clear(screen.getByLabelText('Cuántas preguntas'));
    await userEvent.type(screen.getByLabelText('Cuántas preguntas'), '4');
    await userEvent.selectOptions(screen.getByLabelText('Corrección'), 'at_end');
    await userEvent.click(screen.getByRole('button', { name: 'Crear y empezar la sesión' }));

    await waitFor(() => {
      expect(screen.getByText(/Sesión de práctica lista/)).toBeInTheDocument();
    });
    const enviado = cuerpoJson(fetchMock, '/api/v1/study-sessions', 'POST');
    expect(enviado.mode).toBe('practice');
    expect(enviado.feedback).toBe('at_end');
    expect(enviado.sources).toEqual([
      {
        question_set_id: 'set-1',
        part_code: 'primera_parte',
        count: 4,
        include_reserves: false,
      },
    ]);
  });

  it('en examen oficial no ofrece número ni corrección: los fija la convocatoria', async () => {
    stubEstudio();
    renderEstudiar();

    await screen.findByLabelText('Parte del examen');
    await userEvent.selectOptions(screen.getByLabelText('Modo'), 'official_exam');

    expect(screen.queryByLabelText('Cuántas preguntas')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Corrección')).not.toBeInTheDocument();
    expect(screen.getByText(/los fija la convocatoria \(80 preguntas ordinarias/)).toBeInTheDocument();
  });

  it('explica el 409 del servidor al crear la sesión y no finge que se creó', async () => {
    stubEstudio({
      '/api/v1/study-sessions': {
        status: 409,
        contentType: 'application/problem+json',
        body: {
          title: 'Conflict',
          status: 409,
          detail: 'el conjunto no tiene ninguna clave activa',
          code: 'classification_conflict',
        },
      },
    });
    renderEstudiar();

    await screen.findByRole('option', { name: /Examen de prueba/ });
    await userEvent.selectOptions(screen.getByLabelText('Conjunto de preguntas'), 'set-1');
    await userEvent.click(screen.getByRole('button', { name: 'Crear y empezar la sesión' }));

    expect(
      await screen.findByText(/el conjunto no tiene ninguna clave activa/),
    ).toBeInTheDocument();
    expect(screen.queryByText(/Sesión de práctica lista/)).not.toBeInTheDocument();
  });
});

describe('estudiar: la pregunta', () => {
  it('enseña la pregunta con sus opciones y sin ninguna solución', async () => {
    stubEstudio({
      '/api/v1/study-sessions?limit=50&offset=0&opposition_id=op-1': conSesion(SESION),
    });
    renderEstudiar();

    expect(await screen.findByRole('heading', { name: 'Pregunta 1' })).toBeInTheDocument();
    expect(screen.getByText('La Constitucion espanola se aprobo en:')).toBeInTheDocument();
    expect(screen.getByText('1978')).toBeInTheDocument();
    // El enunciado del payload no trae la clave: la pantalla no tiene nada que enseñar todavía.
    expect(screen.queryByText('Corrección')).not.toBeInTheDocument();
    expect(screen.getByText(/0 de 3 respondidas/)).toBeInTheDocument();
  });

  it('responde, enseña la corrección y avisa de que el intento no se reescribe', async () => {
    const fetchMock = stubEstudio({
      '/api/v1/study-sessions?limit=50&offset=0&opposition_id=op-1': conSesion(SESION),
      '/api/v1/study-sessions/ses-1/answers': {
        status: 201,
        body: {
          saved: true,
          already_answered: false,
          attempt: {
            id: 'att-1',
            session_question_id: 'sq-1',
            question_version_id: 'q-1',
            chosen_option_keys: ['a'],
            elapsed_ms: 0,
            confidence: null,
            client_sequence: null,
            answered_at: '2026-09-17T12:05:00Z',
            outcome: 'wrong',
            score: { numerator: -1, denominator: 3, fraction: '-1/3', decimal: '-0.3333' },
            reason: null,
          },
          session: { ...SESION, answered_questions: 1 },
          correction: CORRECCION,
        },
      },
    });
    renderEstudiar();

    await userEvent.click(await screen.findByLabelText('A) 1976'));
    await userEvent.click(screen.getByRole('button', { name: 'Enviar la respuesta' }));

    expect(await screen.findByText('Respuesta guardada.')).toBeInTheDocument();
    const enviado = cuerpoJson(fetchMock, '/answers');
    expect(enviado.chosen_option_keys).toEqual(['a']);
    expect(enviado.question_version_id).toBe('q-1');
  });

  it('deja una pregunta en blanco sin marcar nada', async () => {
    const fetchMock = stubEstudio({
      '/api/v1/study-sessions?limit=50&offset=0&opposition_id=op-1': conSesion(SESION),
      '/api/v1/study-sessions/ses-1/answers': {
        status: 201,
        body: {
          saved: true,
          already_answered: false,
          attempt: {
            id: 'att-1',
            session_question_id: 'sq-1',
            question_version_id: 'q-1',
            chosen_option_keys: [],
            elapsed_ms: 0,
            confidence: null,
            client_sequence: null,
            answered_at: '2026-09-17T12:05:00Z',
            outcome: 'blank',
            score: { numerator: 0, denominator: 1, fraction: '0', decimal: '0.0000' },
            reason: null,
          },
          session: { ...SESION, answered_questions: 1 },
          correction: {
            outcome: 'blank' as const,
            correct_option_keys: ['b'],
            score: { numerator: 0, denominator: 1, fraction: '0', decimal: '0.0000' },
            reason: null,
            explanation: null,
            evidence: [],
          },
        },
      },
    });
    renderEstudiar();

    await userEvent.click(await screen.findByRole('button', { name: 'Dejar la pregunta en blanco' }));

    await waitFor(() => {
      expect(cuerpoJson(fetchMock, '/answers').chosen_option_keys).toEqual([]);
    });
  });

  it('explica el 409 al reenviar una respuesta distinta y dice que nada cambió', async () => {
    stubEstudio({
      '/api/v1/study-sessions?limit=50&offset=0&opposition_id=op-1': conSesion(SESION),
      '/api/v1/study-sessions/ses-1/answers': {
        status: 409,
        contentType: 'application/problem+json',
        body: {
          title: 'Conflict',
          status: 409,
          detail: 'esa pregunta ya está respondida y el intento no se reescribe',
          code: 'attempt_frozen',
        },
      },
    });
    renderEstudiar();

    await userEvent.click(await screen.findByLabelText('B) 1978'));
    await userEvent.click(screen.getByRole('button', { name: 'Enviar la respuesta' }));

    expect(
      await screen.findByText(/esa pregunta ya está respondida y el intento no se reescribe/),
    ).toBeInTheDocument();
    expect(screen.getByText(/Nada ha cambiado: la sesión sigue como estaba/)).toBeInTheDocument();
  });

  it('navega con el servidor: siguiente y anterior son peticiones, no estado local', async () => {
    const fetchMock = stubEstudio({
      '/api/v1/study-sessions?limit=50&offset=0&opposition_id=op-1': conSesion(SESION),
      '/api/v1/study-sessions/ses-1/navigate': {
        body: { ...ACTUAL, question: { ...PREGUNTA, position: 2 } },
      },
    });
    renderEstudiar();

    await userEvent.click(await screen.findByRole('button', { name: 'Ir a la pregunta siguiente' }));

    await waitFor(() => {
      expect(cuerpoJson(fetchMock, '/navigate').direction).toBe('next');
    });
  });

  it('al recargar retoma la sesión en marcha sin perder lo respondido', async () => {
    stubEstudio({
      '/api/v1/study-sessions?limit=50&offset=0&opposition_id=op-1': conSesion({
        ...SESION,
        answered_questions: 2,
      }),
    });
    renderEstudiar();

    expect(await screen.findByText(/Tienes una sesión en marcha/)).toBeInTheDocument();
    expect(screen.getByText(/2 de 3 preguntas respondidas/)).toBeInTheDocument();
    expect(await screen.findByRole('heading', { name: 'Pregunta 1' })).toBeInTheDocument();
  });
});

describe('estudiar: el resultado', () => {
  it('enseña la puntuación directa por partes y no inventa la calificación oficial', async () => {
    stubEstudio({
      '/api/v1/study-sessions?limit=50&offset=0&opposition_id=op-1': conSesion({
        ...SESION,
        status: 'finished',
        finished_at: '2026-09-17T12:30:00Z',
      }),
      '/api/v1/study-sessions/ses-1/result': { body: RESULTADO },
      '/api/v1/study-sessions/ses-1/review': { body: REVISION },
    });
    renderEstudiar();

    expect(await screen.findByRole('heading', { name: 'Resultado' })).toBeInTheDocument();
    expect(screen.getByText('1.6667 (5/3) puntos')).toBeInTheDocument();
    expect(screen.getByText('calificación oficial no disponible')).toBeInTheDocument();
    expect(screen.getByText(/no se declara aprobado ni suspenso/)).toBeInTheDocument();
    // Los recuentos salen dos veces: los de la parte y los del total (que aquí coinciden).
    expect(screen.getAllByText(/2 aciertos · 1 fallos · 1 en blanco/)).toHaveLength(2);
    expect(screen.getByText(/mínimo oficial 25, que no se aplica/)).toBeInTheDocument();
    expect(screen.getByText(/1 \(no puntúan, ni a favor ni en contra\)/)).toBeInTheDocument();

    // Y la revisión pregunta a pregunta, con lo que se marcó y la respuesta correcta.
    expect(screen.getByRole('heading', { name: 'Revisión, pregunta a pregunta' })).toBeInTheDocument();
    expect(screen.getByText(/Marcaste:/)).toBeInTheDocument();
    expect(screen.getByText('fallada')).toBeInTheDocument();
  });
});
