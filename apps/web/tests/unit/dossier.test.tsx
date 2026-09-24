import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Route, Routes, useSearchParams } from 'react-router-dom';
import { describe, expect, it } from 'vitest';

import { AppShell } from '../../src/app/AppShell';
import { ProgramPage } from '../../src/pages/ProgramPage';
import {
  TAI_CONVOCATION_ID,
  TAI_ID,
  convocationFixture,
  curriculumFixture,
  dossierEmptyFixture,
  dossierFixture,
  dossierHolesFixture,
  dossierVersionsFixture,
  masteryFixture,
  nodeDetailFixture,
  oppositionsFixture,
  renderWithProviders,
  stubApi,
  taiConvocationsFixture,
  type StubbedRoute,
} from './testUtils';

const DOSSIER = '/api/v1/curriculum-nodes/node-i-1/dossier';

/**
 * La sesión que devuelve el servidor al practicar un tema: lo justo para poder abrirla en Estudio.
 * Se declara aquí (y no en el simulador común) porque solo esta prueba la mira.
 */
const SESION_DE_TEMA = {
  id: 'sesion-tema',
  mode: 'practice',
  status: 'draft',
  feedback: 'immediate',
  opposition_id: 'opp-tai',
  convocation_version_id: TAI_CONVOCATION_ID,
  question_set_id: null,
  answer_key_version_id: null,
  key_label: 'Banco privado: plantilla v1',
  configuration: {
    mode: 'practice',
    feedback: 'immediate',
    time_limit_minutes: null,
    shuffle: false,
    sources: [],
    note: 'Práctica de un tema: 3 pregunta(s) catalogadas en él.',
  },
  time_limit_minutes: null,
  total_questions: 3,
  answered_questions: 0,
  started_at: null,
  finished_at: null,
  created_at: '2026-09-24T09:00:00Z',
  result: null,
};

function stubConDossier(extra: Record<string, StubbedRoute> = {}) {
  return stubApi({
    '/api/v1/oppositions': { body: oppositionsFixture },
    [`/api/v1/oppositions/${TAI_ID}/convocations`]: { body: taiConvocationsFixture },
    [`/api/v1/reviews/mastery?opposition_id=${TAI_ID}`]: { body: masteryFixture },
    'POST /api/v1/study-sessions': { status: 201, body: SESION_DE_TEMA },
    '/api/v1/curriculum-nodes/node-i-1': { body: nodeDetailFixture },
    [`${DOSSIER}/versions`]: { body: dossierVersionsFixture },
    [DOSSIER]: { body: dossierFixture },
    [`/api/v1/convocations/${TAI_CONVOCATION_ID}/curriculum`]: { body: curriculumFixture },
    [`/api/v1/convocations/${TAI_CONVOCATION_ID}`]: { body: convocationFixture },
    ...extra,
  });
}

async function abrirTema() {
  renderWithProviders(
    <AppShell>
      <ProgramPage />
    </AppShell>,
    { route: '/programa' },
  );
  await userEvent.click(await screen.findByRole('button', { name: /La Constitución Española/ }));
}

/** Lo que Estudio enseña de la sesión que le llega por la URL: basta para comprobar el salto. */
function EstudioSonda() {
  const [parametros] = useSearchParams();
  return <p>sesión abierta: {parametros.get('sesion') ?? 'ninguna'}</p>;
}

async function abrirTemaConEstudio() {
  renderWithProviders(
    <AppShell>
      <Routes>
        <Route path="/programa" element={<ProgramPage />} />
        <Route path="/estudiar" element={<EstudioSonda />} />
      </Routes>
    </AppShell>,
    { route: '/programa' },
  );
  await userEvent.click(await screen.findByRole('button', { name: /La Constitución Española/ }));
}

