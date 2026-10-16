/**
 * `npm run screens`, con la opción `--datos <dir>` del §3.2 del cierre del objetivo.
 *
 * Las capturas de la siembra de pruebas son las que usan las pruebas, y se quedan donde están. Las que
 * el propietario **revisa** son las de una **copia de la base real**: el 16-oct-2026 se revisaron 60
 * capturas hechas sobre la siembra y no se pudo juzgar la aplicación que va a usar —el tema IV.7 salía
 * «Sin apuntes · 0 preguntas» y el resultado enseñaba preguntas inventadas—.
 *
 * Por eso esta herramienta hace tres cosas y ninguna más:
 *
 * 1. `--datos <dir>` mueve **solo** los datos de la suite (`OPOFUENTE_E2E_DATA_DIR`, que es la variable
 *    que `playwright.config.ts` ya respeta y que **no** borra el directorio: eso es lo que hace que la
 *    copia no se toque);
 * 2. las capturas de la copia van a `artifacts/screens-datos`, así que no pisan las de la siembra;
 * 3. dice **contra qué** está capturando al empezar. Sin eso, dentro de un mes nadie sabría cuál de las
 *    dos está mirando.
 */

import { spawn } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const AQUI = path.dirname(fileURLToPath(import.meta.url));
const RAIZ = path.dirname(AQUI);
const WEB = path.join(RAIZ, 'apps', 'web');

/**
 * Lee los argumentos de la línea de órdenes.
 *
 * Devuelve las opciones ya resueltas —qué datos, qué carpeta de salida, qué entorno y qué mensaje— y
 * `resto`, que son los argumentos que no son de esta herramienta y se le pasan a Playwright tal cual
 * (`--grep`, `--headed`…).
 */
export function leerOpciones(argumentos, raiz) {
  let datos = null;
  const resto = [];

  for (let indice = 0; indice < argumentos.length; indice += 1) {
    const argumento = argumentos[indice];
    if (argumento !== '--datos') {
      resto.push(argumento);
      continue;
    }
    const valor = argumentos[indice + 1];
    if (valor === undefined || valor.startsWith('--')) {
      throw new Error(
        '--datos necesita un directorio: `npm run screens -- --datos <dir>` (la copia de la base real)',
      );
    }
    datos = valor;
    indice += 1;
  }

  const salida = path.join(raiz, 'artifacts', datos === null ? 'screens' : 'screens-datos');
  const entorno = {
    OPOFUENTE_SCREENS_SALIDA: salida,
  };
  if (datos !== null) {
    entorno.OPOFUENTE_E2E_DATA_DIR = datos;
  }

  const siembra = path.join(raiz, '.e2e-data');
  const mensaje =
    datos === null
      ? `Capturando contra la siembra de pruebas (${siembra}) → ${salida}`
      : `Capturando contra los datos de ${datos} → ${salida}`;

  return { datos, salida, entorno, resto, mensaje };
}

function main() {
  let opciones;
  try {
    opciones = leerOpciones(process.argv.slice(2), RAIZ);
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error));
    process.exitCode = 2;
    return;
  }

  // Lo primero que se lee: contra qué datos se captura. Es lo que permite saber, dentro de un mes, cuál
  // de las dos carpetas de PNG se está mirando.
  console.log(opciones.mensaje);

  const cli = path.join(RAIZ, 'node_modules', '@playwright', 'test', 'cli.js');
  const configuracion = path.join(WEB, 'playwright.screens.config.ts');
  const hijo = spawn(
    process.execPath,
    [cli, 'test', '--config', configuracion, ...opciones.resto],
    {
      cwd: WEB,
      stdio: 'inherit',
      env: { ...process.env, ...opciones.entorno },
    },
  );
  hijo.on('exit', (codigo, senal) => {
    if (senal !== null) {
      process.kill(process.pid, senal);
      return;
    }
    process.exitCode = codigo ?? 1;
  });
}

// Solo se ejecuta cuando se lanza como herramienta: importarlo desde una prueba no captura nada.
if (process.argv[1] !== undefined && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main();
}
