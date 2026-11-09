/**
 * Fechas y horas para la interfaz.
 *
 * La API devuelve ISO 8601 (con microsegundos cuando la base es SQLite). Enseñarlo tal cual parece
 * un volcado de base de datos; aquí se pasa a `es-ES`. Nunca se cambia el valor original: las
 * `dateTime` de `<time>` siguen llevando el ISO para quien lo necesite.
 */

const DATE_TIME = new Intl.DateTimeFormat('es-ES', {
  dateStyle: 'short',
  timeStyle: 'short',
});

const DATE_ONLY = new Intl.DateTimeFormat('es-ES', { dateStyle: 'short' });

/** Fecha y hora legibles; `—` si no hay valor y el texto original si no es una fecha válida. */
export function formatDateTime(value: string | null | undefined): string {
  if (value === null || value === undefined || value.trim() === '') {
    return '—';
  }
  const fecha = new Date(value);
  if (Number.isNaN(fecha.getTime())) {
    return value;
  }
  return DATE_TIME.format(fecha);
}

/** Fecha sin hora (para valores que ya vienen como `YYYY-MM-DD`). */
export function formatDate(value: string | null | undefined): string {
  if (value === null || value === undefined || value.trim() === '') {
    return '—';
  }
  const fecha = new Date(`${value.slice(0, 10)}T00:00:00`);
  if (Number.isNaN(fecha.getTime())) {
    return value;
  }
  return DATE_ONLY.format(fecha);
}