describe('dossier del tema (S13)', () => {
  it('enseña los pasajes de cada fuente con su procedencia, citados', async () => {
    stubConDossier();
    await abrirTema();

    expect(await screen.findByRole('heading', { name: 'Apuntes de la Constitución' })).toBeInTheDocument();
    expect(
      screen.getByText('España se constituye en un Estado social y democrático de Derecho.'),
    ).toBeInTheDocument();
    // La cita dice documento, versión, página y sección: lo que hace falta para ir a mirarlo.
    expect(screen.getByText(/Título preliminar, pág. 3/)).toBeInTheDocument();
    expect(screen.getByText(/versión v1 · aceptada · calidad: good · asignación confirmada/)).toBeInTheDocument();
    expect(await screen.findByRole('heading', { name: 'Manual de la oposición' })).toBeInTheDocument();
    expect(screen.getByText(/2 fuentes · 2 pasajes citados/)).toBeInTheDocument();
  });

  it('dice dónde más está un texto repetido en lugar de enseñarlo dos veces', async () => {
    stubConDossier();
    await abrirTema();

    expect(
      await screen.findByText(/El mismo texto también está en: Manual de la oposición, pág. 9/),
    ).toBeInTheDocument();
    const repetido = screen.getAllByText(
      'España se constituye en un Estado social y democrático de Derecho.',
    );
    expect(repetido).toHaveLength(1);
  });

  it('una fuente sin confirmar lleva su etiqueta y el conjunto lo declara', async () => {
    stubConDossier();
    await abrirTema();

    expect(await screen.findByText('asignación sin confirmar')).toBeInTheDocument();
    expect(screen.getByText(/con asignaciones sin confirmar/)).toBeInTheDocument();
    expect(
      screen.getByText(/se asignaron a este tema sin confirmar: revísalas en Revisión/),
    ).toBeInTheDocument();
  });

  it('un tema sin material ofrece subir algo en lugar de enseñar un cero', async () => {
    stubConDossier({
      [DOSSIER]: { body: dossierEmptyFixture },
      [`${DOSSIER}/versions`]: { body: [] },
    });
    await abrirTema();

    expect(
      await screen.findByText(/Este tema todavía no tiene nada que citar de tu material/),
    ).toBeInTheDocument();
    expect(
      screen.getByText('Ningún material de tu biblioteca está asignado a este tema todavía.'),
    ).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Subir material a la bandeja' })).toHaveAttribute(
      'href',
      '/bandeja',
    );
    // La versión se dice con el código del hueco, no con un cero que parecería un dato.
    expect(screen.getByText('sin_material')).toBeInTheDocument();
  });

  it('lo que no se puede citar se enseña con su motivo', async () => {
    stubConDossier({
      [DOSSIER]: { body: dossierHolesFixture },
      [`${DOSSIER}/versions`]: { body: [] },
    });
    await abrirTema();

    expect(
      await screen.findByText(/Hay material asignado a este tema, pero todavía no tiene texto/),
    ).toBeInTheDocument();
    expect(screen.getByText(/Motivo: la versión está en estado «candidate»./)).toBeInTheDocument();
  });

  it('guardar la lectura la archiva y dice si ya estaba guardada', async () => {
    const fetchMock = stubConDossier({
      [`POST ${DOSSIER}/versions`]: {
        status: 201,
        body: { created: false, version_id: 'ver-2', dossier: dossierFixture },
      },
    });
    await abrirTema();

    await userEvent.click(await screen.findByRole('button', { name: 'Guardar esta lectura' }));

    await waitFor(() => {
      expect(
        screen.getByText('Esa lectura ya estaba guardada: no se ha creado otra versión.'),
      ).toBeInTheDocument();
    });
    // Y de verdad se ha pedido archivarla: una promesa de la pantalla sin petición sería mentira.
    const llamado = fetchMock.mock.calls.some(
      (call) =>
        typeof call[0] === 'string' &&
        call[0].includes(`${DOSSIER}/versions`) &&
        call[1]?.method === 'POST',
    );
    expect(llamado).toBe(true);
  });

  it('lista las versiones guardadas y puede leer una anterior', async () => {    const anterior = { ...dossierFixture, sources_total: 1, passages_total: 1 };
    stubApi({
      '/api/v1/oppositions': { body: oppositionsFixture },
      [`/api/v1/oppositions/${TAI_ID}/convocations`]: { body: taiConvocationsFixture },
      [`/api/v1/reviews/mastery?opposition_id=${TAI_ID}`]: { body: masteryFixture },
      '/api/v1/curriculum-nodes/node-i-1': { body: nodeDetailFixture },
      [`${DOSSIER}/versions/ver-1`]: { body: anterior },
      [`${DOSSIER}/versions`]: { body: dossierVersionsFixture },
      [DOSSIER]: { body: dossierFixture },
      [`/api/v1/convocations/${TAI_CONVOCATION_ID}/curriculum`]: { body: curriculumFixture },
      [`/api/v1/convocations/${TAI_CONVOCATION_ID}`]: { body: convocationFixture },
    });
    await abrirTema();

    expect(await screen.findByText(/1 fuente · 1 pasaje/)).toBeInTheDocument();
    await userEvent.click(await screen.findByRole('button', { name: /2026-09-20/ }));

    // Al leer una versión anterior, la pantalla lo dice y ofrece volver a la de hoy.
    expect(
      await screen.findByText(/Estás leyendo lo que este tema decía el 2026-09-24/),
    ).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Volver a la lectura de hoy' })).toBeInTheDocument();
    // Y no se ofrece archivar: una versión guardada se lee, no se cambia.
    expect(screen.queryByRole('button', { name: 'Guardar esta lectura' })).not.toBeInTheDocument();
  });
});

