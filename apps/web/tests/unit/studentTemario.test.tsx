/**
 * Temario de la zona del alumno (F13).
 *
 * Lo que se comprueba:
 *
 * 1. **el orden es el numérico** (`IV.7` antes de `IV.10`): es el orden que ya sirve la API y la
 *    pantalla no lo toca;
 * 2. **hay búsqueda** y filtra por título y por código —y buscar `IV.10` no deja `IV.1` en la
 *    lista, que es la trampa de comparar por trozos—, sin esconder los borradores;
 * 3. **cada tema dice cómo están sus apuntes**: publicados (con la marca), en borrador (se leen
 *    igual) o sin escribir (y entonces no hay enlace a los apuntes, porque no hay qué leer);
 * 4. cada tema lleva a sus apuntes y a su test, y la barra de acierto queda vacía cuando no hay
 *    nada corregido —sin un cero que parezca un dato—.
 */

import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import { SyllabusPage } from '../../src/pages/student/SyllabusPage';
import { syllabusFixture } from './studentFixtures';
import { renderWithProviders, stubApi } from './testUtils';

function montar() {
  stubApi({ '/api/v1/student/syllabus': { body: syllabusFixture } });
  return renderWithProviders(<SyllabusPage />, { route: '/temario' });
}

describe('Temario del alumno', () => {
  it('lista los bloques con su número romano y los temas en orden numérico', async () => {
    montar();

    const temario = await screen.findByRole('list', { name: /temario/i });
    const bloques = within(temario).getAllByRole('listitem', { name: /^Bloque/ });
    expect(bloques.map((bloque) => bloque.getAttribute('aria-label'))).toEqual([
      'Bloque I',
      'Bloque IV',
    ]);

    const temas = within(bloques[1]!).getAllByRole('listitem', { name: /^Tema/ });
    expect(temas.map((tema) => tema.getAttribute('data-codigo'))).toEqual(['IV.1', 'IV.7', 'IV.10']);
  });

  it('cada tema lleva a sus apuntes y a su test, y dice cuántas preguntas tiene', async () => {
    montar();

    const tema = await screen.findByRole('listitem', { name: 'Tema IV.1' });
    expect(within(tema).getByRole('link', { name: 'Apuntes de IV.1' })).toHaveAttribute(
      'href',
      '/temario/IV.1',
    );
    expect(within(tema).getByRole('link', { name: 'Test de IV.1' })).toHaveAttribute(
      'href',
      '/tests?tema=IV.1',
    );
    expect(within(tema).getByText('30 preguntas')).toBeInTheDocument();
    expect(within(tema).getByText('75 %')).toBeInTheDocument();
  });

  it('marca los borradores sin esconderlos y no ofrece apuntes de un tema sin escribir', async () => {
    montar();

    const borrador = await screen.findByRole('listitem', { name: 'Tema IV.7' });
    expect(within(borrador).getByText('Borrador')).toBeInTheDocument();
    expect(within(borrador).getByRole('link', { name: 'Apuntes de IV.7' })).toBeInTheDocument();

    const sinApuntes = screen.getByRole('listitem', { name: 'Tema IV.10' });
    expect(
      within(sinApuntes).queryByRole('link', { name: /^Apuntes/ }),
    ).not.toBeInTheDocument();
    expect(within(sinApuntes).getByText('Sin apuntes')).toBeInTheDocument();
  });

  it('busca por título y por código', async () => {
    const usuario = userEvent.setup();
    montar();
    await screen.findByRole('list', { name: /temario/i });

    const buscador = screen.getByRole('searchbox', { name: /buscar en el temario/i });

    await usuario.type(buscador, 'firma electrónica');
    await waitFor(() =>
      expect(screen.queryByRole('listitem', { name: 'Tema IV.7' })).not.toBeInTheDocument(),
    );
    expect(screen.getByRole('listitem', { name: 'Tema I.6' })).toBeInTheDocument();

    await usuario.clear(buscador);
    await usuario.type(buscador, 'IV.10');
    await waitFor(() =>
      expect(screen.queryByRole('listitem', { name: 'Tema IV.1' })).not.toBeInTheDocument(),
    );
    expect(screen.getByRole('listitem', { name: 'Tema IV.10' })).toBeInTheDocument();

    await usuario.clear(buscador);
    await usuario.type(buscador, 'zzz');
    expect(await screen.findByText(/no hay ningún tema que coincida/i)).toBeInTheDocument();
  });

  it('un tema sin nada corregido no enseña un cero por porcentaje', async () => {
    montar();

    const sinDatos = await screen.findByRole('listitem', { name: 'Tema IV.10' });
    expect(within(sinDatos).queryByText('0 %')).not.toBeInTheDocument();
    expect(within(sinDatos).getByText('Sin empezar')).toBeInTheDocument();
  });
});
