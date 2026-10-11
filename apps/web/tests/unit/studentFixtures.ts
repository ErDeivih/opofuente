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

import type { StudentOverview, StudentSyllabus, StudentTopic } from '../../src/api/studentStudy';
import type { StudentNotes } from '../../src/api/studentStudy';

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
    finished_at: null,
    created_at: '2026-10-11T08:59:00Z',
    result: null,
    practical_case_origin: null,
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
      finished_at: '2026-10-10T09:20:00Z',
      created_at: '2026-10-10T08:59:00Z',
      result: {
        correct: 14,
        wrong: 4,
        blank: 2,
        points: '38/3',
        points_decimal: '12,67',
        maximum: null,
        passed: null,
      },
      practical_case_origin: null,
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
 * Los apuntes de un tema: tres apartados, con tabla en el primero, una cifra de preguntas por
 * apartado y el último sin ninguna —el caso en el que no se pinta nota al margen.
 */
export const notesFixture: StudentNotes = {
  code: 'IV.7',
  state: 'draft',
  generated_at: '2026-10-10T18:09:00Z',
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
