/**
 * Leer la dirección de los apuntes por capítulos (F35, §3.1).
 *
 * La pantalla sirve **un capítulo cada vez**, así que tres decisiones que antes no existían son ahora
 * lógica pura y se prueban sin navegador:
 *
 * 1. **qué capítulo contiene un anclaje** — `#apartado-osi-capas` puede no estar en el capítulo
 *    abierto, y sin resolverlo el enlace deja al alumno arriba (medido: `scrollY = 0` con el párrafo
 *    a 10.288 px);
 * 2. **qué capítulo hay que abrir** — manda el anclaje; y si el capítulo pedido ya no existe, se
 *    corrige al que el servidor sirvió, para no dejar al alumno en un error que no puede arreglar;
 * 3. **qué apartado se está leyendo**, que es lo que marca el índice.
 */

import { describe, expect, it } from 'vitest';

import type { StudentNoteChapter } from '../../src/api/studentStudy';
import {
  anclaDeLaDireccion,
  apartadoALaVista,
  capituloQueAbrir,
  capituloQueContiene,
} from '../../src/features/student/capitulos';

const CAPITULOS: StudentNoteChapter[] = [
  {
    code: 'IV.7.1',
    title: 'El modelo TCP/IP y el modelo de referencia OSI.',
    position: 1,
    sections: [
      { number: 1, key: 'osi-capas', title: 'Las siete capas', anchor: 'osi-capas', questions_covered: 3 },
    ],
  },
  {
    code: 'IV.7.2',
    title: 'Protocolos TCP/IP.',
    position: 2,
    sections: [
      { number: 2, key: 'puertos', title: 'Puertos', anchor: 'puertos', questions_covered: 10 },
    ],
  },
];

describe('el anclaje que trae la dirección', () => {
  it('se lee con y sin el prefijo `apartado-`', () => {
    expect(anclaDeLaDireccion('#apartado-osi-capas')).toBe('osi-capas');
    // Un enlace guardado de antes de F35 traía el anclaje pelado: el elemento se llama
    // `apartado-osi-capas` y el enlace no bajaba a ninguna parte.
    expect(anclaDeLaDireccion('#osi-capas')).toBe('osi-capas');
  });

  it('no hay anclaje cuando no hay almohadilla o está mal formada', () => {
    expect(anclaDeLaDireccion('')).toBe('');
    expect(anclaDeLaDireccion('osi-capas')).toBe('');
    expect(anclaDeLaDireccion('#%ZZ')).toBe('');
  });
});

describe('el capítulo que contiene un anclaje', () => {
  it('dice el capítulo del apartado, no el primero', () => {
    expect(capituloQueContiene(CAPITULOS, 'puertos')).toBe('IV.7.2');
    expect(capituloQueContiene(CAPITULOS, 'osi-capas')).toBe('IV.7.1');
  });

  it('no inventa un capítulo para un anclaje que no está', () => {
    expect(capituloQueContiene(CAPITULOS, 'no-existe')).toBeNull();
    expect(capituloQueContiene(CAPITULOS, '')).toBeNull();
  });
});

describe('el capítulo que hay que abrir', () => {
  it('manda el anclaje sobre el capítulo pedido', () => {
    expect(
      capituloQueAbrir({ pedido: 'IV.7.1', servido: 'IV.7.1', delAncla: 'IV.7.2' }),
    ).toBe('IV.7.2');
  });

  it('no cambia nada si el anclaje es del capítulo que ya se sirve', () => {
    expect(capituloQueAbrir({ pedido: null, servido: 'IV.7.1', delAncla: 'IV.7.1' })).toBeNull();
  });

  it('corrige al capítulo servido cuando el pedido ya no existe', () => {
    // El servidor sirve el primero en vez de un 404: la dirección se corrige a lo que se está
    // leyendo de verdad, que es lo que evita que el alumno acabe en un error.
    expect(capituloQueAbrir({ pedido: 'IV.7.9', servido: 'IV.7.1', delAncla: null })).toBe('IV.7.1');
  });

  it('no hace nada sin apuntes que leer', () => {
    expect(capituloQueAbrir({ pedido: 'IV.7.1', servido: null, delAncla: null })).toBeNull();
  });
});

describe('el apartado que se está leyendo', () => {
  it('es el último cuyo principio ya ha pasado el límite', () => {
    expect(
      apartadoALaVista(
        [
          { anchor: 'a', top: -400 },
          { anchor: 'b', top: 120 },
          { anchor: 'c', top: 900 },
        ],
        300,
      ),
    ).toBe('b');
  });

  it('antes del primero, el primero: la lectura empieza donde empieza el capítulo', () => {
    expect(
      apartadoALaVista(
        [
          { anchor: 'a', top: 400 },
          { anchor: 'b', top: 900 },
        ],
        300,
      ),
    ).toBe('a');
  });

  it('sin apartados no marca nada', () => {
    expect(apartadoALaVista([], 300)).toBeNull();
  });
});
