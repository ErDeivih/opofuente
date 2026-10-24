/**
 * Los datos de la zona del alumno tal como los sirve la API (F13), para las pruebas de las pantallas.
 *
 * Van en un fichero propio y no dentro de `testUtils.tsx` porque son de un área concreta —Inicio,
 * Temario y los apuntes del tema— y porque el temario de TAI se repite en las tres pruebas: un
 * temario de mentira distinto en cada una haría que las tres comprobaran cosas distintas.
 *
 * Los códigos y los títulos son los del programa real (`IV.1`, `IV.10`), que es lo que hace que la
 * prueba del orden numérico sirva de algo.
 */

import type { StudentOverview, StudentSyllabus, StudentTestPlan, StudentTopic } from '../../src/api/studentStudy';
import type {
  StudentMistakes,
  StudentMockExamPlan,
  StudentNotes,
  StudentOfficialExams,
  StudentProgress,
} from '../../src/api/studentStudy';
import type { StudentSessionResult } from '../../src/api/studentTests';

export const TEMA_CON_APUNTES = 'IV.1';
export const TEMA_EN_BORRADOR = 'IV.7';

/** El temario: dos bloques, con `IV.10` detrás de `IV.9` (el caso que ordena mal por texto). */
export const syllabusFixture: StudentSyllabus = {
  opposition: { code: 'tai-age', name: 'Cuerpo de Técnicos Auxiliares de Informática' },
  blocks: [
    {
      code: 'I',
      title: 'Organización del Estado y Administración electrónica',
      position: 1,
      available_questions: 40,
      answered: 25,
      correct: 16,
      accuracy: 0.64,
      due_reviews: 4,
      topics: [
        {
          code: 'I.1',
          number: 1,
          title: 'La Constitución Española de 1978. Derechos y deberes fundamentales.',
          available_questions: 40,
          answered: 25,
          correct: 16,
          accuracy: 0.64,
          due_reviews: 4,
          notes_state: 'published',
        },
        {
          code: 'I.6',
          number: 6,
          title: 'La sociedad de la información. Identidad y firma electrónica.',
          available_questions: 12,
          answered: 0,
          correct: 0,
          accuracy: null,
          due_reviews: 0,
          notes_state: 'draft',
        },
      ],
    },
    {
      code: 'IV',
      title: 'Sistemas y comunicaciones',
      position: 4,
      available_questions: 60,
      answered: 12,
      correct: 9,
      accuracy: 0.75,
      due_reviews: 1,
      topics: [
        {
          code: 'IV.1',
          number: 1,
          title: 'Instalación y configuración de sistemas operativos.',
          available_questions: 30,
          answered: 12,
          correct: 9,
          accuracy: 0.75,
          due_reviews: 1,
          notes_state: 'published',
        },
        {
          code: 'IV.7',
          number: 7,
          title: 'El modelo TCP/IP y el modelo de referencia OSI de ISO. Protocolos TCP/IP.',
          available_questions: 30,
          answered: 0,
          correct: 0,
          accuracy: null,
          due_reviews: 0,
          notes_state: 'draft',
        },
        {
          code: 'IV.10',
          number: 10,
          title: 'Gestión de redes de área local.',
          available_questions: 0,
          answered: 0,
          correct: 0,
          accuracy: null,
          due_reviews: 0,
          notes_state: 'none',
        },
      ],
    },
  ],
};

export const overviewFixture: StudentOverview = {
  opposition: { code: 'tai-age', name: 'Cuerpo de Técnicos Auxiliares de Informática' },
  in_progress: {
    id: 'ses-1',
    mode: 'practice',
    status: 'running',
    title: 'Test de IV.7',
    total_questions: 25,
    answered_questions: 12,
    time_limit_minutes: null,
    started_at: '2026-10-11T09:00:00Z',
    server_now: '2026-10-11T09:00:00Z',
    finished_at: null,
    created_at: '2026-10-11T08:59:00Z',
    result: null,
    practical_case_origin: null,
    practical_case_statement: null,
  },
  due_reviews: 23,
  blocks: syllabusFixture.blocks,
  recent_tests: [
    {
      id: 'ses-2',
      mode: 'practice',
      status: 'finished',
      title: 'Test de IV.1',
      total_questions: 20,
      answered_questions: 20,
      time_limit_minutes: null,
      started_at: '2026-10-10T09:00:00Z',
      server_now: '2026-10-10T09:20:00Z',
      finished_at: '2026-10-10T09:20:00Z',
      created_at: '2026-10-10T08:59:00Z',
      result: {
        correct: 14,
        wrong: 4,
        blank: 2,
        points: '38/3',
        // La API manda el decimal con **punto y cuatro cifras** (`decimal_text`), no con coma: la
        // coma es de la interfaz, que lo formatea con `Intl`. Este dato estuvo escrito «12,67» y por
        // eso la prueba no veía el «12.6667» que el propietario tenía delante.
        points_decimal: '12.6667',
        maximum: null,
        passed: null,
      },
      practical_case_origin: null,
      practical_case_statement: null,
    },
  ],
};

