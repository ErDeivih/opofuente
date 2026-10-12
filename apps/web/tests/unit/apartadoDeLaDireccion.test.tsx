/**
 * Llevar la vista al apartado que dice la dirección (F16).
 *
 * El enlace de la bandeja del panel apunta al apartado exacto de los apuntes
 * (`/temario/IV.7#apartado-redes-tcpip`), y el ancla del navegador **no basta**: los apuntes llegan
 * por la API después del primer pintado, así que cuando el navegador busca el elemento todavía no
 * está. Medido con Playwright el 11-oct-2026, con el apartado a 5.894 px: `scrollY` se quedaba en 0.
 *
 * Lo que se prueba aquí es el comportamiento del efecto, sin navegador de verdad: que busca el
 * elemento, que **reintenta** mientras los apuntes llegan, que se rinde si no aparecen nunca y que no
 * hace nada cuando la dirección no trae ancla.
 */

import { renderHook } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { ReactNode } from 'react';

import { useApartadoDeLaDireccion } from '../../src/app/apartadoDeLaDireccion';

/** Un `scrollIntoView` de mentira: jsdom no lo implementa. */
const desplazamientos: string[] = [];

beforeEach(() => {
  vi.useFakeTimers();
  desplazamientos.length = 0;
  Element.prototype.scrollIntoView = function scrollIntoView(this: Element) {
    desplazamientos.push(this.id);
  };
  document.body.innerHTML = '';
});

afterEach(() => {
  vi.useRealTimers();
});

function montar(ruta: string) {
  const envoltorio = ({ children }: { children: ReactNode }) => (
    <MemoryRouter initialEntries={[ruta]}>{children}</MemoryRouter>
  );
  return renderHook(() => {
    useApartadoDeLaDireccion();
  }, { wrapper: envoltorio });
}

describe('el apartado que dice la dirección', () => {
  it('baja al apartado cuando ya está pintado', () => {
    const apartado = document.createElement('section');
    apartado.id = 'apartado-redes-tcpip';
    document.body.append(apartado);

    montar('/temario/IV.7#apartado-redes-tcpip');

    expect(desplazamientos).toEqual(['apartado-redes-tcpip']);
  });

  it('reintenta mientras los apuntes llegan, y baja cuando aparecen', () => {
    montar('/temario/IV.7#apartado-redes-tcpip');

    // Todavía no está: los primeros intentos no encuentran nada y no pasa nada.
    vi.advanceTimersByTime(500);
    expect(desplazamientos).toEqual([]);

    const apartado = document.createElement('section');
    apartado.id = 'apartado-redes-tcpip';
    document.body.append(apartado);
    vi.advanceTimersByTime(200);

    expect(desplazamientos).toEqual(['apartado-redes-tcpip']);
  });

  it('se rinde si el apartado no aparece nunca', () => {
    montar('/temario/IV.7#apartado-que-no-existe');

    vi.advanceTimersByTime(6000);

    expect(desplazamientos).toEqual([]);
    // Y no deja nada programado: la pantalla no se queda con un bucle vivo.
    expect(vi.getTimerCount()).toBe(0);
  });

  it('sin ancla no hace nada', () => {
    const apartado = document.createElement('section');
    apartado.id = 'apartado-redes-tcpip';
    document.body.append(apartado);

    montar('/temario/IV.7');

    vi.advanceTimersByTime(1000);
    expect(desplazamientos).toEqual([]);
  });
});
