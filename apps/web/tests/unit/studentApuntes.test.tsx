/**
 * La lectura de los apuntes en la zona del alumno (F13, diseño Stitch en tres columnas).
 *
 * Lo que se comprueba aquí es lo que una captura no puede demostrar:
 *
 * 1. **la estructura de tres columnas**: el índice navegable (con un enlace por apartado al ancla de
 *    su sección), la columna de lectura y la nota al margen **dentro** de su apartado;
 * 2. **las tablas se pintan como tablas** (con su cabecera), no como tuberías;
 * 3. **la nota al margen dice una cifra real** —las preguntas del tema que contesta ese apartado— y
 *    no aparece cuando no hay ninguna;
 * 4. **el botón «Esto está mal»**: pide el motivo en una línea, no deja enviarlo vacío y manda el
 *    aviso con la clave del apartado (el anclaje lo pone el servidor);
 * 5. **el estado**: un tema en borrador se lee entero y lo dice; uno publicado lleva la marca; y uno
 *    sin apuntes no ofrece nada que leer.
 */

import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';

import type { StudentNotes } from '../../src/api/studentStudy';
import { TopicNotesPage } from '../../src/pages/student/TopicNotesPage';
import { notesFixture, notesPublishedFixture, topicFixture } from './studentFixtures';
import { renderWithProviders, stubApi } from './testUtils';

function montar(notes: StudentNotes = notesFixture) {
  const fetchMock = stubApi({
    '/api/v1/student/topics/IV.7/notes': { body: notes },
    'POST /api/v1/student/topics/IV.7/reports': {
      status: 201,
      body: {
        section_key: 'udp',
        reason: 'La cabecera de UDP no es de 12 bytes.',
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
      { route: '/temario/IV.7' },
    ),
  };
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

describe('Los apuntes del tema', () => {
  it('monta las tres columnas: índice navegable, lectura y nota al margen por apartado', async () => {
    montar();

    const indice = await screen.findByRole('navigation', { name: /apartados/i });
    const enlaces = within(indice).getAllByRole('link');
    expect(enlaces.map((enlace) => enlace.getAttribute('href'))).toEqual([
      '#apartado-tcpip-arquitectura',
      '#apartado-udp',
      '#apartado-otros-protocolos',
    ]);

    const apartado = screen.getByRole('region', { name: /UDP: datagramas sin conexión/i });
    expect(apartado).toHaveAttribute('id', 'apartado-udp');
    // La nota al margen vive **dentro** de su apartado: en el móvil cae debajo de su párrafo.
    expect(within(apartado).getByRole('note', { name: /esto se pregunta/i })).toBeInTheDocument();
  });

  it('pinta las tablas de los apuntes como tablas, con su cabecera', async () => {
    montar();

    const apartado = await screen.findByRole('region', { name: /arquitectura TCP\/IP/i });
    const tabla = within(apartado).getByRole('table');
    expect(within(tabla).getByRole('columnheader', { name: 'Capa' })).toBeInTheDocument();
    expect(within(tabla).getByRole('cell', { name: 'Segmento' })).toBeInTheDocument();
    expect(within(apartado).queryByText('| Capa |')).not.toBeInTheDocument();
  });

  it('la nota al margen lleva el recuento del apartado y no aparece sin preguntas', async () => {
    montar();

    const conPreguntas = await screen.findByRole('region', { name: /UDP/i });
    expect(
      within(conPreguntas).getByText('1 pregunta de este tema se contesta en este apartado.'),
    ).toBeInTheDocument();

    const sinPreguntas = screen.getByRole('region', { name: /Otros protocolos/i });
    expect(within(sinPreguntas).queryByRole('note')).not.toBeInTheDocument();
  });

  it('cada apartado lleva su botón «Esto está mal», que pide el motivo y lo manda', async () => {
    const usuario = userEvent.setup();
    const { fetchMock } = montar();

    const apartado = await screen.findByRole('region', { name: /UDP/i });
    await usuario.click(within(apartado).getByRole('button', { name: /esto está mal/i }));

    const motivo = within(apartado).getByRole('textbox', { name: /motivo/i });
    expect(within(apartado).getByRole('button', { name: /enviar el aviso/i })).toBeDisabled();

    await usuario.type(motivo, 'La cabecera de UDP no es de 12 bytes.');
    await usuario.click(within(apartado).getByRole('button', { name: /enviar el aviso/i }));

    expect(await within(apartado).findByText(/queda apuntado/i)).toBeInTheDocument();
    expect(cuerpoEnviado(fetchMock, 'POST', '/api/v1/student/topics/IV.7/reports')).toEqual({
      section_key: 'udp',
      reason: 'La cabecera de UDP no es de 12 bytes.',
    });
    // El formulario se cierra: el aviso ya está dado.
    expect(within(apartado).queryByRole('textbox', { name: /motivo/i })).not.toBeInTheDocument();
  });

  it('se puede cerrar el formulario sin mandar nada', async () => {
    const usuario = userEvent.setup();
    montar();

    const apartado = await screen.findByRole('region', { name: /UDP/i });
    await usuario.click(within(apartado).getByRole('button', { name: /esto está mal/i }));
    await usuario.click(within(apartado).getByRole('button', { name: /cancelar/i }));

    expect(within(apartado).queryByRole('textbox', { name: /motivo/i })).not.toBeInTheDocument();
  });

  it('un tema en borrador se lee entero y lo dice', async () => {
    montar();

    expect(await screen.findByText('Borrador')).toBeInTheDocument();
    const indice = screen.getByRole('navigation', { name: /apartados/i });
    expect(within(indice).getAllByRole('link')).toHaveLength(notesFixture.sections.length);
  });

  it('un tema publicado lleva la marca de la versión generada', async () => {
    montar(notesPublishedFixture);

    await waitFor(() =>
      expect(screen.getByText('Versión generada · en revisión')).toBeInTheDocument(),
    );
  });

  it('un tema sin apuntes lo dice y no ofrece avisar de nada', async () => {
    montar({ ...notesFixture, state: 'none', sections: [], generated_at: null });

    expect(await screen.findByText(/todavía no tiene apuntes/i)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /esto está mal/i })).not.toBeInTheDocument();
  });
});
