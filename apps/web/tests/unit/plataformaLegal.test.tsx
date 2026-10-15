/**
 * El §9 y el §10 en el navegador: el aviso de cookies, la puerta de las cookies y las páginas legales.
 *
 * **La prueba que da sentido al bloque es `no se pone ninguna cookie no esencial antes de aceptar`.**
 * No comprueba un texto: comprueba el hecho. Se navega sin decidir, se intenta escribir la cookie de
 * preferencias por la vía por la que la escribe la aplicación, y se mira el almacén del navegador.
 * Antes de aceptar, no hay nada.
 *
 * Las demás comprueban lo que el §9 pide y lo que una revisión de accesibilidad preguntaría:
 *
 * - aceptar y rechazar son **dos botones iguales**, y los dos resuelven en una pulsación;
 * - la decisión se recuerda en una cookie propia —la misma que lee el servidor para no contar nada
 *   sin permiso— y no en el estado de un componente;
 * - con las páginas legales apagadas **no hay aviso**: es la configuración de siempre, y no puede
 *   aparecer nada nuevo por defecto;
 * - la página de cookies enseña la tabla de datos completa, **incluido lo que no se recoge**.
 */

import { QueryClientProvider } from '@tanstack/react-query';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { PolicyProvider } from '../../src/app/policy';
import { CookieNotice } from '../../src/features/legal/CookieNotice';
import { LegalPage } from '../../src/features/legal/LegalPage';
import {
  CONSENT_COOKIE,
  PREFERENCES_COOKIE,
  isGranted,
  readConsent,
  readCookie,
  rememberReadingScale,
  setNonEssentialCookie,
} from '../../src/lib/consent';
import type { PlatformPolicy } from '../../src/api/platform';
import { createTestQueryClient, stubApi } from './testUtils';

const POLITICA: PlatformPolicy = {
  accounts: {
    enabled: false,
    anonymous_study: true,
    session_cookie_name: 'opofuente_session',
    session_days: 30,
    delivery_channel: 'fichero_local',
  },
  legal: {
    enabled: true,
    policy_version: 1,
    text_version: 1,
    updated_on: '2026-10-15',
    purposes: ['necessary', 'preferences', 'analytics'],
    essential: ['necessary'],
    owner_fields_pending: true,
  },
  analytics: { enabled: true, requires_consent: true, retention_days: 365 },
  payments: false,
};

const POLITICA_SIN_LEGALES: PlatformPolicy = {
  ...POLITICA,
  legal: { ...POLITICA.legal, enabled: false },
  analytics: { ...POLITICA.analytics, enabled: false },
};

const DOCUMENTO = {
  key: 'cookies',
  title: 'Cookies',
  summary: 'Qué cookies se ponen.',
  body_markdown:
    '## Qué es una cookie\n\nUn fichero pequeño.\n\n- Necesarias: la de la sesión.\n- Preferencias: el tamaño del texto.\n',
};

const COOKIES = {
  policy_version: 1,
  updated_on: '2026-10-15',
  cookies: [
    {
      name: 'opofuente_consent',
      purpose: 'Recordar la decisión.',
      essential: true,
      duration: '6 meses',
      set_by: 'Esta aplicación',
      purpose_key: 'necessary',
    },
    {
      name: 'opofuente_prefs',
      purpose: 'Recordar el tamaño del texto.',
      essential: false,
      duration: '12 meses',
      set_by: 'Esta aplicación',
      purpose_key: 'preferences',
    },
  ],
  essential: ['necessary'],
  purposes: ['necessary', 'preferences', 'analytics'],
  notice: 'Antes de que decidas no se pone ninguna cookie que no sea necesaria.',
};

const INVENTARIO = {
  uses: [
    {
      what: 'Tu dirección de correo.',
      why: 'Identificar tu cuenta.',
      where: 'La base de datos.',
      retention: 'Mientras la cuenta exista.',
      lawful_basis: 'Ejecución de un contrato.',
      needs_account: true,
      needs_consent: null,
    },
  ],
  not_collected: [{ claim: 'No se guarda tu dirección IP.' }],
  notice: 'Sin cuenta no se recoge ningún dato tuyo.',
};

/** Borra todas las cookies del documento: el almacén de jsdom vive entre pruebas del mismo fichero. */
function borrarCookies(): void {
  for (const trozo of document.cookie.split(';')) {
    const nombre = trozo.split('=')[0]?.trim();
    if (nombre) {
      document.cookie = `${nombre}=; Max-Age=0; Path=/`;
    }
  }
}

beforeEach(() => {
  borrarCookies();
});

afterEach(() => {
  borrarCookies();
});

/** Monta un componente con la política pedida y las respuestas del §9 simuladas. */
function montar(
  ui: React.ReactElement,
  {
    route = '/',
    politica = POLITICA,
    patron,
    acepta = { analytics: true, preferences: true },
  }: {
    route?: string;
    politica?: PlatformPolicy;
    patron?: string;
    acepta?: { analytics: boolean; preferences: boolean };
  } = {},
) {
  stubApi({
    '/api/v1/platform/policy': { body: politica },
    '/api/v1/legal/documents/cookies': { body: DOCUMENTO },
    '/api/v1/legal/cookies': { body: COOKIES },
    '/api/v1/legal/data-inventory': { body: INVENTARIO },
    'POST /api/v1/legal/consent': {
      body: {
        policy_version: 1,
        decided_at: '2026-10-15T10:00:00Z',
        necessary: true,
        analytics: acepta.analytics,
        preferences: acepta.preferences,
      },
    },
  });
  return render(
    <QueryClientProvider client={createTestQueryClient()}>
      <PolicyProvider>
        <MemoryRouter initialEntries={[route]}>
          {/*
            La página legal lee el nombre del texto de la **dirección** (`/legal/:documento`). Sin un
            `Route` que la declare, `useParams` devuelve nada y la pantalla pediría otro texto: la
            prueba estaría midiendo una pantalla que no es la que se navega de verdad.
          */}
          {patron === undefined ? (
            ui
          ) : (
            <Routes>
              <Route path={patron} element={ui} />
            </Routes>
          )}
        </MemoryRouter>
      </PolicyProvider>
    </QueryClientProvider>,
  );
}

