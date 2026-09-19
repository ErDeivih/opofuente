import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import type { ChangeSet, DerivedArtifact } from '../../src/api/changes';
import { AppShell } from '../../src/app/AppShell';
import { AppRoutes } from '../../src/app/routes';
import {
  capabilitiesFixture,
  oppositionsFixture,
  readinessReady,
  renderWithProviders,
  settingsFixture,
  stubApi,
  type StubbedRoute,
} from './testUtils';

/**
 * Pantalla Cambios (S11) desde el comportamiento real: qué enseña una propuesta de cambio, qué dice
 * de lo que **no** decide, qué pasa al confirmarla y cómo se revisa un derivado marcado.
 *
 * Las respuestas imitan el contrato real, incluido el aviso de efecto jurídico y el hecho de que una
 * respuesta guardada se marca pero no se revisa.
 */

const CAMBIO: ChangeSet = {
  id: 'chg-1',
  document_id: 'doc-1',
  document_title: 'Plazos administrativos',
  previous_version_id: 'ver-1',
  previous_version_label: 'v1',
  new_version_id: 'ver-2',
  new_version_label: 'v2',
  status: 'proposed',
  created_at: '2026-09-18T09:00:00Z',
  confirmed_at: null,
  discarded_at: null,
  reviewed_by: null,
  sections: [
    {
      label: 'Tema 1. Plazos administrativos',
      kind: 'unchanged',
      left: 'El plazo es de diez dias habiles.',
      right: 'El plazo es de diez dias habiles.',
    },
    {
      label: 'sección 2',
      kind: 'changed',
      left: 'El plazo es de diez dias habiles.',
      right: 'El plazo es de veinte dias habiles.',
    },
  ],
  affected: [
    {
      kind: 'derived_artifact',
      id: 'art-1',
      title: 'Resumen del plazo',
      sections: ['sección 2'],
      reason: 'depende de «sección 2», que ha cambiado',
      reviewable: true,
    },
    {
      kind: 'rag_answer',
      id: 'rag-1',
      title: 'respuesta guardada sobre este material',
      sections: ['sección 2'],
      reason: 'depende de «sección 2», que ha cambiado',
      reviewable: false,
    },
  ],
  sections_changed: 1,
  sections_added: 0,
  sections_removed: 0,
  sections_unchanged: 1,
  effect_note:
    'OpoFuente describe qué texto cambió y qué depende de él. No decide si una norma sigue vigente, si algo deja de ser válido ni qué hay que hacer con el material: eso lo decide una persona.',
  notes: [],
};

const CONFIRMADO: ChangeSet = {
  ...CAMBIO,
  status: 'confirmed',
  confirmed_at: '2026-09-18T10:00:00Z',
  reviewed_by: 'local',
};

const PENDIENTE: DerivedArtifact = {
  id: 'art-1',
  kind: 'summary',
  title: 'Resumen del plazo',
  content: '- sección 2: El plazo es de diez dias habiles.',
  document_version_id: 'ver-1',
  document_id: 'doc-1',
  document_title: 'Plazos administrativos',
  generator: 'extractive-summary-v1',
  prompt_template_version: 'extractive-summary-v1',
  model: null,
  review_status: 'pending',
  needs_review: true,
  needs_review_reason:
    'el material del que sale ha cambiado: «Plazos administrativos» («v1» → «v2»)',
  needs_review_at: '2026-09-18T10:00:00Z',
  reviewed_at: null,
  created_at: '2026-09-18T08:00:00Z',
  updated_at: '2026-09-18T10:00:00Z',
  sections: ['sección 2'],
};

function stubCambios(overrides: Record<string, StubbedRoute> = {}) {
  return stubApi({
    '/api/v1/health/ready': { body: readinessReady },
    '/api/v1/capabilities': { body: capabilitiesFixture },
    '/api/v1/settings': { body: settingsFixture },
    '/api/v1/oppositions': { body: oppositionsFixture },
    '/api/v1/change-sets?limit=100': { body: [CAMBIO] },
    '/api/v1/change-sets/chg-1': { body: CAMBIO },
    '/api/v1/change-sets/chg-1/confirm': {
      body: {
        change: CONFIRMADO,
        applied: true,
        reason: null,
        marked: ['art-1'],
        superseded_version_id: 'ver-1',
      },
    },
    '/api/v1/change-sets/chg-1/discard': {
      body: {
        change: { ...CAMBIO, status: 'discarded', discarded_at: '2026-09-18T10:00:00Z' },
        applied: true,
        reason: 'propuesta descartada: nada se ha invalidado',
        marked: [],
        superseded_version_id: null,
      },
    },
    '/api/v1/derived-artifacts?needs_review=true': { body: [PENDIENTE] },
    '/api/v1/derived-artifacts/art-1/resolution': { body: { ...PENDIENTE, needs_review: false } },
    ...overrides,
  });
}

function renderCambios() {
  return renderWithProviders(
    <AppShell>
      <AppRoutes />
    </AppShell>,
    { route: '/cambios' },
  );
}

