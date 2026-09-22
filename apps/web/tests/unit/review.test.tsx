import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import type {
  BulkDecisionResponse,
  Coverage,
  DecisionOutcome,
  Proposal,
  ReviewGroup,
} from '../../src/api/classification';
import { AppShell } from '../../src/app/AppShell';
import { ReviewPage } from '../../src/pages/ReviewPage';
import {
  TAI_CONVOCATION_ID,
  curriculumFixture,
  oppositionsFixture,
  renderWithProviders,
  stubApi,
  type StubbedRoute,
} from './testUtils';

/**
 * Pantalla de Revisión (S04) desde el comportamiento real: qué se ve, qué se envía y qué se deja
 * deshacer. Las respuestas imitan el contrato real, incluido el 409 con motivo.
 */

const ARCHIVO_UNO = 'apuntes-tema-01.txt';
const ARCHIVO_DOS = 'apuntes-tema-02.txt';

/** Tipo documental de banda baja: una propuesta normal, no crítica. */
const propuestaTipoUno: Proposal = {
  id: 'p-tipo-1',
  subject_type: 'artifact',
  subject_id: 'art-1',
  subject_label: ARCHIVO_UNO,
  axis: 'document_type',
  proposed_value: 'community_material',
  value_label: 'Material de la comunidad',
  confidence: 0.4,
  band: 'low',
  is_critical: false,
  status: 'pending',
  engine_name: 'determinista',
  engine_version: '1',
  alternatives: [{ value: 'personal_notes', confidence: 0.4 }],
  evidence: ['«apuntes de»'],
  created_at: '2026-07-01T09:00:00Z',
  decided_at: null,
  decision_note: null,
};

const propuestaTipoDos: Proposal = {
  ...propuestaTipoUno,
  id: 'p-tipo-2',
  subject_id: 'art-2',
  subject_label: ARCHIVO_DOS,
};

/** Autoridad: eje crítico. El servidor nunca la aplica solo, ni con confianza alta. */
const propuestaAutoridad: Proposal = {
  id: 'p-autoridad',
  subject_type: 'artifact',
  subject_id: 'art-1',
  subject_label: ARCHIVO_UNO,
  axis: 'authority',
  proposed_value: 'A',
  value_label: 'Publicación oficial',
  confidence: 0.9,
  band: 'medium',
  is_critical: true,
  status: 'pending',
  engine_name: 'determinista',
  engine_version: '1',
  alternatives: [],
  evidence: ['«Boletín Oficial del Estado»'],
  created_at: '2026-07-01T09:00:00Z',
  decided_at: null,
  decision_note: null,
};

/** Tema: se puede corregir contra los nodos del programa. */
const propuestaTema: Proposal = {
  id: 'p-tema',
  subject_type: 'artifact',
  subject_id: 'art-1',
  subject_label: ARCHIVO_UNO,
  axis: 'topic',
  proposed_value: '4.1',
  value_label: null,
  confidence: 0.68,
  band: 'medium',
  is_critical: false,
  status: 'pending',
  engine_name: 'determinista',
  engine_version: '1',
  alternatives: [{ value: '1.1', confidence: 0.55 }],
  evidence: ['título del programa «Derechos humanos»'],
  created_at: '2026-07-01T09:00:00Z',
  decided_at: null,
  decision_note: null,
};

/** Aplicada sola por banda alta: sigue siendo provisional y reversible. */
const propuestaProvisional: Proposal = {
  ...propuestaTipoDos,
  id: 'p-provisional',
  subject_id: 'art-3',
  subject_label: 'notas-provisionales.txt',
  confidence: 0.9,
  band: 'high',
  status: 'auto_applied_provisional',
};

const PENDIENTES: Proposal[] = [
  propuestaTipoUno,
  propuestaTipoDos,
  propuestaAutoridad,
  propuestaTema,
];
const PROVISIONALES: Proposal[] = [propuestaProvisional];

