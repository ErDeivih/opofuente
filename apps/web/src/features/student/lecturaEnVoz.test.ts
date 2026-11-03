import { describe, expect, it } from 'vitest';

import type { StudentNoteSection } from '../../api/studentStudy';
import {
  VELOCIDADES,
  fragmentosDelApartado,
  fragmentosDelCapitulo,
  frases,
  hayVozEnEspanol,
  sinAdornos,
  vozPreferida,
} from './lecturaEnVoz';

/** Un apartado de apuntes con lo mínimo que necesita la lectura en voz. */
function apartado(cambios: Partial<StudentNoteSection> = {}): StudentNoteSection {
  return {
    number: 1,
    key: 'IV.7.1.1',
    title: 'Modelo OSI',
    epigraph_code: 'IV.7.1',
    anchor: 'modelo-osi',
    body_markdown: '',
    questions_covered: 0,
    ...cambios,
  };
}

describe('sinAdornos', () => {
  it('quita negritas, código y enlaces y deja el texto que se dice', () => {
    expect(sinAdornos('El **modelo** OSI usa `tcp_ip` y [el enlace](https://x.test).')).toBe(
      'El modelo OSI usa tcp_ip y el enlace.',
    );
  });

  it('quita la cursiva de markdown pero no la barra baja de un identificador', () => {
    expect(sinAdornos('La _capa de enlace_ y tcp_ip.')).toBe('La capa de enlace y tcp_ip.');
  });

  it('no deja huecos dobles ni espacios en los extremos', () => {
    expect(sinAdornos('   <p>hola   mundo</p>  ')).toBe('hola mundo');
  });
});

describe('frases', () => {
  it('devuelve una lista vacía para un texto que no se puede decir', () => {
    expect(frases('   ')).toEqual([]);
  });

  it('junta frases cortas en un solo trozo', () => {
    expect(frases('Una. Dos. Tres.')).toEqual(['Una. Dos. Tres.']);
  });

  it('no parte una frase larga aunque pase del máximo', () => {
    const larga = `${'a'.repeat(300)}.`;
    expect(frases(larga)).toEqual([larga]);
  });

  it('corta antes de pasarse del máximo', () => {
    const trozos = frases(`${'a'.repeat(100)}. ${'b'.repeat(100)}. ${'c'.repeat(100)}.`);
    expect(trozos).toHaveLength(2);
    expect(trozos[0]).toHaveLength(203);
    expect(trozos[1]).toHaveLength(101);
  });
});

describe('fragmentosDelApartado', () => {
  const seccion = apartado({
    number: 2,
    key: 'IV.7.1.2',
    title: 'Capas',
    body_markdown: [
      '## Capas',
      'El modelo **OSI** separa el problema en capas. La segunda es la _capa de enlace_.',
      '',
      '- Capa física',
      '- Capa de enlace',
      '',
      '| Capa | Unidad |',
      '| --- | --- |',
      '| Transporte | Segmento |',
      '',
      '<!-- revisar: comprobar la cita -->',
    ].join('\n'),
  });

  it('dice títulos, párrafos, listas y filas de tabla en orden, sin marcas de revisión', () => {
    expect(fragmentosDelApartado(seccion).map((tramo) => tramo.text)).toEqual([
      'Capas',
      'El modelo OSI separa el problema en capas. La segunda es la capa de enlace.',
      'Capa física',
      'Capa de enlace',
      'Capa, Unidad',
      'Transporte, Segmento',
    ]);
  });

  it('marca cada tramo con su apartado y con una clave estable y única', () => {
    const tramos = fragmentosDelApartado(seccion);
    expect(tramos.map((tramo) => tramo.key)).toEqual([
      'IV.7.1.2:0',
      'IV.7.1.2:1',
      'IV.7.1.2:2',
      'IV.7.1.2:3',
      'IV.7.1.2:4',
      'IV.7.1.2:5',
    ]);
    expect(new Set(tramos.map((tramo) => tramo.key)).size).toBe(tramos.length);
    expect(tramos.every((tramo) => tramo.sectionNumber === 2)).toBe(true);
    expect(tramos.every((tramo) => tramo.sectionTitle === 'Capas')).toBe(true);
  });

  it('no dice nada de un apartado sin texto', () => {
    expect(fragmentosDelApartado(apartado())).toEqual([]);
  });
});

describe('fragmentosDelCapitulo', () => {
  it('dice el título de cada apartado antes de su texto', () => {
    const tramos = fragmentosDelCapitulo([
      apartado({ key: 'a', number: 1, title: 'Modelo OSI' }),
      apartado({
        key: 'b',
        number: 2,
        title: 'Capas',
        body_markdown: 'El modelo separa el problema en capas.',
      }),
    ]);
    expect(tramos.map((tramo) => tramo.text)).toEqual([
      'Modelo OSI',
      'Capas',
      'El modelo separa el problema en capas.',
    ]);
    expect(tramos.map((tramo) => tramo.sectionNumber)).toEqual([1, 2, 2]);
  });
});

describe('vozPreferida', () => {
  it('no inventa una voz cuando el equipo no tiene ninguna', () => {
    expect(vozPreferida([])).toBeNull();
  });

  it('prefiere el castellano de España', () => {
    const voces = [
      { name: 'Inglés', lang: 'en-US', localService: true },
      { name: 'Castellano de México', lang: 'es-MX', localService: true },
      { name: 'Español de España', lang: 'es-ES', localService: true },
    ];
    expect(vozPreferida(voces)?.name).toBe('Español de España');
  });

  it('entre dos voces del mismo idioma prefiere la del propio equipo', () => {
    const voces = [
      { name: 'Español de red', lang: 'es-ES', localService: false },
      { name: 'Español local', lang: 'es-ES', localService: true },
    ];
    expect(vozPreferida(voces)?.name).toBe('Español local');
  });

  it('si no hay español devuelve la que haya para no quedarse mudo', () => {
    const voces = [
      { name: 'Inglés británico', lang: 'en-GB', localService: true },
      { name: 'Inglés de red', lang: 'en-US', localService: false },
    ];
    expect(vozPreferida(voces)?.name).toBe('Inglés británico');
  });
});

describe('hayVozEnEspanol', () => {
  it('reconoce el español sin importar mayúsculas ni el país', () => {
    expect(hayVozEnEspanol([{ name: 'Voz', lang: 'ES-es' }])).toBe(true);
  });

  it('no cuenta un idioma que no habla español', () => {
    expect(hayVozEnEspanol([{ name: 'Voz', lang: 'en-GB' }])).toBe(false);
    expect(hayVozEnEspanol([])).toBe(false);
  });
});

describe('VELOCIDADES', () => {
  it('ofrece lenta, normal y rápida, de menor a mayor', () => {
    expect(VELOCIDADES.map((velocidad) => velocidad.valor)).toEqual([0.8, 1, 1.25]);
    expect(VELOCIDADES.map((velocidad) => velocidad.etiqueta)).toEqual([
      'Lenta',
      'Normal',
      'Rápida',
    ]);
    expect(VELOCIDADES.every((velocidad) => velocidad.descripcion.length > 0)).toBe(true);
  });
});
