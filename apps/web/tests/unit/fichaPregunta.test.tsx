/**
 * La ficha de pregunta (F20, §4.2 del objetivo: el bloque C del panel).
 *
 * Lo que se comprueba, y es lo que el propietario necesita de esta pantalla:
 *
 * 1. **se ve qué se está estudiando**: el enunciado, las opciones con su letra y **cuál está marcada
 *    hoy** como respuesta correcta;
 * 2. **se ve con qué garantía**: qué plantilla la da, de qué material salió y en qué estado está esa
 *    versión del material, más el veredicto de fiabilidad del banco. Si no consta, se dice en vez de
 *    inventarse un veredicto;
 * 3. **se ve qué dicen los apuntes**: la letra que contestan, la frase que lo demuestra y el enlace
 *    al apartado exacto;
 * 4. **se ve lo que ha señalado el sistema**, con su categoría;
 * 5. **se puede marcar la respuesta correcta**: la elección se manda a la ruta auditada con la nota, y
 *    la pantalla dice qué letra había antes y que se conserva;
 * 6. **una respuesta correcta oficial no se cambia**: con el banco protegido no hay botón, y el
 *    motivo del servidor se enseña con la lista de bancos protegidos;
 * 7. **se puede reparar** lo que una regla pueda arreglar, con el motivo obligatorio, y **no** se
 *    ofrece reparación cuando no la hay: en su lugar se dice por qué;
 * 8. **el historial enseña las dos cosas**: las vistas de la pregunta y las listas de respuestas del
 *    banco con lo que cada una decía de esta pregunta.
 */

import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import type { QuestionFile } from '../../src/api/questionFile';
import { AppRoutes } from '../../src/app/routes';
import { QuestionFilePage } from '../../src/pages/QuestionFilePage';
import { renderWithProviders, stubApi } from './testUtils';

const PREGUNTA = 'pregunta-1';