const grupos: ReviewGroup[] = [
  {
    key: 'artifact:document_type:community_material',
    subject_type: 'artifact',
    axis: 'document_type',
    proposed_value: 'community_material',
    label: 'Material de la comunidad',
    proposal_ids: [propuestaTipoUno.id, propuestaTipoDos.id],
    size: 2,
    min_confidence: 0.4,
    max_confidence: 0.4,
    is_critical: false,
  },
  {
    key: 'artifact:authority:A',
    subject_type: 'artifact',
    axis: 'authority',
    proposed_value: 'A',
    label: 'Publicación oficial',
    proposal_ids: [propuestaAutoridad.id],
    size: 1,
    min_confidence: 0.9,
    max_confidence: 0.9,
    is_critical: true,
  },
];

const cobertura: Coverage = {
  node_id: 'node-i',
  path: 'I',
  title: 'Organización del Estado y Administración electrónica',
  provisional: 2,
  accepted: 1,
  unclassified_subjects: 4,
  materials_total: 7,
  subtree: [
    {
      node_id: 'node-i',
      path: 'I',
      title: 'Organización del Estado y Administración electrónica',
      depth: 0,
      provisional: 2,
      accepted: 1,
      materials: [ARCHIVO_UNO],
    },
    {
      node_id: 'node-i-1',
      path: 'I.1',
      title: 'La Constitución Española de 1978',
      depth: 1,
      provisional: 0,
      accepted: 1,
      materials: [ARCHIVO_UNO],
    },
  ],
};

const aceptadaUno: DecisionOutcome = {
  proposal_id: propuestaTipoUno.id,
  status: 'accepted',
  applied: true,
  mapping_id: null,
  audit_event_id: 'evt-1',
  reason: null,
};

const loteAplicado: BulkDecisionResponse = {
  outcomes: [{ ...aceptadaUno, proposal_id: propuestaTipoUno.id }],
  applied: 1,
  conflicts: 0,
  requested: 2,
  excluded: [propuestaTipoDos.id],
};

function stubReviewApi(overrides: Record<string, StubbedRoute> = {}) {
  return stubApi({
    '/api/v1/classification-proposals?status=pending': { body: { proposals: PENDIENTES, total: PENDIENTES.length, limit: 200, offset: 0 } },
    '/api/v1/classification-proposals?status=auto_applied_provisional': {
      body: { proposals: PROVISIONALES, total: PROVISIONALES.length, limit: 200, offset: 0 },
    },
    '/api/v1/classification-proposals/bulk-decision': { body: loteAplicado },
    '/api/v1/classification-proposals/p-tipo-1/accept': { body: aceptadaUno },
    '/api/v1/classification-proposals/p-tipo-1/reject': {
      body: { ...aceptadaUno, status: 'rejected', mapping_id: null },
    },
    '/api/v1/classification-proposals/p-tema/accept': {
      body: { ...aceptadaUno, proposal_id: propuestaTema.id, mapping_id: 'map-1' },
    },
    '/api/v1/classification-decisions/evt-1/undo': {
      body: { ...aceptadaUno, status: 'pending', audit_event_id: 'evt-2' },
    },
    // La pasada de clasificación devuelve un **trabajo** encolado (DEBT-024), y su `step` lleva el
    // resumen cuando termina.
    '/api/v1/classification-runs': {
      body: {
        id: 'job-clasificar',
        job_type: 'classify_document',
        status: 'queued',
        progress: 0,
        attempts: 0,
        max_attempts: 3,
        created_at: '2026-09-22T10:00:00Z',
        updated_at: '2026-09-22T10:00:00Z',
        step: null,
        error_code: null,
        error_message: null,
        started_at: null,
        finished_at: null,
        cancel_requested: false,
      },
    },
    '/api/v1/jobs/job-clasificar': {
      body: {
        id: 'job-clasificar',
        job_type: 'classify_document',
        status: 'succeeded',
        progress: 1,
        attempts: 1,
        max_attempts: 3,
        created_at: '2026-09-22T10:00:00Z',
        updated_at: '2026-09-22T10:00:05Z',
        step: '6 sujetos: 4 propuestas nuevas, 0 ya existentes, 1 sin señales',
        error_code: null,
        error_message: null,
        started_at: '2026-09-22T10:00:01Z',
        finished_at: '2026-09-22T10:00:05Z',
        cancel_requested: false,
      },
    },
    '/api/v1/review-groups': { body: grupos },
    '/api/v1/curriculum-nodes/node-i/coverage': { body: cobertura },
    '/api/v1/oppositions': { body: oppositionsFixture },
    [`/api/v1/convocations/${TAI_CONVOCATION_ID}/curriculum`]: { body: curriculumFixture },
    ...overrides,
  });
}

