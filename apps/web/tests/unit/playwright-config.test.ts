import { describe, expect, it, vi } from 'vitest';

import { default as configuracion } from '../../playwright.config';

/**
 * La configuración del E2E, comprobada como código (DEBT-021 criterio 2 y DEBT-026).
 *
 * Estas tres propiedades no son estilo: son lo que impide que la suite escriba en los datos de verdad
 * del propietario. El 22 de septiembre de 2026 un servidor olvidado con
 * `OPOFUENTE_DATA_DIR` apuntando a una copia del material real recibió lotes, documentos y conjuntos
 * de preguntas de la suite, porque la configuración **reutilizaba** el servidor que ya estaba
 * escuchando y heredaba su directorio de datos.
 *
 * La prueba lee la configuración de verdad (no una copia) y comprueba la propiedad que la mitiga. Lo
 * que no puede comprobar desde aquí es el efecto completo —Playwright negándose a arrancar con el
 * puerto ocupado—: eso se verificó a mano el 23 de septiembre de 2026 y está anotado en DEBT-021.
 */

type Servidor = { command?: string; env?: Record<string, string>; reuseExistingServer?: boolean };

const servidores = (
  Array.isArray(configuracion.webServer) ? configuracion.webServer : [configuracion.webServer]
) as Servidor[];

describe('configuración del E2E', () => {
  it('no reutiliza ningún servidor que ya esté escuchando', () => {
    expect(servidores).toHaveLength(2);
    for (const servidor of servidores) {
      expect(servidor.reuseExistingServer, servidor.command).toBe(false);
    }
  });

  it('la API del E2E usa su propio directorio de datos, no el del entorno', () => {
    const api = servidores[0];
    expect(api?.env?.OPOFUENTE_DATA_DIR).toMatch(/\.e2e-data$/);
    // Y lo fija: no copia lo que hubiera en el entorno del desarrollador.
    expect(api?.env?.OPOFUENTE_DATA_DIR).not.toBe(process.env.OPOFUENTE_DATA_DIR);
  });

  it('solo su propia variable mueve el directorio de datos del E2E', async () => {
    const originales = {
      datos: process.env.OPOFUENTE_DATA_DIR,
      e2e: process.env.OPOFUENTE_E2E_DATA_DIR,
    };
    try {
      process.env.OPOFUENTE_DATA_DIR = 'F:\\datos-de-verdad';
      process.env.OPOFUENTE_E2E_DATA_DIR = 'F:\\otro-sitio';
      vi.resetModules();
      const recargada = (await import('../../playwright.config')).default;
      const api = (
        Array.isArray(recargada.webServer) ? recargada.webServer : [recargada.webServer]
      ) as Servidor[];
      expect(api[0]?.env?.OPOFUENTE_DATA_DIR).toBe('F:\\otro-sitio');
    } finally {
      if (originales.datos === undefined) {
        delete process.env.OPOFUENTE_DATA_DIR;
      } else {
        process.env.OPOFUENTE_DATA_DIR = originales.datos;
      }
      if (originales.e2e === undefined) {
        delete process.env.OPOFUENTE_E2E_DATA_DIR;
      } else {
        process.env.OPOFUENTE_E2E_DATA_DIR = originales.e2e;
      }
      vi.resetModules();
    }
  });
});