/** La ficha de una pregunta con una incidencia de clave: el caso de uso de la pantalla. */
const FICHA: QuestionFile = {
  question_version_id: PREGUNTA,
  question_set_id: 'banco-1',
  set_title: 'TAI · Test por temas (respuestas marcadas en el material)',
  set_type: 'private_bank',
  set_distribution: 'personal',
  stable_key: 'q030',
  version_no: 2,
  position: 30,
  question_type: 'single_choice',
  status: 'complete',
  origin_type: 'private',
  is_reserve: false,
  reserve_order: null,
  created_at: '2026-10-13T10:00:00Z',
  note: 'la extracción fundió dos opciones en una',
  stem: 'Las Cámaras se reunirán anualmente:',
  options: [
    {
      stable_key: 'a',
      position: 1,
      text: 'En dos periodos ordinarios de sesiones, conforme a lo indicado en la opción c).',
      label: 'A',
    },
    {
      stable_key: 'b',
      position: 2,
      text: 'En un solo periodo ordinario de sesiones, de septiembre a junio.',
      label: 'B',
    },
    {
      stable_key: 'c',
      position: 3,
      text: 'En dos periodos ordinarios, el primero de septiembre a diciembre.',
      label: 'C',
    },
    {
      stable_key: 'd',
      position: 4,
      text: 'En dos periodos ordinarios, el primero de septiembre a enero.',
      label: 'D',
    },
  ],
  key: {
    answer_key_version_id: 'lista-3',
    version_no: 3,
    status: 'active',
    outcome: 'keyed',
    correct_option_keys: ['a'],
    approved_at: '2026-10-12T09:00:00Z',
    published_at: null,
    source_document_id: 'documento-1',
    source_document_title: 'Plantilla respuestas TAI-L-A_act.pdf',
    source_document_type: 'answer_key',
    source_version_label: 'definitiva',
    source_version_status: 'accepted',
    notes: null,
  },
  key_reliability: 'dudosa',
  reliability_source: 'la columna question_sets.key_reliability (§1)',
  notes: [
    {
      answer_letter: 'c',
      expected_letters: ['a'],
      result: 'doubtful',
      phrase: 'las Cámaras se reúnen en dos periodos ordinarios, de septiembre a diciembre y de febrero a junio',
      anchor: 'cortes-generales',
      section_title: 'Las Cortes Generales',
      topic_code: 'I.2',
      topic_title: 'Las Cortes Generales',
      key_status: 'active',
      checked_at: '2026-10-12T10:00:00Z',
      coincides: false,
    },
  ],
  incidents: [
    {
      id: 'incidencia-1',
      category: 'clave_sospechosa',
      reason: 'letra_no_coincide',
      status: 'open',
      coverage: 'conflict',
      detail: 'la clave contradice los apuntes',
      phrase: 'las Cámaras se reúnen en dos periodos ordinarios',
      topic_code: 'I.2',
      topic_title: 'Las Cortes Generales',
      resolution_note: null,
      reviewed_at: null,
    },
  ],
  exclusion: null,
  protection: { protected: false, reason: null, sets: [] },
  repair: {
    reglas: [],
    titulos: [],
    detalle: '',
    stem: null,
    opciones: null,
    por_que_no:
      'la opción nombra a otra opción («… en la opción c)») y eso no es una fusión: la pregunta está bien escrita y lo que falla es la regla mecánica',
  },
  versions: [
    {
      id: PREGUNTA,
      version_no: 2,
      status: 'complete',
      stem: 'Las Cámaras se reunirán anualmente:',
      note: 'la extracción fundió dos opciones en una',
      created_at: '2026-10-13T10:00:00Z',
      option_count: 4,
      correct_option_keys: ['a'],
    },
    {
      id: 'pregunta-0',
      version_no: 1,
      status: 'superseded',
      stem: 'Las Cámaras se reunirán anualmente (versión de la extracción):',
      note: null,
      created_at: '2026-10-01T10:00:00Z',
      option_count: 4,
      correct_option_keys: [],
    },
  ],
  keys: [
    {
      id: 'lista-3',
      version_no: 3,
      status: 'active',
      approved_at: '2026-10-12T09:00:00Z',
      created_at: '2026-10-12T09:00:00Z',
      source_document_title: 'Plantilla respuestas TAI-L-A_act.pdf',
      correct_option_keys: ['a'],
    },
    {
      id: 'lista-2',
      version_no: 2,
      status: 'superseded',
      approved_at: '2026-09-30T09:00:00Z',
      created_at: '2026-09-30T09:00:00Z',
      source_document_title: 'Plantilla respuestas TAI-L-A_act.pdf',
      correct_option_keys: ['c'],
    },
    {
      id: 'lista-1',
      version_no: 1,
      status: 'superseded',
      approved_at: null,
      created_at: '2026-09-01T09:00:00Z',
      source_document_title: null,
      correct_option_keys: [],
    },
  ],
  superseded_by: null,
};

function montar(cuerpo: QuestionFile = FICHA, ruta = `/admin/preguntas?pregunta=${PREGUNTA}`) {
  const fetchMock = stubApi({
    'POST /api/v1/question-files/': {
      body: {
        file: cuerpo,
        key_version_id: 'lista-4',
        superseded_key_version_id: 'lista-3',
        previous_option_keys: ['a'],
        correct_option_keys: ['c'],
        actor: 'local',
      },
    },
    '/api/v1/question-files/': { body: cuerpo },
  });
  renderWithProviders(<QuestionFilePage />, { route: ruta });
  return fetchMock;
}

