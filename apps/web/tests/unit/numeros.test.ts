/**
 * Los números de la interfaz, en español (§2.2 del cierre del objetivo).
 *
 * El propietario lo vio en las capturas: las notas salían «0.0000» en vez de «0,00». El dato viaja
 * del servidor con **punto y cuatro decimales** (`decimal_text`, que es el decimal de la fracción
 * exacta); la coma y las dos cifras son de la interfaz. Aquí se comprueba que hay **un solo** sitio
 * donde eso se decide, que es lo que impide que vuelvan a convivir tres formatos.
 */

import { describe, expect, it } from 'vitest';

import {
  formatearEscala,
  formatearNota,
  formatearPorcentaje,
  notaDeDecimal,
  notaDeFraccion,
} from '../../src/lib/numeros';

describe('los números de la interfaz', () => {
  it('una nota va con coma y dos decimales', () => {
    expect(formatearNota(0)).toBe('0,00');
    expect(formatearNota(12.5)).toBe('12,50');
    expect(formatearNota(-1 / 3)).toBe('-0,33');
    expect(formatearNota(28.125)).toBe('28,13');
  });

  it('la nota se calcula de la fracción exacta, no del decimal que manda el servidor', () => {
    // El decimal del servidor viene con cuatro cifras y con punto: la pantalla no lo enseña tal cual.
    expect(notaDeFraccion('1/3')).toBe('0,33');
    expect(notaDeFraccion('38/3')).toBe('12,67');
    expect(notaDeFraccion('42')).toBe('42,00');
    expect(notaDeFraccion('-1/3')).toBe('-0,33');
    expect(notaDeFraccion(' 128/3 ')).toBe('42,67');
  });

  it('un texto que no es una fracción no se inventa', () => {
    expect(notaDeFraccion('')).toBeNull();
    expect(notaDeFraccion('sin clave')).toBeNull();
    expect(notaDeFraccion('1/0')).toBeNull();
  });

  it('el decimal suelto del servidor también se lee en español', () => {
    expect(notaDeDecimal('0.0000')).toBe('0,00');
    expect(notaDeDecimal('1.6667')).toBe('1,67');
    expect(notaDeDecimal('-0.3333')).toBe('-0,33');
    expect(notaDeDecimal('sin clave')).toBeNull();
  });

  it('la escala (máximos y mínimos) no arrastra ceros de más', () => {
    // «sobre 50» y no «sobre 50,00»: la cifra del ejercicio se lee como la publica la convocatoria.
    expect(formatearEscala(50)).toBe('50');
    expect(formatearEscala(25.5)).toBe('25,5');
    expect(formatearEscala(0.33)).toBe('0,33');
  });

  it('los porcentajes van sin decimales salvo que se pidan', () => {
    expect(formatearPorcentaje(0.9)).toBe('90 %');
    expect(formatearPorcentaje(0)).toBe('0 %');
    expect(formatearPorcentaje(1)).toBe('100 %');
    expect(formatearPorcentaje(0.902, { decimales: 1 })).toBe('90,2 %');
  });
});
