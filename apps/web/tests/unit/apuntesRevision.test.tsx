/**
 * La revisión de los apuntes (F24, §4.3 del objetivo).
 *
 * Lo que se comprueba, que es lo que el propietario necesita de estas dos pantallas:
 *
 * 1. **la tabla enseña los temas con su estado** y, en los que esperan una decisión, **el motivo con su
 *    cifra**: las frases y los números los compone el servidor y aquí se pintan tal cual (no se
 *    recalcula ningún porcentaje ni se resume ningún párrafo);
 * 2. **la ficha lee el borrador apartado a apartado**, con su texto y su forma, y con las cifras de
 *    cada apartado; «los peores primero» reordena lo que hay que mirar sin cambiar el número que el
 *    apartado ocupa en el tema;
 * 3. **se aprueba y se rechaza por la ruta auditada**: `POST /notes-review/{codigo}/decision` con la
 *    decisión y la nota, en una sola llamada;
 * 4. **rechazar sin motivo no se puede enviar**, y el motivo del rechazo viaja en el cuerpo;
 * 5. **al aprobar se dice qué ha pasado**: si el tema ha quedado publicado o qué puerta lo frena.
 */

import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';

import type { NotesReviewFile, NotesReviewPage, NotesReviewResult } from '../../src/api/notesReview';
import { NotesReviewPage as TablaPage } from '../../src/pages/NotesReviewPage';
import { NotesReviewTopicPage } from '../../src/pages/NotesReviewTopicPage';
import { renderWithProviders, stubApi } from './testUtils';

/** El tema de la prueba: el publicado y el borrador, como en la base real del 14 de octubre de 2026. */
const PUBLICADO = 'IV.2';
const BORRADOR = 'I.4';

/**
 * La tabla: un tema publicado (sin medir) y un borrador medido que **cumple las puertas**.
 *
 * Es el caso que decide el diseño: I.4 medía 489/542 = 90,2 % el 14 de octubre de 2026, así que su
 * motivo no es «le falta cobertura» sino «no está publicado y aprobarlo lo publica».
 */
const TABLA: NotesReviewPage = {
  counters: {
    topics_total: 33,
    with_notes: 19,
    published: 15,
    draft: 4,
    without_notes: 14,
    approved: 1,
    rejected: 0,
    pending_decision: 4,
  },
  topics: [
    {
      code: PUBLICADO,
      title: 'Administración de bases de datos. Sistemas de almacenamiento y su virtualización.',
      block_code: 'IV',
      block_title: 'Tecnología básica',
      state: 'published',
      sections_written: 16,
      facts: 1543,
      checks: { total: 807, covered: 767, gaps: 0, doubtful: 39, conflicts: 1 },
      incidents_open: 36,
      incidents_by_category: { norma_cambiada: 35, clave_sospechosa: 1 },
      version: { id: 'version-1', built_at: '2026-10-12T11:17:00Z' },
      review: null,
      reasons: [
        {
          code: 'publicado',
          text: 'Está publicado: su versión se archivó al pasar las dos puertas.',
          figure: null,
        },
        {
          code: 'incidencias',
          text: '36 incidencias del motor sin despachar (35 normas cambiadas, 1 respuestas correctas que no cuadran).',
          figure: '36 incidencia(s)',
        },
      ],
      measured: false,
      coverage: null,
      coverage_all_keys: null,
      coverage_threshold: 0.9,
    },
    {
      code: BORRADOR,
      title: 'El EBEP, la Ley 19/2013 de transparencia y la Agenda 2030',
      block_code: 'I',
      block_title: 'Organización del Estado y Administración electrónica',
      state: 'draft',
      sections_written: 15,
      facts: 1056,
      checks: { total: 602, covered: 517, gaps: 0, doubtful: 30, conflicts: 55 },
      incidents_open: 55,
      incidents_by_category: { clave_sospechosa: 30, norma_cambiada: 17, pregunta_ambigua: 5 },
      version: null,
      review: null,
      reasons: [
        {
          code: 'a_las_puertas',
          text: 'Cumple las dos puertas y **no está publicado**: no es que le falte nada, es que nadie ha archivado su versión. Aprobarlo la publica.',
          figure: '489/542 = 90,2 %',
        },
        {
          code: 'conflictos',
          text: '30 las contestan los apuntes con otra letra que su respuesta correcta: hay que decidir cuál de las dos está mal.',
          figure: '30 preguntas',
        },
        {
          code: 'sin_decision',
          text: 'Nadie ha revisado este tema todavía: no hay ninguna decisión escrita sobre él.',
          figure: null,
        },
      ],
      measured: true,
      coverage: [489, 542],
      coverage_all_keys: [489, 556],
      coverage_threshold: 0.9,
    },
    {
      code: 'I.3',
      title: 'El Gobierno: composición, nombramiento y funciones',
      block_code: 'I',
      block_title: 'Organización del Estado y Administración electrónica',
      state: 'none',
      sections_written: 0,
      facts: 0,
      checks: { total: 0, covered: 0, gaps: 0, doubtful: 0, conflicts: 0 },
      incidents_open: 0,
      incidents_by_category: {},
      version: null,
      review: null,
      reasons: [
        {
          code: 'sin_apartados',
          text: 'Este tema todavía no tiene apuntes escritos: no hay nada que revisar.',
          figure: null,
        },
      ],
      measured: false,
      coverage: null,
      coverage_all_keys: null,
      coverage_threshold: 0.9,
    },
  ],
};