export const topicFixture: StudentTopic = {
  code: 'IV.7',
  number: 7,
  title: 'El modelo TCP/IP y el modelo de referencia OSI de ISO. Protocolos TCP/IP.',
  description: null,
  block_code: 'IV',
  block_title: 'Sistemas y comunicaciones',
  epigraphs: [
    { code: 'IV.7.1', title: 'La arquitectura TCP/IP' },
    { code: 'IV.7.2', title: 'Direccionamiento y protocolos' },
  ],
  progress: {
    code: 'IV.7',
    number: 7,
    title: 'El modelo TCP/IP',
    available_questions: 30,
    answered: 8,
    correct: 5,
    accuracy: 0.625,
    due_reviews: 2,
    notes_state: 'draft',
  },
};

/**
 * Los apuntes de un tema: dos **capítulos** (epígrafes oficiales) y tres apartados, con tabla en el
 * primero, una cifra de preguntas por apartado y el último sin ninguna —el caso en el que no se
 * pinta nota al margen—. El primero va en su propio capítulo para que se pueda probar que el índice
 * lleva al capítulo que toca y que un anclaje de otro capítulo abre el suyo.
 */
export const notesFixture: StudentNotes = {
  code: 'IV.7',
  state: 'draft',
  generated_at: '2026-10-10T18:09:00Z',
  chapter: 'IV.7.1',
  chapters: [
    {
      code: 'IV.7.1',
      title: 'El modelo TCP/IP y el modelo de referencia OSI.',
      position: 1,
      sections: [
        {
          number: 1,
          key: 'tcpip-arquitectura',
          title: 'La arquitectura TCP/IP: capas, protocolos y familias',
          anchor: 'tcpip-arquitectura',
          questions_covered: 7,
        },
      ],
    },
    {
      code: 'IV.7.2',
      title: 'Protocolos TCP/IP.',
      position: 2,
      sections: [
        {
          number: 2,
          key: 'udp',
          title: 'UDP: datagramas sin conexión',
          anchor: 'udp',
          questions_covered: 1,
        },
        {
          number: 3,
          key: 'otros-protocolos',
          title: 'Otros protocolos',
          anchor: 'otros-protocolos',
          questions_covered: 0,
        },
      ],
    },
  ],
  sections: [
    {
      number: 1,
      key: 'tcpip-arquitectura',
      title: 'La arquitectura TCP/IP: capas, protocolos y familias',
      epigraph_code: 'IV.7.1',
      anchor: 'tcpip-arquitectura',
      body_markdown:
        '## Las cuatro capas\n\nEl modelo describe la comunicación en cuatro capas.\n\n' +
        '| Capa | Unidad |\n| --- | --- |\n| Transporte | Segmento |\n| Internet | Paquete |\n',
      questions_covered: 7,
    },
  ],
};

/**
 * Los mismos apuntes con el **segundo** capítulo abierto: es el caso del anclaje que vive en un
 * capítulo que no es el primero (`#apartado-udp`), que es el que se rompía al paginar.
 */
export const notesSegundoCapituloFixture: StudentNotes = {
  ...notesFixture,
  chapter: 'IV.7.2',
  sections: [
    {
      number: 2,
      key: 'udp',
      title: 'UDP: datagramas sin conexión',
      epigraph_code: 'IV.7.2',
      anchor: 'udp',
      body_markdown: 'El datagrama UDP no tiene conexión ni acuse de recibo.',
      questions_covered: 1,
    },
    {
      number: 3,
      key: 'otros-protocolos',
      title: 'Otros protocolos',
      epigraph_code: 'IV.7.2',
      anchor: 'otros-protocolos',
      body_markdown: 'Otros protocolos de la familia.',
      questions_covered: 0,
    },
  ],
};

