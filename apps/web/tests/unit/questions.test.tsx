import { fireEvent, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import type {
  AnswerKey,
  OutdatedSessions,
  Question,
  QuestionEvidence,
  QuestionImportReport,
  QuestionSet,
} from '../../src/api/questions';
import { AppShell } from '../../src/app/AppShell';
import { QuestionsPage } from '../../src/pages/QuestionsPage';
import { renderWithProviders, stubApi, type StubbedRoute } from './testUtils';

/**
 * Pantalla de Preguntas (S06) desde el comportamiento real: qué se ve del banco, qué se importa, qué
 * se rechaza con su causa, cómo se corrigen las transcripciones y qué pasa al activar una plantilla.
 *
 * Las respuestas imitan el contrato real, incluidos los 409 con su motivo.
 */

const CONJUNTO: QuestionSet = {
  id: 'set-1',
  title: 'Examen de prueba',
  set_type: 'official_exam',
  status: 'draft',
  opposition_id: 'op-1',
  convocation_version_id: null,
  model_code: 'A',
  held_at: null,
  source_document_version_id: null,
  created_at: '2026-09-17T10:00:00Z',
  question_count: 2,
  reserve_count: 1,
  incomplete_count: 1,
  key_count: 1,
  active_key_id: null,
  is_official: true,
};

const PREGUNTA: Question = {
  id: 'q-1',
  question_set_id: 'set-1',
  stable_key: 'q001',
  version_no: 1,
  stem: 'La Constitucion espanola se aprobo en:',
  question_type: 'single_choice',
  position: 1,
  status: 'complete',
  origin_type: 'official',
  is_reserve: false,
  reserve_order: null,
  source_section_id: null,
  supersedes_id: null,
  created_at: '2026-09-17T10:00:00Z',
  note: null,
  options: [
    { id: 'o-1', stable_key: 'a', label: 'A', text: '1976', position: 1 },
    { id: 'o-2', stable_key: 'b', label: 'B', text: '1978', position: 2 },
  ],
  correct_option_keys: ['b'],
  key_outcome: 'keyed',
  explanation_count: 0,
};

const CONFLICTIVA: Question = {
  ...PREGUNTA,
  id: 'q-2',
  stable_key: 'q002',
  position: 2,
  is_reserve: true,
  reserve_order: 1,
  status: 'conflicting',
  key_outcome: 'conflicting',
  stem: 'El plazo de alegaciones es de diez dias habiles.',
  options: [
    { id: 'o-3', stable_key: 'a', label: 'A', text: 'Verdadero', position: 1 },
    { id: 'o-4', stable_key: 'b', label: 'B', text: 'Falso', position: 2 },
  ],
  correct_option_keys: ['a'],
};

const EVIDENCIA: QuestionEvidence[] = [
  {
    span_id: 'span-1',
    role: 'correct',
    claim: 'Sostiene la respuesta correcta',
    status: 'accepted',
    text: 'La Constitucion espanola de 1978',
    page: 3,
    citation_label: 'Tema 1, pág. 3',
    document_version_id: 'ver-1',
    section_id: 'sec-1',
  },
];

const CLAVE: AnswerKey = {
  id: 'key-1',
  question_set_id: 'set-1',
  version_no: 1,
  status: 'draft',
  source_document_version_id: null,
  supersedes_id: null,
  published_at: null,
  approved_at: null,
  created_at: '2026-09-17T10:00:00Z',
  entries: [{ question_version_id: 'q-1', outcome: 'keyed', correct_option_keys: ['b'], notes: null }],
};

const INFORME: QuestionImportReport = {
  set_id: 'set-1',
  created: 1,
  existing: 0,
  incomplete: 0,
  with_key: 1,
  key_entries: 1,
  keys_in_conflict: 1,
  rejected: [{ row_number: 2, cause: 'no_stem', detail: 'la fila no trae enunciado' }],
  issues: [],
  duplicates: [],
  missing_columns: ['explanation'],
  ignored_columns: ['tags'],
  unmatched_positions: [40],
  model_code_detected: null,
  key_id: 'key-1',
};

/** Las sesiones del conjunto que no están corregidas con la plantilla activa (DEBT-013). */
const DESACTUALIZADAS: OutdatedSessions = {
  question_set_id: 'set-1',
  key_version: 1,
  key_id: 'key-1',
  finished: 2,
  up_to_date: 0,
  outdated: 2,
  without_evaluation: 0,
  outdated_session_ids: ['ses-1', 'ses-2'],
  detail: 'de 2 sesión(es) terminadas, 2 no están corregidas con la plantilla v1 activa',
};

function stubQuestions(overrides: Record<string, StubbedRoute> = {}) {
  return stubApi({
    '/api/v1/oppositions': {
      body: [
        {
          id: 'op-1',
          code: 'tai-age',
          name: 'Técnico Auxiliar de Informática',
          description: null,
          active: true,
          active_convocation: null,
        },
      ],
    },
    '/api/v1/question-sets?limit=100&offset=0&opposition_id=op-1': {
      body: { sets: [CONJUNTO], total: 1, limit: 100, offset: 0 },
    },
    '/api/v1/question-sets/set-1/questions?limit=100&offset=0': {
      body: { questions: [PREGUNTA, CONFLICTIVA], total: 2, limit: 100, offset: 0 },
    },
    '/api/v1/question-sets/set-1/questions?limit=100&offset=0&status=conflicting': {
      body: { questions: [CONFLICTIVA], total: 1, limit: 100, offset: 0 },
    },
    '/api/v1/question-sets/set-1/answer-keys': { body: [CLAVE] },
    '/api/v1/question-sets/set-1/outdated-sessions': { body: DESACTUALIZADAS },
    '/api/v1/questions/q-1': { body: PREGUNTA },
    '/api/v1/questions/q-2': { body: CONFLICTIVA },
    '/api/v1/questions/q-1/evidence': { body: [] },
    '/api/v1/questions/q-2/evidence': { body: EVIDENCIA },
    ...overrides,
  });
}

function renderPreguntas() {
  return renderWithProviders(
    <AppShell>
      <QuestionsPage />
    </AppShell>,
    { route: '/preguntas' },
  );
}

/** El cuerpo JSON de la primera petición cuya URL contiene el fragmento. */
function cuerpoJson(
  fetchMock: ReturnType<typeof stubQuestions>,
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
    throw new Error(`la petición a ${fragmento} no llevaba un cuerpo JSON`);
  }
  return JSON.parse(body) as Record<string, unknown>;
}

