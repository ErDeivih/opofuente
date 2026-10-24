/**
 * Las dos zonas de OpoFuente (F1 del rediseño, 6 de octubre de 2026).
 *
 * La aplicación tiene **dos mapas de navegación y ninguna entrada compartida**: el alumno estudia y
 * el propietario administra. Cada mapa vive aquí, junto, porque son la misma decisión —qué ve cada
 * zona— y porque tenerlos en un solo sitio hace imposible que una sección se cuele en la otra sin
 * que se vea en el diff.
 *
 * `summary` es lo que se lee en la pantalla de una sección que todavía no está construida: una frase
 * corta de qué hará, sin jerga de la trastienda (nada de conjuntos, claves ni versiones).
 */
export interface NavItem {
  readonly path: string;
  readonly label: string;
  readonly summary: string;
}

/** La zona del alumno: ocho entradas y ninguna más (remate, punto 2). */
export const STUDENT_NAV_ITEMS: readonly NavItem[] = [
  {
    path: '/',
    label: 'Hoy',
    summary: 'Lo que toca hoy y cómo llevas la preparación.',
  },
  {
    path: '/temario',
    label: 'Temario',
    summary:
      'Los bloques y los temas del programa, con tus apuntes y un test de cada tema.',
  },
  {
    path: '/tests',
    label: 'Tests',
    summary: 'Tú eliges los temas, cuántas preguntas quieres y cómo se corrigen.',
  },
  {
    path: '/simulacros',
    label: 'Simulacros',
    summary: 'Un examen completo como el del día, con su tiempo y su penalización.',
  },
  {
    path: '/examenes',
    label: 'Exámenes',
    summary: 'Los exámenes oficiales de años anteriores, hechos como en el examen.',
  },
  {
    path: '/repaso',
    label: 'Repaso',
    summary:
      'Las tarjetas de hoy, con el teclado: espacio para dar la vuelta y 1 a 4 para responder.',
  },
  {
    path: '/fallos',
    label: 'Fallos',
    summary: 'Las preguntas que has fallado, para repasarlas hasta dominarlas.',
  },
  {
    path: '/progreso',
    label: 'Progreso',
    summary: 'Tu porcentaje de acierto por bloque y por tema, y cómo evolucionas.',
  },
];

/**
 * La zona del propietario: su propio menú lateral, con las pantallas que ya existían (bandeja,
 * biblioteca, revisión, cambios, errores de importación, buscar, ajustes) más el banco, el programa y
 * la práctica, que desde aquí se administran.
 */
export const ADMIN_NAV_ITEMS: readonly NavItem[] = [
  {
    path: '/admin/importar',
    label: 'Importaciones',
    summary: 'Inventario en lectura, importación de una copia, incidencias e informe.',
  },
  {
    path: '/admin/biblioteca',
    label: 'Biblioteca',
    summary: 'Documentos lógicos, versiones, derechos, lector y asignaciones.',
  },
  {
    path: '/admin/revision',
    label: 'Revisión',
    summary: 'Propuestas de clasificación esperando una decisión.',
  },
  {
    path: '/admin/clasificacion',
    label: 'Clasificación',
    summary:
      'Las preguntas dudosas del clasificador: dales tema o márcalas fuera, con el teclado.',
  },
  {
    path: '/admin/avisos',
    label: 'Avisos',
    summary: 'Lo que el alumno marca como error en los apuntes, con su apartado, para despacharlo.',
  },
  {
    path: '/admin/incidencias',
    label: 'Incidencias',
    summary:
      'Lo que el sistema no ha podido resolver solo: respuestas correctas que no cuadran, huecos, normas cambiadas.',
  },
  {
    path: '/admin/apuntes',
    label: 'Apuntes',
    summary:
      'Los temas con lo que ha medido el motor: leer un borrador con su motivo y aprobarlo o rechazarlo.',
  },
  {
    path: '/admin/no-son-preguntas',
    label: 'No son preguntas',
    summary: 'Los enunciados que no se pueden contestar y las preguntas de otras administraciones.',
  },
  {
    path: '/admin/cambios',
    label: 'Cambios',
    summary: 'Versiones sustituidas y derivados que necesitan revisión.',
  },
  {
    path: '/admin/errores',
    label: 'Errores',
    summary: 'Cuaderno de errores y cola de repaso determinista.',
  },
  {
    path: '/admin/preguntas',
    label: 'Preguntas',
    summary: 'Banco de preguntas, claves versionadas, conflictos y procedencia.',
  },
  {
    path: '/admin/programa',
    label: 'Programa',
    summary: 'Árbol oficial del temario con su procedencia y las reglas del examen.',
  },
  {
    path: '/admin/estudiar',
    label: 'Estudiar',
    summary: 'Práctica, examen y corrección con puntuación calculada en servidor.',
  },
  {
    path: '/admin/buscar',
    label: 'Buscar',
    summary: 'Búsqueda y preguntas sobre el material recopilado, con sus citas.',
  },
  {
    path: '/admin/ajustes',
    label: 'Ajustes',
    summary: 'Almacenamiento, capacidades instaladas, proveedores, copias y diagnóstico.',
  },
  {
    path: '/admin/ui',
    label: 'Componentes',
    summary: 'Las piezas de la interfaz, en todos sus estados, para revisarlas en pantalla.',
  },
];

/**
 * Las direcciones de antes del rediseño y a dónde van ahora.
 *
 * No se borra ninguna: las que el propietario tiene en marcadores (y las pruebas que entran por URL)
 * siguen llegando a su pantalla. Se conserva la consulta y el ancla, porque hay enlaces con estado
 * dentro (`/biblioteca?documento=…` abre la ficha de ese documento).
 */
export const ROUTE_REDIRECTS: readonly { readonly from: string; readonly to: string }[] = [
  // **`/inicio` era la portada vieja y ya no existe** (remate, punto 3): la portada es «Hoy».
  // **Se redirige en vez de borrar la dirección** porque hay marcadores y enlaces dentro de la app
  // que siguen apuntando ahí, y un 404 no es una respuesta.
  { from: '/inicio', to: '/' },
  { from: '/bandeja', to: '/admin/importar' },
  { from: '/biblioteca', to: '/admin/biblioteca' },
  { from: '/revision', to: '/admin/revision' },
  { from: '/clasificacion', to: '/admin/clasificacion' },
  { from: '/cambios', to: '/admin/cambios' },
  { from: '/errores', to: '/admin/errores' },
  { from: '/preguntas', to: '/admin/preguntas' },
  { from: '/programa', to: '/admin/programa' },
  { from: '/estudiar', to: '/admin/estudiar' },
  { from: '/buscar', to: '/admin/buscar' },
  { from: '/ajustes', to: '/admin/ajustes' },
];
