/**
 * La sección «No son preguntas» (F16, decisión D6 del objetivo).
 *
 * El propietario decidió que los enunciados rotos y las preguntas de otra administración **no se
 * tiran**: no entran en ningún test, simulacro ni comprobación de apuntes, pero se quedan en la base
 * y tienen que poder mirarse. Esta pantalla es ese «poder mirarse», y lo que se comprueba es
 * exactamente eso:
 *
 * 1. **se listan con su motivo** —la pregunta, por qué está fuera, quién lo decidió y cuándo—;
 * 2. **las cifras son las de la base** (`totals_by_reason`), no la cuenta de las filas que se ven;
 * 3. **se puede buscar** en el enunciado, y la búsqueda viaja a la API;
 * 4. **no se toca nada desde aquí**: no hay botón de borrar ni de editar, y la pantalla lo dice,
 *    porque devolver una pregunta al temario se hace en Clasificación (asignándole un tema).
 */

import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import type { ExclusionPage } from '../../src/api/topicReview';
import { NoSonPreguntasPage } from '../../src/pages/NoSonPreguntasPage';
import { renderWithProviders, stubApi } from './testUtils';

/** Lo que devuelve el listado: dos enunciados rotos y las cifras de los dos motivos. */
const excluidas: ExclusionPage = {
  total: 2,
  limit: 100,
  offset: 0,
  totals_by_reason: { enunciado_roto: 769, otra_administracion: 325 },
  exclusions: [
    {
      question_version_id: 'q-1',
      reason: 'enunciado_roto',
      actor: 'llm:deepseek-flash',
      note: 'el enunciado es un trozo de norma',
      created_at: '2026-10-08T10:00:00Z',
      stem: 'Los funcionarios tendrán derecho a las vacaciones, permisos y licencias.',
    },
    {
      question_version_id: 'q-2',
      reason: 'enunciado_roto',
      actor: 'local',
      note: null,
      created_at: '2026-10-07T09:00:00Z',
      stem: 'Artículo 14. Los españoles son iguales ante la ley',
    },
  ],
};

function montar(entrada = '', cuerpo: ExclusionPage = excluidas) {
  const fetchMock = stubApi({ '/api/v1/question-exclusions': { body: cuerpo } });
  renderWithProviders(<NoSonPreguntasPage />, { route: `/admin/no-son-preguntas${entrada}` });
  return fetchMock;
}

function urlsDe(fetchMock: ReturnType<typeof stubApi>): string[] {
  return fetchMock.mock.calls.map(([url]) =>
    typeof url === 'string' ? url : url instanceof URL ? url.href : url.url,
  );
}

describe('la sección «no son preguntas»', () => {
  it('lista los enunciados con su motivo, quién lo decidió y cuándo', async () => {
    montar();

    const lista = await screen.findByRole('list', { name: /preguntas que no son preguntas/i });
    const filas = within(lista).getAllByRole('listitem');
    expect(filas).toHaveLength(2);

    const primera = filas[0]!;
    expect(
      within(primera).getByText(
        'Los funcionarios tendrán derecho a las vacaciones, permisos y licencias.',
      ),
    ).toBeInTheDocument();
    expect(within(primera).getByText('Enunciado roto')).toBeInTheDocument();
    expect(within(primera).getByText(/el enunciado es un trozo de norma/)).toBeInTheDocument();
    expect(within(primera).getByText(/lo decidió llm:deepseek-flash el 2026-10-08/)).toBeInTheDocument();

    // Y la segunda fila, con lo que no tiene: sin nota del modelo, pero con su actor.
    expect(within(filas[1]!).getByText(/lo decidió local el 2026-10-07/)).toBeInTheDocument();
  });

  it('enseña las cifras de la base, no las de la página que se está viendo', async () => {
    montar();

    // Dos filas en pantalla y 769 en la base: lo que se dice es lo de la base.
    await screen.findByRole('list', { name: /preguntas que no son preguntas/i });
    expect(screen.getByRole('button', { name: /enunciado roto/i })).toHaveTextContent('769');
    expect(screen.getByRole('button', { name: /de otra administración/i })).toHaveTextContent('325');
    expect(screen.getByText(/2 en total/)).toBeInTheDocument();
  });

  it('busca en el enunciado y lo pide a la API', async () => {
    const usuario = userEvent.setup();
    const fetchMock = montar();

    await screen.findByRole('list', { name: /preguntas que no son preguntas/i });
    await usuario.type(screen.getByLabelText(/buscar en el enunciado/i), 'vacaciones');
    await usuario.click(screen.getByRole('button', { name: /^buscar$/i }));

    await waitFor(() => {
      const conBusqueda = urlsDe(fetchMock).filter((url) => url.includes('q=vacaciones'));
      expect(conBusqueda).toHaveLength(1);
      expect(conBusqueda[0]).toContain('reason=enunciado_roto');
    });
  });

  it('no ofrece nada para borrar ni para editar: aquí solo se mira', async () => {
    montar();

    const lista = await screen.findByRole('list', { name: /preguntas que no son preguntas/i });
    const filas = within(lista).getAllByRole('listitem');
    for (const fila of filas) {
      expect(within(fila).queryByRole('button')).toBeNull();
      expect(within(fila).queryByRole('textbox')).toBeNull();
    }
    expect(screen.getByText(/siguen en la base/i)).toBeInTheDocument();
  });

  it('cambia de motivo y sin coincidencias lo dice', async () => {
    const usuario = userEvent.setup();
    montar('', { ...excluidas, total: 0, exclusions: [] });

    await usuario.click(screen.getByRole('button', { name: /de otra administración/i }));

    await waitFor(() => {
      expect(
        screen.getByText(/ninguna pregunta fuera por «de otra administración»/i),
      ).toBeInTheDocument();
    });
  });
});