function renderReview() {
  return renderWithProviders(
    <AppShell>
      <ReviewPage />
    </AppShell>,
    { route: '/revision' },
  );
}

function tablaDeGrupos() {
  return screen.getByRole('table', { name: /Grupos de revisión/ });
}

function tablaDePropuestas() {
  return screen.getByRole('table', { name: /propuestas esperando tu decisión/ });
}

/** Nombre accesible de la fila de una propuesta: material, tipo de sujeto y eje. */
function nombreDeFila(material: string, tipo: string, eje: string): RegExp {
  const escapado = material.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return new RegExp(`${escapado} \\(${tipo}\\) ${eje}`);
}

/** Nombre accesible de una acción de la fila, tal y como lo escribe la pantalla. */
function accion(verbo: string, material: string, tipo: string, eje: string): string {
  return `${verbo}: ${material} (${tipo}) · ${eje}`;
}

const TIPO_DOCUMENTAL = 'Tipo de documento';
const TEMA = 'Tema del programa';
const AUTORIDAD = 'Autoridad';
const MATERIAL = 'material';

function cuerpoJson(llamada: ReturnType<typeof peticion>): unknown {
  const body = llamada?.[1]?.body;
  if (typeof body !== 'string') {
    throw new Error('la petición no llevaba un cuerpo JSON');
  }
  return JSON.parse(body) as unknown;
}

function peticion(
  fetchMock: ReturnType<typeof stubReviewApi>,
  fragmento: string,
) {
  return fetchMock.mock.calls.find(
    (call) => typeof call[0] === 'string' && call[0].includes(fragmento),
  );
}

