/**
 * La bandeja del motor (F18, el bloque C del objetivo).
 *
 * Lo que se comprueba, y es lo que el propietario necesita de esta pantalla:
 *
 * 1. **lo que el motor encontró se ve entero**: la categoría, el motivo, el porqué del dominio, el
 *    enunciado de la pregunta que la provoca y la frase verificada cuando la hay;
 * 2. **se puede ir a mirarlo**: el enlace al apartado exacto de los apuntes y el enlace a la pregunta
 *    del banco. La pregunta que no se pudo situar en ninguna materia lo dice, en vez de mandar a un
 *    ancla que no está;
 * 3. **las cuatro cifras son las de la base**, no las de la página: con una sola fila en la lista,
 *    los botones de categoría siguen diciendo 291, 110, 40 y 12;
 * 4. **se despacha por la ruta auditada**: `PATCH /notes-incidents/{id}` con el estado y la nota de lo
 *    decidido —una sola llamada, la que deja el evento—;
 * 5. **el estado se puede cambiar a los cuatro del modelo**, y el que ya está no se vuelve a poner;
 * 6. **los filtros y la búsqueda van en la dirección**, así que una bandeja filtrada se puede enlazar.
 */

import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import type { IncidentPage } from '../../src/api/notesIncidents';
import { IncidentsPage } from '../../src/pages/IncidentsPage';
import { curriculumFixture, oppositionsFixture } from './testUtils';
import { renderWithProviders, stubApi } from './testUtils';

const TEMA = 'I.2';

/**
 * Las seis cifras **reclasificadas** del §2 del documento de ajustes, con **una sola** incidencia en
 * la página: es lo que prueba que los números salen de la base y no de las filas que se están
 * mirando. Son las de la copia de la base real después de la reclasificación (13-oct-2026): 430 en
 * la bandeja de las 453, y `norma_cambiada` a cero porque esa categoría exige la cita de la norma
 * vigente con su versión o fecha, y sin esa evidencia una clave que contradice los apuntes es una
 * clave sospechosa.
 */
const BANDEJA: IncidentPage = {
  pending: 430,
  in_progress: 0,
  reviewed: 0,
  dismissed: 0,
  total: 430,
  totals_by_category: {
    pregunta_mal_importada: 29,
    clave_no_fiable: 158,
    clave_sospechosa: 200,
    norma_cambiada: 0,
    hueco_sin_material: 34,
    pregunta_ambigua: 9,
  },
  incidents: [
    {
      id: 'incidencia-1',
      topic_code: TEMA,
      topic_title: 'La organización del Estado. La Administración General del Estado',
      category: 'clave_sospechosa',
      category_help:
        'los apuntes sí contestan la pregunta, y con otra letra que su clave: hay que mirar cuál de las dos está mal',
      reason: 'letra_no_coincide',
      coverage: 'conflict',
      detail: 'la clave contradice los apuntes\nclave: d (active) — los apuntes dicen: a\nvueltas: 1',
      phrase: 'la competencia la ejerce el Ministerio de Hacienda',
      attempts: 1,
      anchor: 'organizacion-age',
      section_title: 'La Administración General del Estado y sus órganos',
      question_version_id: 'pregunta-1',
      stem: '¿Quién ejerce la competencia sobre el patrimonio del Estado?',
      set_title: 'Banco privado del propietario',
      source_document_id: 'documento-1',
      source_document_title: 'Cuestionarios del material propio',
      source_document_type: 'private_question_bank',
      source_version_status: 'superseded',
      source_version_label: 'v2',
      status: 'open',
      created_at: '2026-10-12T11:26:17Z',
      reviewed_at: null,
      resolution_note: null,
    },
  ],
};

