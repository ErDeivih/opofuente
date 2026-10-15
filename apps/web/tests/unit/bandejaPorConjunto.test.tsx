/**
 * La bandeja agrupada por conjunto (F31, §2 del cierre del objetivo).
 *
 * Lo que se comprueba, y es lo que hace que una bandeja de cientos de filas se pueda trabajar:
 *
 * 1. **un conjunto es una fila**, con su resumen («50 claves sospechosas») y su cifra de decisión;
 * 2. **lo oficial va aparte y no admite acciones en bloque**: la fila del examen llega con la lista
 *    de acciones vacía —la decide el servidor— y la pantalla **no las inventa**;
 * 3. **las acciones son en bloque**: una pulsación es **una** llamada a
 *    `POST /notes-incidents/tray/bulk` con el conjunto entero, no una por incidencia;
 * 4. **la fila despliega**: pide las incidencias de ese conjunto —`?set=…`— y las enseña con la misma
 *    fila que la lista de abajo.
 */

import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import type { TrayPage } from '../../src/api/notesIncidents';
import { IncidentsPage } from '../../src/pages/IncidentsPage';
import {
  curriculumFixture,
  oppositionsFixture,
  renderWithProviders,
  stubApi,
} from './testUtils';

const CONJUNTO = 'conjunto-1';
const CONJUNTO_OFICIAL = 'conjunto-oficial';

const BANDEJA: TrayPage = {
  official_section: [
    {
      set_id: CONJUNTO_OFICIAL,
      title: 'TAI ingreso libre 2025 · modelo A (examen oficial INAP)',
      section: 'oficial',
      origin_scope: 'age',
      key_reliability: 'fiable',
      official: true,
      pendientes: { pregunta_ambigua: 2 },
      total_pendiente: 2,
      propuestas: 0,
      entradas_de_decision: 2,
      resumen: '2 preguntas que no se pueden juzgar',
      acciones: [],
    },
  ],
  rest: [
    {
      set_id: CONJUNTO,
      title: 'TEST VARIOS',
      section: 'resto',
      origin_scope: 'desconocida',
      key_reliability: 'no_fiable',
      official: false,
      pendientes: { clave_sospechosa: 50, hueco_sin_material: 3 },
      total_pendiente: 53,
      propuestas: 12,
      entradas_de_decision: 1,
      resumen: '50 claves sospechosas · 3 huecos sin material',
      acciones: ['aceptar_derivadas', 'dejar_fuera', 'no_son_preguntas'],
    },
  ],
  filas: 2,
  total_pendiente: 55,
  propuestas: 12,
  entradas_de_decision: 3,
};

const INCIDENCIA = {
  id: 'incidencia-1',
  topic_code: 'IV.1',
  topic_title: 'Redes',
  category: 'clave_sospechosa' as const,
  category_help: 'la clave contradice lo que dicen los apuntes',
  reason: 'letra_no_coincide' as const,
  coverage: 'conflict' as const,
  detail: 'la clave contradice los apuntes',
  phrase: 'el puerto de LDAPS es el 636',
  attempts: 1,
  anchor: 'redes-tcpip',
  section_title: 'El modelo TCP/IP y sus cuatro capas',
  question_version_id: 'pregunta-1',
  stem: 'El puerto de LDAPS es el 636.',
  set_title: 'TEST VARIOS',
  source_document_id: null,
  source_document_title: null,
  source_document_type: null,
  source_version_status: null,
  source_version_label: null,
  status: 'open' as const,
  created_at: '2026-10-15T10:00:00Z',
  reviewed_at: null,
  resolution_note: null,
};

function montar() {
  const fetchMock = stubApi({
    '/api/v1/oppositions': { body: oppositionsFixture },
    '/api/v1/convocations/conv-tai/curriculum': { body: curriculumFixture },
    'POST /api/v1/notes-incidents/tray/bulk': {
      body: { action: 'dejar_fuera', set_id: CONJUNTO, incidents: 53, keys_written: 0 },
    },
    '/api/v1/notes-incidents/tray/actions': {
      body: {
        aceptar_derivadas: 'acepta todas las claves derivadas del conjunto',
        dejar_fuera: 'deja el conjunto fuera de tests, simulacros y repasos',
        no_son_preguntas: 'el conjunto no son preguntas contestables',
      },
    },
    '/api/v1/notes-incidents/tray': { body: BANDEJA },
    '/api/v1/notes-incidents': {
      body: {
        pending: 1,
        in_progress: 0,
        reviewed: 0,
        dismissed: 0,
        total: 1,
        totals_by_category: {},
        incidents: [INCIDENCIA],
      },
    },
  });
  renderWithProviders(<IncidentsPage />, { route: '/admin/incidencias' });
  return fetchMock;
}

