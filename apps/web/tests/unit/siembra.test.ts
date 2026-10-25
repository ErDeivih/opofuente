import { describe, expect, it } from 'vitest';

import { frasesDeLaSiembra, frasesSembradasEn } from '../screens/siembra';

/**
 * **El guardián de las capturas** (fase «lo que ve el alumno», punto 7).
 *
 * Lo que se comprueba aquí es lo que no se puede ver mirando un PNG: **que el programa sabe qué es la
 * siembra y que la reconoce**. Las tres comprobaciones son las que hacen falta para que sirva:
 *
 * 1. **las frases salen solas de los fixtures** —no de una lista escrita a mano que se queda vieja—;
 * 2. **la frase que se coló dos veces se detecta** cuando una pantalla la enseña;
 * 3. **una pantalla de la base real no la dispara** —un guardián que salta siempre no protege, estorba—.
 */
describe('el guardián de las capturas', () => {
  it('saca de los fixtures la frase que se coló dos veces', () => {
    const frases = frasesDeLaSiembra();
    expect(frases.length).toBeGreaterThan(0);
    expect(frases.some((frase) => frase.includes('Esquema Nacional de Seguridad'))).toBe(true);
  });

  it('la encuentra en una pantalla que la enseña', () => {
    const pantalla =
      'Test · 4 preguntas. El Esquema Nacional de Seguridad se regula en el Real Decreto ' +
      '311/2022 · Verdadero/Falso. Quedan 2 de 4.';
    expect(frasesSembradasEn(pantalla, frasesDeLaSiembra()).length).toBeGreaterThan(0);
  });

  it('no la encuentra en una pantalla de la base real', () => {
    const pantalla =
      'Hoy. Repaso: 9 para hoy. Repasar fallos (1). Tu progreso. Primera parte. IV.7 Redes.';
    expect(frasesSembradasEn(pantalla, frasesDeLaSiembra())).toHaveLength(0);
  });
});
