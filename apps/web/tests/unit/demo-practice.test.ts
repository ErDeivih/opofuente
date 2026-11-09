import { beforeEach, describe, expect, it } from 'vitest';

import { loadProgress, resetProgress, saveResult, scoreAnswers } from '../../demo/practice';

beforeEach(() => {
  resetProgress();
});

describe('progreso de la demo estática', () => {
  it('puntúa aciertos sobre el total, sin penalización', () => {
    const preguntas = [{ correct: 'a' }, { correct: 'b' }, { correct: 'c' }];
    expect(scoreAnswers({ 0: 'a', 1: 'c', 2: 'c' }, preguntas)).toEqual({ correct: 2, total: 3 });
    expect(scoreAnswers({}, preguntas)).toEqual({ correct: 0, total: 3 });
  });

  it('guarda el mejor resultado y cuenta los intentos', () => {
    saveResult('i-1', 4, 10);
    const segundo = saveResult('i-1', 8, 10);
    expect(segundo.best).toBe(80);
    expect(segundo.attempts).toBe(2);
    expect(segundo.lastScore).toBe(8);
    expect(loadProgress()['i-1']?.best).toBe(80);
  });

  it('borra el progreso sin tocar nada más', () => {
    saveResult('ii-13', 5, 10);
    resetProgress();
    expect(loadProgress()).toEqual({});
  });
});