describe('cambios: la propuesta', () => {
  it('enseña el diff por sección, lo afectado y el aviso de lo que no decide', async () => {
    stubCambios();
    renderCambios();

    expect(await screen.findByRole('heading', { level: 1, name: 'Cambios' })).toBeInTheDocument();
    // El diff: la sección que cambió y la que no.
    const tabla = await screen.findByRole('table', { name: 'Diff por sección' });
    expect(within(tabla).getByText('Tema 1. Plazos administrativos')).toBeInTheDocument();
    expect(within(tabla).getByText('con el texto cambiado')).toBeInTheDocument();
    expect(within(tabla).getByText('sin cambios')).toBeInTheDocument();
    expect(within(tabla).getByText(/veinte dias habiles/)).toBeInTheDocument();

    // Lo que depende de lo que cambió, separando lo revisable de lo que no.
    expect(screen.getByText('Qué depende de lo que ha cambiado')).toBeInTheDocument();
    const afectados = screen.getByRole('list', { name: 'Derivados afectados' });
    expect(within(afectados).getByText('Resumen del plazo')).toBeInTheDocument();
    expect(within(afectados).getByText('por revisar')).toBeInTheDocument();
    expect(within(afectados).getByText('no se revisa')).toBeInTheDocument();
    expect(within(afectados).getAllByText(/que ha cambiado/)).toHaveLength(2);

    // Y el aviso de lo que la aplicación no interpreta.
    expect(screen.getByText(/No decide si una norma sigue vigente/)).toBeInTheDocument();
    expect(screen.getByText(/lo decide una persona/)).toBeInTheDocument();
  });

  it('confirmar aplica el cambio y lo dice', async () => {
    const fetchMock = stubCambios();
    renderCambios();

    await screen.findByRole('heading', { name: 'Qué ha cambiado' });
    await userEvent.click(screen.getByRole('button', { name: 'Confirmar el cambio' }));

    await waitFor(() => {
      const llamada = fetchMock.mock.calls.find(
        (call) => typeof call[0] === 'string' && call[0].includes('/confirm'),
      );
      expect(llamada).toBeDefined();
    });
  });

  it('descartar no invalida nada y lo dice', async () => {
    stubCambios();
    renderCambios();

    await screen.findByRole('heading', { name: 'Qué ha cambiado' });
    await userEvent.click(screen.getByRole('button', { name: 'Descartar la propuesta' }));

    await waitFor(() => {
      expect(screen.getByText(/propuesta descartada: nada se ha invalidado/)).toBeInTheDocument();
    });
  });

  it('un cambio confirmado ya no se puede confirmar otra vez', async () => {
    stubCambios({ '/api/v1/change-sets?limit=100': { body: [CONFIRMADO] } });
    renderCambios();

    await screen.findByRole('heading', { name: 'Qué ha cambiado' });
    expect(screen.queryByRole('button', { name: 'Confirmar el cambio' })).toBeNull();
    expect(screen.getByText(/Este cambio está confirmado/)).toBeInTheDocument();
  });

  it('sin cambios explica que aparecen al promocionar una segunda versión', async () => {
    stubCambios({
      '/api/v1/change-sets?limit=100': { body: [] },
      '/api/v1/derived-artifacts?needs_review=true': { body: [] },
    });
    renderCambios();

    expect(await screen.findByRole('heading', { name: 'Sin cambios' })).toBeInTheDocument();
    expect(screen.getByText(/cuando promocionas una segunda versión/)).toBeInTheDocument();
  });
});

describe('cambios: los resúmenes pendientes', () => {
  it('enseña el motivo de la marca y deja revisarlo o apartarlo', async () => {
    const fetchMock = stubCambios();
    renderCambios();

    const tarjeta = await screen.findByRole('list', {
      name: 'Resúmenes pendientes de revisar',
    });
    expect(within(tarjeta).getByText('Resumen del plazo')).toBeInTheDocument();
    expect(within(tarjeta).getByText(/el material del que sale ha cambiado/)).toBeInTheDocument();
    expect(within(tarjeta).getByText(/secciones: sección 2/)).toBeInTheDocument();

    await userEvent.click(
      within(tarjeta).getByRole('button', {
        name: 'Marcar que el resumen sigue valiendo: Resumen del plazo',
      }),
    );

    await waitFor(() => {
      const llamada = fetchMock.mock.calls.find(
        (call) => typeof call[0] === 'string' && call[0].includes('/resolution'),
      );
      expect(llamada).toBeDefined();
      expect(cuerpoJsonDe(llamada)).toMatchObject({ resolution: 'reviewed' });
    });
    expect(
      screen.getByText(/Descartar no borra: aparta el resumen para que deje de usarse/),
    ).toBeInTheDocument();
  });
});

/** El cuerpo JSON de una llamada simulada, con el tipo comprobado antes de leerlo. */
function cuerpoJsonDe(llamada: readonly unknown[] | undefined): unknown {
  const init = llamada?.[1];
  const body = typeof init === 'object' && init !== null && 'body' in init ? init.body : undefined;
  if (typeof body !== 'string') {
    throw new Error('la petición no llevaba cuerpo JSON');
  }
  return JSON.parse(body) as unknown;
}
