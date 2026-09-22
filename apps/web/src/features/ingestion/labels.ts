import type { StatusTone } from '../../components/StatusBadge';

/**
 * Cómo se llama cada estado de un lote y de una entrada de la bandeja (DEBT-019).
 *
 * Vive aquí y no dentro de `TrayPage` porque lo usan dos pantallas: la bandeja y la actividad reciente
 * de Inicio (07_UI-UX §3.4). Dos tablas de etiquetas serían dos verdades y una de ellas acabaría
 * enseñando el valor crudo del enum —`unsupported_preserved`—, que no dice nada a quien lo lee.
 */

/** Tono del estado de un lote, para la insignia. */
export const BATCH_STATUS_TONE: Record<string, StatusTone> = {
  queued: 'info',
  running: 'info',
  cancel_requested: 'warning',
  succeeded: 'ok',
  failed: 'blocked',
  cancelled: 'info',
};

/** Cómo se lee el estado de un lote en palabras. */
export const BATCH_STATUS_LABEL: Record<string, string> = {
  queued: 'en cola',
  running: 'trabajando',
  cancel_requested: 'cancelación pedida',
  succeeded: 'terminado',
  failed: 'fallido',
  cancelled: 'cancelado',
};

/** Cómo se lee de dónde salió un lote. */
export const BATCH_KIND_LABEL: Record<string, string> = {
  file: 'carpeta elegida',
  folder: 'carpeta elegida',
  paste: 'texto pegado',
  url: 'descarga de una URL',
  upload: 'ficheros subidos',
};

export const SEVERITY_TONE: Record<string, StatusTone> = {
  info: 'info',
  warning: 'warning',
  error: 'blocked',
};

/**
 * Cómo se llama cada estado de una entrada, y qué hacer con él (DEBT-019).
 *
 * Antes la tabla pintaba el valor crudo del enum (`unsupported_preserved`), que no dice nada a quien
 * lo lee. Desde S03 un formato sin extractor **se conserva** en lugar de omitirse, y eso tiene que
 * verse: la entrada está copiada, no se ha extraído nada de ella, y no es un fallo.
 */
export const ITEM_STATUS: Record<string, { label: string; tone: StatusTone }> = {
  discovered: { label: 'descubierta', tone: 'info' },
  inventoried: { label: 'inventariada', tone: 'info' },
  omitted: { label: 'omitida', tone: 'warning' },
  copied: { label: 'copiada', tone: 'ok' },
  hashed: { label: 'copiada y verificada', tone: 'ok' },
  extracted: { label: 'copiada y con texto extraído', tone: 'ok' },
  unsupported_preserved: {
    label: 'conservada sin extractor (copiada, sin texto)',
    tone: 'warning',
  },
  expanded: { label: 'contenedor expandido', tone: 'info' },
  ocr_pending: { label: 'pendiente de OCR (copiada, sin texto)', tone: 'warning' },
  failed: { label: 'fallida', tone: 'blocked' },
  cancelled: { label: 'cancelada', tone: 'info' },
};

/** El estado de un lote, en palabras; lo que no esté en la tabla se dice tal cual, no se inventa. */
export function batchStatusLabel(status: string): string {
  return BATCH_STATUS_LABEL[status] ?? status;
}

/** De dónde salió el lote, en palabras. */
export function batchKindLabel(kind: string): string {
  return BATCH_KIND_LABEL[kind] ?? kind;
}