const APARTADOS: NotesReviewFile = {
  topic: TABLA.topics[1]!,
  // La ficha va paginada: tres apartados en una sola hoja de seis.
  sections_total: 3,
  page: 1,
  pages: 1,
  page_size: 6,
  sections: [
    {
      key: 'marco-constitucional',
      title: 'El marco constitucional del empleo público',
      epigraph_code: 'I.4.1',
      anchor: 'marco-constitucional',
      position: 1,
      body_markdown:
        '## El EBEP\n\nEl texto refundido del EBEP regula los derechos y deberes.\n\n' +
        '| Norma | Año |\n| --- | --- |\n| Ley 19/2013 | 2013 |\n',
      words: 12,
      facts_total: 40,
      covered: 300,
      gaps: 0,
      doubtful: 10,
      conflicts: 30,
      needs_review_reason: null,
      worst: 40,
    },
    {
      key: 'agenda-2030',
      title: 'La Agenda 2030 y los Objetivos de Desarrollo Sostenible',
      epigraph_code: 'I.4.3',
      anchor: 'agenda-2030',
      position: 2,
      body_markdown: '## La Agenda 2030\n\nLos diecisiete objetivos los aprobó la Asamblea General.\n',
      words: 11,
      facts_total: 12,
      covered: 100,
      gaps: 0,
      doubtful: 1,
      conflicts: 0,
      needs_review_reason: 'sin material de apoyo',
      worst: 1,
    },
    {
      key: 'ley-transparencia',
      title: 'La Ley 19/2013, de transparencia',
      epigraph_code: 'I.4.2',
      anchor: 'ley-transparencia',
      position: 3,
      body_markdown: '## La Ley 19/2013\n\nRegula el acceso a la información pública.\n',
      words: 9,
      facts_total: 20,
      covered: 80,
      gaps: 3,
      doubtful: 2,
      conflicts: 5,
      needs_review_reason: null,
      worst: 10,
    },
  ],
};

/** Lo que contesta el servidor al aprobar: el tema publicado, con su decisión escrita. */
const RESULTADO: NotesReviewResult = {
  topic: {
    ...TABLA.topics[1]!,
    state: 'published',
    version: { id: 'version-nueva', built_at: '2026-10-14T08:46:21Z' },
    review: {
      decision: 'approved',
      note: 'leído el 14 de octubre',
      actor: 'local',
      reviewed_at: '2026-10-14T08:46:21Z',
    },
    reasons: [
      {
        code: 'publicado',
        text: 'Está publicado: su versión se archivó al pasar las dos puertas.',
        figure: '489/542 = 90,2 %',
      },
    ],
  },
  published: true,
  version_created: true,
  blocked_by: null,
};

function montarTabla() {
  return stubApi({ '/api/v1/notes-review': { body: TABLA } });
}

function montarFicha(ficha: NotesReviewFile = APARTADOS) {
  return stubApi({
    'POST /api/v1/notes-review/': { body: RESULTADO },
    '/api/v1/notes-review/': { body: ficha },
  });
}

/**
 * Las filas de la tabla: los hijos directos de la lista.
 *
 * No vale `getAllByRole('listitem')` a secas: **el motivo de cada tema es otra lista** dentro de su
 * fila, así que la consulta por rol devolvería también los motivos. Se leen los hijos directos, que
 * son las filas.
 */
async function filas(): Promise<HTMLElement[]> {
  const lista = await screen.findByRole('list', { name: /temas con apuntes/i });
  return Array.from(lista.children).filter((hijo): hijo is HTMLElement => hijo.tagName === 'LI');
}

