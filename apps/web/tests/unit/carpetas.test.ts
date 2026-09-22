/**
 * Pruebas del recorrido de carpetas que se sueltan o se eligen (S12.4).
 *
 * La parte que decide **qué entra y con qué nombre** es pura: entra un árbol de entradas con la
 * misma forma que da el navegador y sale la lista de ficheros con su ruta relativa. Se prueba aquí,
 * sin navegador, con entradas de mentira.
 */

import { describe, expect, it } from 'vitest';

import {
  esBasura,
  ficherosDeEntradas,
  ficherosDeSelector,
  MAX_FICHEROS_POR_TANDA,
  type EntradaDeCarpeta,
} from '../../src/features/ingestion/carpetas';

function fichero(nombre: string, contenido = 'x'): File {
  return new File([contenido], nombre, { type: 'text/plain' });
}

function entradaFichero(nombre: string, ruta: string): EntradaDeCarpeta {
  const contenido = fichero(nombre);
  return {
    isFile: true,
    isDirectory: false,
    name: nombre,
    fullPath: ruta,
    file: (exito) => {
      exito(contenido);
    },
  };
}

/** Una carpeta cuyo lector entrega las hijas en lotes, como hace el navegador (de 100 en 100). */
function entradaCarpeta(
  nombre: string,
  ruta: string,
  hijas: EntradaDeCarpeta[],
  porLote = 100,
): EntradaDeCarpeta {
  return {
    isFile: false,
    isDirectory: true,
    name: nombre,
    fullPath: ruta,
    createReader: () => {
      let servidas = 0;
      return {
        readEntries: (exito) => {
          const lote = hijas.slice(servidas, servidas + porLote);
          servidas += lote.length;
          exito(lote);
        },
      };
    },
  };
}

describe('recorrido de carpetas', () => {
  it('un fichero suelto entra con su nombre', async () => {
    const seleccion = await ficherosDeEntradas([entradaFichero('tema-01.txt', '/tema-01.txt')]);

    expect(seleccion).toHaveLength(1);
    expect(seleccion[0]?.name).toBe('tema-01.txt');
  });

  it('una carpeta entra entera y conserva la ruta de cada fichero', async () => {
    const arbol = entradaCarpeta('Apuntes TAI', '/Apuntes TAI', [
      entradaFichero('tema-01.pdf', '/Apuntes TAI/tema-01.pdf'),
      entradaCarpeta('Tema 3', '/Apuntes TAI/Tema 3', [
        entradaFichero('resumen.pdf', '/Apuntes TAI/Tema 3/resumen.pdf'),
      ]),
    ]);

    const seleccion = await ficherosDeEntradas([arbol]);

    expect(seleccion.map((item) => item.name)).toEqual([
      'Apuntes TAI/tema-01.pdf',
      'Apuntes TAI/Tema 3/resumen.pdf',
    ]);
  });

  it('no se queda con el primer lote del lector de carpeta', async () => {
    // El navegador entrega 100 entradas por llamada; quedarse con la primera perdería el resto.
    const hijas = Array.from({ length: 7 }, (_, indice) =>
      entradaFichero(`tema-${indice}.txt`, `/Carpeta/tema-${indice}.txt`),
    );
    const arbol = entradaCarpeta('Carpeta', '/Carpeta', hijas, 2);

    const seleccion = await ficherosDeEntradas([arbol]);

    expect(seleccion).toHaveLength(7);
    expect(seleccion[6]?.name).toBe('Carpeta/tema-6.txt');
  });

  it('deja fuera la basura que meten los sistemas operativos', async () => {
    const arbol = entradaCarpeta('Curso', '/Curso', [
      entradaFichero('tema.txt', '/Curso/tema.txt'),
      entradaFichero('.DS_Store', '/Curso/.DS_Store'),
      entradaFichero('._recurso', '/Curso/._recurso'),
      entradaFichero('Thumbs.db', '/Curso/Thumbs.db'),
      entradaCarpeta('__MACOSX', '/Curso/__MACOSX', [
        entradaFichero('fantasma.txt', '/Curso/__MACOSX/fantasma.txt'),
      ]),
    ]);

    const seleccion = await ficherosDeEntradas([arbol]);

    expect(seleccion.map((item) => item.name)).toEqual(['Curso/tema.txt']);
  });

  it('un fichero que el navegador no deja leer no tumba la tanda', async () => {
    const roto: EntradaDeCarpeta = {
      isFile: true,
      isDirectory: false,
      name: 'protegido.pdf',
      fullPath: '/Curso/protegido.pdf',
      file: (_exito, fallo) => {
        fallo?.(new Error('sin permisos'));
      },
    };
    const arbol = entradaCarpeta('Curso', '/Curso', [
      roto,
      entradaFichero('tema.txt', '/Curso/tema.txt'),
    ]);

    const seleccion = await ficherosDeEntradas([arbol]);

    expect(seleccion.map((item) => item.name)).toEqual(['Curso/tema.txt']);
  });

  it('una carpeta con demasiados ficheros se declara en lugar de subirse a medias', async () => {
    const hijas = Array.from({ length: MAX_FICHEROS_POR_TANDA + 1 }, (_, indice) =>
      entradaFichero(`tema-${indice}.txt`, `/Enorme/tema-${indice}.txt`),
    );
    const arbol = entradaCarpeta('Enorme', '/Enorme', hijas);

    await expect(ficherosDeEntradas([arbol])).rejects.toThrow(/más de 2000 ficheros/);
  });
});

describe('selector de ficheros y carpetas', () => {
  it('conserva la ruta relativa que rellena el navegador al elegir una carpeta', () => {
    const elegido = fichero('resumen.pdf', 'x');
    Object.defineProperty(elegido, 'webkitRelativePath', {
      value: 'Apuntes TAI/Tema 3/resumen.pdf',
    });

    const seleccion = ficherosDeSelector([elegido]);

    expect(seleccion[0]?.name).toBe('Apuntes TAI/Tema 3/resumen.pdf');
  });

  it('sin carpeta elegida, el nombre es el del fichero', () => {
    const seleccion = ficherosDeSelector([fichero('tema.txt')]);

    expect(seleccion[0]?.name).toBe('tema.txt');
  });

  it('la basura del sistema no llega al servidor', () => {
    expect(esBasura('.DS_Store')).toBe(true);
    expect(esBasura('Thumbs.db')).toBe(true);
    expect(esBasura('__MACOSX')).toBe(true);
    expect(esBasura('._oculto')).toBe(true);
    expect(esBasura('tema-01.pdf')).toBe(false);

    const seleccion = ficherosDeSelector([fichero('.DS_Store'), fichero('tema.pdf')]);

    expect(seleccion.map((item) => item.name)).toEqual(['tema.pdf']);
  });
});
