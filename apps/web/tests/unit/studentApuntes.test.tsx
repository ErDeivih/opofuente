/**
 * La lectura de los apuntes en la zona del alumno (F13) y su lectura **por capítulos** (F35, §3.1).
 *
 * Lo que se comprueba aquí es lo que una captura no puede demostrar:
 *
 * 1. **la estructura de columnas**: el índice de capítulos que lleva a su capítulo, la columna de
 *    lectura del capítulo abierto y la nota al margen **dentro** de su apartado;
 * 2. **que se sirve un capítulo cada vez**: el apartado de otro capítulo no está en la página, y el
 *    índice lleva a él por su capítulo;
 * 3. **que un anclaje de otro capítulo abre el suyo**: `/temario/IV.7#apartado-udp` con el primer
 *    capítulo abierto acaba pidiendo `?capitulo=IV.7.2`, que es lo que hace que «Ver en apuntes» no
 *    deje al alumno arriba;
 * 4. **las tablas se pintan como tablas** (con su cabecera) y **en su propio marco**, con nombre y
 *    enfocable, porque se desplazan;
 * 5. **el recuento de la nota al margen está plegado**: la frase explicativa no se ve hasta que el
 *    lector abre «Esto se pregunta» (la regla de la zona del alumno);
 * 6. **el botón «Esto está mal»**: pide el motivo en una línea, no deja enviarlo vacío y manda el
 *    aviso con la clave del apartado;
 * 7. **el estado**: un tema en borrador se lee entero y lo dice; uno publicado lleva la marca; y uno
 *    sin apuntes no ofrece nada que leer.
 */

import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';

import type { StudentNotes } from '../../src/api/studentStudy';
import { TopicNotesPage } from '../../src/pages/student/TopicNotesPage';
import {
  notesFixture,
  notesPublishedFixture,
  notesSegundoCapituloFixture,
  topicFixture,
} from './studentFixtures';
import { renderWithProviders, stubApi } from './testUtils';

const PRIMER_CAPITULO = notesFixture;
const SEGUNDO_CAPITULO = notesSegundoCapituloFixture;

function montar(notes: StudentNotes = notesFixture, route = '/temario/IV.7') {
  const fetchMock = stubApi({
    '/api/v1/student/topics/IV.7/notes?capitulo=IV.7.2': { body: SEGUNDO_CAPITULO },
    '/api/v1/student/topics/IV.7/notes?capitulo=IV.7.1': { body: PRIMER_CAPITULO },
    '/api/v1/student/topics/IV.7/notes': { body: notes },
    'POST /api/v1/student/topics/IV.7/reports': {
      status: 201,
      body: {
        section_key: 'tcpip-arquitectura',
        reason: 'La cuarta capa no es la de aplicación.',
        status: 'open',
        created_at: '2026-10-11T10:00:00Z',
      },
    },
    '/api/v1/student/topics/IV.7': { body: topicFixture },
  });
  return {
    fetchMock,
    ...renderWithProviders(
      <Routes>
        <Route path="/temario/:codigo" element={<TopicNotesPage />} />
      </Routes>,
      { route },
    ),
  };
}

/** Los cuerpos JSON de las llamadas que casan con el trozo de URL. */
function urlsPedidas(fetchMock: ReturnType<typeof stubApi>, trozo: string): string[] {
  return fetchMock.mock.calls
    .map(([url]) => (typeof url === 'string' ? url : url instanceof URL ? url.href : url.url))
    .filter((texto) => texto.includes(trozo));
}

/** El cuerpo JSON de la primera llamada que casa con el método y el trozo de URL. */
function cuerpoEnviado(fetchMock: ReturnType<typeof stubApi>, metodo: string, trozo: string): unknown {
  const llamada = fetchMock.mock.calls.find(([url, init]) => {
    const texto = typeof url === 'string' ? url : url instanceof URL ? url.href : url.url;
    return texto.includes(trozo) && (init?.method ?? 'GET').toUpperCase() === metodo;
  });
  if (llamada?.[1]?.body === undefined || typeof llamada[1].body !== 'string') {
    throw new Error(`no se encontró una llamada ${metodo} a ${trozo} con cuerpo`);
  }
  return JSON.parse(llamada[1].body) as unknown;
}