async function abrirPregunta(posicion: number) {
  await userEvent.click(
    await screen.findByRole('button', { name: `Abrir la pregunta ${String(posicion)}` }),
  );
  return waitFor(() => screen.getByRole('heading', { name: `Pregunta ${String(posicion)}` }));
}

describe('preguntas: el banco', () => {
  it('lista el conjunto con sus recuentos y el estado de su clave', async () => {
    stubQuestions();
    renderPreguntas();

    // El conjunto llega del servidor y la pantalla lo elige sola mientras carga: se espera al
    // selector **poblado**, no a la primera pintura. En la suite entera (quince entornos jsdom en
    // paralelo) la primera opción puede tardar más que el tiempo de espera por defecto, y eso no es
    // un fallo de la pantalla.
    const selector = await screen.findByLabelText('Conjunto abierto');
    await waitFor(
      () => {
        expect(within(selector).getAllByRole('option').length).toBeGreaterThan(0);
      },
      { timeout: 15_000 },
    );
    expect(
      within(selector).getByRole('option', { name: /Examen de prueba/ }),
    ).toBeInTheDocument();
    expect(screen.getByText(/2 preguntas \(1 incompleta · 1 reserva\) · 1 plantilla/)).toBeInTheDocument();
    expect(screen.getByText('sin clave activa')).toBeInTheDocument();
  });

  it('pagina el banco con el desplazamiento en el servidor y dice en qué tramo está', async () => {
    // DEBT-011: antes solo se pedían las primeras cien y la 101 no se veía nunca.
    const fetchMock = stubQuestions({
      '/api/v1/question-sets/set-1/questions?limit=100&offset=0': {
        body: { questions: [PREGUNTA, CONFLICTIVA], total: 250, limit: 100, offset: 0 },
      },
      '/api/v1/question-sets/set-1/questions?limit=100&offset=100': {
        body: { questions: [CONFLICTIVA], total: 250, limit: 100, offset: 100 },
      },
    });
    renderPreguntas();

    expect(await screen.findByText('1–2 de 250 preguntas del conjunto')).toBeInTheDocument();
    const anterior = screen.getByRole('button', { name: 'Página anterior' });
    expect(anterior).toBeDisabled();

    await userEvent.click(screen.getByRole('button', { name: 'Página siguiente' }));

    expect(await screen.findByText('101–101 de 250 preguntas del conjunto')).toBeInTheDocument();
    expect(
      fetchMock.mock.calls.some((call) =>
        typeof call[0] === 'string' && call[0].endsWith('offset=100'),
      ),
    ).toBe(true);

    await userEvent.click(screen.getByRole('button', { name: 'Página anterior' }));
    expect(await screen.findByText('1–2 de 250 preguntas del conjunto')).toBeInTheDocument();
  });

  it('muestra las preguntas con sus badges de origen, clave y estado', async () => {
    stubQuestions();
    renderPreguntas();

    const tabla = await screen.findByRole('table', { name: /preguntas del conjunto/ });
    const fila = within(tabla).getByRole('row', { name: /La Constitucion espanola/ });
    expect(within(fila).getByText('OFICIAL')).toBeInTheDocument();
    expect(within(fila).getByText('clave: b')).toBeInTheDocument();
    expect(within(fila).getByText('completa')).toBeInTheDocument();
    expect(within(tabla).getByText('reserva 1')).toBeInTheDocument();
  });

  it('pone los conflictos arriba, no escondidos en los filtros', async () => {
    stubQuestions();
    renderPreguntas();

    const aviso = await screen.findByRole('region', { name: /Claves en conflicto/ });
    expect(aviso).toBeInTheDocument();
    expect(within(aviso).getByText(/no se pueden juntar sin decidir cuál es la buena/)).toBeInTheDocument();
  });

  it('crea un conjunto y lo deja abierto', async () => {
    const fetchMock = stubQuestions({
      '/api/v1/question-sets': {
        body: { ...CONJUNTO, id: 'set-2', title: 'Banco privado', question_count: 0 },
      },
    });
    renderPreguntas();

    await userEvent.click(await screen.findByText('Crear un conjunto'));
    await userEvent.type(screen.getByLabelText('Título'), 'Banco privado');
    await userEvent.click(screen.getByRole('button', { name: 'Crear el conjunto de preguntas' }));

    await waitFor(() => {
      const llamada = fetchMock.mock.calls.find(
        (call) => typeof call[0] === 'string' && call[0].endsWith('/api/v1/question-sets'),
      );
      expect(llamada?.[1]?.method).toBe('POST');
    });
    expect(await screen.findByText(/Conjunto «Banco privado» creado/)).toBeInTheDocument();
  });

  it('filtra por estado en el servidor', async () => {
    const fetchMock = stubQuestions();
    renderPreguntas();
    await screen.findByRole('table', { name: /preguntas del conjunto/ });

    await userEvent.selectOptions(screen.getByLabelText('Estado'), 'conflicting');

    await waitFor(() => {
      expect(
        fetchMock.mock.calls.some(
          (call) =>
            typeof call[0] === 'string' &&
            call[0].includes('/question-sets/set-1/questions') &&
            call[0].includes('status=conflicting'),
        ),
      ).toBe(true);
    });
  });
});

