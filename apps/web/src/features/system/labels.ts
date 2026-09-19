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
