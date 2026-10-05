import { describe, expect, it } from 'vitest';

import { diaLegible, fechaLegible } from '../../src/lib/fechas';

/**
 * Fechas legibles (5 de octubre de 2026).
 *
 * La interfaz enseñaba el valor en bruto de la API («2026-10-01T13:41:58.984423»), que no dice nada.
 * Aquí se comprueba que se lee en la hora local de quien estudia y que una fecha ilegible se enseña
 * tal cual en vez de inventarse una.
 */
describe('las fechas que se enseñan', () => {
  it('una fecha con zona se enseña en formato legible', () => {
    const texto = fechaLegible('2026-10-05T10:43:52.793645Z');
    expect(texto).toContain('2026');
    expect(texto).toContain('oct');
    expect(texto).not.toContain('T');
    expect(texto).toMatch(/\d{2}:\d{2}/);
  });

  it('una fecha sin zona se toma por UTC, igual que en el cronómetro', () => {
    expect(fechaLegible('2026-10-05T10:43:52.793645')).toBe(
      fechaLegible('2026-10-05T10:43:52.793645+00:00'),
    );
  });

  it('sin fecha se dice «sin fecha» y con una ilegible se enseña tal cual', () => {
    expect(fechaLegible(null)).toBe('sin fecha');
    expect(fechaLegible(undefined)).toBe('sin fecha');
    expect(fechaLegible('vaya')).toBe('vaya');
    expect(diaLegible('vaya')).toBe('vaya');
  });

  it('el día va sin hora', () => {
    const dia = diaLegible('2026-10-05T10:43:52Z');
    expect(dia).toContain('5');
    expect(dia).toContain('oct');
    expect(dia).not.toMatch(/\d{2}:\d{2}/);
  });
});