describe('la ficha de pregunta', () => {
  it('enseña el enunciado, las opciones y cuál está marcada como correcta', async () => {
    montar();

    expect(await screen.findByText('Las Cámaras se reunirán anualmente:')).toBeDefined();
    const opciones = screen.getAllByRole('listitem').filter((fila) =>
      fila.className.includes('resultado__opcion'),
    );
    expect(opciones).toHaveLength(4);
    expect(opciones[0]!.className).toContain('resultado__opcion--correcta');
    expect(within(opciones[0]!).getByText('respuesta correcta')).toBeDefined();
    expect(opciones[2]!.className).not.toContain('resultado__opcion--correcta');
  });

  it('dice de dónde sale la respuesta correcta y con qué garantía se estudia el banco', async () => {
    montar();

    expect(await screen.findByText('De dónde sale la respuesta correcta')).toBeDefined();
    expect(screen.getByText(/vista 3 de la lista de respuestas del banco/)).toBeDefined();
    // El material sale dos veces —en la procedencia y en el historial de la lista— y las dos valen:
    // es el mismo documento, y el historial dice cuál lo traía.
    expect(screen.getAllByText('Plantilla respuestas TAI-L-A_act.pdf').length).toBeGreaterThan(0);
    expect(screen.getByText(/definitiva · aceptada/)).toBeDefined();
    expect(screen.getByText('en duda')).toBeDefined();
    expect(
      screen.getByText(/Entre el 15 % y el 30 % de las respuestas de este banco/),
    ).toBeDefined();
  });

  it('dice que la fiabilidad no consta en vez de inventarse un veredicto', async () => {
    montar({
      ...FICHA,
      key_reliability: null,
      reliability_source:
        'la columna question_sets.key_reliability todavía no existe en esta base: la mantiene la puerta de datos del §1 y aquí no se recalcula',
    });

    expect(await screen.findByText(/todavía no existe en esta base/)).toBeDefined();
  });

  it('enseña la letra de los apuntes, su frase y el enlace al apartado', async () => {
    montar();

    expect(await screen.findByText('Qué dicen los apuntes')).toBeDefined();
    expect(screen.getByText(/Los apuntes contestan con la letra/)).toBeDefined();
    expect(
      screen.getByText(
        'las Cámaras se reúnen en dos periodos ordinarios, de septiembre a diciembre y de febrero a junio',
      ),
    ).toBeDefined();
    const enlace = screen.getByRole('link', { name: 'Ver el apartado' });
    expect(enlace.getAttribute('href')).toBe('/temario/I.2#apartado-cortes-generales');
  });

  it('enseña la incidencia que ha señalado el sistema con su categoría', async () => {
    montar();

    expect(await screen.findByText('Lo que ha señalado el sistema')).toBeDefined();
    expect(screen.getByText('Clave sospechosa')).toBeDefined();
    expect(screen.getByText('Pendiente')).toBeDefined();
  });

  it('marca la respuesta correcta por la ruta auditada y dice qué había antes', async () => {
    const fetchMock = montar();
    const usuario = userEvent.setup();

    await screen.findByText('Marcar la respuesta correcta');
    // La tercera opción es la `C`: las letras van en el orden de las opciones.
    await usuario.click(screen.getAllByRole('radio')[2]!);
    await usuario.type(
      screen.getByLabelText('Por qué (opcional)'),
      'los apuntes lo contestan en dos periodos',
    );
    await usuario.click(screen.getByRole('button', { name: 'Guardar la respuesta correcta' }));

    await waitFor(() => {
      expect(screen.getByText(/Respuesta correcta guardada/)).toBeDefined();
    });
    const llamada = fetchMock.mock.calls.find(
      ([, init]) => (init?.method ?? 'GET').toUpperCase() === 'POST',
    );
    expect(llamada).toBeDefined();
    const bruto = llamada?.[1]?.body;
    const cuerpo = JSON.parse(typeof bruto === 'string' ? bruto : '{}') as {
      correct_option_keys: string[];
      note: string;
    };
    expect(cuerpo.correct_option_keys).toEqual(['c']);
    expect(cuerpo.note).toBe('los apuntes lo contestan en dos periodos');
  });

  it('no deja marcar cuando el banco es un examen oficial, y dice por qué', async () => {
    montar({
      ...FICHA,
      protection: {
        protected: true,
        reason:
          'el conjunto es un examen oficial: su respuesta correcta es la que publicó la administración y no se cambia desde aquí',
        sets: [
          {
            id: 'banco-1',
            title: 'TAI ingreso libre 2025 · modelo A (examen oficial INAP)',
            set_type: 'official_exam',
            source_document_title: 'Plantilla respuestas TAI-L-A_act.pdf',
            reason:
              'el conjunto es un examen oficial: su respuesta correcta es la que publicó la administración y no se cambia desde aquí',
          },
        ],
      },
    });

    expect(await screen.findByText('Marcar la respuesta correcta')).toBeDefined();
    // No hay botón: no es que esté apagado, es que no se puede. El motivo va con la lista.
    expect(screen.queryByRole('button', { name: 'Guardar la respuesta correcta' })).toBeNull();
    expect(screen.queryAllByRole('radio')).toHaveLength(0);
    expect(screen.getAllByText(/es un examen oficial/).length).toBeGreaterThan(0);
    expect(screen.getByText(/Qué bancos están protegidos y por qué \(1\)/)).toBeDefined();
  });

  it('repara lo que una regla puede y exige el motivo', async () => {
    montar({
      ...FICHA,
      repair: {
        reglas: ['quitar_referencia_del_examen'],
        titulos: ['Quitar la referencia del examen'],
        detalle: 'se quita del enunciado la referencia del examen que quedó pegada al final',
        stem: 'Las Cámaras se reunirán anualmente:',
        opciones: null,
        por_que_no: null,
      },
    });
    const usuario = userEvent.setup();

    expect(await screen.findByText('Quitar la referencia del examen')).toBeDefined();
    const boton = screen.getByRole('button', { name: 'Reparar el texto de la pregunta' });
    expect(boton).toBeDisabled();

    await usuario.type(
      screen.getByLabelText('Por qué se repara (obligatorio)'),
      'la referencia del examen quedó pegada',
    );
    expect(boton).toBeEnabled();
  });

  it('cuando no hay reparación posible dice por qué, sin ofrecer el botón', async () => {
    montar();

    expect(await screen.findByText('Reparar el texto importado')).toBeDefined();
    expect(screen.getByText(/nombra a otra opción/)).toBeDefined();
    expect(
      screen.queryByRole('button', { name: 'Reparar el texto de la pregunta' }),
    ).toBeNull();
  });

  it('el historial enseña las vistas de la pregunta y las listas de respuestas', async () => {
    montar();

    expect(await screen.findByText('Historial')).toBeDefined();
    // El motivo del cambio sale dos veces —bajo el enunciado y en la fila del historial— y las dos
    // son el mismo dato: lo que se anotó al corregirla.
    expect(
      screen.getAllByText('la extracción fundió dos opciones en una').length,
    ).toBeGreaterThan(0);
    // La lista anterior decía `C` y se conserva: es lo que hace comprobable que no se pisa.
    const filas = screen.getAllByRole('row');
    const conC = filas.filter((fila) => within(fila).queryByText('C') !== null);
    expect(conC.length).toBeGreaterThan(0);
    // La vista 1 de la pregunta y las dos listas de respuestas anteriores están sustituidas: el
    // historial lo dice con la misma palabra en los dos casos, y las dos veces es verdad.
    expect(screen.getAllByText('sustituida').length).toBeGreaterThanOrEqual(3);
  });

  it('avisa cuando la vista que se está mirando está sustituida', async () => {
    montar({ ...FICHA, superseded_by: 'pregunta-2' });

    expect(await screen.findByText('Esta vista está sustituida')).toBeDefined();
    const enlace = screen.getByRole('link', { name: 'Abrir la vista que manda' });
    expect(enlace.getAttribute('href')).toBe('/admin/preguntas?pregunta=pregunta-2');
  });

  it('sin pregunta en la dirección lo dice en vez de quedarse en blanco', async () => {
    stubApi({});
    renderWithProviders(<QuestionFilePage />, { route: '/admin/preguntas' });

    expect(await screen.findByText('Falta la pregunta')).toBeDefined();
  });

  it('la dirección que la bandeja ya enlazaba abre la ficha, no la tabla del banco', async () => {
    // Se monta **el árbol de direcciones entero**: es lo que comprueba que
    // `/admin/preguntas?pregunta=<id>` —el enlace que la bandeja del motor usa desde F18— lleva a la
    // ficha, y que sin la consulta la dirección sigue siendo el banco de preguntas.
    stubApi({ '/api/v1/question-files/': { body: FICHA } });
    renderWithProviders(<AppRoutes />, { route: `/admin/preguntas?pregunta=${PREGUNTA}` });

    expect(
      await screen.findByRole('heading', { level: 1, name: 'Ficha de la pregunta' }),
    ).toBeDefined();
    expect(screen.queryByRole('heading', { level: 1, name: 'Preguntas' })).toBeNull();
  });
});