/**
 * Monta la ficha **con su ruta**, que es como llega el código del tema.
 *
 * La pantalla lee el código de la dirección (`/admin/apuntes/:codigo`), así que sin su `Route` el
 * parámetro no existe, la consulta no se lanza y la pantalla se queda cargando. Es el mismo motivo por
 * el que las otras pantallas que llevan parámetro se prueban así (`studentApuntes.test.tsx`).
 */
function renderFicha(codigo: string) {
  return renderWithProviders(
    <Routes>
      <Route path="/admin/apuntes/:codigo" element={<NotesReviewTopicPage />} />
    </Routes>,
    { route: `/admin/apuntes/${codigo}` },
  );
}

/** Los apartados de la ficha, en el orden en el que están pintados. */
function apartados(): HTMLElement[] {
  return screen.getAllByRole('article');
}

/** El título de un apartado tal como se lee: su número y su nombre. */
function tituloDe(apartado: HTMLElement): string {
  return within(apartado).getAllByRole('heading', { level: 3 })[0]?.textContent ?? '';
}

/** La URL de una llamada simulada, escrita. */
function urlDe(url: RequestInfo | URL): string {
  if (typeof url === 'string') {
    return url;
  }
  return url instanceof URL ? url.href : url.url;
}

/** La decisión que se mandó por la ruta auditada: su dirección y su cuerpo, ya leído. */
function decisionEnviada(fetchMock: ReturnType<typeof stubApi>): {
  url: string;
  cuerpo: unknown;
} {
  const llamada = fetchMock.mock.calls.find(([, init]) => init?.method === 'POST');
  if (llamada === undefined) {
    throw new Error('no se hizo ninguna llamada POST');
  }
  const cuerpo = llamada[1]?.body;
  if (typeof cuerpo !== 'string') {
    throw new Error('la llamada POST no llevaba cuerpo de texto');
  }
  return { url: urlDe(llamada[0]), cuerpo: JSON.parse(cuerpo) };
}

describe('la tabla de la revisión de apuntes', () => {
  it('enseña el estado de cada tema y el motivo del borrador con su cifra', async () => {
    montarTabla();
    renderWithProviders(<TablaPage />, { route: '/admin/apuntes' });

    const temas = await filas();
    expect(temas).toHaveLength(2);

    const publicado = temas[0]!;
    expect(within(publicado).getByText('Publicado')).toBeInTheDocument();
    expect(within(publicado).getByText('16')).toBeInTheDocument();
    // Un tema publicado no se mide en la tabla y lo dice, en vez de enseñar un cero que mentiría.
    expect(within(publicado).getByText(/sin medir en esta tabla/i)).toBeInTheDocument();

    const borrador = temas[1]!;
    expect(within(borrador).getByText('En borrador')).toBeInTheDocument();
    // La cifra de la puerta, tal cual la manda el servidor: 489 de 542, con su porcentaje.
    expect(within(borrador).getByText(/489 de 542/)).toBeInTheDocument();
    expect(within(borrador).getByText('(90,2 %)')).toBeInTheDocument();
    // La cifra la compone el servidor, y el §2.2 alcanza también a su prosa: era la última frase
    // con el punto del decimal. La aserción esperaba el formato viejo.
    expect(within(borrador).getByText('489/542 = 90,2 %')).toBeInTheDocument();
    expect(within(borrador).getByText(/Cumple las dos puertas/i)).toBeInTheDocument();
    expect(within(borrador).getByText(/nadie ha revisado este tema todavía/i)).toBeInTheDocument();
    expect(within(borrador).getByText('30 preguntas')).toBeInTheDocument();
  });

  it('lleva a la ficha del tema para leerlo y decidirlo', async () => {
    montarTabla();
    renderWithProviders(<TablaPage />, { route: '/admin/apuntes' });

    const temas = await filas();

    expect(within(temas[1]!).getByRole('link', { name: /leer y decidir/i })).toHaveAttribute(
      'href',
      `/admin/apuntes/${BORRADOR}`,
    );
  });

  it('cuenta lo que espera una decisión con lo que dice el servidor', async () => {
    montarTabla();
    renderWithProviders(<TablaPage />, { route: '/admin/apuntes' });

    expect(await screen.findByText(/esperan tu decisión/i)).toBeInTheDocument();
    expect(screen.getByText('4')).toBeInTheDocument();
    expect(screen.getByText(/15 publicados y 4 en borrador/i)).toBeInTheDocument();
  });

  it('dice cuáles no tienen apuntes sin mezclarlos con los que se revisan', async () => {
    montarTabla();
    renderWithProviders(<TablaPage />, { route: '/admin/apuntes' });

    const seccion = await screen.findByRole('region', { name: /temas sin apuntes escritos/i });

    expect(within(seccion).getByText(/I\.3/)).toBeInTheDocument();
  });
});