describe('el aviso de cookies y la puerta de las cookies', () => {
  it('no se pone ninguna cookie no esencial antes de aceptar', async () => {
    montar(<CookieNotice />);

    // El aviso está delante, esperando una decisión.
    expect(await screen.findByRole('heading', { name: 'Cookies' })).toBeInTheDocument();
    expect(readConsent()).toBeNull();

    // Y la puerta por la que se escribe lo no esencial dice que no: no hay cookie.
    expect(setNonEssentialCookie(PREFERENCES_COOKIE, '1.20', 'preferences', 365)).toBe(false);
    expect(rememberReadingScale(1.2)).toBe(false);
    expect(readCookie(PREFERENCES_COOKIE)).toBeNull();
    expect(readCookie(CONSENT_COOKIE)).toBeNull();
    expect(isGranted('preferences')).toBe(false);
    expect(isGranted('analytics')).toBe(false);
  });

  it('aceptar y rechazar son dos botones iguales, y los dos resuelven en una pulsación', async () => {
    // El rechazo se simula como lo contesta el servidor: los dos fines en falso. Es lo que comprueba
    // el backend; aquí se comprueba que la pantalla **guarda** esa respuesta y no otra.
    montar(<CookieNotice />, { acepta: { analytics: false, preferences: false } });

    const aceptar = await screen.findByRole('button', { name: 'Aceptar' });
    const rechazar = screen.getByRole('button', { name: 'Rechazar' });

    // Mismo papel, mismo tipo de control: no hay un botón «de verdad» y un enlace escondido.
    expect(aceptar.tagName).toBe(rechazar.tagName);
    expect(aceptar).toHaveAttribute('type', 'button');
    expect(rechazar).toHaveAttribute('type', 'button');

    await userEvent.click(rechazar);

    // Una pulsación, y la decisión queda guardada: la puerta sigue cerrada porque se rechazó.
    expect(readConsent()).not.toBeNull();
    expect(isGranted('preferences')).toBe(false);
    expect(setNonEssentialCookie(PREFERENCES_COOKIE, '1.20', 'preferences', 365)).toBe(false);
    expect(readCookie(PREFERENCES_COOKIE)).toBeNull();
  });

  it('aceptar deja la decisión guardada y abre la puerta de lo no esencial', async () => {
    montar(<CookieNotice />);

    await userEvent.click(await screen.findByRole('button', { name: 'Aceptar' }));

    const decision = readConsent();
    expect(decision).not.toBeNull();
    expect(isGranted('preferences')).toBe(true);
    // Ahora sí: la cookie de preferencias se puede escribir.
    expect(rememberReadingScale(1.2)).toBe(true);
    expect(readCookie(PREFERENCES_COOKIE)).toBe('1.20');
  });

  it('con las páginas legales apagadas no hay ningún aviso', async () => {
    montar(<CookieNotice />, { politica: POLITICA_SIN_LEGALES });

    // No se encuentra el aviso: no es que esté escondido, es que no se pinta.
    expect(screen.queryByRole('heading', { name: 'Cookies' })).toBeNull();
    expect(readConsent()).toBeNull();
  });
});

describe('las páginas legales', () => {
  it('enseña el texto que sirve el servidor y avisa de lo que falta por rellenar', async () => {
    montar(<LegalPage />, { route: '/legal/cookies', patron: '/legal/:documento' });

    expect(await screen.findByRole('heading', { level: 1, name: 'Cookies' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Qué es una cookie' })).toBeInTheDocument();
    expect(screen.getByText(/Un fichero pequeño/)).toBeInTheDocument();
    expect(screen.getByRole('note')).toHaveTextContent(/Faltan datos del titular/);
  });

  it('la tabla de datos dice lo que se recoge y también lo que no', async () => {
    montar(<LegalPage />, { route: '/legal/cookies', patron: '/legal/:documento' });

    const tabla = await screen.findByRole('table', { name: /Una fila por dato/ });
    expect(within(tabla).getByText('Tu dirección de correo.')).toBeInTheDocument();
    expect(within(tabla).getByText('Mientras la cuenta exista.')).toBeInTheDocument();

    expect(screen.getByRole('heading', { name: 'Lo que no se recoge' })).toBeInTheDocument();
    expect(screen.getByText('No se guarda tu dirección IP.')).toBeInTheDocument();
  });

  it('la tabla de cookies enseña cuáles son necesarias y cuáles no', async () => {
    montar(<LegalPage />, { route: '/legal/cookies', patron: '/legal/:documento' });

    const tabla = await screen.findByRole('table', { name: /Todas las cookies/ });
    const filas = within(tabla).getAllByRole('row');
    // Cabecera más las dos cookies declaradas.
    expect(filas).toHaveLength(3);
    expect(within(tabla).getByText('opofuente_prefs')).toBeInTheDocument();
    expect(within(tabla).getByText('No')).toBeInTheDocument();
  });

  it('con las páginas legales apagadas no se sirve ningún texto', async () => {
    montar(<LegalPage />, {
      route: '/legal/cookies',
      patron: '/legal/:documento',
      politica: POLITICA_SIN_LEGALES,
    });

    expect(
      await screen.findByRole('heading', { name: 'No hay páginas legales' }),
    ).toBeInTheDocument();
  });
});
