/**
 * Inicio de la zona del alumno (F13): lo que se ve al entrar.
 *
 * Lo que se comprueba, y es lo que el encargo pide:
 *
 * 1. **qué toca hacer** —seguir el test a medias, repasar los fallos vencidos y las tres acciones
 *    rápidas—, con la ruta a la que lleva cada una;
 * 2. **cómo va**: una barra fina por bloque con su porcentaje escrito, que es el dibujo del diseño;
 * 3. **por dónde ibas**: «Seguir leyendo» con el último apartado abierto y su enlace, y un enlace al
 *    Temario —en lugar de la lista de los 29 temas con su título entero, que era lo que había—;
 * 4. y que un tema **sin apuntes no se ofrece** como si los tuviera.
 */

import { screen, within } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';

import { StudentHomePage } from '../../src/pages/student/StudentHomePage';
import {
  CLAVE_ULTIMO_APARTADO,
  guardarUltimoApartado,
  olvidarUltimoApartado,
} from '../../src/lib/ultimoApartado';
import { overviewFixture } from './studentFixtures';
import { renderWithProviders, stubApi } from './testUtils';

function montar(overrides: Record<string, unknown> = {}) {
  stubApi({
    '/api/v1/student/overview': { body: { ...overviewFixture, ...overrides } },
  });
  return renderWithProviders(<StudentHomePage />, { route: '/' });
}

describe('Inicio del alumno', () => {
  beforeEach(() => {
    olvidarUltimoApartado();
  });

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

  it('la cifra del bloque va en la fila de su bloque, no en una línea aparte', async () => {
    montar();

    const bloques = await screen.findByRole('list', { name: /progreso por bloque/i });
    const filas = within(bloques).getAllByRole('listitem');
    // La cifra cuelga de la misma fila que su bloque: es lo que se arregló del «67 %» que saltaba
    // a una línea propia debajo de la barra (la fila declaraba tres columnas y tenía cuatro hijos).
    for (const fila of filas) {
      expect(fila.querySelector('.barras__cifra')).not.toBeNull();
    }
    expect(filas[0]!.querySelector('.barras__barra')).not.toBeNull();
  });

  it('después de abrir un apartado, Inicio ofrece «Seguir leyendo» con su enlace', async () => {
    guardarUltimoApartado({
      codigo: 'IV.7',
      titulo: 'Redes y comunicaciones',
      capitulo: 'IV.7.2',
      tituloCapitulo: 'Protocolos de red',
      apartado: 'osi-capas',
      tituloApartado: 'El modelo OSI',
    });
    montar();

    const seguir = await screen.findByRole('heading', { name: /seguir leyendo/i });
    const bloque = seguir.closest('section');
    expect(bloque).not.toBeNull();
    const enlace = within(bloque as HTMLElement).getByRole('link', { name: /IV\.7\.2/ });
    expect(enlace).toHaveAttribute('href', '/temario/IV.7?capitulo=IV.7.2#apartado-osi-capas');
    expect(within(bloque as HTMLElement).getByRole('link', { name: /ver el temario/i })).toHaveAttribute(
      'href',
      '/temario',
    );
  });

  it('sin nada abierto todavía lo dice y ofrece el Temario, sin inventarse una lectura', async () => {
    montar();

    const seguir = await screen.findByRole('heading', { name: /seguir leyendo/i });
    const bloque = seguir.closest('section') as HTMLElement;
    expect(
      within(bloque).getByText(/todavía no has abierto ningún apartado/i),
    ).toBeInTheDocument();
    expect(within(bloque).getByRole('link', { name: /ver el temario/i })).toHaveAttribute(
      'href',
      '/temario',
    );
  });

  it('ya no lista los 29 temas con su título entero', async () => {
    montar();

    await screen.findByRole('heading', { name: /seguir leyendo/i });
    // La sección «Tus apuntes» con la lista completa desapareció: su sitio lo ocupa «Seguir leyendo».
    expect(screen.queryByRole('list', { name: /temas con apuntes/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: /tus apuntes/i })).not.toBeInTheDocument();
    expect(window.localStorage.getItem(CLAVE_ULTIMO_APARTADO)).toBeNull();
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
