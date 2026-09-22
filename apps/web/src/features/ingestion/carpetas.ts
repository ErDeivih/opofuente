/**
 * Soltar o elegir **carpetas enteras**: qué ficheros entran, con qué nombre y qué se deja fuera.
 *
 * El navegador no da la ruta de una carpeta que se suelta —y hace bien: la aplicación corre en un
 * puerto local, pero no puede leer el disco por su cuenta—, así que una carpeta se recorre en el
 * propio navegador y sus ficheros se suben uno a uno **con su ruta relativa**. Esa ruta es lo que
 * permite que el lote conserve la estructura («Tema 3/apuntes.pdf») en vez de quedarse con treinta
 * ficheros sueltos llamados «apuntes.pdf».
 *
 * Dos formas de lo mismo, y las dos acaban en la misma lista:
 *
 * 1. **arrastrar** una carpeta sobre la zona de soltar: se recorre con `webkitGetAsEntry`, que es lo
 *    único que permite bajar por los directorios;
 * 2. **elegirla** con un selector de carpeta (`webkitdirectory`), que es la forma en la que el
 *    navegador sí rellena `webkitRelativePath`.
 *
 * Lo que se deja fuera: la basura que los sistemas operativos meten en las carpetas
 * (`__MACOSX`, `.DS_Store`, `Thumbs.db`, `desktop.ini` y los ficheros `._algo` de macOS). No es
 * material de estudio y llenaría la bandeja de entradas vacías.
 */

/** Un fichero a subir y el nombre con el que tiene que llegar al servidor. */
export interface FicheroParaSubir {
  file: File;
  /** Ruta relativa dentro de lo que se soltó o eligió. Es el nombre que viaja en la subida. */
  name: string;
}

/** Lo mínimo que se necesita de una entrada del navegador, para poder recorrerla y probarla. */
export interface EntradaDeCarpeta {
  isFile: boolean;
  isDirectory: boolean;
  name: string;
  fullPath: string;
  file?: (exito: (file: File) => void, fallo?: (error: unknown) => void) => void;
  createReader?: () => LectorDeCarpeta;
}

export interface LectorDeCarpeta {
  readEntries: (
    exito: (entradas: EntradaDeCarpeta[]) => void,
    fallo?: (error: unknown) => void,
  ) => void;
}

/** Tope de ficheros por tanda: más que esto no es «soltar una carpeta», es un volcado. */
export const MAX_FICHEROS_POR_TANDA = 2000;

/**
 * Tope de lotes por carpeta. `readEntries` entrega de cien en cien y termina con una lista vacía;
 * este tope existe para que un lector que no termine nunca (una implementación rota, un directorio
 * que crece mientras se lee) no deje la pantalla girando sin fin: se corta y el tope de ficheros
 * hace el resto, con su error y su mensaje.
 */
const MAX_LOTES_POR_CARPETA = 200;

const BASURA = new Set(['.ds_store', 'thumbs.db', 'desktop.ini', '__macosx']);

/** ¿Es basura del sistema operativo? Se compara en minúsculas y por nombre suelto. */
export function esBasura(nombre: string): boolean {
  const limpio = nombre.trim().toLowerCase();
  return BASURA.has(limpio) || limpio.startsWith('._');
}

/** Ficheros que llegan de un `input` de carpeta (`webkitdirectory`) o de uno normal. */
export function ficherosDeSelector(ficheros: FileList | File[]): FicheroParaSubir[] {
  const lista = Array.from(ficheros);
  const resultado: FicheroParaSubir[] = [];
  for (const file of lista) {
    // `webkitRelativePath` solo lo rellena el navegador cuando la elección es una carpeta: si está,
    // es la ruta con la que entró y es la que se conserva. Se comprueba que sea una cadena no vacía
    // porque hay entornos donde el campo no existe (`undefined`), y ahí el nombre es el del fichero.
    const relativa = file.webkitRelativePath;
    const ruta = typeof relativa === 'string' && relativa !== '' ? relativa : file.name;
    if (esBasura(file.name)) {
      continue;
    }
    resultado.push({ file, name: ruta });
  }
  return resultado;
}