/** Los mismos apuntes, ya publicados: es lo que lleva la marca «Versión generada · en revisión». */
export const notesPublishedFixture: StudentNotes = { ...notesFixture, state: 'published' };

/** El plan de un test (F22): los tamaños que ofrece la aplicación y lo que dura el reloj de cada uno. */
export const testPlanFixture: StudentTestPlan = {
  counts: [
    { questions: 10, minutes: 20 },
    { questions: 20, minutes: 40 },
    { questions: 25, minutes: 50 },
    { questions: 50, minutes: 100 },
    { questions: 100, minutes: 200 },
  ],
  timed_note:
    'El reloj de un test lo pone la aplicación —dos minutos por pregunta, redondeado a cinco—. El ' +
    'tiempo de un examen lo fija la convocatoria, y es el que lleva un test cuando no se le pone ' +
    'el reloj del test.',
  convocation_minutes: 120,
};

/** El mismo plan sin el tiempo del ejercicio en la convocatoria: `null` no es «sin tiempo». */
export const testPlanSinTiempoFixture: StudentTestPlan = {
  ...testPlanFixture,
  convocation_minutes: null,
};

/* ------------------------------------------------------------------ F14: el cierre del ciclo */

/**
 * El resultado de un test terminado: cuatro preguntas de dos temas, una bien y tres mal.
 *
 * Lleva **de todo** a propósito: una pregunta de cada tema fallada, la acertada en un tema distinto
 * del de las falladas (para que el desglose no se pueda escribir por posición), una reserva y una
 * pregunta que la plantilla no corrige (`void`), que es el caso que la pantalla tiene que saber
 * contar sin llamarlo fallo.
 */
