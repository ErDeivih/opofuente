import { screen, waitFor, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { useLocation } from 'react-router-dom';

import { AdminShell } from '../../src/app/AdminShell';
import { AppShell } from '../../src/app/AppShell';
import {
  ADMIN_NAV_ITEMS,
  ROUTE_REDIRECTS,
  STUDENT_NAV_ITEMS,
} from '../../src/app/navigation';
import { AppRoutes } from '../../src/app/routes';
import { NotFoundPage } from '../../src/pages/NotFoundPage';
import { revisarPantalla } from '../palabrasProhibidas';
import {
  capabilitiesFixture,
  oppositionsFixture,
  pendingActionsEmptyFixture,
  readinessReady,
  renderWithProviders,
  settingsFixture,
  stubApi,
  type StubbedRoute,
} from './testUtils';

/** Lo que necesita la zona de administración para pintarse: cabecera, avisos y contadores. */
function stubPanel(extra: Record<string, StubbedRoute> = {}) {
  return stubApi({
    '/api/v1/health/ready': { body: readinessReady },
    '/api/v1/capabilities': { body: capabilitiesFixture },
    '/api/v1/settings': { body: settingsFixture },
    '/api/v1/oppositions': { body: oppositionsFixture },
    '/api/v1/pending-actions': { body: pendingActionsEmptyFixture },
    '/api/v1/reviews/due': {
      body: {
        items: [],
        stats: { active: 0, due: 0, next_due_at: null, lapses: 0 },
        concepts: [],
        notes: [],
      },
    },
    '/api/v1/questions?status=conflicting&limit=1': {
      body: { questions: [], total: 0, limit: 1, offset: 0 },
    },
    ...extra,
  });
}

/** Lo que lee Inicio desde F13: el resumen del alumno (sin tests, sin fallos y sin progreso). */
function stubInicio(extra: Record<string, StubbedRoute> = {}) {
  return stubPanel({
    '/api/v1/student/overview': {
      body: {
        opposition: { code: 'tai-age', name: 'Cuerpo de Técnicos Auxiliares de Informática' },
        in_progress: null,
        due_reviews: 0,
        blocks: [],
        recent_tests: [],
      },
    },
    ...extra,
  });
}

/** La dirección en la que está el navegador, para poder comprobar una redirección. */
function RutaActual() {
  const { pathname, search } = useLocation();
  return <p data-testid="ruta">{`${pathname}${search}`}</p>;
}

/** Lo que se lee en la pantalla: la interfaz (sin el contenido) y todo. */
function textoDeLaPantalla() {
  const copia = document.body.cloneNode(true) as HTMLElement;
  for (const nodo of Array.from(copia.querySelectorAll('[data-contenido]'))) {
    nodo.remove();
  }
  return { interfaz: copia.textContent ?? '', todo: document.body.textContent ?? '' };
}

describe('los dos mapas de navegación', () => {
  it('la zona del alumno tiene siete entradas, en orden, y ninguna de la trastienda', () => {
    expect(STUDENT_NAV_ITEMS.map((item) => item.label)).toEqual([
      'Inicio',
      'Temario',
      'Tests',
      'Simulacros',
      'Exámenes',
      'Fallos',
      'Progreso',
    ]);
    expect(STUDENT_NAV_ITEMS.map((item) => item.path)).toEqual([
      '/',
      '/temario',
      '/tests',
      '/simulacros',
      '/examenes',
      '/fallos',
      '/progreso',
    ]);
  });

  it('el panel tiene su propio menú, con las pantallas que se administran', () => {
    expect(ADMIN_NAV_ITEMS.map((item) => item.label)).toEqual([
      'Importaciones',
      'Biblioteca',
      'Revisión',
      'Clasificación',
      // Las dos entradas que estrena el bloque C (F16): lo que avisa el alumno —que se despacha— y lo
      // que el motor dejó fuera de los tests —que solo se mira—.
      'Avisos',
      // Y la bandeja del **motor** (F18): la otra mitad del §4.1, que hasta ahora no tenía ni ruta.
      'Incidencias',
      // La revisión de los apuntes (F24, §4.3): leer un borrador dentro del panel, con su motivo
      // medido, y aprobarlo o rechazarlo.
      'Apuntes',
      'No son preguntas',
      'Cambios',
      'Errores',
      'Preguntas',
      'Programa',
      'Estudiar',
      'Buscar',
      'Ajustes',
      'Componentes',
    ]);
    for (const item of ADMIN_NAV_ITEMS) {
      expect(item.path.startsWith('/admin/')).toBe(true);
    }
  });

  it('las dos zonas no comparten ninguna dirección', () => {
    const alumno = new Set(STUDENT_NAV_ITEMS.map((item) => item.path));
    for (const item of ADMIN_NAV_ITEMS) {
      expect(alumno.has(item.path)).toBe(false);
    }
  });

  it('cada dirección vieja tiene su destino nuevo', () => {
    expect(ROUTE_REDIRECTS.map(({ from, to }) => `${from} -> ${to}`)).toEqual([
      '/bandeja -> /admin/importar',
      '/biblioteca -> /admin/biblioteca',
      '/revision -> /admin/revision',
      '/clasificacion -> /admin/clasificacion',
      '/cambios -> /admin/cambios',
      '/errores -> /admin/errores',
      '/preguntas -> /admin/preguntas',
      '/programa -> /admin/programa',
      '/estudiar -> /admin/estudiar',
      '/buscar -> /admin/buscar',
      '/ajustes -> /admin/ajustes',
    ]);
  });
});

describe('el marco del alumno', () => {
  it('tiene las siete entradas y nada de la trastienda', () => {
    renderWithProviders(<AppRoutes />, { route: '/temario' });

    const nav = screen.getByRole('navigation', { name: 'Secciones de la aplicación' });
    expect(within(nav).getAllByRole('link').map((enlace) => enlace.textContent)).toEqual([
      'Inicio',
      'Temario',
      'Tests',
      'Simulacros',
      'Exámenes',
      'Fallos',
      'Progreso',
    ]);
    // Ni buscar en el material recopilado, ni selector de oposición, ni indicadores del sistema.
    expect(screen.queryByLabelText('Buscar en el corpus')).toBeNull();
    expect(screen.queryByLabelText('Oposición')).toBeNull();
    expect(screen.queryByLabelText('Estado de capacidades clave')).toBeNull();
    // Y ningún contador: lo que espera trabajo es cosa del panel.
    expect(document.querySelectorAll('.nav__count')).toHaveLength(0);
  });

  it('deja una sola puerta al panel, discreta, en el pie', () => {
    renderWithProviders(<AppRoutes />, { route: '/temario' });

    const administrar = screen.getByRole('link', { name: 'Administrar' });
    expect(administrar).toHaveAttribute('href', '/admin');
  });

  it('la zona del alumno ya no tiene ninguna sección pendiente: Tests lleva a su pantalla', () => {
    // F22 cerró la última que faltaba (Tests). Antes, esta dirección pintaba la pantalla de «todavía
    // no está»; ahora tiene que pintar el formulario de verdad. Se comprueba en las dos direcciones:
    // que el aviso de sección pendiente **no** sale, y que lo que sale es la pantalla con su título.
    // Sin datos de la API, la pantalla dice que no pudo preparar el test —eso también es una pantalla,
    // y distinta de una promesa—, así que aquí se mira lo que el marco tiene que garantizar.
    stubApi({});
    renderWithProviders(<AppRoutes />, { route: '/tests' });

    expect(screen.getByRole('heading', { level: 1, name: 'Tests' })).toBeInTheDocument();
    expect(screen.queryByText(/Llega en la siguiente fase/)).toBeNull();
  });

  it('el enlace de salto al contenido existe y apunta al main', () => {
    renderWithProviders(<AppRoutes />, { route: '/temario' });

    const skipLink = screen.getByRole('link', { name: 'Saltar al contenido' });
    expect(skipLink).toHaveAttribute('href', '#contenido');
    expect(document.getElementById('contenido')).not.toBeNull();
  });

  it('no enseña lenguaje interno en el HTML', async () => {
    stubInicio();
    renderWithProviders(<AppRoutes />, { route: '/' });

    expect(await screen.findByRole('heading', { level: 1, name: 'Hoy' })).toBeInTheDocument();
    expect(await screen.findByText('Aún no has hecho ningún test.')).toBeInTheDocument();

    const { interfaz, todo } = textoDeLaPantalla();
    expect(revisarPantalla(interfaz, todo)).toEqual([]);
  });
});

describe('el marco de administración', () => {
  it('avisa de que no hay contraseña y trae la cocina del panel', async () => {
    stubPanel();
    renderWithProviders(<AppRoutes />, { route: '/admin/ui' });

    const aviso = screen.getByText(/sin contraseña: solo en este ordenador/);
    expect(aviso).toHaveTextContent(
      'Modo administración · sin contraseña: solo en este ordenador',
    );
    const nav = screen.getByRole('navigation', { name: 'Secciones de administración' });
    expect(within(nav).getAllByRole('link')).toHaveLength(ADMIN_NAV_ITEMS.length);
    // Lo que se fue de la zona del alumno sigue aquí: oposición, búsqueda e indicadores.
    expect(await screen.findByLabelText('Oposición')).toBeInTheDocument();
    expect(await screen.findByLabelText('Buscar en el corpus')).toBeInTheDocument();
    expect(await screen.findByLabelText('Estado de capacidades clave')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Volver a la zona de estudio' })).toHaveAttribute(
      'href',
      '/',
    );
  });

  it('la dirección decide el marco: cada zona trae el suyo', () => {
    stubPanel();
    const alumno = renderWithProviders(<AppRoutes />, { route: '/progreso' });
    expect(screen.queryByText(/Modo administración/)).toBeNull();
    alumno.unmount();

    renderWithProviders(<AppRoutes />, { route: '/admin/ui' });
    expect(screen.getByText(/Modo administración/)).toBeInTheDocument();
    // El marco del alumno no aparece dentro del panel.
    expect(screen.queryByRole('navigation', { name: 'Secciones de la aplicación' })).toBeNull();
  });

  it('una ruta desconocida del panel se declara no encontrada dentro del panel', () => {
    stubPanel();
    renderWithProviders(<AppRoutes />, { route: '/admin/no-existe' });

    expect(
      screen.getByRole('heading', { level: 1, name: 'Página no encontrada' }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Modo administración/)).toBeInTheDocument();
  });
});

describe('las direcciones de antes', () => {
  it('llevan a la nueva ubicación sin perder la consulta', () => {
    for (const { from, to } of ROUTE_REDIRECTS) {
      stubPanel();
      const { unmount } = renderWithProviders(
        <>
          <AppRoutes />
          <RutaActual />
        </>,
        { route: `${from}?documento=doc-1` },
      );
      expect(screen.getByTestId('ruta')).toHaveTextContent(`${to}?documento=doc-1`);
      unmount();
    }
  });

  it('no dan 404: la pantalla de la nueva ubicación es la que se ve', async () => {
    stubPanel({
      '/api/v1/change-sets?limit=100': { body: [] },
      '/api/v1/derived-artifacts?needs_review=true': { body: [] },
    });
    renderWithProviders(<AppRoutes />, { route: '/cambios' });

    expect(await screen.findByRole('heading', { level: 1, name: 'Cambios' })).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Página no encontrada' })).toBeNull();
  });

  it('una ruta que no existe de verdad sí se declara no encontrada', () => {
    renderWithProviders(<AppRoutes />, { route: '/no-existe' });

    expect(
      screen.getByRole('heading', { level: 1, name: 'Página no encontrada' }),
    ).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Volver a Inicio' })).toBeInTheDocument();
  });
});

describe('contadores del panel', () => {
  function stubContadores(extra: Record<string, StubbedRoute> = {}) {
    return stubPanel({
      '/api/v1/pending-actions': {
        body: {
          actions: [
            {
              key: 'importaciones',
              title: 'Importaciones con avisos o errores',
              detail: '7 aviso(s) y error(es) de importación sin resolver',
              count: 7,
              href: '/bandeja',
              label: 'Ver la bandeja',
            },
            {
              key: 'cambios',
              title: 'Cambios de fuente sin confirmar',
              detail: '4 cambio(s) propuesto(s) entre versiones',
              count: 4,
              href: '/cambios',
              label: 'Ver los cambios',
            },
          ],
          total: 11,
        },
      },
      '/api/v1/reviews/due': {
        body: {
          items: [],
          stats: { active: 9, due: 5, next_due_at: null, lapses: 1 },
          concepts: [],
          notes: [],
        },
      },
      '/api/v1/questions?status=conflicting&limit=1': {
        body: { questions: [], total: 3, limit: 1, offset: 0 },
      },
      ...extra,
    });
  }

  it('dice cuánto espera en cada sección, con la cifra que cuenta el servidor', async () => {
    stubContadores();
    renderWithProviders(<AppRoutes />, { route: '/admin/ui' });

    // El nombre del enlace dice el número **y** qué es, así que el contador no es decorativo ni mudo.
    const importaciones = await screen.findByRole('link', {
      name: 'Importaciones: 7 avisos o errores de importación',
    });
    expect(importaciones).toHaveTextContent('7');
    expect(
      screen.getByRole('link', { name: 'Preguntas: 3 preguntas en conflicto' }),
    ).toBeInTheDocument();
    expect(
      await screen.findByRole('link', { name: 'Errores: 5 repasos vencidos' }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('link', { name: 'Cambios: 4 cambios sin confirmar' }),
    ).toBeInTheDocument();
  });

  it('no enseña ceros: una sección sin nada pendiente no lleva insignia', async () => {
    stubPanel();
    renderWithProviders(<AppRoutes />, { route: '/admin/ui' });

    expect(await screen.findByLabelText('Estado de capacidades clave')).toBeInTheDocument();
    await waitFor(() => {
      expect(document.querySelectorAll('.nav__count')).toHaveLength(0);
    });
  });
});

describe('la página no encontrada de siempre', () => {
  it('un aviso claro con la vuelta a Inicio', () => {
    renderWithProviders(<NotFoundPage />, { route: '/no-existe' });

    expect(
      screen.getByRole('heading', { level: 1, name: 'Página no encontrada' }),
    ).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Volver a Inicio' })).toBeInTheDocument();
  });
});

describe('los dos marcos existen por separado', () => {
  it('AppShell es el del alumno y AdminShell el del panel', () => {
    stubPanel();
    const alumno = renderWithProviders(
      <AppShell>
        <p>contenido</p>
      </AppShell>,
      { route: '/' },
    );
    expect(screen.queryByText(/Modo administración/)).toBeNull();
    alumno.unmount();

    renderWithProviders(
      <AdminShell>
        <p>contenido</p>
      </AdminShell>,
      { route: '/admin/ui' },
    );
    expect(screen.getByText(/Modo administración/)).toBeInTheDocument();
  });
});
