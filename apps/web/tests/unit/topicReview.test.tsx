import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import type {
  ConflictCard,
  TopicAssignmentReport,
  TopicProposalCard,
  Exclusion,
} from '../../src/api/topicReview';
import { AdminShell } from '../../src/app/AdminShell';
import { TopicReviewPage } from '../../src/pages/TopicReviewPage';
import { curriculumFixture, oppositionsFixture, renderWithProviders, stubApi } from './testUtils';

/**
 * La pantalla de Clasificación (F5) desde el comportamiento real: qué se ve, qué se manda al
 * teclado y qué se guarda en una sola llamada.
 *
 * Lo que se defiende aquí es lo que hace utilizable la cola: una tarjeta por pregunta, el teclado de
 * verdad, las decisiones acumuladas y el lote que las escribe de una vez.
 */

const TEMA_UNO = 'node-i-1';
const TEMA_DOS = 'node-i-2';
const EPIGRAFE_UNO = 'node-i-1-1';

/** Un programa con un tema con epígrafe y otro sin él: los dos casos existen en TAI. */
const programaConEpigrafe = {
  ...curriculumFixture,
  nodes: [
    {
      ...curriculumFixture.nodes[0]!,
      children: [
        { ...curriculumFixture.nodes[0]!.children[0]!, children: [] },
        {
          ...curriculumFixture.nodes[0]!.children[1]!,
          children: [
            {
              id: EPIGRAFE_UNO,
              node_type: 'epigraph' as const,
              official_code: '1',
              title: 'La soberanía nacional',
              description: null,
              position: 1,
              path: 'I.1.1',
              depth: 2,
              children: [],
            },
          ],
        },
      ],
    },
  ],
};

const tarjetaDudosa: TopicProposalCard = {
  question_version_id: 'q-1',
  question_set_id: 'set-1',
  set_title: 'Exámenes TAI',
  stem: '¿Quién es el jefe del Estado?',
  options: [
    { id: 'o-1', stable_key: 'a', label: 'a', text: 'El Rey', position: 1 },
    { id: 'o-2', stable_key: 'b', label: 'b', text: 'El Presidente', position: 2 },
  ],
  accepted: null,
  proposals: [
    {
      mapping_id: 'map-1',
      topic: { node_id: TEMA_UNO, official_code: '1', path: 'I.1', title: 'La Constitución' },
      epigraphs: [{ node_id: EPIGRAFE_UNO, official_code: '1', path: 'I.1.1', title: 'La soberanía nacional' }],
      confidence: 0.6,
      reason: 'el modelo dudaba entre la Corona y el Gobierno',
      created_at: '2026-10-08T11:15:00Z',
    },
  ],
};

/** La misma pregunta con **dos** propuestas: dos corridas que se pisaron. */
const tarjetaConDosPropuestas: TopicProposalCard = {
  ...tarjetaDudosa,
  question_version_id: 'q-2',
  stem: '¿Cuánto dura el mandato del Rey?',
  proposals: [
    tarjetaDudosa.proposals[0]!,
    {
      mapping_id: 'map-2',
      topic: { node_id: TEMA_DOS, official_code: '2', path: 'I.2', title: 'Las Cortes Generales' },
      epigraphs: [],
      confidence: 0.7,
      reason: 'de otra corrida',
      created_at: '2026-10-08T11:16:00Z',
    },
  ],
};

/** Una pregunta que ya tiene tema aceptado y arrastra una propuesta que sobra. */
const tarjetaConTemaAceptado: TopicProposalCard = {
  ...tarjetaDudosa,
  question_version_id: 'q-3',
  stem: '¿Cuándo se aprobó la Constitución?',
  accepted: { node_id: TEMA_UNO, official_code: '1', path: 'I.1', title: 'La Constitución' },
  proposals: [
    {
      mapping_id: 'map-3',
      topic: { node_id: TEMA_DOS, official_code: '2', path: 'I.2', title: 'Las Cortes Generales' },
      epigraphs: [],
      confidence: 0.55,
      reason: 'de otra corrida',
      created_at: '2026-10-08T11:17:00Z',
    },
  ],
};

const marcaFueraDeTemario: Exclusion = {
  question_version_id: 'q-9',
  reason: 'enunciado_roto',
  actor: 'llm:deepseek-flash',
  note: 'las opciones están incompletas',
  created_at: '2026-10-08T11:21:00Z',
  stem: 'En LINUX, ¿qué orden se utiliza para crear directorios?',
};