export const sessionResultFixture: StudentSessionResult = {
  session: {
    id: 'ses-9',
    mode: 'practice',
    status: 'finished',
    title: 'Test · 4 preguntas',
    total_questions: 4,
    answered_questions: 4,
    time_limit_minutes: null,
    started_at: '2026-10-11T09:00:00Z',
    server_now: '2026-10-11T09:00:00Z',
    finished_at: '2026-10-11T09:12:30Z',
    created_at: '2026-10-11T08:59:00Z',
    result: {
      correct: 1,
      wrong: 2,
      blank: 0,
      points: '1/3',
      points_decimal: '0.3333',
      maximum: null,
      passed: null,
    },
    practical_case_origin: null,
    practical_case_statement: null,
  },
  parts: [
    {
      part_code: 'primera_parte',
      part_name: 'Primera parte: cuestionario de conocimientos',
      // F38: en un test de práctica la puntuación es la **directa**, no una estimación escalada a la
      // banda del examen: la escala sobre 50 es del simulacro y del examen oficial.
      kind: 'direct',
      correct: 1,
      wrong: 2,
      blank: 0,
      score: '1/3',
      score_decimal: '0.3333',
      // La banda viaja igual —es el dato declarado de la convocatoria— y la pantalla **no la enseña**
      // fuera de un examen: por eso esta prueba sirve para exigirlo.
      score_max: 50,
      pass_score: 25,
      passed: null,
      // El aviso lo compone el **dominio** y viaja tal cual. Sus cifras van en español desde el
      // arreglo del §2.2 **en el servidor**: la nota con coma y dos decimales (`0,33`) y el máximo y
      // el mínimo sin ceros de más (`sobre 50`, `(25)`). Antes este texto llevaba el decimal del
      // contrato (`0.3333 sobre 50.00 ... (25.00)`), que es el formato de máquina.
      verdict_note:
        'el mínimo de 25 es de la calificación oficial, que necesita los baremos de la ' +
        'convocatoria: no se aplica a la puntuación directa',
    },
  ],
  total: {
    part_code: null,
    part_name: null,
    kind: 'direct',
    correct: 1,
    wrong: 2,
    blank: 0,
    score: '1/3',
    score_decimal: '0.3333',
    score_max: 50,
    pass_score: null,
    passed: null,
    // El total no repite el aviso de la parte: cuando la sesión no declara parte, la nota total la
    // explica `official_note`. Así la pantalla tiene **los dos** párrafos que el propietario vio —el de
    // la parte y el del total—, que es lo que hay que plegar.
    verdict_note: null,
  },
  official_available: false,
  official_note:
    'La calificación oficial 0-50 resulta de transformar la puntuación directa con los baremos que ' +
    'fija la Comisión de Selección, y esa tabla no está importada: se muestra la puntuación directa ' +
    'y no se declara aprobado ni suspenso.',
  duration_seconds: 750,
  questions: [
    {
      position: 1,
      is_reserve: false,
      in_review: false,
      derived_key: false,
      part_code: 'primera_parte',
      part_name: 'Primera parte: cuestionario de conocimientos',
      stem: '¿Cuántas capas tiene el modelo OSI?',
      options: [
        { key: 'a', text: 'Cuatro' },
        { key: 'b', text: 'Siete' },
      ],
      chosen: ['b'],
      correct: ['a'],
      outcome: 'wrong',
      elapsed_ms: 2400,
      topics: [{ code: 'IV.7', title: 'El modelo TCP/IP y el modelo de referencia OSI de ISO.' }],
      note_anchor: { topic_code: 'IV.7', anchor: 'tcpip-arquitectura', epigraph_code: 'IV.7.1' },
    },
    {
      position: 2,
      is_reserve: false,
      in_review: false,
      derived_key: false,
      part_code: 'primera_parte',
      part_name: 'Primera parte: cuestionario de conocimientos',
      stem: 'El puerto 443 corresponde a HTTPS.',
      options: [
        { key: 'a', text: 'Verdadero' },
        { key: 'b', text: 'Falso' },
      ],
      chosen: ['a'],
      correct: ['a'],
      outcome: 'correct',
      elapsed_ms: 900,
      topics: [{ code: 'IV.1', title: 'Instalación y configuración de sistemas operativos.' }],
      note_anchor: { topic_code: 'IV.1', anchor: 'instalacion-de-sistemas', epigraph_code: 'IV.1.1' },
    },
    {
      position: 3,
      is_reserve: false,
      in_review: false,
      derived_key: false,
      part_code: 'primera_parte',
      part_name: 'Primera parte: cuestionario de conocimientos',
      stem: 'El puerto 22 se usa para SSH.',
      options: [
        { key: 'a', text: 'Verdadero' },
        { key: 'b', text: 'Falso' },
      ],
      chosen: ['b'],
      correct: ['a'],
      outcome: 'wrong',
      elapsed_ms: 1500,
      topics: [
        { code: 'IV.7', title: 'El modelo TCP/IP y el modelo de referencia OSI de ISO.' },
        { code: 'IV.1', title: 'Instalación y configuración de sistemas operativos.' },
      ],
      note_anchor: { topic_code: 'IV.7', anchor: 'udp', epigraph_code: 'IV.7.2' },
    },
    {
      position: 4,
      is_reserve: true,
      in_review: false,
      derived_key: false,
      part_code: 'primera_parte',
      part_name: 'Primera parte: cuestionario de conocimientos',
      stem: 'Una pregunta que la plantilla anuló.',
      options: [
        { key: 'a', text: 'Verdadero' },
        { key: 'b', text: 'Falso' },
      ],
      chosen: ['a'],
      correct: [],
      outcome: 'void',
      elapsed_ms: 300,
      topics: [{ code: 'IV.7', title: 'El modelo TCP/IP y el modelo de referencia OSI de ISO.' }],
      note_anchor: { topic_code: 'IV.7', anchor: 'otros-protocolos', epigraph_code: 'IV.7.2' },
    },
  ],
  topics: [
    {
      code: 'IV.7',
      title: 'El modelo TCP/IP y el modelo de referencia OSI de ISO.',
      correct: 0,
      wrong: 2,
      blank: 0,
      graded: 2,
      accuracy: 0,
    },
    {
      code: 'IV.1',
      title: 'Instalación y configuración de sistemas operativos.',
      correct: 1,
      wrong: 1,
      blank: 0,
      graded: 2,
      accuracy: 0.5,
    },
  ],
};

