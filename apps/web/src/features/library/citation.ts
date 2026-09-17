import type { Version } from '../../api/library';
import { versionName } from '../../api/library';

/**
 * Cita de una fuente: lo mínimo para poder volver a ella (07_UI-UX §6).
 *
 * Una cita sin título no se sabe de qué es; sin versión, de cuándo; y sin sección o página, no se
 * puede abrir. Las cuatro partes van siempre, y las que no constan se declaran como tales en lugar
 * de desaparecer en silencio: una cita incompleta que parece completa es peor que una que lo dice.
 */
export interface CitationInput {
  /** Título lógico del documento. */
  title: string;
  /** Versión citada: de ella salen su etiqueta y su URL. */
  version: Version;
  /** Dónde está el fragmento: la etiqueta de cita de la evidencia, o su sección y su página. */
  place: string;
}

export function buildCitation({ title, version, place }: CitationInput): string {
  const url = version.official_url;
  return [
    `Título: «${title}»`,
    `Versión: ${versionName(version)}`,
    `Lugar: ${place}`,
    `URL: ${url === null || url === undefined || url === '' ? 'no consta' : url}`,
  ].join('\n');
}

/**
 * Copia un texto al portapapeles.
 *
 * Devuelve `false` cuando el navegador no la deja copiar (permiso denegado, sin contexto seguro o
 * sin portapapeles) para que la pantalla lo diga, en vez de dar por copiado algo que no lo está.
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  const clipboard = navigator.clipboard;
  if (clipboard === undefined) {
    return false;
  }
  try {
    await clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
}

/** Lugar citado de una evidencia: su etiqueta del servidor o, si no la trae, su página. */
export function evidencePlace(
  citationLabel: string | null | undefined,
  page: number | null | undefined,
  ordinal: number,
): string {
  if (citationLabel !== null && citationLabel !== undefined && citationLabel !== '') {
    return citationLabel;
  }
  if (page !== null && page !== undefined) {
    return `página ${page}`;
  }
  return `evidencia ${ordinal}`;
}