/** Recorre las entradas de un «soltar» y devuelve los ficheros con su ruta relativa. */
export async function ficherosDeEntradas(
  entradas: EntradaDeCarpeta[],
): Promise<FicheroParaSubir[]> {
  const encontrados: FicheroParaSubir[] = [];
  for (const entrada of entradas) {
    await recorrer(entrada, '', encontrados);
  }
  return encontrados;
}

/** Recorre los elementos de un `DataTransfer` (lo que el navegador da al soltar algo). */
export async function ficherosSoltados(dataTransfer: DataTransfer): Promise<FicheroParaSubir[]> {
  const entradas: EntradaDeCarpeta[] = [];
  const items = Array.from(dataTransfer.items ?? []);
  for (const item of items) {
    if (item.kind !== 'file') {
      continue;
    }
    const entrada = leerEntrada(item);
    if (entrada !== null) {
      entradas.push(entrada);
    }
  }
  if (entradas.length === 0) {
    // Sin `webkitGetAsEntry` (o al soltar algo que no es un fichero) queda la lista plana: es el
    // caso de los ficheros sueltos, que el navegador sí entrega directamente.
    return ficherosDeSelector(dataTransfer.files);
  }
  return ficherosDeEntradas(entradas);
}

function leerEntrada(item: DataTransferItem): EntradaDeCarpeta | null {
  const conEntradas = item as DataTransferItem & {
    webkitGetAsEntry?: () => EntradaDeCarpeta | null;
  };
  if (typeof conEntradas.webkitGetAsEntry !== 'function') {
    return null;
  }
  return conEntradas.webkitGetAsEntry();
}

async function recorrer(
  entrada: EntradaDeCarpeta,
  prefijo: string,
  encontrados: FicheroParaSubir[],
): Promise<void> {
  if (esBasura(entrada.name)) {
    return;
  }
  const ruta = prefijo === '' ? entrada.fullPath.replace(/^\//, '') : `${prefijo}/${entrada.name}`;
  if (entrada.isFile) {
    if (encontrados.length >= MAX_FICHEROS_POR_TANDA) {
      throw new Error(
        `la carpeta trae más de ${MAX_FICHEROS_POR_TANDA} ficheros: suéltala por partes`,
      );
    }
    const file = await leerFichero(entrada);
    if (file !== null) {
      encontrados.push({ file, name: ruta });
    }
    return;
  }
  if (!entrada.isDirectory || entrada.createReader === undefined) {
    return;
  }
  for (const hija of await leerCarpeta(entrada)) {
    await recorrer(hija, ruta, encontrados);
  }
}

/** `readEntries` entrega como mucho un centenar de entradas por llamada: hay que insistir. */
async function leerCarpeta(entrada: EntradaDeCarpeta): Promise<EntradaDeCarpeta[]> {
  const lector = entrada.createReader?.();
  if (lector === undefined) {
    return [];
  }
  const todas: EntradaDeCarpeta[] = [];
  for (let ronda = 0; ronda < MAX_LOTES_POR_CARPETA; ronda += 1) {
    const lote = await new Promise<EntradaDeCarpeta[]>((resolver, rechazar) => {
      lector.readEntries(resolver, rechazar);
    });
    if (lote.length === 0) {
      return todas;
    }
    todas.push(...lote);
  }
  return todas;
}

async function leerFichero(entrada: EntradaDeCarpeta): Promise<File | null> {
  if (entrada.file === undefined) {
    return null;
  }
  return new Promise<File | null>((resolver) => {
    // Un fichero que el navegador no puede leer (permisos, borrado a mitad) no puede tumbar la
    // tanda entera: se deja fuera y los demás entran.
    entrada.file?.(
      (file) => {
        resolver(file);
      },
      () => {
        resolver(null);
      },
    );
  });
}