describe('pantalla Revisión', () => {
  it('dice que las propuestas son propuestas y que lo autoaplicado es reversible', async () => {
    stubReviewApi();
    renderReview();

    const aviso = await screen.findByRole('region', { name: 'Esto son propuestas, no hechos' });
    expect(within(aviso).getByText(/cada propuesta espera tu decisión/)).toBeInTheDocument();
    expect(within(aviso).getByText(/no se aplican solas nunca, ni con confianza alta/)).toBeInTheDocument();
    // Lo aplicado por el motor se declara tal cual: provisional y reversible, no hecho.
    const propuestas = await screen.findByRole('table', { name: /propuestas esperando tu decisión/ });
    const fila = within(propuestas).getByRole('row', { name: /notas-provisionales\.txt/ });
    expect(within(fila).getByText('aplicada provisionalmente')).toBeInTheDocument();
    expect(within(fila).getByText(/sigue siendo reversible/)).toBeInTheDocument();
    expect(within(fila).getByRole('button', { name: /^Confirmar: / })).toBeInTheDocument();
  });

  it('muestra los grupos con su tamaño y su confianza, y las propuestas con su evidencia', async () => {
    stubReviewApi();
    renderReview();

    const grupos = within(await waitFor(() => tablaDeGrupos()));
    const filaTipo = grupos.getByRole('row', { name: /Material de la comunidad/ });
    expect(within(filaTipo).getByText('2')).toBeInTheDocument();
    expect(within(filaTipo).getByText('40 %')).toBeInTheDocument();
    expect(within(filaTipo).getByText('Tipo de documento')).toBeInTheDocument();

    const propuestas = within(await waitFor(() => tablaDePropuestas()));
    const fila = propuestas.getByRole('row', {
      name: nombreDeFila(ARCHIVO_UNO, MATERIAL, TIPO_DOCUMENTAL),
    });
    // El eje, el valor legible, la confianza con su banda, la evidencia y las alternativas.
    expect(within(fila).getByText(TIPO_DOCUMENTAL)).toBeInTheDocument();
    expect(within(fila).getByText('Material de la comunidad')).toBeInTheDocument();
    expect(within(fila).getByText('confianza baja')).toBeInTheDocument();
    expect(within(fila).getByText('«apuntes de»')).toBeInTheDocument();
    expect(within(fila).getByText('personal_notes')).toBeInTheDocument();
  });

  it('marca las propuestas de eje crítico como requiere tu confirmación', async () => {
    stubReviewApi();
    renderReview();

    const grupos = within(await waitFor(() => tablaDeGrupos()));
    const filaAutoridad = grupos.getByRole('row', { name: /Publicación oficial/ });
    expect(within(filaAutoridad).getByText('requiere tu confirmación')).toBeInTheDocument();

    const propuestas = within(await waitFor(() => tablaDePropuestas()));
    const fila = propuestas.getByRole('row', {
      name: nombreDeFila(ARCHIVO_UNO, MATERIAL, AUTORIDAD),
    });
    expect(within(fila).getByText(AUTORIDAD)).toBeInTheDocument();
    expect(within(fila).getByText('requiere tu confirmación')).toBeInTheDocument();
  });

  it('acepta una propuesta, la registra en el historial y ofrece deshacerla', async () => {
    const fetchMock = stubReviewApi();
    renderReview();

    await userEvent.click(
      await screen.findByRole('button', {
        name: accion('Aceptar', ARCHIVO_UNO, MATERIAL, TIPO_DOCUMENTAL),
      }),
    );

    await waitFor(() => {
      expect(peticion(fetchMock, '/classification-proposals/p-tipo-1/accept')).toBeDefined();
    });
    const llamada = peticion(fetchMock, '/classification-proposals/p-tipo-1/accept');
    expect(llamada?.[1]?.method).toBe('POST');
    expect(cuerpoJson(llamada)).toEqual({ coverage_type: 'partial' });

    const historial = await screen.findByRole('region', { name: 'Decisiones de esta sesión' });
    expect(within(historial).getByText('aceptada')).toBeInTheDocument();
    expect(
      within(historial).getByRole('button', { name: new RegExp(`^Deshacer la decisión sobre ${ARCHIVO_UNO}`) }),
    ).toBeInTheDocument();
  });

  it('deshace una decisión con su traza de auditoría y devuelve la propuesta a la cola', async () => {
    const fetchMock = stubReviewApi();
    renderReview();

    await userEvent.click(
      await screen.findByRole('button', {
        name: accion('Aceptar', ARCHIVO_UNO, MATERIAL, TIPO_DOCUMENTAL),
      }),
    );
    const historial = await screen.findByRole('region', { name: 'Decisiones de esta sesión' });
    const consultasAntes = fetchMock.mock.calls.filter(
      (call) =>
        typeof call[0] === 'string' &&
        call[0].includes('/classification-proposals?status=pending'),
    ).length;

    await userEvent.click(
      within(historial).getByRole('button', { name: new RegExp(`^Deshacer la decisión sobre ${ARCHIVO_UNO}`) }),
    );

    await waitFor(() => {
      expect(peticion(fetchMock, '/classification-decisions/evt-1/undo')).toBeDefined();
    });
    expect(peticion(fetchMock, '/classification-decisions/evt-1/undo')?.[1]?.method).toBe('POST');
    expect(await within(historial).findByText(/deshecha: la propuesta volvió a la cola/)).toBeInTheDocument();
    // Y la cola se vuelve a pedir al servidor: el estado que se ve es el suyo, no una suposición.
    await waitFor(() => {
      const consultasDespues = fetchMock.mock.calls.filter(
        (call) =>
          typeof call[0] === 'string' &&
          call[0].includes('/classification-proposals?status=pending'),
      ).length;
      expect(consultasDespues).toBeGreaterThan(consultasAntes);
    });
  });

  it('corrige el tema con un nodo del programa y envía la corrección al aceptar', async () => {
    const fetchMock = stubReviewApi();
    renderReview();

    const propuestas = within(await waitFor(() => tablaDePropuestas()));
    const fila = propuestas.getByRole('row', { name: nombreDeFila(ARCHIVO_UNO, MATERIAL, TEMA) });
    const selector = within(fila).getByLabelText('Corregir el tema');
    // Las opciones son los nodos reales del programa, no una lista escrita a mano.
    expect(
      await within(selector).findByRole('option', { name: 'I.1 · La Constitución Española de 1978' }),
    ).toBeInTheDocument();

    await userEvent.selectOptions(selector, 'I.1');
    await userEvent.click(
      within(fila).getByRole('button', {
        name: accion('Aceptar con la corrección', ARCHIVO_UNO, MATERIAL, TEMA),
      }),
    );

    await waitFor(() => {
      expect(peticion(fetchMock, '/classification-proposals/p-tema/accept')).toBeDefined();
    });
    expect(cuerpoJson(peticion(fetchMock, '/classification-proposals/p-tema/accept'))).toEqual({
      coverage_type: 'partial',
      override_value: 'I.1',
    });
  });

  it('decide en lote y deja fuera del lote la fila que se excluye', async () => {
    const fetchMock = stubReviewApi();
    renderReview();

    await userEvent.click(
      await screen.findByRole('checkbox', {
        // El nombre accesible incluye el sujeto y el eje, para que dos grupos con la misma etiqueta
        // se distingan al navegar con lector de pantalla; aquí basta con identificar el grupo.
        name: /^Marcar el grupo Material de la comunidad/,
      }),
    );

    const lote = within(await screen.findByRole('region', { name: 'Cola de revisión' }));
    expect(lote.getByRole('button', { name: 'Aceptar 2 propuestas' })).toBeInTheDocument();
    expect(lote.getByText(/El lote decide/)).toBeInTheDocument();

    await userEvent.click(lote.getByRole('checkbox', { name: `Dejar fuera del lote: ${ARCHIVO_DOS}` }));

    const aceptar = lote.getByRole('button', { name: 'Aceptar 1 propuesta' });
    await userEvent.click(aceptar);

    await waitFor(() => {
      expect(peticion(fetchMock, '/classification-proposals/bulk-decision')).toBeDefined();
    });
    // La excepción viaja aparte: el lote pide las dos y excluye explícitamente una.
    expect(cuerpoJson(peticion(fetchMock, '/classification-proposals/bulk-decision'))).toEqual({
      proposal_ids: [propuestaTipoUno.id, propuestaTipoDos.id],
      decision: 'accepted',
      excluded: [propuestaTipoDos.id],
    });
    // Y el resultado se cuenta tal cual lo devolvió el servidor.
    const resultado = await screen.findByRole('region', { name: 'Cola de revisión' });
    expect(within(resultado).getByText('Propuestas pedidas').nextElementSibling).toHaveTextContent('2');
    expect(within(resultado).getByText('Aplicadas').nextElementSibling).toHaveTextContent('1');
    expect(within(resultado).getByText('Excepciones').nextElementSibling).toHaveTextContent('1');
    expect(within(resultado).getByRole('button', { name: 'Deshacer el lote' })).toBeInTheDocument();
  });

  it('cuenta el 409 como decisión no aplicada, con su motivo delante', async () => {
    stubReviewApi({
      '/api/v1/classification-proposals/p-tema/accept': {
        status: 409,
        contentType: 'application/problem+json',
        body: {
          type: 'about:blank',
          title: 'Conflict',
          status: 409,
          detail: 'El nodo «tema/que-no-existe» no está en el programa sembrado',
          code: 'classification_conflict',
          correlation_id: 'corr-de-prueba',
          instance: '/api/v1/classification-proposals/p-tema/accept',
        },
      },
    });
    renderReview();

    const propuestas = within(await waitFor(() => tablaDePropuestas()));
    const fila = propuestas.getByRole('row', { name: nombreDeFila(ARCHIVO_UNO, MATERIAL, TEMA) });
    const selector = within(fila).getByLabelText('Corregir el tema');
    await within(selector).findByRole('option', { name: 'I.1 · La Constitución Española de 1978' });
    await userEvent.selectOptions(selector, 'I.1');
    await userEvent.click(
      within(fila).getByRole('button', {
        name: accion('Aceptar con la corrección', ARCHIVO_UNO, MATERIAL, TEMA),
      }),
    );

    expect(await screen.findByText('La decisión no se aplicó')).toBeInTheDocument();
    expect(screen.getByText(/no está en el programa sembrado/)).toBeInTheDocument();
    expect(screen.getByText(/Un conflicto no cambia nada/)).toBeInTheDocument();
    // Un conflicto no se apunta como decisión tomada: no hay nada que deshacer.
    expect(screen.queryByRole('region', { name: 'Decisiones de esta sesión' })).not.toBeInTheDocument();
  });

  it('separa la cobertura provisional de la aceptada, sin mezclarlas', async () => {
    stubReviewApi();
    renderReview();

    const coberturaRegion = await screen.findByRole('region', { name: 'Cobertura del programa' });
    // El árbol del programa es el mismo del Programa: se elige el bloque y se ve su cobertura.
    await userEvent.click(
      await within(coberturaRegion).findByRole('button', { name: /Organización del Estado/ }),
    );

    const hechos = within(await screen.findByRole('region', { name: 'Cobertura del programa' }));
    const provisional = await waitFor(() => hechos.getByText('Cobertura provisional'));
    const aceptada = hechos.getByText('Cobertura aceptada');
    expect(provisional.nextElementSibling).toHaveTextContent('2 (aplicada por el motor, sin confirmar)');
    expect(aceptada.nextElementSibling).toHaveTextContent('1 (confirmada por ti)');
    // Lo que no tiene propuesta se declara aparte, y el material total es otro número distinto.
    expect(hechos.getByText('Materiales sin clasificar').nextElementSibling).toHaveTextContent('4');
    expect(hechos.getByText('Materiales totales').nextElementSibling).toHaveTextContent('7');
    // El subárbol también lleva las dos cifras separadas, nodo a nodo.
    const subarbol = within(hechos.getByRole('table', { name: /Nodos del subárbol/ }));
    const filaTema = subarbol.getByRole('row', { name: /I\.1 La Constitución Española de 1978/ });
    expect(within(filaTema).getByText('1')).toBeInTheDocument();
    expect(within(filaTema).getByText(ARCHIVO_UNO)).toBeInTheDocument();
  });

  it('busca propuestas ahora sin aplicar nada definitivo', async () => {
    // Desde DEBT-024 la pasada es un **trabajo**: se encola (202), la pantalla lo sigue y, cuando
    // termina, enseña su resumen y recarga las propuestas. El resumen lo dice el servidor en el
    // paso del trabajo, no lo compone la pantalla sumando cifras por su cuenta.
    const fetchMock = stubReviewApi();
    renderReview();

    await userEvent.click(await screen.findByRole('button', { name: 'Buscar propuestas ahora' }));

    await waitFor(() => {
      expect(peticion(fetchMock, '/classification-runs')).toBeDefined();
    });
    expect(peticion(fetchMock, '/classification-runs')?.[1]?.method).toBe('POST');
    await waitFor(() => {
      expect(peticion(fetchMock, '/jobs/job-clasificar')).toBeDefined();
    });
    expect(
      await screen.findByText(/6 sujetos: 4 propuestas nuevas, 0 ya existentes, 1 sin señales/),
    ).toBeInTheDocument();
    expect(screen.getByText(/no cambia nada por sí sola: solo propone/)).toBeInTheDocument();
  });

  it('dice por dónde va la clasificación mientras está trabajando', async () => {
    // Mientras el trabajo corre, la pantalla enseña el paso que informa el servidor —no uno que se
    // invente la interfaz— y el avance que trae (DEBT-024): el trabajo ya no salta de 0,05 a 1.
    const fetchMock = stubReviewApi({
      '/api/v1/jobs/job-clasificar': {
        body: {
          id: 'job-clasificar',
          job_type: 'classify_document',
          status: 'running',
          progress: 0.42,
          attempts: 1,
          max_attempts: 3,
          created_at: '2026-09-22T10:00:00Z',
          updated_at: '2026-09-22T10:00:05Z',
          step: 'clasificando material (40 de 312)',
          error_code: null,
          error_message: null,
          started_at: '2026-09-22T10:00:01Z',
          finished_at: null,
          cancel_requested: false,
        },
      },
    });
    renderReview();

    await userEvent.click(await screen.findByRole('button', { name: 'Buscar propuestas ahora' }));

    await waitFor(() => {
      expect(peticion(fetchMock, '/jobs/job-clasificar')).toBeDefined();
    });
    const aviso = await screen.findByText(/clasificando material \(40 de 312\)/);
    expect(aviso).toHaveTextContent('42 %');
  });
});
