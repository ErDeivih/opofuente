/**
 * Secciones del MVP (07_UI-UX §2 y 01_PRODUCT-SPEC §4).
 *
 * `slice` es `null` cuando la sección ya existe. Las que no existen se anuncian como
 * pendientes con su slice: la interfaz nunca muestra una pantalla vacía sin explicación ni
 * un botón que no hace nada (16_TRACEABILITY §4).
 */
export interface NavItem {
  readonly path: string;
  readonly label: string;
  readonly slice: string | null;
  readonly summary: string;
}

export const NAV_ITEMS: readonly NavItem[] = [
  {
    path: '/',
    label: 'Inicio',
    slice: null,
    summary: 'Estado real del sistema y siguientes pasos.',
  },
  {
    path: '/bandeja',
    label: 'Bandeja',
    slice: 'S02',
    summary: 'Inventario, importación, incidencias y revisión en lote de material.',
  },
  {
    path: '/programa',
    label: 'Programa',
    slice: 'S01',
    summary: 'Árbol oficial del temario con cobertura, preguntas y dominio.',
  },
  {
    path: '/biblioteca',
    label: 'Biblioteca',
    slice: 'S05',
    summary: 'Documentos lógicos, versiones, derechos, lector y asignaciones.',
  },
  {
    path: '/preguntas',
    label: 'Preguntas',
    slice: 'S06',
    summary: 'Banco de preguntas, claves versionadas, conflictos y procedencia.',
  },
  {
    path: '/estudiar',
    label: 'Estudiar',
    slice: 'S07',
    summary: 'Práctica, examen y corrección con puntuación calculada en servidor.',
  },
  {
    path: '/errores',
    label: 'Errores',
    slice: 'S10',
    summary: 'Cuaderno de errores y cola de repaso determinista.',
  },
  {
    path: '/cambios',
    label: 'Cambios',
    slice: 'S11',
    summary: 'Versiones sustituidas y derivados que necesitan revisión.',
  },
  {
    path: '/ajustes',
    label: 'Ajustes',
    slice: 'S12',
    summary: 'Almacenamiento, capacidades instaladas, proveedores y copias.',
  },
];

export function findNavItem(path: string): NavItem | undefined {
  return NAV_ITEMS.find((item) => item.path === path);
}