function urlDe(url: RequestInfo | URL): string {
  if (typeof url === 'string') {
    return url;
  }
  return url instanceof URL ? url.href : url.url;
}

/** La fila de un conjunto, por su título. */
async function filaDe(titulo: string): Promise<HTMLElement> {
  const lista = await screen.findByRole('list', { name: /avisos agrupados por examen/i });
  const filas = within(lista).getAllByRole('listitem');
  const fila = filas.find((cual) => within(cual).queryByText(titulo) !== null);
  if (fila === undefined) {
    throw new Error(`no hay ninguna fila para ${titulo}`);
  }
  return fila;
}

describe('la bandeja agrupada por conjunto', () => {
  it('enseña cada conjunto como una fila, con su resumen y su cifra de decisión', async () => {
    montar();

    const fila = await filaDe('TEST VARIOS');
    expect(within(fila).getByText(/50 claves sospechosas/)).toBeInTheDocument();
    expect(within(fila).getByText(/3 huecos sin material/)).toBeInTheDocument();
    // La cifra que mide si la bandeja sirve: 53 incidencias de un conjunto no oficial son **una**
    // entrada de decisión, y la pantalla la enseña tal como la cuenta el servidor.
    expect(within(fila).getByText(/cuenta como una decisión tuya/)).toBeInTheDocument();
    // Las propuestas se cuentan aparte de lo pendiente: significan cosas distintas —una se aprueba
    // en bloque y la otra espera criterio— y la fila las enseña por separado.
    const cifras = within(fila).getByText((_texto, elemento) =>
      Boolean(
        elemento?.classList.contains('conjunto__cifras') &&
          (elemento.textContent ?? '').includes('12 respuestas derivadas'),
      ),
    );
    expect(cifras).toBeInTheDocument();
  });

  it('pone lo oficial aparte y no le ofrece ninguna acción en bloque', async () => {
    montar();

    const seccion = await screen.findByRole('region', { name: /exámenes oficiales/i });
    const fila = within(seccion).getByRole('listitem');
    expect(
      within(fila).getByText('TAI ingreso libre 2025 · modelo A (examen oficial INAP)'),
    ).toBeInTheDocument();
    expect(within(fila).getByText(/no se cambia desde aquí/i)).toBeInTheDocument();
    // Las acciones las dice el servidor: la fila oficial llega con la lista vacía y aquí no se
    // inventa ninguna. Una clave oficial no se toca ni desde un botón.
    expect(within(fila).queryByRole('button', { name: /Aceptar todas las derivadas/i })).toBeNull();
    expect(
      within(fila).queryByRole('button', { name: /Dejar fuera del estudio/i }),
    ).toBeNull();
    expect(
      within(fila).getByRole('button', { name: /Ver lo que tiene dentro/i }),
    ).toBeInTheDocument();
  });

  it('aplica una acción en bloque con una sola llamada, con el conjunto entero', async () => {
    const fetchMock = montar();
    const usuario = userEvent.setup();

    const fila = await filaDe('TEST VARIOS');
    await usuario.click(
      within(fila).getByRole('button', { name: /Dejar fuera del estudio/i }),
    );

    await waitFor(() => {
      const llamada = fetchMock.mock.calls.find(
        ([url, init]) =>
          urlDe(url).includes('/notes-incidents/tray/bulk') && init?.method === 'POST',
      );
      expect(llamada).toBeDefined();
      const crudo = llamada?.[1]?.body;
      const cuerpo = JSON.parse(typeof crudo === 'string' ? crudo : '') as Record<string, unknown>;
      expect(cuerpo).toEqual({ action: 'dejar_fuera', set_id: CONJUNTO });
    });
    // Una pulsación, una llamada: no hay una petición por incidencia.
    const envios = fetchMock.mock.calls.filter(
      ([url, init]) =>
        urlDe(url).includes('/notes-incidents/tray/bulk') && init?.method === 'POST',
    );
    expect(envios).toHaveLength(1);
  });

  it('despliega la fila: pide las incidencias del conjunto y las enseña', async () => {
    const fetchMock = montar();
    const usuario = userEvent.setup();

    const fila = await filaDe('TEST VARIOS');
    await usuario.click(within(fila).getByRole('button', { name: /Ver lo que tiene dentro/i }));

    await waitFor(() => {
      const llamada = fetchMock.mock.calls.find(([url]) =>
        urlDe(url).includes('/notes-incidents?') && urlDe(url).includes(`set=${CONJUNTO}`),
      );
      expect(llamada).toBeDefined();
    });

    const dentro = await within(fila).findByRole('list', { name: /avisos de test varios/i });
    expect(within(dentro).getByText('El puerto de LDAPS es el 636.')).toBeInTheDocument();
    expect(within(dentro).getByText('Clave sospechosa')).toBeInTheDocument();
  });
});