describe('preguntas: la ficha', () => {
  it('enseña el enunciado, sus opciones y cuál es la correcta', async () => {
    stubQuestions();
    renderPreguntas();
    await abrirPregunta(1);

    // El enunciado sale dos veces a propósito: los campos estructurados y el original, para comparar.
    expect(
      (await screen.findAllByText('La Constitucion espanola se aprobo en:')).length,
    ).toBeGreaterThan(1);
    expect(screen.getByText('1978')).toBeInTheDocument();
    expect(screen.getByText('correcta')).toBeInTheDocument();
  });

  it('dice que no hay documento de origen en lugar de inventar una cita', async () => {
    stubQuestions();
    renderPreguntas();
    await abrirPregunta(1);

    expect(
      await screen.findByText(/no tiene documento de origen adjunto/),
    ).toBeInTheDocument();
    expect(screen.getByText(/DEBT-010/)).toBeInTheDocument();
  });

  it('muestra la evidencia con su cita cuando existe', async () => {
    stubQuestions();
    renderPreguntas();
    await abrirPregunta(2);

    expect(await screen.findByText('Tema 1, pág. 3')).toBeInTheDocument();
    expect(screen.getByText('La Constitucion espanola de 1978')).toBeInTheDocument();
    expect(screen.getByText(/sostiene: Sostiene la respuesta correcta/)).toBeInTheDocument();
  });

  it('guarda la composición con el tipo y la reserva elegidos', async () => {
    const fetchMock = stubQuestions();
    renderPreguntas();
    await abrirPregunta(1);

    await userEvent.selectOptions(await screen.findByLabelText('Tipo de pregunta'), 'true_false');
    await userEvent.click(screen.getByLabelText('es reserva'));
    await userEvent.click(screen.getByRole('button', { name: 'Guardar la composición de la pregunta' }));

    await waitFor(() => {
      const enviado = cuerpoJson(fetchMock, '/api/v1/questions/q-1', 'PATCH');
      expect(enviado.question_type).toBe('true_false');
      expect(enviado.is_reserve).toBe(true);
    });
  });

  it('al cambiar de pregunta la ficha arranca con el texto de la nueva', async () => {
    stubQuestions();
    renderPreguntas();
    await abrirPregunta(1);

    const opciones = (): HTMLElement => screen.getByLabelText('Opciones corregidas (una por línea, opcional)');
    expect(await screen.findByLabelText('Enunciado corregido (opcional)')).toHaveValue('');
    expect(opciones()).toHaveValue('1976\n1978');

    await abrirPregunta(2);

    // Sin remontar la ficha, el formulario de corrección seguiría trayendo el texto de la anterior.
    await waitFor(() => {
      expect(opciones()).toHaveValue('Verdadero\nFalso');
    });
  });

  it('no deja corregir sin motivo', async () => {
    stubQuestions();
    renderPreguntas();
    await abrirPregunta(1);

    const boton = await screen.findByRole('button', { name: 'Guardar la corrección local' });
    expect(boton).toBeDisabled();
    expect(screen.getByText(/El motivo es obligatorio/)).toBeInTheDocument();

    await userEvent.type(screen.getByLabelText('Motivo (obligatorio)'), 'errata');
    expect(boton).toBeEnabled();
  });

  it('corrige con motivo y avisa de que el original no se ha tocado', async () => {
    const fetchMock = stubQuestions({
      '/api/v1/questions/q-1/local-corrections': {
        body: {
          question: {
            ...PREGUNTA,
            id: 'q-1-v2',
            version_no: 2,
            supersedes_id: 'q-1',
            note: 'errata del original',
          },
          key_id: null,
        },
      },
      '/api/v1/questions/q-1-v2': {
        body: {
          ...PREGUNTA,
          id: 'q-1-v2',
          version_no: 2,
          supersedes_id: 'q-1',
          note: 'errata del original',
        },
      },
      // La ficha salta a la versión nueva, así que también se pide su evidencia (y sin esta
      // respuesta el stub general de `q-1` devolvería la pregunta entera como si fuera evidencia).
      '/api/v1/questions/q-1-v2/evidence': { body: [] },
    });
    renderPreguntas();
    await abrirPregunta(1);

    await userEvent.type(await screen.findByLabelText('Motivo (obligatorio)'), 'errata del original');
    await userEvent.click(screen.getByRole('button', { name: 'Guardar la corrección local' }));

    expect(
      await screen.findByText(/Corrección guardada como versión 2. El original no se ha tocado/),
    ).toBeInTheDocument();
    // Se envía el motivo y **nada** más: no se toca el enunciado ni se reescriben las opciones, así
    // que el cuerpo lleva solo `note` (el contrato lee el campo ausente como «no lo cambies»).
    const enviado = cuerpoJson(fetchMock, '/local-corrections', 'POST');
    expect(enviado.note).toBe('errata del original');
    expect(enviado).not.toHaveProperty('stem');
    expect(enviado).not.toHaveProperty('options');
  });

  it('reporta una incidencia con su tipo y su detalle', async () => {
    const fetchMock = stubQuestions({
      '/api/v1/questions/q-1/report-issue': {
        body: {
          id: 'issue-1',
          question_version_id: 'q-1',
          kind: 'ambiguous',
          detail: 'no queda claro',
          status: 'open',
          created_at: '2026-09-17T10:00:00Z',
        },
      },
    });
    renderPreguntas();
    await abrirPregunta(1);

    await userEvent.selectOptions(await screen.findByLabelText('Qué pasa'), 'wrong_key');
    await userEvent.type(screen.getByLabelText('Detalle'), 'la clave deberia ser la a');
    await userEvent.click(screen.getByRole('button', { name: 'Enviar la incidencia de la pregunta' }));

    expect(await screen.findByText(/Incidencia registrada/)).toBeInTheDocument();
    expect(cuerpoJson(fetchMock, '/report-issue').kind).toBe('wrong_key');
  });
});