/** Una pregunta que cuenta en dos temas a la vez: lo que quedó torcido antes de esta tanda. */
const conflicto: ConflictCard = {
  question_version_id: 'q-8',
  question_set_id: 'set-9',
  set_title: 'TAI ingreso libre 2025 · modelo A (examen oficial INAP)',
  stem: 'En el formato de ficheros CSV, descrito en RFC 4180, ¿qué regla es correcta?',
  options: [
    { id: 'o-8', stable_key: 'a', label: 'a', text: 'Los campos van separados por comas', position: 1 },
  ],
  topics: [
    {
      mapping_id: 'map-8a',
      topic: { node_id: TEMA_UNO, official_code: '1', path: 'I.3', title: 'La Constitución' },
      confidence: 1,
      actor: 'local',
      created_at: '2026-09-01T09:00:00Z',
    },
    {
      mapping_id: 'map-8b',
      topic: { node_id: TEMA_DOS, official_code: '2', path: 'II.3', title: 'Las Cortes Generales' },
      confidence: 1,
      actor: 'llm:deepseek-flash',
      created_at: '2026-10-08T11:15:00Z',
    },
  ],
};

const lote: TopicAssignmentReport = {
  results: [],
  created: 0,
  existing: 0,
  promoted: 2,
  excluded: 1,
  already_excluded: 0,
  errors: 0,
};

function montar(
  tarjetas: TopicProposalCard[],
  {
    marcadas = [],
    conflictos = [],
  }: { marcadas?: Exclusion[]; conflictos?: ConflictCard[] } = {},
) {
  const fetchMock = stubApi({
    '/api/v1/oppositions': { body: oppositionsFixture },
    '/api/v1/convocations/conv-tai/curriculum': { body: programaConEpigrafe },
    '/api/v1/question-topic-proposals': {
      body: { questions: tarjetas, total: tarjetas.length, limit: 50, offset: 0 },
    },
    '/api/v1/question-exclusions': {
      body: { exclusions: marcadas, total: marcadas.length, limit: 100, offset: 0 },
    },
    '/api/v1/question-topic-conflicts': {
      body: { questions: conflictos, total: conflictos.length, limit: 100, offset: 0 },
    },
    'POST /api/v1/questions/topics/bulk': { body: lote },
  });
  renderWithProviders(
    <AdminShell>
      <TopicReviewPage />
    </AdminShell>,
    { route: '/admin/clasificacion' },
  );
  return fetchMock;
}

/** Las filas que se han mandado de verdad a la ruta por lotes, en orden. */
function filasEnviadas(fetchMock: ReturnType<typeof stubApi>) {
  return fetchMock.mock.calls
    .filter(([url, init]) => {
      const direccion = typeof url === 'string' ? url : url instanceof URL ? url.href : url.url;
      return direccion.includes('/questions/topics/bulk') && init?.method === 'POST';
    })
    .map(([, init]) => {
      const cuerpo = init?.body;
      return JSON.parse(typeof cuerpo === 'string' ? cuerpo : '{}') as {
        assignments: Record<string, unknown>[];
      };
    })
    .flatMap((cuerpo) => cuerpo.assignments);
}

