/**
 * La opción `--datos <dir>` de `npm run screens` (§3.2 del cierre del objetivo).
 *
 * Las 60 capturas de la siembra se quedan —las usan las pruebas—; las de la copia de la base real son
 * las que el propietario revisa. Lo que se comprueba aquí es lo que separa una cosa de la otra:
 *
 * 1. `--datos` **elige el directorio de datos** y no toca la siembra (`.e2e-data` del repositorio);
 * 2. las capturas de la copia van a **otra carpeta**, así que no pisan las de la siembra;
 * 3. la salida **dice contra cuál está capturando**: dentro de un mes nadie sabría cuál de las dos
 *    está mirando.
 */

import { describe, expect, it } from 'vitest';

import { leerOpciones } from '../../../../scripts/screens.mjs';

const RAIZ = 'F:\\temp-opofuente\\opofuente-acabado';

describe('las opciones de npm run screens', () => {
  it('sin --datos se captura contra la siembra de siempre', () => {
    const opciones = leerOpciones([], RAIZ);
    expect(opciones.datos).toBeNull();
    expect(opciones.entorno.OPOFUENTE_E2E_DATA_DIR).toBeUndefined();
    expect(opciones.salida).toBe('F:\\temp-opofuente\\opofuente-acabado\\artifacts\\screens');
  });

  it('--datos apunta las capturas a la copia y las saca de la carpeta de la siembra', () => {
    const opciones = leerOpciones(['--datos', 'F:\\copia-real'], RAIZ);
    expect(opciones.datos).toBe('F:\\copia-real');
    expect(opciones.entorno.OPOFUENTE_E2E_DATA_DIR).toBe('F:\\copia-real');
    expect(opciones.salida).toBe('F:\\temp-opofuente\\opofuente-acabado\\artifacts\\screens-datos');
    // Y la siembra no se toca: no hay ninguna variable que la mueva.
    expect(opciones.entorno.OPOFUENTE_DATA_DIR).toBeUndefined();
  });

  it('la ruta de la copia se resuelve tal cual se escribe', () => {
    const opciones = leerOpciones(['--datos', 'F:\\temp-opofuente\\f24-datos'], RAIZ);
    expect(opciones.datos).toBe('F:\\temp-opofuente\\f24-datos');
  });

  it('--datos sin valor es un error que se explica, no una captura contra la siembra', () => {
    expect(() => leerOpciones(['--datos'], RAIZ)).toThrow(/--datos necesita un directorio/i);
  });

  it('los argumentos que no son de esta herramienta se le pasan a Playwright', () => {
    const opciones = leerOpciones(['--grep', 'resultado', '--datos', 'F:\\copia'], RAIZ);
    expect(opciones.datos).toBe('F:\\copia');
    expect(opciones.resto).toEqual(['--grep', 'resultado']);
  });

  it('el mensaje de arranque dice contra qué datos está capturando', () => {
    const conDatos = leerOpciones(['--datos', 'F:\\copia'], RAIZ);
    expect(conDatos.mensaje).toContain('F:\\copia');
    const sinDatos = leerOpciones([], RAIZ);
    expect(sinDatos.mensaje).toMatch(/siembra/i);
    expect(sinDatos.mensaje).toContain('.e2e-data');
  });
});
