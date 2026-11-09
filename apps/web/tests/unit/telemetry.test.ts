/**
 * Pruebas unitarias del módulo de telemetría web.
 *
 * Se comprueba lo que promete el encargo sin depender de la red: la ruta se convierte en un nombre
 * estable de pantalla, el envío usa `navigator.sendBeacon`, cae a `fetch` con `keepalive` cuando el
 * beacon no puede encolar el evento, y con la telemetría apagada no se envía **nada**.
 */

import { afterEach, describe, expect, it, vi } from 'vitest';

import { screenForPath, trackPageView } from '../../src/telemetry';

afterEach(() => {
  vi.unstubAllEnvs();
});

describe('telemetría web', () => {
  it('deduce un nombre de pantalla estable de la ruta, sin identificadores ni URL', () => {
    expect(screenForPath('/')).toBe('inicio');
    expect(screenForPath('/bandeja')).toBe('bandeja');
    expect(screenForPath('/temario/tema-con-id-123')).toBe('tema');
    expect(screenForPath('/temario/tema-con-id-123/practicar')).toBe('practica');
    expect(screenForPath('/buscar')).toBe('buscar');
    expect(screenForPath('/ruta-que-no-existe/123')).toBe('no_encontrada');
  });

  it('envía el page_view con sendBeacon cuando la telemetría está activa', async () => {
    vi.stubEnv('VITE_TELEMETRY', 'on');
    const beacon = vi.fn<(url: string | URL, data?: BodyInit | null) => boolean>(() => true);
    const fetchMock = vi.fn<(input: RequestInfo | URL, init?: RequestInit) => Promise<Response>>(
      () => Promise.resolve(new Response(null, { status: 202 })),
    );
    vi.stubGlobal('navigator', { sendBeacon: beacon });
    vi.stubGlobal('fetch', fetchMock);

    trackPageView('/temario/tema-con-id-123');

    expect(beacon).toHaveBeenCalledTimes(1);
    expect(fetchMock).not.toHaveBeenCalled();

    const call = beacon.mock.calls[0];
    expect(call).toBeDefined();
    if (call === undefined) throw new Error('no se envió ningún beacon');
    const [url, body] = call;
    expect(url).toBe('http://127.0.0.1:8765/api/v1/telemetry/events');
    expect(body).toBeInstanceOf(Blob);
    if (!(body instanceof Blob)) throw new Error('el beacon no recibió un Blob');
    const payload: unknown = JSON.parse(await body.text());
    expect(payload).toEqual({ type: 'page_view', screen: 'tema' });
  });

  it('cae a fetch con keepalive si sendBeacon no puede encolar el evento', () => {
    vi.stubEnv('VITE_TELEMETRY', 'on');
    const beacon = vi.fn<(url: string | URL, data?: BodyInit | null) => boolean>(() => false);
    const fetchMock = vi.fn<(input: RequestInfo | URL, init?: RequestInit) => Promise<Response>>(
      () => Promise.resolve(new Response(null, { status: 202 })),
    );
    vi.stubGlobal('navigator', { sendBeacon: beacon });
    vi.stubGlobal('fetch', fetchMock);

    trackPageView('/');

    expect(beacon).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const call = fetchMock.mock.calls[0];
    expect(call).toBeDefined();
    if (call === undefined) throw new Error('no se llamó a fetch');
    const [url, init] = call;
    expect(url).toBe('http://127.0.0.1:8765/api/v1/telemetry/events');
    expect(init).toMatchObject({ method: 'POST', keepalive: true });
  });

  it('no envía nada cuando la telemetría está apagada', () => {
    vi.stubEnv('VITE_TELEMETRY', 'off');
    const beacon = vi.fn<(url: string | URL, data?: BodyInit | null) => boolean>(() => true);
    const fetchMock = vi.fn<(input: RequestInfo | URL, init?: RequestInit) => Promise<Response>>(
      () => Promise.resolve(new Response(null, { status: 202 })),
    );
    vi.stubGlobal('navigator', { sendBeacon: beacon });
    vi.stubGlobal('fetch', fetchMock);

    trackPageView('/bandeja');

    expect(beacon).not.toHaveBeenCalled();
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
