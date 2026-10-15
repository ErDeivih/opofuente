/**
 * El número con su palabra en su forma (F31).
 *
 * Nace de un defecto que se vio en la pantalla: la fila de un examen decía «1 claves sospechosas».
 * La prueba del servidor ata las seis categorías y esta ata el ayudante que usa la pantalla, para
 * que el mismo fallo no pueda volver por el otro lado.
 */

import { describe, expect, it } from 'vitest';

import { conNumero } from '../../src/lib/plural';

describe('el número con su palabra', () => {
  it('escribe el singular cuando hay uno', () => {
    expect(conNumero(1, 'clave sospechosa', 'claves sospechosas')).toBe('1 clave sospechosa');
  });

  it('escribe el plural cuando hay más de uno, cero incluido', () => {
    expect(conNumero(2, 'clave sospechosa', 'claves sospechosas')).toBe('2 claves sospechosas');
    expect(conNumero(0, 'clave sospechosa', 'claves sospechosas')).toBe('0 claves sospechosas');
  });

  it('no deriva el plural del singular: las dos formas se escriben', () => {
    // «pregunta que no se puede juzgar» no pluraliza añadiendo una «s».
    expect(conNumero(3, 'pregunta que no se puede juzgar', 'preguntas que no se pueden juzgar')).toBe(
      '3 preguntas que no se pueden juzgar',
    );
  });
});
