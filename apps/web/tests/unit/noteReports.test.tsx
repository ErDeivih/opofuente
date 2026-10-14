/**
 * La bandeja de avisos del alumno (F16, el bloque C del objetivo).
 *
 * Lo que se comprueba, y es lo que el propietario necesita de esta pantalla:
 *
 * 1. **lo que dijo el alumno se ve entero**: su tema, su apartado, su motivo y su fecha;
 * 2. **se puede ir al apartado exacto**: el aviso enlaza al ancla de los apuntes, y cuando el
 *    apartado ya no existe lo dice en vez de mandar a un sitio que no está;
 * 3. **se despacha por la ruta auditada**: `PATCH /notes-reports/{id}` con el estado y la nota de lo
 *    que se ha hecho —una sola llamada, la que deja el evento—;
 * 4. **el estado se puede cambiar a los cuatro del modelo**, y el que ya está no se vuelve a poner;
 * 5. **los filtros y la búsqueda van en la dirección**, así que una bandeja filtrada se puede
 *    enlazar y volver a abrir.
 */

import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import type { NoteReportPage } from '../../src/api/notesReports';
import { NoteReportsPage } from '../../src/pages/NoteReportsPage';
import { curriculumFixture, oppositionsFixture } from './testUtils';
import { renderWithProviders, stubApi } from './testUtils';

const TEMA = 'IV.1';

/** Dos avisos: uno de un apartado que existe y otro que apunta a un texto ya reescrito. */
const bandeja: NoteReportPage = {
  pending: 1,
  in_progress: 1,
  reviewed: 0,
  dismissed: 0,
  total: 2,
  reports: [
    {
      id: 'aviso-1',
      topic_code: TEMA,
      topic_title: 'La Constitución Española de 1978',
      section_key: 'redes-tcpip',
      section_title: 'El modelo TCP/IP y sus cuatro capas',
      anchor: 'redes-tcpip',
      reason: 'La tabla mezcla capas con protocolos.',
      status: 'open',
      created_at: '2026-10-11T09:00:00Z',
      reviewed_at: null,
      resolution_note: null,
    },
    {
      id: 'aviso-2',
      topic_code: TEMA,
      topic_title: 'La Constitución Española de 1978',
      section_key: 'puertos-familias',
      section_title: null,
      anchor: 'puertos-familias',
      reason: 'El puerto de LDAPS no es 389.',
      status: 'in_progress',
      created_at: '2026-10-10T18:30:00Z',
      reviewed_at: null,
      resolution_note: 'Mirando el apartado de puertos.',
    },
  ],
};

function montar(entrada: string | null = null, ruta = '/admin/avisos', cuerpo = bandeja) {
  const fetchMock = stubApi({
    '/api/v1/oppositions': { body: oppositionsFixture },
    '/api/v1/convocations/conv-tai/curriculum': { body: curriculumFixture },
    'PATCH /api/v1/notes-reports/': { body: { ...bandeja.reports[0]!, status: 'reviewed' } },
    '/api/v1/notes-reports': { body: cuerpo },
  });
  renderWithProviders(<NoteReportsPage />, { route: `${ruta}${entrada ?? ''}` });
  return fetchMock;
}

function urlDe(url: RequestInfo | URL): string {
  if (typeof url === 'string') {
    return url;
  }
  return url instanceof URL ? url.href : url.url;
}

function patcheDe(fetchMock: ReturnType<typeof stubApi>) {
  const llamada = fetchMock.mock.calls.find(([, init]) => init?.method === 'PATCH');
  if (llamada === undefined) {
    throw new Error('no se hizo ninguna llamada PATCH');
  }
  const cuerpo = llamada[1]?.body;
  if (typeof cuerpo !== 'string') {
    throw new Error('la llamada PATCH no llevaba cuerpo de texto');
  }
  return { url: urlDe(llamada[0]), cuerpo: JSON.parse(cuerpo) as Record<string, unknown> };
}

/** Las filas de la bandeja, ya leídas: cada prueba mira la que le toca. */
async function filas(): Promise<HTMLElement[]> {
  const lista = await screen.findByRole('list', { name: /avisos del alumno/i });
  return within(lista).getAllByRole('listitem');
}