describe('Los apuntes del tema, por capítulos', () => {
  it('monta el índice de capítulos, la lectura del capítulo abierto y la nota al margen', async () => {
    montar();

    const indice = await screen.findByRole('navigation', { name: /apartados/i });
    // El índice lleva **a su capítulo**: es lo que hace que un tema de 314.000 px se pueda recorrer.
    expect(within(indice).getByRole('link', { name: /IV\.7\.2/ })).toHaveAttribute(
      'href',
      '/temario/IV.7?capitulo=IV.7.2',
    );
    // Y con los apartados del capítulo abierto, con su ancla.
    expect(
      within(indice).getByRole('link', { name: /La arquitectura TCP\/IP/i }),
    ).toHaveAttribute('href', '#apartado-tcpip-arquitectura');

    const apartado = screen.getByRole('region', { name: /arquitectura TCP\/IP/i });
    expect(apartado).toHaveAttribute('id', 'apartado-tcpip-arquitectura');
    // La nota al margen vive **dentro** de su apartado: en el móvil cae debajo de su párrafo.
    expect(within(apartado).getByRole('button', { name: /esto se pregunta/i })).toBeInTheDocument();
  });

  it('sirve un capítulo cada vez: el apartado del otro capítulo no está en la página', async () => {
    montar();

    await screen.findByRole('region', { name: /arquitectura TCP\/IP/i });
    // El apartado 2 vive en IV.7.2 y **no** viaja con el primer capítulo: es la paginación.
    expect(screen.queryByRole('region', { name: /UDP: datagramas/i })).toBeNull();
    expect(document.getElementById('apartado-udp')).toBeNull();
  });

  it('marca el capítulo que se está leyendo', async () => {
    montar();

    const indice = await screen.findByRole('navigation', { name: /apartados/i });
    expect(within(indice).getByRole('link', { name: /IV\.7\.1/ })).toHaveAttribute(
      'aria-current',
      'page',
    );
    expect(within(indice).getByRole('link', { name: /IV\.7\.2/ })).not.toHaveAttribute(
      'aria-current',
    );
  });

  it('pide a la API el capítulo que dice la dirección', async () => {
    const { fetchMock } = montar(notesFixture, '/temario/IV.7?capitulo=IV.7.2');

    await screen.findByRole('region', { name: /UDP: datagramas/i });
    expect(urlsPedidas(fetchMock, '/notes?capitulo=IV.7.2')).toHaveLength(1);
  });

  it('abre el capítulo que contiene el anclaje de la dirección y lo pide', async () => {
    // `/temario/IV.7#apartado-udp`: el apartado vive en IV.7.2, que no es el capítulo que se sirve
    // por defecto. Sin esta corrección la página se queda con el primer capítulo, donde el párrafo
    // no está, y el alumno acaba arriba: es el defecto medido (`scrollY = 0`).
    const { fetchMock } = montar(notesFixture, '/temario/IV.7#apartado-udp');

    expect(await screen.findByRole('region', { name: /UDP: datagramas/i })).toBeInTheDocument();
    await waitFor(() =>
      expect(urlsPedidas(fetchMock, '/notes?capitulo=IV.7.2')).toHaveLength(1),
    );
  });

  it('pinta las tablas de los apuntes como tablas, con su cabecera', async () => {
    montar();

    const apartado = await screen.findByRole('region', { name: /arquitectura TCP\/IP/i });
    const tabla = within(apartado).getByRole('table');
    expect(within(tabla).getByRole('columnheader', { name: 'Capa' })).toBeInTheDocument();
    expect(within(tabla).getByRole('cell', { name: 'Segmento' })).toBeInTheDocument();
    expect(within(apartado).queryByText('| Capa |')).not.toBeInTheDocument();
  });

  it('la tabla va en su propio marco, con nombre y enfocable: se desplaza ella, no el texto', async () => {
    montar();

    const apartado = await screen.findByRole('region', { name: /arquitectura TCP\/IP/i });
    // Una región que se desplaza tiene que poder recorrerse con el teclado (axe lo comprueba): el
    // marco lleva nombre y está en el orden de tabulación, y la tabla no se estrecha al de la
    // columna de texto —lo que rompía las palabras («Aplic|ación»)—.
    const marco = within(apartado).getByRole('region', { name: /^Tabla: Capa, Unidad$/ });
    expect(marco).toHaveAttribute('tabindex', '0');
    expect(marco).toHaveClass('apuntes__tabla-marco');
  });

  it('el recuento de la nota al margen está plegado y se abre a petición', async () => {
    const usuario = userEvent.setup();
    montar();

    const apartado = await screen.findByRole('region', { name: /arquitectura TCP\/IP/i });
    const boton = within(apartado).getByRole('button', { name: /esto se pregunta/i });
    // La regla de la zona del alumno: ningún párrafo explicativo visible por defecto. El rótulo se
    // ve, la frase que lo explica no.
    expect(boton).toHaveAttribute('aria-expanded', 'false');
    expect(
      within(apartado).queryByText('7 preguntas de este tema se contestan en este apartado.'),
    ).not.toBeVisible();

    await usuario.click(boton);
    expect(boton).toHaveAttribute('aria-expanded', 'true');
    expect(
      await within(apartado).findByText('7 preguntas de este tema se contestan en este apartado.'),
    ).toBeVisible();
  });

  it('un apartado sin preguntas no lleva nota al margen', async () => {
    montar(notesSegundoCapituloFixture, '/temario/IV.7?capitulo=IV.7.2');

    const sinPreguntas = await screen.findByRole('region', { name: /Otros protocolos/i });
    expect(within(sinPreguntas).queryByRole('button', { name: /esto se pregunta/i })).toBeNull();
  });

  it('cada apartado lleva su botón «Esto está mal», que pide el motivo y lo manda', async () => {
    const usuario = userEvent.setup();
    const { fetchMock } = montar();

    const apartado = await screen.findByRole('region', { name: /arquitectura TCP\/IP/i });
    await usuario.click(within(apartado).getByRole('button', { name: /esto está mal/i }));

    const motivo = within(apartado).getByRole('textbox', { name: /motivo/i });
    expect(within(apartado).getByRole('button', { name: /enviar el aviso/i })).toBeDisabled();

    await usuario.type(motivo, 'La cuarta capa no es la de aplicación.');
    await usuario.click(within(apartado).getByRole('button', { name: /enviar el aviso/i }));

    expect(await within(apartado).findByText(/queda apuntado/i)).toBeInTheDocument();
    expect(cuerpoEnviado(fetchMock, 'POST', '/api/v1/student/topics/IV.7/reports')).toEqual({
      section_key: 'tcpip-arquitectura',
      reason: 'La cuarta capa no es la de aplicación.',
    });
    expect(within(apartado).queryByRole('textbox', { name: /motivo/i })).not.toBeInTheDocument();
  });

  it('se puede cerrar el formulario sin mandar nada', async () => {
    const usuario = userEvent.setup();
    montar();

    const apartado = await screen.findByRole('region', { name: /arquitectura TCP\/IP/i });
    await usuario.click(within(apartado).getByRole('button', { name: /esto está mal/i }));
    await usuario.click(within(apartado).getByRole('button', { name: /cancelar/i }));

    expect(within(apartado).queryByRole('textbox', { name: /motivo/i })).not.toBeInTheDocument();
  });

  it('lleva al capítulo anterior y al siguiente', async () => {
    montar(notesSegundoCapituloFixture, '/temario/IV.7?capitulo=IV.7.2');

    const paso = await screen.findByRole('navigation', { name: /capítulos del tema/i });
    expect(within(paso).getByRole('link', { name: /anterior/i })).toHaveAttribute(
      'href',
      '/temario/IV.7?capitulo=IV.7.1',
    );
    // El último capítulo no ofrece «siguiente».
    expect(within(paso).queryByRole('link', { name: /siguiente/i })).toBeNull();
  });

  it('un tema en borrador se lee entero y lo dice', async () => {
    montar();

    expect(await screen.findByText('Borrador')).toBeInTheDocument();
    expect(screen.getByRole('region', { name: /arquitectura TCP\/IP/i })).toBeInTheDocument();
  });

  it('un tema publicado lleva la marca de la versión generada', async () => {
    montar(notesPublishedFixture);

    await waitFor(() =>
      expect(screen.getByText('Versión generada · en revisión')).toBeInTheDocument(),
    );
  });

  it('un tema sin apuntes lo dice y no ofrece avisar de nada', async () => {
    montar({ ...notesFixture, state: 'none', sections: [], chapters: [], chapter: null });

    expect(await screen.findByText(/todavía no tiene apuntes/i)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /esto está mal/i })).not.toBeInTheDocument();
  });
});
