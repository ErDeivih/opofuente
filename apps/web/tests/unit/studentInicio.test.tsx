/**
 * Inicio de la zona del alumno (F13): lo que se ve al entrar.
 *
 * Lo que se comprueba, y es lo que el encargo pide:
 *
 * 1. **qué toca hacer** —seguir el test a medias, repasar los fallos vencidos y las tres acciones
 *    rápidas—, con la ruta a la que lleva cada una;
 * 2. **cómo va**: una barra fina por bloque con su porcentaje escrito, que es el dibujo del diseño;
 * 3. **los temas con apuntes y su estado** (publicado o borrador) y, cuando están publicados, la
 *    marca «Versión generada · en revisión» —lo que el alumno tiene que saber antes de fiarse del
 *    texto—;
 * 4. y que un tema **sin apuntes no se ofrece** como si los tuviera.
 */

import { screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { StudentHomePage } from '../../src/pages/student/StudentHomePage';
import { overviewFixture } from './studentFixtures';
import { renderWithProviders, stubApi } from './testUtils';

function montar(overrides: Record<string, unknown> = {}) {
  stubApi({
    '/api/v1/student/overview': { body: { ...overviewFixture, ...overrides } },
  });
  return renderWithProviders(<StudentHomePage />, { route: '/' });
}

describe('Inicio del alumno', () => {
  it('enseña qué toca hacer, con la ruta de cada acción', async () => {
    montar();

    const continuar = await screen.findByRole('link', { name: /continuar el test/i });
    expect(continuar).toHaveAttribute('href', '/test/ses-1');
    expect(screen.getByText(/12 de 25/)).toBeInTheDocument();
    expect(screen.getByText(/23 preguntas para repasar hoy/)).toBeInTheDocument();

    expect(screen.getByRole('link', { name: /test rápido de 20/i })).toHaveAttribute(
      'href',
      '/tests?count=20',
    );
    expect(screen.getByRole('link', { name: /^simulacro$/i })).toHaveAttribute(
      'href',
      '/simulacros',
    );
    expect(screen.getByRole('link', { name: /examen oficial/i })).toHaveAttribute(
      'href',
      '/examenes',
    );
  });

  it('enseña el progreso por bloque con su porcentaje escrito', async () => {
    montar();

    const bloques = await screen.findByRole('list', { name: /progreso por bloque/i });
    const filas = within(bloques).getAllByRole('listitem');
    expect(filas).toHaveLength(2);
    expect(within(filas[0]!).getByText('I')).toBeInTheDocument();
    expect(within(filas[0]!).getByText('64 %')).toBeInTheDocument();
    expect(within(filas[1]!).getByText('75 %')).toBeInTheDocument();
  });

  it('lista los temas con apuntes con su estado y la marca de la versión generada', async () => {
    montar();

    const temas = await screen.findByRole('list', { name: /temas con apuntes/i });
    // I.1 y IV.1 están publicados; I.6 y IV.7, en borrador. IV.10 no tiene apuntes y no sale.
    const filas = within(temas).getAllByRole('listitem');
    expect(filas).toHaveLength(4);
    expect(within(filas[0]!).getByText('Versión generada · en revisión')).toBeInTheDocument();
    expect(within(filas[1]!).getByText('Borrador')).toBeInTheDocument();
    expect(within(filas[2]!).getByRole('link', { name: /^IV\.1/ })).toHaveAttribute(
      'href',
      '/temario/IV.1',
    );
  });

  it('no ofrece apuntes de un tema que no los tiene', async () => {
    montar();

    await screen.findByRole('list', { name: /temas con apuntes/i });
    expect(screen.queryByRole('link', { name: /^IV\.10/ })).not.toBeInTheDocument();
  });

  it('cuando no hay test a medias lo dice y ofrece empezar uno', async () => {
    montar({ in_progress: null, recent_tests: [] });

    expect(await screen.findByText(/aún no has hecho ningún test/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /empezar un test/i })).toHaveAttribute('href', '/tests');
  });

  it('con tests hechos pero ninguno a medias, tampoco se inventa una sesión', async () => {
    montar({ in_progress: null });

    expect(await screen.findByText(/no tienes ningún test a medias/i)).toBeInTheDocument();
  });
});
