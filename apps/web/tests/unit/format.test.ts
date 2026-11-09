import { describe, expect, it } from 'vitest';

import { formatDate, formatDateTime } from '../../src/lib/format';

describe('fechas para la interfaz', () => {
  it('formatea una fecha ISO con microsegundos como fecha y hora en es-ES', () => {
    const texto = formatDateTime('2026-11-08T22:43:07.294168');
    expect(texto).toContain('22:43');
    expect(texto).toContain('8/11/26');
    expect(texto).not.toContain('T');
    expect(texto).not.toContain('294168');
  });

  it('formatea una fecha sin hora', () => {
    expect(formatDate('2026-11-08')).toBe('8/11/26');
  });

  it('no inventa con valores ausentes o inválidos', () => {
    expect(formatDateTime(null)).toBe('—');
    expect(formatDateTime('')).toBe('—');
    expect(formatDateTime('no es una fecha')).toBe('no es una fecha');
  });
});
