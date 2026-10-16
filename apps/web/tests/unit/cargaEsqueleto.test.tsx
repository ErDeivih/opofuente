/**
 * Los esqueletos de carga (§2.5 del cierre del objetivo).
 *
 * La regla del encargo: **esqueletos en las listas que tardan más de 300 ms**, sin animaciones de
 * entrada decorativas y respetando `prefers-reduced-motion`. Y la otra mitad, que es la que se olvida:
 * una respuesta que llega **antes** de esos 300 ms no puede hacer parpadear un esqueleto —eso es peor
 * que no ponerlo—, así que la pantalla tiene que seguir enseñando su estado de carga normal.
 *
 * Se comprueba sobre las tres pantallas que el encargo nombra (Temario, Progreso y Tema) porque el
 * esqueleto tiene que ser el mismo en las tres, no uno por pantalla.
 */

import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactElement } from 'react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi, afterEach } from 'vitest';

import { ProgressPage } from '../../src/pages/student/ProgressPage';
import { SyllabusPage } from '../../src/pages/student/SyllabusPage';
import { TopicNotesPage } from '../../src/pages/student/TopicNotesPage';
import { notesFixture, progressFixture, syllabusFixture, topicFixture } from './studentFixtures';

/** Una respuesta que tarda lo que se le diga, para poder mirar la pantalla mientras espera. */
function stubApiLento(rutas: Record<string, unknown>, retardoMs: number) {
  const fetchMock = vi.fn((input: RequestInfo | URL) => {
    const url = typeof input === 'string' ? input : input instanceof URL ? input.href : input.url;
    const elegida = Object.entries(rutas)
      .filter(([camino]) => url.includes(camino))
      .sort((izquierda, derecha) => derecha[0].length - izquierda[0].length)[0];
    return new Promise<Response>((resolver) => {
      setTimeout(() => {
        resolver(
          new Response(JSON.stringify(elegida === undefined ? {} : elegida[1]), {
            status: elegida === undefined ? 404 : 200,
            headers: { 'content-type': 'application/json' },
          }),
        );
      }, retardoMs);
    });
  });
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

function montar(ui: ReactElement, ruta: string) {
  render(
    <QueryClientProvider
      client={
        new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0, staleTime: 0 } } })
      }
    >
      <MemoryRouter initialEntries={[ruta]}>
        <Routes>
          <Route path="/temario" element={ui} />
          <Route path="/progreso" element={ui} />
          <Route path="/temario/:codigo" element={ui} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

const LENTO = 600;

describe('los esqueletos de carga', () => {
  it('el Temario enseña su esqueleto mientras el servidor tarda', async () => {
    stubApiLento({ '/api/v1/student/syllabus': syllabusFixture }, LENTO);
    montar(<SyllabusPage />, '/temario');

    const esqueleto = await screen.findByTestId('esqueleto-temario');
    expect(esqueleto).toHaveAttribute('role', 'status');
    // Y dice qué está pasando: un esqueleto mudo no se anuncia.
    expect(esqueleto).toHaveAccessibleName(/cargando/i);

    // Cuando llega, el esqueleto se va y queda la lista de verdad.
    await waitFor(
      () => {
        expect(screen.queryByTestId('esqueleto-temario')).toBeNull();
      },
      { timeout: 5000 },
    );
    expect(screen.getByRole('list', { name: 'Temario' })).toBeInTheDocument();
  });

  it('el Progreso enseña su esqueleto mientras el servidor tarda', async () => {
    stubApiLento({ '/api/v1/student/progress': progressFixture }, LENTO);
    montar(<ProgressPage />, '/progreso');

    expect(await screen.findByTestId('esqueleto-progreso')).toHaveAttribute('role', 'status');
  });

  it('el Tema enseña su esqueleto mientras el servidor tarda', async () => {
    stubApiLento(
      {
        '/api/v1/student/topics/IV.7/notes': notesFixture,
        '/api/v1/student/topics/IV.7': topicFixture,
      },
      LENTO,
    );
    montar(<TopicNotesPage />, '/temario/IV.7');

    expect(await screen.findByTestId('esqueleto-tema')).toHaveAttribute('role', 'status');
  });

  it('una respuesta rápida no hace parpadear ningún esqueleto', async () => {
    stubApiLento({ '/api/v1/student/syllabus': syllabusFixture }, 0);
    montar(<SyllabusPage />, '/temario');

    // Antes de los 300 ms no hay esqueleto: lo que hay es el estado de carga de siempre.
    expect(screen.queryByTestId('esqueleto-temario')).toBeNull();
    expect(await screen.findByRole('list', { name: 'Temario' })).toBeInTheDocument();
    expect(screen.queryByTestId('esqueleto-temario')).toBeNull();
  });
});
