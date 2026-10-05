/**
 * Fechas legibles para la interfaz, en un solo sitio.
 *
 * La API sirve las fechas en UTC con su zona («2026-10-05T10:43:52.793645Z»), así que el navegador
 * las convierte a la hora local de quien estudia. Antes cada pantalla enseñaba el valor en bruto
 * («2026-10-01T13:41:58.984423»), que no dice nada (5 de octubre de 2026).
 */

const FORMATO_COMPLETO = new Intl.DateTimeFormat('es-ES', {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
});

const FORMATO_DIA = new Intl.DateTimeFormat('es-ES', {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
});

/** El instante de una fecha del servidor, tolerando que llegue sin zona (se toma por UTC). */
function instante(valor: string): Date | null {
  const limpio = valor.trim();
  const tieneZona = /(?:Z|[+-]\d{2}:?\d{2})$/.test(limpio);
  const fecha = new Date(tieneZona ? limpio : `${limpio}Z`);
  return Number.isNaN(fecha.getTime()) ? null : fecha;
}

/** «5 oct 2026, 12:43». Si la fecha no se entiende, se devuelve tal cual en vez de inventar nada. */
export function fechaLegible(valor: string | null | undefined): string {
  if (!valor) {
    return 'sin fecha';
  }
  const fecha = instante(valor);
  return fecha === null ? valor : FORMATO_COMPLETO.format(fecha);
}

/** «5 oct 2026». */
export function diaLegible(valor: string | null | undefined): string {
  if (!valor) {
    return 'sin fecha';
  }
  const fecha = instante(valor);
  return fecha === null ? valor : FORMATO_DIA.format(fecha);
}