describe('la bandeja de avisos del alumno', () => {
  it('enseña cada aviso con su tema, su apartado, su motivo y su fecha', async () => {
    montar();

    const lista = await screen.findByRole('list', { name: /avisos del alumno/i });
    const primeros = within(lista).getAllByRole('listitem');
    expect(primeros).toHaveLength(2);

    const primera = primeros[0]!;
    expect(within(primera).getByText(TEMA)).toBeInTheDocument();
    expect(
      within(primera).getByText('El modelo TCP/IP y sus cuatro capas'),
    ).toBeInTheDocument();
    expect(within(primera).getByText('La tabla mezcla capas con protocolos.')).toBeInTheDocument();
    expect(within(primera).getByText(/Lo mandó el alumno el 2026-10-11/)).toBeInTheDocument();
    // La insignia del estado, que es la que dice en qué punto está el aviso (el botón con el mismo
    // texto es la acción de volver a ponerlo, y por eso hay dos).
    expect(within(primera).getByText('Pendiente', { selector: '.badge__text' })).toBeInTheDocument();
  });

  it('enlaza al apartado exacto de los apuntes, y lo dice cuando el apartado ya no está', async () => {
    montar();

    const primeros = await filas();

    expect(
      within(primeros[0]!).getByRole('link', { name: /ver el apartado en los apuntes/i }),
    ).toHaveAttribute('href', `/temario/${TEMA}#apartado-redes-tcpip`);
    // El segundo apunta a un texto que se ha reescrito: se dice y no se enlaza a ninguna parte.
    expect(
      within(primeros[1]!).getByText(/el apartado ya no existe en los apuntes/i),
    ).toBeInTheDocument();
    expect(
      within(primeros[1]!).queryByRole('link', { name: /ver el apartado en los apuntes/i }),
    ).toBeNull();
    expect(within(primeros[1]!).getByText(/Mirando el apartado de puertos/)).toBeInTheDocument();
  });

  it('despacha un aviso con su estado y su nota por la ruta auditada', async () => {
    const usuario = userEvent.setup();
    const fetchMock = montar();

    const primeros = await filas();
    const primera = primeros[0]!;
    await usuario.type(
      within(primera).getByLabelText(/qué has hecho/i),
      'Arreglado en la versión del 12-oct',
    );
    await usuario.click(within(primera).getByRole('button', { name: /^Resuelto: lo has arreglado/i }));

    await waitFor(() => {
      expect(patcheDe(fetchMock)).toEqual({
        url: 'http://127.0.0.1:8765/api/v1/notes-reports/aviso-1',
        cuerpo: { status: 'reviewed', note: 'Arreglado en la versión del 12-oct' },
      });
    });
  });

  it('deja despachar sin nota y no deja volver a poner el estado en el que ya está', async () => {
    const usuario = userEvent.setup();
    const fetchMock = montar();

    const primeros = await filas();
    const primera = primeros[0]!;
    // El aviso pendiente puede pasar a cualquiera de los otros tres; el que ya es, no.
    expect(within(primera).getByRole('button', { name: /^Pendiente:/i })).toBeDisabled();
    expect(within(primera).getByRole('button', { name: /^En curso:/i })).toBeEnabled();

    await usuario.click(within(primera).getByRole('button', { name: /^Descartado:/i }));

    await waitFor(() => {
      expect(patcheDe(fetchMock).cuerpo).toEqual({ status: 'dismissed' });
    });
  });

  it('filtra por estado y por búsqueda desde la dirección', async () => {
    const fetchMock = montar('?estado=open&q=LDAPS&tema=IV.1');

    await filas();

    const llamada = fetchMock.mock.calls
      .map(([url]) => urlDe(url))
      .find((url) => url.includes('/api/v1/notes-reports'));
    expect(llamada).toContain('status=open');
    expect(llamada).toContain('q=LDAPS');
    expect(llamada).toContain('topic=IV.1');
    // Y lo que se está mirando se dice: el filtro no es invisible.
    expect(screen.getByLabelText(/buscar en el motivo y en el apartado/i)).toHaveValue('LDAPS');
  });

  it('cuando no hay ningún aviso lo dice, y distingue «ninguno» de «ninguno con estos filtros»', async () => {
    montar('?estado=reviewed', '/admin/avisos', {
      pending: 3,
      in_progress: 0,
      reviewed: 0,
      dismissed: 0,
      total: 0,
      reports: [],
    });

    expect(await screen.findByText(/ningún aviso con estos filtros/i)).toBeInTheDocument();
    expect(screen.getByText(/quita algún filtro para verlos/i)).toBeInTheDocument();
  });
});