describe('preguntas: importar', () => {
  it('importa un CSV con su mapeo y muestra lo rechazado con su causa', async () => {
    const fetchMock = stubQuestions({
      '/api/v1/question-sets/set-1/parse': { body: INFORME },
    });
    renderPreguntas();

    await userEvent.click(await screen.findByRole('tab', { name: 'Importar' }));
    await userEvent.selectOptions(screen.getByLabelText('Qué se importa'), 'csv');
    await userEvent.clear(screen.getByLabelText('Columna del enunciado'));
    await userEvent.type(screen.getByLabelText('Columna del enunciado'), 'pregunta');
    // Pegar y no escribir: un CSV en un textarea controlado se escribe carácter a carácter muy
    // despacio, y aquí lo que se prueba es la importación, no el teclado.
    fireEvent.change(screen.getByLabelText('Contenido del CSV (con su cabecera)'), {
      target: { value: 'pregunta;option_a;option_b\nuno;dos;tres\n' },
    });
    await userEvent.click(screen.getByRole('button', { name: 'Importar en el conjunto' }));

    const tabla = await screen.findByRole('table', { name: /filas rechazadas con su causa/ });
    expect(within(tabla).getByText('no_stem')).toBeInTheDocument();
    expect(within(tabla).getByText('la fila no trae enunciado')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Descargar las filas rechazadas/ })).toBeInTheDocument();
    expect(screen.getByText(/El mapeo pedía columnas que el fichero no trae/)).toBeInTheDocument();
    expect(screen.getByText(/no se guardan/)).toBeInTheDocument();
    expect(screen.getByText(/Posiciones de la plantilla sin pregunta/)).toBeInTheDocument();

    const peticion = cuerpoJson(fetchMock, '/parse');
    expect(peticion.kind).toBe('csv');
    expect((peticion.mapping as { stem: string }).stem).toBe('pregunta');
  });

  it('importa un JSON con su kind y explica el formato que espera', async () => {
    const fetchMock = stubQuestions({
      '/api/v1/question-sets/set-1/parse': { body: INFORME },
    });
    renderPreguntas();

    await userEvent.click(await screen.findByRole('tab', { name: 'Importar' }));
    await userEvent.selectOptions(
      screen.getByLabelText('Qué se importa'),
      'preguntas de un JSON',
    );

    // El panel declara el formato en vez de dejar que se adivine.
    expect(screen.getByText(/al menos dos/)).toBeInTheDocument();

    // `userEvent.type` interpreta `{` y `[` como sintaxis de teclas: aquí se pega un texto literal.
    fireEvent.change(screen.getByLabelText(/Contenido del JSON/), {
      target: { value: '[{"stem": "uno?", "options": ["a", "b"]}]' },
    });
    await userEvent.click(screen.getByRole('button', { name: 'Importar en el conjunto' }));

    const peticion = cuerpoJson(fetchMock, '/parse');
    expect(peticion.kind).toBe('json');
    expect(peticion.mapping).toBeUndefined();
  });

  it('construye el CSV de lo rechazado solo con lo que se rechazó', async () => {
    const { rejectedRowsCsv } = await import('../../src/api/questions');
    const csv = rejectedRowsCsv([
      { row_number: 2, cause: 'no_stem', detail: 'la fila no trae "enunciado"' },
    ]);

    expect(csv.split('\n')[0]).toBe('fila,causa,detalle');
    expect(csv).toContain('2,no_stem,"la fila no trae ""enunciado"""');
  });
});