/**
 * El mismo resultado, pero de un **simulacro**: aquí sí hay banda oficial (0–50) y mínimo.
 *
 * Es el caso que el propietario vio bien resuelto y el que el arreglo de F38 deja intacto: la
 * puntuación sobre 50 con su mínimo solo se enseña en simulacros y exámenes oficiales. El aviso es el
 * de la estimación, compuesto por el dominio, con sus cifras en español.
 */
export const resultadoDeSimulacroFixture: StudentSessionResult = {
  ...sessionResultFixture,
  session: {
    ...sessionResultFixture.session,
    mode: 'mock_exam',
    title: 'Simulacro completo · 4 preguntas',
    time_limit_minutes: 120,
  },
  parts: [
    {
      ...sessionResultFixture.parts[0]!,
      kind: 'estimated',
      verdict_note:
        'La estimación de «Primera parte: cuestionario de conocimientos» es 0,33 sobre 50 y ' +
        'no llega al mínimo publicado (25), pero Es una **estimación**: la puntuación directa ' +
        '(aciertos menos errores por su penalización) escalada a la banda que publica la ' +
        'convocatoria para esta parte. La calificación oficial 0-50 resulta de los baremos que fija ' +
        'la Comisión de Selección, y esa tabla no está importada: esto no es la calificación ' +
        'oficial.',
    },
  ],
  total: { ...sessionResultFixture.total, kind: 'estimated', score_max: 50 },
};

/**
 * Un resultado con **puntuación directa negativa**, que es lo que el recorrido midió: 0 aciertos y 1
 * fallo con la penalización de un tercio dan `-1/3`.
 *
 * Es la cifra que **no se puede enseñar**: en pantalla la puntuación no baja de 0,00 y la exacta va
 * dentro del pliegue. Vale igual para la práctica (netos) y para el examen (puntuación directa).
 */
export const resultadoNegativoFixture: StudentSessionResult = {
  ...sessionResultFixture,
  parts: [{ ...sessionResultFixture.parts[0]!, correct: 0, wrong: 1, score: '-1/3' }],
  total: { ...sessionResultFixture.total, correct: 0, wrong: 1, score: '-1/3' },
};

/**
 * El caso que el propietario leyó en su captura: **un test de práctica de 10 preguntas** con 6
 * aciertos. Es el que decía «6,00 sobre 50 · mínimo 25» y el que ahora dice las cuatro cifras de una
 * práctica.
 *
 * Las preguntas y los temas son los del resultado de arriba: lo que cambia —y es lo que se mide— es la
 * nota y los recuentos, que son los de su caso.
 */
export const resultadoDePracticaDeDiezFixture: StudentSessionResult = {
  ...sessionResultFixture,
  session: {
    ...sessionResultFixture.session,
    title: 'Test · 10 preguntas',
    total_questions: 10,
    answered_questions: 10,
  },
  parts: [{ ...sessionResultFixture.parts[0]!, correct: 6, wrong: 0, blank: 4, score: '6' }],
  total: { ...sessionResultFixture.total, correct: 6, wrong: 0, blank: 4, score: '6' },
};

/** El simulacro tal como lo declara el perfil de TAI: 80 + 5 y 20 + 5, en 120 minutos. */
export const mockPlanFixture: StudentMockExamPlan = {
  opposition: { code: 'tai-age', name: 'Cuerpo de Técnicos Auxiliares de Informática' },
  full: {
    variant: 'full',
    title: 'Simulacro completo',
    time_limit_minutes: 120,
    parts: [
      {
        code: 'primera_parte',
        name: 'Primera parte: cuestionario de conocimientos',
        ordinary_items: 80,
        reserve_items: 5,
        score_max: 50,
        pass_score: 25,
        penalty: '1/3',
        time_minutes: 120,
      },
      {
        code: 'segunda_parte',
        name: 'Segunda parte: supuesto práctico',
        ordinary_items: 20,
        reserve_items: 5,
        score_max: 50,
        pass_score: 25,
        penalty: '1/3',
        time_minutes: 120,
      },
    ],
    note:
      'simulacro con el perfil del examen: primera parte de 80 preguntas más 5 de reserva y supuesto ' +
      'práctico de 20 más 5, con el tiempo y la penalización de la convocatoria. No es un examen ' +
      'oficial, y su nota por parte es una **estimación** (la puntuación directa escalada a la banda ' +
      'de cada parte), no la calificación oficial.',
  },
  short: {
    variant: 'short',
    title: 'Simulacro corto',
    time_limit_minutes: 48,
    parts: [
      {
        code: 'primera_parte',
        name: 'Primera parte: cuestionario de conocimientos',
        ordinary_items: 40,
        reserve_items: null,
        score_max: 50,
        pass_score: 25,
        penalty: '1/3',
        time_minutes: 48,
      },
    ],
    note: 'simulacro corto de 40 preguntas, sin supuesto práctico. No es un examen oficial.',
  },
  case_blocks: [
    {
      code: 'III',
      title: 'Bloque III: técnicas de gestión',
      topics: [
        { code: 'III.1', title: 'Gestión de proyectos.', available_questions: 12 },
        { code: 'III.2', title: 'Documentación técnica.', available_questions: 0 },
      ],
    },
    {
      code: 'IV',
      title: 'Bloque IV: sistemas y comunicaciones',
      topics: [{ code: 'IV.7', title: 'El modelo TCP/IP.', available_questions: 30 }],
    },
  ],
};