describe('la cola de clasificación', () => {
  it('enseña una tarjeta por pregunta con el enunciado, sus opciones, el tema y el motivo', async () => {
    montar([tarjetaDudosa]);

    await screen.findByText('¿Quién es el jefe del Estado?');
    const cola = screen.getByRole('region', { name: /Propuestas pendientes/ });
    expect(within(cola).getByText('¿Quién es el jefe del Estado?')).toBeInTheDocument();
    expect(within(cola).getByText(/El Rey/)).toBeInTheDocument();
    expect(within(cola).getByText('I.1')).toBeInTheDocument();
    expect(within(cola).getByText(/La Constitución$/)).toBeInTheDocument();
    expect(within(cola).getByText(/Epígrafes propuestos: I\.1\.1 · La soberanía nacional/)).toBeInTheDocument();
    expect(within(cola).getByText(/60 % de confianza/)).toBeInTheDocument();
    expect(
      within(cola).getByText(/el modelo dudaba entre la Corona y el Gobierno/),
    ).toBeInTheDocument();
    // Y los atajos, en pantalla: el propietario no tiene que aprendérselos de memoria.
    expect(within(document.body).getByText('aceptar la propuesta elegida')).toBeInTheDocument();
  });

  it('acepta con A y guarda con G en una sola llamada, no una por pregunta', async () => {
    const usuario = userEvent.setup();
    const fetchMock = montar([tarjetaDudosa, tarjetaConDosPropuestas]);

    await screen.findByText('¿Quién es el jefe del Estado?');
    await usuario.keyboard('a');
    await usuario.keyboard('a');
    // Todavía no se ha escrito nada: las decisiones están en la bandeja.
    expect(filasEnviadas(fetchMock)).toHaveLength(0);
    const cola = screen.getByRole('region', { name: /Propuestas pendientes/ });
    expect(within(cola).getByText(/sin guardar/)).toHaveTextContent('2 decisión(es) sin guardar');

    await usuario.keyboard('g');

    await waitFor(() => {
      expect(filasEnviadas(fetchMock)).toHaveLength(2);
    });
    expect(filasEnviadas(fetchMock)[0]).toMatchObject({
      question_version_id: 'q-1',
      curriculum_node_id: TEMA_UNO,
      status: 'accepted',
      retire_others: true,
    });
    // La segunda pregunta también trae su epígrafe propuesto: se escribe con el tema.
    expect(filasEnviadas(fetchMock)[1]).toMatchObject({
      question_version_id: 'q-2',
      curriculum_node_id: TEMA_UNO,
      epigraph_node_id: EPIGRAFE_UNO,
    });
  });

  it('marca fuera de temario con F y con X, con el motivo que decide el servidor', async () => {
    const usuario = userEvent.setup();
    const fetchMock = montar([tarjetaDudosa, tarjetaConDosPropuestas]);

    await screen.findByText('¿Quién es el jefe del Estado?');
    await usuario.keyboard('f');
    await usuario.keyboard('x');
    await usuario.keyboard('g');

    await waitFor(() => {
      expect(filasEnviadas(fetchMock)).toHaveLength(2);
    });
    expect(filasEnviadas(fetchMock)[0]).toMatchObject({
      exclusion_reason: 'otra_administracion',
      retire_others: true,
    });
    expect(filasEnviadas(fetchMock)[1]).toMatchObject({
      exclusion_reason: 'enunciado_roto',
    });
  });

  it('con dos propuestas, el número elige la segunda y se acepta esa', async () => {
    const usuario = userEvent.setup();
    const fetchMock = montar([tarjetaConDosPropuestas]);

    await screen.findByText('¿Cuánto dura el mandato del Rey?');
    await usuario.keyboard('2');
    await usuario.keyboard('a');
    await usuario.keyboard('g');

    await waitFor(() => {
      expect(filasEnviadas(fetchMock)).toHaveLength(1);
    });
    expect(filasEnviadas(fetchMock)[0]).toMatchObject({
      question_version_id: 'q-2',
      curriculum_node_id: TEMA_DOS,
    });
  });

  it('una pregunta con tema aceptado avisa, y R retira lo que sobra', async () => {
    const usuario = userEvent.setup();
    const fetchMock = montar([tarjetaConTemaAceptado]);

    await screen.findByText('¿Cuándo se aprobó la Constitución?');
    expect(screen.getByText(/Ya tiene tema decidido:/)).toBeInTheDocument();
    // Con tema decidido, `A` no elige nada: lo que toca es retirar las propuestas que sobran.
    await usuario.keyboard('a');
    expect(screen.queryByText(/sin guardar/)).not.toBeInTheDocument();

    await usuario.keyboard('r');
    await usuario.keyboard('g');

    await waitFor(() => {
      expect(filasEnviadas(fetchMock)).toHaveLength(1);
    });
    expect(filasEnviadas(fetchMock)[0]).toMatchObject({
      question_version_id: 'q-3',
      curriculum_node_id: TEMA_UNO,
      status: 'accepted',
      retire_others: true,
    });
  });

  it('cambiar de tema se hace con el selector y se manda con su epígrafe', async () => {
    const usuario = userEvent.setup();
    const fetchMock = montar([tarjetaDudosa]);

    await screen.findByText('¿Quién es el jefe del Estado?');
    await usuario.keyboard('c');

    const tema = screen.getByLabelText('Tema');
    await usuario.selectOptions(tema, TEMA_DOS);
    await usuario.click(screen.getByRole('button', { name: 'Aplicar el cambio' }));
    await usuario.keyboard('g');

    await waitFor(() => {
      expect(filasEnviadas(fetchMock)).toHaveLength(1);
    });
    expect(filasEnviadas(fetchMock)[0]).toMatchObject({
      question_version_id: 'q-1',
      curriculum_node_id: TEMA_DOS,
      status: 'accepted',
      retire_others: true,
    });
    expect(String(filasEnviadas(fetchMock)[0]?.reason)).toContain('cambiada a mano');
  });

  it('encadena decisiones sin saltarse ninguna pregunta: al decidir una, la siguiente ocupa su sitio', async () => {
    const usuario = userEvent.setup();
    const tercera: TopicProposalCard = {
      ...tarjetaDudosa,
      question_version_id: 'q-4',
      stem: '¿Qué es la Corona?',
      proposals: [{ ...tarjetaDudosa.proposals[0]!, mapping_id: 'map-4' }],
    };
    const fetchMock = montar([tarjetaDudosa, tarjetaConDosPropuestas, tercera]);

    await screen.findByText('¿Quién es el jefe del Estado?');
    // Se decide la primera y la segunda **sin tocar el ratón ni el cursor**: la siguiente ocupa el
    // sitio de la decidida, así que con dos pulsaciones se despachan las dos primeras.
    await usuario.keyboard('a');
    expect(screen.getByRole('listitem', { current: true })).toHaveTextContent(
      '¿Cuánto dura el mandato del Rey?',
    );
    await usuario.keyboard('a');
    await usuario.keyboard('g');

    await waitFor(() => {
      expect(filasEnviadas(fetchMock)).toHaveLength(2);
    });
    expect(filasEnviadas(fetchMock).map((fila) => fila.question_version_id)).toEqual(['q-1', 'q-2']);
  });

  it('las marcas de fuera de temario se leen con su enunciado y se deshacen asignando un tema', async () => {
    const usuario = userEvent.setup();
    const fetchMock = montar([], { marcadas: [marcaFueraDeTemario] });

    const seccion = await screen.findByRole('region', { name: 'Fuera de temario' });
    expect(await within(seccion).findByText(/En LINUX, ¿qué orden se utiliza/)).toBeInTheDocument();
    expect(within(seccion).getByText('Enunciado roto')).toBeInTheDocument();
    expect(within(seccion).getByText(/las opciones están incompletas/)).toBeInTheDocument();

    await usuario.selectOptions(
      within(seccion).getByLabelText('Tema'),
      await within(seccion).findByRole('option', { name: /I\.1 · / }),
    );
    await usuario.click(within(seccion).getByRole('button', { name: 'Asignar y levantar la marca' }));

    await waitFor(() => {
      expect(filasEnviadas(fetchMock)).toHaveLength(1);
    });
    expect(filasEnviadas(fetchMock)[0]).toMatchObject({
      question_version_id: 'q-9',
      curriculum_node_id: TEMA_UNO,
      status: 'accepted',
      retire_others: true,
    });
  });

  it('al terminar la cola lo dice, en lugar de dejar una lista vacía sin explicación', async () => {
    montar([]);

    expect(await screen.findByText('No queda ninguna propuesta')).toBeInTheDocument();
    expect(screen.getByText(/La cola está despachada/)).toBeInTheDocument();
  });

  it('una pregunta en dos temas sale con sus dos temas, su autor, y se deja con uno', async () => {
    const usuario = userEvent.setup();
    const fetchMock = montar([], { conflictos: [conflicto] });

    const dosTemas = await screen.findByRole('region', { name: /Preguntas en dos temas/ });
    expect(await within(dosTemas).findByText(/En el formato de ficheros CSV/)).toBeInTheDocument();
    expect(within(dosTemas).getByText('I.3')).toBeInTheDocument();
    expect(within(dosTemas).getByText('II.3')).toBeInTheDocument();
    // Y de quién es cada uno, que es lo que permite juzgar cuál se queda.
    expect(within(dosTemas).getByText(/a mano o heredado/)).toBeInTheDocument();
    expect(within(dosTemas).getByText(/propuesto por el modelo \(deepseek-flash\)/)).toBeInTheDocument();
    // Sin elegir, el botón no escribe: nada se toca por nuestra cuenta.
    expect(within(dosTemas).getByRole('button', { name: /Dejar este tema/ })).toBeDisabled();

    await usuario.click(within(dosTemas).getByRole('radio', { name: /II\.3/ }));
    await usuario.click(within(dosTemas).getByRole('button', { name: /Dejar este tema/ }));

    await waitFor(() => {
      expect(filasEnviadas(fetchMock)).toHaveLength(1);
    });
    expect(filasEnviadas(fetchMock)[0]).toMatchObject({
      question_version_id: 'q-8',
      curriculum_node_id: TEMA_DOS,
      status: 'accepted',
      retire_others: true,
    });
    expect(String(filasEnviadas(fetchMock)[0]?.reason)).toContain('un solo tema');
  });
});