describe('preguntas: plantillas', () => {
  it('activa una plantilla con confirmación y explica que activar es aprobar', async () => {
    const fetchMock = stubQuestions({
      '/api/v1/question-sets/set-1/answer-keys/key-1/activate': {
        body: { ...CLAVE, status: 'active', approved_at: '2026-09-17T11:00:00Z' },
      },
      '/api/v1/question-sets?limit=100&offset=0&opposition_id=op-1': {
        body: {
          sets: [{ ...CONJUNTO, active_key_id: 'key-1' }],
          total: 1,
          limit: 100,
          offset: 0,
        },
      },
    });
    renderPreguntas();

    await userEvent.click(await screen.findByRole('tab', { name: 'Plantillas' }));
    await userEvent.click(screen.getByRole('button', { name: 'Activar la plantilla v1' }));

    // La confirmación lo dice con esas palabras y en negrita: activar no es un clic neutro.
    expect(screen.getByText(/¿Activar la plantilla v1\?/)).toBeInTheDocument();
    expect(screen.getByText('es aprobarla').tagName).toBe('STRONG');
    await userEvent.click(screen.getByRole('button', { name: 'Confirmar la activación de la plantilla v1' }));

    expect(await screen.findByText(/queda registrado en la auditoría/)).toBeInTheDocument();
    expect(
      fetchMock.mock.calls.some(
        (call) =>
          typeof call[0] === 'string' && call[0].includes('/answer-keys/key-1/activate'),
      ),
    ).toBe(true);
  });

  it('explica el 409 del servidor al activar y dice que nada cambió', async () => {
    stubQuestions({
      '/api/v1/question-sets/set-1/answer-keys/key-1/activate': {
        status: 409,
        contentType: 'application/problem+json',
        body: {
          type: 'about:blank',
          title: 'Conflict',
          status: 409,
          detail: 'una clave oficial necesita la plantilla oficial enlazada',
          code: 'classification_conflict',
        },
      },
    });
    renderPreguntas();

    await userEvent.click(await screen.findByRole('tab', { name: 'Plantillas' }));
    await userEvent.click(screen.getByRole('button', { name: 'Activar la plantilla v1' }));
    await userEvent.click(screen.getByRole('button', { name: 'Confirmar la activación de la plantilla v1' }));

    expect(
      await screen.findByText('una clave oficial necesita la plantilla oficial enlazada'),
    ).toBeInTheDocument();
    expect(screen.getByText(/la plantilla se queda como estaba/)).toBeInTheDocument();
  });

  it('dice cuántas sesiones quedan desactualizadas y las recalcula en bloque (DEBT-013)', async () => {
    const fetchMock = stubQuestions({
      '/api/v1/question-sets/set-1/recalculate-sessions': {
        body: {
          question_set_id: 'set-1',
          key_version: 1,
          changed: 1,
          detail: '2 sesión(es) recalculadas con la plantilla v1: 1 cambiaron de puntuación',
          sessions: [
            {
              session_id: 'ses-1',
              previous_total: '3',
              new_total: '1',
              previous_key_label: 'plantilla v1',
              new_key_label: 'plantilla v1',
              changed: true,
            },
            {
              session_id: 'ses-2',
              previous_total: '2',
              new_total: '2',
              previous_key_label: 'plantilla v1',
              new_key_label: 'plantilla v1',
              changed: false,
            },
          ],
        },
      },
    });
    renderPreguntas();

    await userEvent.click(await screen.findByRole('tab', { name: 'Plantillas' }));

    // Lo primero es el número, que es lo que antes no se podía saber sin abrir sesión a sesión.
    expect(await screen.findByText('2 sesiones desactualizadas')).toBeInTheDocument();
    expect(
      screen.getByText('de 2 sesión(es) terminadas, 2 no están corregidas con la plantilla v1 activa'),
    ).toBeInTheDocument();

    await userEvent.click(
      screen.getByRole('button', { name: 'Recalcular las 2 sesiones desactualizadas' }),
    );

    // El recálculo va al servidor **en bloque**, no sesión a sesión.
    await waitFor(() => {
      expect(
        fetchMock.mock.calls.some(
          (call) =>
            typeof call[0] === 'string' &&
            call[0].includes('/question-sets/set-1/recalculate-sessions') &&
            call[1]?.method === 'POST',
        ),
      ).toBe(true);
    });

    // Y el informe dice qué cambió en cada una, incluidas las que no cambiaron nada.
    expect(
      await screen.findByText(/2 sesión\(es\) recalculadas con la plantilla v1/),
    ).toBeInTheDocument();
    expect(screen.getByText(/de 3 a 1/)).toBeInTheDocument();
    expect(screen.getByText(/sin cambios \(2\)/)).toBeInTheDocument();
  });

  it('con todas las sesiones al día no ofrece recalcular nada', async () => {
    stubQuestions({
      '/api/v1/question-sets/set-1/outdated-sessions': {
        body: {
          ...DESACTUALIZADAS,
          up_to_date: 2,
          outdated: 0,
          outdated_session_ids: [],
          detail: 'de 2 sesión(es) terminadas, 0 no están corregidas con la plantilla v1 activa',
        },
      },
    });
    renderPreguntas();

    await userEvent.click(await screen.findByRole('tab', { name: 'Plantillas' }));

    expect(await screen.findByText('0 sesiones desactualizadas')).toBeInTheDocument();
    // Un botón para recalcular cero sesiones no es una acción: no se enseña.
    expect(screen.queryByRole('button', { name: /Recalcular las/ })).not.toBeInTheDocument();
  });

  it('si no se puede contar cuántas quedan atrás, lo dice en lugar de callarse', async () => {
    stubQuestions({
      '/api/v1/question-sets/set-1/outdated-sessions': {
        status: 500,
        contentType: 'application/problem+json',
        body: {
          type: 'about:blank',
          title: 'Internal Server Error',
          status: 500,
          detail: 'la base de datos no responde',
          code: 'internal_error',
        },
      },
    });
    renderPreguntas();

    await userEvent.click(await screen.findByRole('tab', { name: 'Plantillas' }));

    expect(await screen.findByText(/No se ha podido contar cuántas sesiones/)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Recalcular las/ })).not.toBeInTheDocument();
  });
});