describe('la ficha de un tema', () => {
  it('lee el borrador apartado a apartado, con su texto y sus cifras', async () => {
    montarFicha();
    renderFicha(BORRADOR);

    expect(
      await screen.findByRole('heading', { level: 1, name: new RegExp(BORRADOR) }),
    ).toBeInTheDocument();
    // El texto de los apuntes, con su forma: el título del epígrafe y su tabla.
    expect(await screen.findByText('El EBEP')).toBeInTheDocument();
    expect(screen.getByRole('table')).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: 'Norma' })).toBeInTheDocument();
    // Y las cifras de cada apartado, que es lo que dice dónde mirar.
    const primero = apartados()[0]!;
    expect(within(primero).getByText(/40 hechos · 12 palabras/)).toBeInTheDocument();
    expect(within(primero).getByText(/300 cubiertas/)).toBeInTheDocument();
    expect(within(primero).getByText(/30 en conflicto/)).toBeInTheDocument();
    expect(screen.getByText(/El motor lo dejó marcado: sin material de apoyo/)).toBeInTheDocument();
  });

  it('pide los peores al servidor, que es quien ordena el tema entero y no la hoja', async () => {
    const fetchMock = montarFicha();
    renderFicha(BORRADOR);
    const usuario = userEvent.setup();

    await screen.findByText('El EBEP');
    const ordenLectura = apartados().map(tituloDe);
    expect(ordenLectura[0]).toContain('1.');
    expect(ordenLectura[0]).toContain('marco constitucional');
    expect(ordenLectura[1]).toContain('2.');
    expect(ordenLectura[2]).toContain('3.');

    await usuario.click(await screen.findByRole('button', { name: /los peores primero/i }));

    // El orden ya no se compone en la pantalla: la ficha llega **cortada** por el servidor, así que
    // ordenar aquí ordearía la hoja («los peores de estos seis») y no el tema. Se pide `orden=peores`
    // y se vuelve a la primera hoja, que es donde están los peores.
    await waitFor(() => {
      const pedidas = fetchMock.mock.calls.map(([url]) => urlDe(url));
      expect(pedidas.some((url) => url.includes('orden=peores'))).toBe(true);
    });
  });

  it('aprueba por la ruta auditada y dice que el tema ha quedado publicado', async () => {
    const fetchMock = montarFicha();
    renderFicha(BORRADOR);
    const usuario = userEvent.setup();

    await screen.findByText('El EBEP');
    await usuario.type(screen.getByLabelText(/qué has decidido/i), 'leído el 14 de octubre');
    await usuario.click(screen.getByRole('button', { name: /aprobar los apuntes/i }));

    const enviada = decisionEnviada(fetchMock);
    expect(enviada.url).toContain(`/api/v1/notes-review/${BORRADOR}/decision`);
    expect(enviada.cuerpo).toEqual({
      decision: 'approved',
      note: 'leído el 14 de octubre',
    });
    expect(await screen.findByRole('status')).toHaveTextContent(/el tema ha quedado publicado/i);
  });

  it('rechaza con el motivo, y sin motivo no deja enviarlo', async () => {
    const fetchMock = montarFicha();
    renderFicha(BORRADOR);
    const usuario = userEvent.setup();

    await screen.findByText('El EBEP');
    const rechazar = screen.getByRole('button', { name: /rechazar con este motivo/i });
    // Sin motivo no se puede rechazar: el botón está apagado y dice por qué.
    expect(rechazar).toBeDisabled();
    expect(rechazar).toHaveAttribute('title', expect.stringMatching(/hace falta el motivo/i));

    await usuario.type(
      screen.getByLabelText(/qué has decidido/i),
      'faltan 43 preguntas por contestar',
    );
    await waitFor(() => {
      expect(rechazar).toBeEnabled();
    });
    await usuario.click(rechazar);

    expect(decisionEnviada(fetchMock).cuerpo).toEqual({
      decision: 'rejected',
      note: 'faltan 43 preguntas por contestar',
    });
  });

  it('un tema sin apuntes no se puede aprobar y lo dice', async () => {
    montarFicha({ topic: TABLA.topics[2]!, sections: [], sections_total: 0, page: 1, pages: 1, page_size: 6 });
    renderFicha('I.3');

    expect(await screen.findByText(/no hay nada que leer ni que decidir/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /aprobar los apuntes/i })).toBeDisabled();
  });
});
