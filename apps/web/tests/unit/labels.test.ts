import { describe, expect, it } from 'vitest';

import { clock, elapsedSeconds } from '../../src/features/study/labels';

/**
 * El cronómetro de una sesión (5 de octubre de 2026).
 *
 * La API servía las fechas **sin zona** («2026-10-05T10:43:52.793645», que es UTC) y el navegador
 * las leía como hora local: en Madrid el cronómetro de una práctica empezaba en `2:00:03` y un
 * examen oficial de 120 minutos nacía con el tiempo agotado. Ahora la API las sirve con su zona
 * (`+00:00`) y esto comprueba que se cuentan los segundos reales en los dos casos.
 */
describe('el cronómetro de una sesión', () => {
  it('cuenta los segundos reales con la fecha que sirve la API (UTC con zona)', () => {
    const ahora = Date.UTC(2026, 9, 5, 10, 0, 30);
    expect(elapsedSeconds('2026-10-05T10:00:00.000000+00:00', ahora)).toBe(30);
  });

  it('una fecha sin zona se toma por UTC, no por hora local', () => {
    const ahora = Date.UTC(2026, 9, 5, 10, 0, 30);
    expect(elapsedSeconds('2026-10-05T10:00:00.000000', ahora)).toBe(30);
    expect(elapsedSeconds('2026-10-05T10:00:00.000000Z', ahora)).toBe(30);
  });

  it('sin fecha de arranque (o con una ilegible) no hay tiempo que enseñar', () => {
    expect(elapsedSeconds(null, Date.UTC(2026, 9, 5))).toBe(0);
    expect(elapsedSeconds('vaya', Date.UTC(2026, 9, 5))).toBe(0);
  });

  it('una fecha en el futuro no cuenta hacia atrás', () => {
    const ahora = Date.UTC(2026, 9, 5, 10, 0, 0);
    expect(elapsedSeconds('2026-10-05T10:00:30.000000+00:00', ahora)).toBe(0);
  });
});

describe('el reloj en texto', () => {
  it('en mm:ss por debajo de una hora y en h:mm:ss por encima', () => {
    expect(clock(0)).toBe('00:00');
    expect(clock(3)).toBe('00:03');
    expect(clock(125)).toBe('02:05');
    expect(clock(3600)).toBe('1:00:00');
    expect(clock(7200)).toBe('2:00:00');
  });
});
