import type { MappingStatus, OwnerScope, RightsReview, VersionStatus } from '../../api/library';
import type { StatusTone } from '../../components/StatusBadge';

/**
 * Vocabulario de la biblioteca en español (07_UI-UX §6 y §12).
 *
 * El servidor habla en códigos (`candidate`, `private_user`, `law_or_regulation`); la pantalla los
 * traduce para leerlos. La traducción es solo de presentación: qué estado tiene una versión, si sus
 * derechos están restringidos y de quién es la obra lo decide el servidor y viaja en la propia
 * respuesta. Aquí no se recalcula nada de eso.
 */

/**
 * Tipos documentales del vocabulario del servidor (04_INGESTION §6 y `domain/classification.py`).
 *
 * Se enumeran para poder **filtrar** por ellos, que es lo que el listado del servidor admite; un
 * código que no esté aquí se muestra tal cual en lugar de inventarle un nombre.
 */
export const DOCUMENT_TYPES: readonly string[] = [
  'convocation',
  'curriculum',
  'law_or_regulation',
  'official_technical',
  'private_syllabus',
  'personal_notes',
  'official_exam',
  'answer_key',
  'private_question_bank',
  'practical_case',
  'flashcards',
  'community_material',
  'unknown',
];

export const DOCUMENT_TYPE_LABEL: Record<string, string> = {
  convocation: 'Convocatoria',
  curriculum: 'Programa o temario',
  law_or_regulation: 'Norma o reglamento',
  official_technical: 'Documento técnico oficial',
  private_syllabus: 'Temario privado',
  personal_notes: 'Notas personales',
  official_exam: 'Examen oficial',
  answer_key: 'Plantilla de respuestas',
  private_question_bank: 'Banco de preguntas privado',
  practical_case: 'Caso práctico',
  flashcards: 'Fichas de repaso',
  community_material: 'Material de la comunidad',
  unknown: 'Sin clasificar',
};

export const OWNER_SCOPE_LABEL: Record<OwnerScope, string> = {
  public: 'público',
  private_user: 'privado tuyo',
  generated: 'generado por la aplicación',
};

export const OWNER_SCOPES: readonly OwnerScope[] = ['public', 'private_user', 'generated'];

export const VERSION_STATUS_LABEL: Record<VersionStatus, string> = {
  candidate: 'candidata, sin aceptar',
  accepted: 'aceptada',
  outdated: 'desactualizada',
  superseded: 'sustituida',
  withdrawn: 'retirada',
  rejected: 'rechazada',
};

export const VERSION_STATUS_TONE: Record<VersionStatus, StatusTone> = {
  candidate: 'warning',
  accepted: 'ok',
  outdated: 'warning',
  superseded: 'info',
  withdrawn: 'info',
  rejected: 'blocked',
};

export const RIGHTS_REVIEW_LABEL: Record<RightsReview, string> = {
  unknown: 'sin revisar',
  reviewed: 'revisada',
  restricted: 'restringida',
};

export const RIGHTS_REVIEW_TONE: Record<RightsReview, StatusTone> = {
  unknown: 'warning',
  reviewed: 'ok',
  restricted: 'blocked',
};

export const MAPPING_STATUS_LABEL: Record<MappingStatus, string> = {
  provisional: 'provisional, sin confirmar',
  accepted: 'aceptada',
  rejected: 'rechazada',
};

export const MAPPING_STATUS_TONE: Record<MappingStatus, StatusTone> = {
  provisional: 'warning',
  accepted: 'ok',
  rejected: 'info',
};

export const COVERAGE_TYPE_LABEL: Record<string, string> = {
  mention: 'se menciona',
  partial: 'cobertura parcial',
  complete: 'cobertura completa',
};

/** Etiqueta del estado de una versión cuando el código llega como texto libre. */
export function versionStatusLabel(status: string): string {
  return VERSION_STATUS_LABEL[status as VersionStatus] ?? status;
}

/** Tono del estado de una versión; un estado que no se conoce se marca como informativo. */
export function versionStatusTone(status: string): StatusTone {
  return VERSION_STATUS_TONE[status as VersionStatus] ?? 'info';
}

/** Etiqueta del tipo documental, con el código a la vista cuando no consta su nombre. */
export function documentTypeLabel(documentType: string): string {
  return DOCUMENT_TYPE_LABEL[documentType] ?? documentType;
}

/** Etiqueta del estado de revisión de derechos, o el código si el servidor añade uno nuevo. */
export function rightsReviewLabel(review: string): string {
  return RIGHTS_REVIEW_LABEL[review as RightsReview] ?? review;
}

/** Etiqueta del estado de un mapeo de programa. */
export function mappingStatusLabel(status: string): string {
  return MAPPING_STATUS_LABEL[status as MappingStatus] ?? status;
}

export function mappingStatusTone(status: string): StatusTone {
  return MAPPING_STATUS_TONE[status as MappingStatus] ?? 'info';
}

/** Etiqueta del tipo de cobertura de un mapeo. */
export function coverageTypeLabel(coverage: string): string {
  return COVERAGE_TYPE_LABEL[coverage] ?? coverage;
}

/**
 * Qué le pasó a una sección entre dos versiones (contrato: `SectionDiffSchema`).
 *
 * «Sin cambios» es un resultado, no un hueco: dice que la sección se comparó y su texto es el mismo.
 */
export const SECTION_DIFF_LABEL: Record<string, string> = {
  added: 'sección nueva',
  removed: 'sección quitada',
  changed: 'texto cambiado',
  unchanged: 'sin cambios',
};

export const SECTION_DIFF_TONE: Record<string, StatusTone> = {
  added: 'info',
  removed: 'warning',
  changed: 'warning',
  unchanged: 'ok',
};

export function sectionDiffLabel(kind: string): string {
  return SECTION_DIFF_LABEL[kind] ?? kind;
}

export function sectionDiffTone(kind: string): StatusTone {
  return SECTION_DIFF_TONE[kind] ?? 'info';
}

/**
 * Autoridad declarada del documento.
 *
 * El nivel es un código del servidor (A, B, C, D): aquí solo se muestra y se dice si falta, en
 * lugar de traducir la letra a un juicio que la aplicación no puede hacer.
 */
export function authorityLabel(authorityTier: string | null | undefined): string {
  return authorityTier === null || authorityTier === undefined || authorityTier === ''
    ? 'sin autoridad declarada'
    : `nivel ${authorityTier}`;
}

/** Página de una sección, escrita como se lee en el original. */
export function pageLabel(
  pageStart: number | null | undefined,
  pageEnd: number | null | undefined,
): string {
  if (pageStart === null || pageStart === undefined) {
    return 'sin página';
  }
  if (pageEnd !== null && pageEnd !== undefined && pageEnd !== pageStart) {
    return `páginas ${pageStart}-${pageEnd}`;
  }
  return `página ${pageStart}`;
}
