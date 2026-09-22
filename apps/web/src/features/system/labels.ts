/** Tamaños legibles para la pantalla de Ajustes. Se comparte con el estado del sistema. */
export function formatBytes(value: number): string {
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let size = value;
  let unit = 0;
  while (size >= 1024 && unit < units.length - 1) {
    size /= 1024;
    unit += 1;
  }
  return `${size.toFixed(unit === 0 ? 0 : 1)} ${units[unit] ?? 'B'}`;
}

export function describeError(error: unknown): string {
  return error instanceof Error ? error.message : 'Error desconocido';
}

/**
 * El destino de un proveedor con palabras que no se pueden confundir (07_UI-UX §11, DEBT-001).
 *
 * `unknown` **nunca** se presenta como local: si no se puede determinar a dónde va el contenido, se
 * dice así. Es la misma frase en las dos pantallas donde se lee el destino (Ajustes y el estado del
 * sistema) porque tener dos maneras de decir lo mismo es tener dos maneras de equivocarse.
 */
export function destinationLabel(destination: string): string {
  if (destination === 'local') {
    return 'no sale de tu equipo';
  }
  if (destination === 'remote') {
    return 'sale a un tercero';
  }
  if (destination === 'unknown') {
    return 'no se puede determinar';
  }
  return 'sin proveedor';
}