/** La lista de exámenes oficiales **vacía**, que es el estado de hoy: no hay ninguno importado. */
export const officialExamsVacioFixture: StudentOfficialExams = { exams: [] };

/** Y con un examen importado, que es lo que la pantalla tiene que saber ofrecer. */
export const officialExamsFixture: StudentOfficialExams = {
  exams: [
    {
      position: 1,
      title: 'TAI ingreso libre 2025 · examen oficial',
      held_at: '2025-11-22',
      held_year: 2025,
      questions: 85,
      ready: true,
      blocked_reason: null,
      origin_scope: 'age',
    },
    {
      position: 2,
      title: 'TAI ingreso libre 2024 · examen oficial',
      held_at: '2024-10-06',
      held_year: 2024,
      questions: 85,
      ready: false,
      blocked_reason: 'faltan_respuestas',
      origin_scope: 'otra_administracion',
    },
    {
      // El caso del §3.7: el documento declara el año y no el día. La fila dice «Ejercicio de
      // 2019» y **no** un 1 de enero inventado.
      position: 3,
      title: 'TAI ingreso libre 2019 · ejercicio único (examen oficial INAP)',
      held_at: null,
      held_year: 2019,
      questions: 85,
      ready: true,
      blocked_reason: null,
      origin_scope: 'age',
    },
    {
      // Y el que no declara ni el año: se dice que no hay fecha y por qué.
      position: 4,
      title: 'Examen oficial sin año en el título',
      held_at: null,
      held_year: null,
      questions: 79,
      ready: false,
      blocked_reason: 'faltan_preguntas',
      origin_scope: 'desconocida',
    },
  ],
};

/** Los fallos: dos preguntas de dos temas, una de ellas vencida. */
export const mistakesFixture: StudentMistakes = {
  total: 2,
  due_total: 1,
  servable_total: 2,
  questions: [
    {
      stem: '¿Cuántas capas tiene el modelo OSI?',
      topics: [{ code: 'IV.7', title: 'El modelo TCP/IP.' }],
      last_failed_at: '2026-10-11T09:05:00Z',
      times_failed: 3,
      due: true,
    },
    {
      stem: 'El puerto 22 se usa para SSH.',
      topics: [{ code: 'IV.1', title: 'Instalación de sistemas operativos.' }],
      last_failed_at: '2026-10-10T18:00:00Z',
      times_failed: 1,
      due: false,
    },
  ],
  topics: [
    { code: 'IV.7', title: 'El modelo TCP/IP.', failed: 1, due: 1 },
    { code: 'IV.1', title: 'Instalación de sistemas operativos.', failed: 1, due: 0 },
  ],
};

/** El progreso con dos bloques, tests hechos y un tema flojo. */
export const progressFixture: StudentProgress = {
  opposition: { code: 'tai-age', name: 'Cuerpo de Técnicos Auxiliares de Informática' },
  blocks: syllabusFixture.blocks,
  weakest_topics: [syllabusFixture.blocks[1]!.topics[0]!],
  history: [overviewFixture.recent_tests[0]!],
  tests_finished: 14,
};
