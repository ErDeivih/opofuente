/**
 * El reloj del test (§3.4), sin navegador: la cuenta y las palabras.
 *
 * Es lo que no se puede comprobar con una captura —un reloj parado se ve igual que uno que cuenta— y
 * por eso se prueba aquí: que el tiempo salga de la hora de arranque **del servidor**, que el
 * transcurrido avance con el reloj del navegador, que un equipo con la hora mal puesta no invente
 * horas de examen, y que el límite se note cuando se agota.
 */

import { describe, expect, it } from 'vitest';

import { relojDeSesion, tiempoEnPalabras } from '../../src/features/study/sessionClock';

const ARRANQUE = '2026-10-16T10:00:00Z';

/** El estado del reloj cuando el servidor dice que ya habían pasado `minutos` al responder. */
function enMinutos(minutos: number, desdeLaLecturaMs = 0) {
  const servidor = new Date(Date.parse(ARRANQUE) + minutos * 60_000).toISOString();
  return relojDeSesion({
    startedAt: ARRANQUE,
    timeLimitMinutes: 120,
    serverNow: servidor,
    desdeLaLecturaMs,
  });
}

describe('el reloj de la sesión', () => {
  it('no pinta nada en un test sin reloj, pero sí sabe lo que llevas', () => {
    const servidor = new Date(Date.parse(ARRANQUE) + 5_000).toISOString();
    const reloj = relojDeSesion({
      startedAt: ARRANQUE,
      timeLimitMinutes: null,
      serverNow: servidor,
      desdeLaLecturaMs: 0,
    });

    expect(reloj.restanteMs).toBeNull();
    expect(reloj.transcurridoMs).toBe(5_000);
  });

  it('no pinta nada en una sesión sin arrancar', () => {
    const reloj = relojDeSesion({
      startedAt: null,
      timeLimitMinutes: 120,
      serverNow: ARRANQUE,
      desdeLaLecturaMs: 5_000,
    });

    expect(reloj.restanteMs).toBeNull();
    expect(reloj.transcurridoMs).toBeNull();
  });

  it('cuenta lo que queda desde la hora de arranque del servidor', () => {
    // El servidor responde diez minutos después de arrancar: quedan 110 de los 120.
    const reloj = enMinutos(10);

    expect(reloj.restanteMs).toBe(110 * 60_000);
    expect(reloj.transcurridoMs).toBe(10 * 60_000);
    expect(reloj.vencido).toBe(false);
    expect(reloj.apurado).toBe(false);
  });

  it('avanza con el reloj del navegador sin volver a preguntar al servidor', () => {
    const reloj = enMinutos(10, 30_000);

    expect(reloj.restanteMs).toBe(110 * 60_000 - 30_000);
    expect(reloj.transcurridoMs).toBe(10 * 60_000 + 30_000);
  });

  it('un equipo con la hora adelantada mide lo mismo que uno en hora', () => {
    // La hora del servidor es la que manda: el reloj local solo aporta lo que pasa desde la lectura,
    // y ese trozo de tiempo es el mismo en un equipo en hora que en uno que va tres horas por delante.
    const enHora = enMinutos(10, 2 * 60_000);
    const adelantado = enMinutos(10, 2 * 60_000);

    expect(adelantado.transcurridoMs).toBe(enHora.transcurridoMs);
    expect(adelantado.restanteMs).toBe(enHora.restanteMs);
  });

  it('avisa cuando queda poco y cuando se ha agotado', () => {
    const apurado = enMinutos(117);
    expect(apurado.apurado).toBe(true);
    expect(apurado.vencido).toBe(false);

    const agotado = enMinutos(121);
    expect(agotado.restanteMs).toBe(0);
    expect(agotado.vencido).toBe(true);
    expect(agotado.apurado).toBe(false);
  });

  it('sin la hora del servidor dice que no sabe, en vez de inventar un cero', () => {
    const sinServidor = relojDeSesion({
      startedAt: ARRANQUE,
      timeLimitMinutes: 120,
      serverNow: null,
      desdeLaLecturaMs: 5_000,
    });
    const sinArranque = relojDeSesion({
      startedAt: 'no es una fecha',
      timeLimitMinutes: 120,
      serverNow: ARRANQUE,
      desdeLaLecturaMs: 5_000,
    });

    expect(sinServidor.restanteMs).toBeNull();
    expect(sinServidor.transcurridoMs).toBeNull();
    expect(sinArranque.restanteMs).toBeNull();
    expect(sinArranque.transcurridoMs).toBeNull();
  });
});

describe('el tiempo en palabras', () => {
  it('escribe minutos y segundos, y horas cuando las hay', () => {
    expect(tiempoEnPalabras(0)).toBe('0:00');
    expect(tiempoEnPalabras(65_000)).toBe('1:05');
    expect(tiempoEnPalabras(59 * 60_000 + 59_000)).toBe('59:59');
    expect(tiempoEnPalabras(120 * 60_000)).toBe('2:00:00');
    expect(tiempoEnPalabras(-5_000)).toBe('0:00');
  });
});