describe('preguntas del tema (S13, parte 3)', () => {
  it('un tema con preguntas dice cuántas tiene y deja practicarlo', async () => {
    const fetchMock = stubConDossier();
    await abrirTemaConEstudio();

    expect(
      await screen.findByText(/3 preguntas catalogadas en este tema/),
    ).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Practicar este tema' }));

    // La sesión la monta el servidor: se pide sin conjuntos y con el tema, y se abre en Estudio.
    await waitFor(() => {
      const peticion = fetchMock.mock.calls.find(
        (call) =>
          typeof call[0] === 'string' &&
          call[0].includes('/api/v1/study-sessions') &&
          call[1]?.method === 'POST',
      );
      expect(peticion).toBeDefined();
      const cuerpo: unknown = peticion?.[1]?.body;
      expect(typeof cuerpo).toBe('string');
      expect(JSON.parse(cuerpo as string)).toMatchObject({
        mode: 'practice',
        sources: [],
        curriculum_node_id: 'node-i-1',
      });
    });
    expect(await screen.findByText('sesión abierta: sesion-tema')).toBeInTheDocument();
  });

  it('un tema sin preguntas lo dice y lleva al banco, sin prometer una sesión', async () => {
    stubConDossier({
      [`/api/v1/reviews/mastery?opposition_id=${TAI_ID}`]: {
        body: {
          ...masteryFixture,
          nodes: [
            {
              ...masteryFixture.nodes[1]!,
              study_state: {
                questions_total: 0,
                questions_by_status: [],
                questions_by_origin: [],
                reviews_due: 0,
                next_review_at: null,
              },
            },
          ],
        },
      },
    });
    await abrirTema();

    expect(
      await screen.findByText(/Este tema no tiene ninguna pregunta catalogada/),
    ).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Ir al banco de preguntas' })).toHaveAttribute(
      'href',
      '/preguntas',
    );
    expect(screen.queryByRole('button', { name: 'Practicar este tema' })).not.toBeInTheDocument();
  });

  it('si el tema no tiene preguntas corregibles, lo dice el servidor y se enseña su motivo', async () => {
    stubConDossier({
      'POST /api/v1/study-sessions': {
        status: 409,
        contentType: 'application/problem+json',
        body: {
          type: 'about:blank',
          title: 'Conflict',
          status: 409,
          detail: 'las preguntas de este tema no se pueden corregir todavía: 2 sin plantilla activa',
          instance: '/api/v1/study-sessions',
          code: 'unsupported',
          correlation_id: 'corr-de-prueba',
        },
      },
    });
    await abrirTemaConEstudio();

    await userEvent.click(await screen.findByRole('button', { name: 'Practicar este tema' }));

    expect(
      await screen.findByText(/no se pueden corregir todavía: 2 sin plantilla activa/),
    ).toBeInTheDocument();
  });
});