function montar(entrada = '', ruta = '/admin/incidencias', cuerpo: IncidentPage = BANDEJA) {
  const fetchMock = stubApi({
    '/api/v1/oppositions': { body: oppositionsFixture },
    '/api/v1/convocations/conv-tai/curriculum': { body: curriculumFixture },
    'PATCH /api/v1/notes-incidents/': { body: { ...cuerpo.incidents[0], status: 'reviewed' } },
    '/api/v1/notes-incidents': { body: cuerpo },
  });
  renderWithProviders(<IncidentsPage />, { route: `${ruta}${entrada}` });
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

/** Las filas de la bandeja, ya leídas. */
async function filas(): Promise<HTMLElement[]> {
  const lista = await screen.findByRole('list', { name: /incidencias del motor/i });
  return within(lista).getAllByRole('listitem');
}

describe('la bandeja del motor', () => {
  it('enseña la incidencia con su categoría, su motivo, su porqué y la pregunta que la provoca', async () => {
    montar();

    const primeros = await filas();
    expect(primeros).toHaveLength(1);
    const fila = primeros[0]!;

    expect(within(fila).getByText('Clave sospechosa')).toBeInTheDocument();
    expect(
      within(fila).getByText(/los apuntes contestan con otra letra que la respuesta correcta/i),
    ).toBeInTheDocument();
    // El porqué, tal cual lo manda el dominio desde el servidor: aquí no se copia ni se resume.
    expect(
      within(fila).getByText(/los apuntes sí contestan la pregunta, y con otra letra que su clave/i),
    ).toBeInTheDocument();
    expect(
      within(fila).getByText('¿Quién ejerce la competencia sobre el patrimonio del Estado?'),
    ).toBeInTheDocument();
    expect(
      within(fila).getByText('la competencia la ejerce el Ministerio de Hacienda'),
    ).toBeInTheDocument();
    expect(within(fila).getByText(TEMA)).toBeInTheDocument();
    expect(within(fila).getByText('Pendiente', { selector: '.badge__text' })).toBeInTheDocument();
  });

  it('lleva al apartado de los apuntes, a la pregunta del banco y al material de la clave', async () => {
    montar();

    const fila = (await filas())[0]!;

    expect(
      within(fila).getByRole('link', { name: /ver el apartado en los apuntes/i }),
    ).toHaveAttribute('href', `/temario/${TEMA}#apartado-organizacion-age`);
    expect(
      within(fila).getByRole('link', { name: /ver la pregunta en el banco/i }),
    ).toHaveAttribute('href', '/admin/preguntas?pregunta=pregunta-1');
    // El material del que salió la clave, con el estado de su versión: una versión **sustituida** es
    // justo lo que hay que mirar cuando la clave contradice la norma.
    expect(within(fila).getByRole('link', { name: /cuestionarios del material propio/i })).toHaveAttribute(
      'href',
      '/admin/biblioteca?documento=documento-1',
    );
    expect(within(fila).getByText(/v2, sustituida/i)).toBeInTheDocument();
  });

  it('dice que la pregunta no se pudo situar en vez de mandar a un ancla que no está', async () => {
    montar('', '/admin/incidencias', {
      ...BANDEJA,
      incidents: [
        {
          ...BANDEJA.incidents[0]!,
          category: 'pregunta_ambigua',
          category_help:
            'la pregunta no se puede situar en ninguna materia del tema ni por su enunciado ni por el texto de sus hechos: no hay apartado de apuntes donde contestarla, así que hay que reescribirla o asignarle un tema a mano (no se ha metido en ningún cajón de «otros»)',
          reason: 'sin_materia_en_el_indice',
          anchor: '',
          section_title: null,
          phrase: null,
        },
      ],
    });

    const fila = (await filas())[0]!;

    expect(within(fila).getByText(/no se pudo situar en ninguna materia/i)).toBeInTheDocument();
    expect(
      within(fila).queryByRole('link', { name: /ver el apartado en los apuntes/i }),
    ).toBeNull();
    // Y el enlace a la pregunta sigue estando: es lo que hay que reescribir.
    expect(within(fila).getByRole('link', { name: /ver la pregunta en el banco/i })).toBeInTheDocument();
  });

  it('las cifras por categoría son las de la base, no las de la página', async () => {
    montar();

    await filas();

    const categorias = screen.getByRole('group', { name: /filtrar por categoría/i });
    expect(within(categorias).getByRole('button', { name: /todas\s*430/i })).toBeInTheDocument();
    // Las seis, en el orden de comprobación del §2, y con la cifra medida en la base.
    expect(
      within(categorias).getByRole('button', { name: /pregunta mal importada\s*29/i }),
    ).toBeInTheDocument();
    expect(within(categorias).getByRole('button', { name: /clave no fiable\s*158/i })).toBeInTheDocument();
    expect(within(categorias).getByRole('button', { name: /clave sospechosa\s*200/i })).toBeInTheDocument();
    expect(within(categorias).getByRole('button', { name: /norma cambiada\s*0/i })).toBeInTheDocument();
    expect(within(categorias).getByRole('button', { name: /hueco sin material\s*34/i })).toBeInTheDocument();
    expect(within(categorias).getByRole('button', { name: /pregunta ambigua\s*9/i })).toBeInTheDocument();
    // Un cero se enseña: un botón que desaparece obliga a la pantalla a inventarse la ausencia.
    expect(within(categorias).getByRole('button', { name: /norma cambiada\s*0/i })).toBeEnabled();
    // La lista trae una y el total dice 430: el número no se cuenta de las filas.
    expect(screen.getByText(/· 430 con estos filtros/i)).toBeInTheDocument();
  });

  it('dice cuándo una clave sospechosa no trae la frase que la demuestra', async () => {
    montar('', '/admin/incidencias', {
      ...BANDEJA,
      incidents: [{ ...BANDEJA.incidents[0]!, phrase: null }],
    });

    const fila = (await filas())[0]!;

    // Sin la cita verificada la sospecha es más débil, y cambia lo que hay que hacer: abrir la
    // pregunta en lugar de leer la frase.
    expect(within(fila).getByText(/sin la frase que lo demuestra/i)).toBeInTheDocument();
    expect(within(fila).queryByText(/la competencia la ejerce el Ministerio/i)).toBeNull();
  });

  it('despacha una incidencia con su estado y su nota por la ruta auditada', async () => {
    const usuario = userEvent.setup();
    const fetchMock = montar();

    const fila = (await filas())[0]!;
    await usuario.type(
      within(fila).getByLabelText(/qué has decidido/i),
      'La clave estaba mal; corregida.',
    );
    await usuario.click(within(fila).getByRole('button', { name: /^Resuelta: has hecho/i }));

    await waitFor(() => {
      expect(patcheDe(fetchMock)).toEqual({
        url: 'http://127.0.0.1:8765/api/v1/notes-incidents/incidencia-1',
        cuerpo: { status: 'reviewed', note: 'La clave estaba mal; corregida.' },
      });
    });
  });

  it('deja despachar sin nota y no deja volver a poner el estado en el que ya está', async () => {
    const usuario = userEvent.setup();
    const fetchMock = montar();

    const fila = (await filas())[0]!;
    expect(within(fila).getByRole('button', { name: /^Pendiente:/i })).toBeDisabled();
    // «Descartada» no es un adorno: es la salida para la incidencia en la que el motor se equivoca.
    expect(within(fila).getByRole('button', { name: /^Descartada:/i })).toBeEnabled();

    await usuario.click(within(fila).getByRole('button', { name: /^Descartada:/i }));

    await waitFor(() => {
      expect(patcheDe(fetchMock).cuerpo).toEqual({ status: 'dismissed' });
    });
  });

  it('filtra por categoría, estado, tema y búsqueda desde la dirección', async () => {
    const fetchMock = montar('?categoria=norma_cambiada&estado=open&tema=I.2&q=patrimonio');

    await filas();

    const llamada = fetchMock.mock.calls
      .map(([url]) => urlDe(url))
      .find((url) => url.includes('/api/v1/notes-incidents'));
    expect(llamada).toContain('category=norma_cambiada');
    expect(llamada).toContain('status=open');
    expect(llamada).toContain('topic=I.2');
    expect(llamada).toContain('q=patrimonio');
    // Y lo que se está mirando se dice: el filtro no es invisible.
    expect(screen.getByLabelText(/buscar en la pregunta, el motivo y el apartado/i)).toHaveValue(
      'patrimonio',
    );
    expect(
      screen.getByRole('button', { name: /norma cambiada\s*0/i, pressed: true }),
    ).toBeInTheDocument();
  });

  it('cuando no hay ninguna lo dice, y distingue «ninguna» de «ninguna con estos filtros»', async () => {
    montar('?estado=reviewed', '/admin/incidencias', {
      ...BANDEJA,
      total: 0,
      incidents: [],
    });

    expect(await screen.findByText(/ninguna incidencia con estos filtros/i)).toBeInTheDocument();
    expect(screen.getByText(/quita algún filtro para verlas/i)).toBeInTheDocument();
  });
});
