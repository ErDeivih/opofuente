import { screen, waitFor } from '@testing-library/react';
import { Route, Routes } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { StudentTestRunner } from '../../src/features/study/StudentTestRunner';
import { renderWithProviders, stubApi } from './testUtils';

/**
 * La marca «clave revisada automáticamente» en el test que está haciendo el alumno (§1 del encargo
 * F29).
 *
 * Una pregunta de un conjunto en cuarentena puede volver al estudio con una **clave derivada**: la
 * letra de los apuntes (con su cita verificada) y la que el modelo contesta sin apuntes coinciden.
 * La letra no es la de la plantilla del conjunto, y por eso el alumno lo ve. Lo que se prueba aquí
 * es lo que ve: que la marca **aparece** cuando la API dice que la clave es derivada y que **no
 * aparece** cuando no lo es —una marca que sale siempre no avisa de nada—.
 */

const SESION = {
  id: 'sesion-1',
  mode: 'practice',
  status: 'running',
  title: 'Test de prueba',
  total_questions: 1,
  answered_questions: 0,
  time_limit_minutes: null,
  started_at: '2026-10-15T10:00:00Z',
  finished_at: null,
  created_at: '2026-10-15T10:00:00Z',
  result: null,
  practical_case_origin: null,
};

function carrera(derivedKey: boolean) {
  return {
    session: SESION,
    total: 1,
    answered: 0,
    pending: 1,
    finished: false,
    position: 1,
    question: {
      position: 1,
      is_reserve: false,
      stem: '¿Cuál de estas opciones es la correcta?',
      question_type: 'single_choice',
      options: [
        { key: 'a', text: 'La primera.' },
        { key: 'b', text: 'La segunda.' },
      ],
      answered: false,
      chosen: [],
      confidence: null,
      correction: null,
      in_review: false,
      derived_key: derivedKey,
    },
    sheet: [
      { position: 1, answered: false, chosen: [], confidence: null, outcome: null, correct: [] },
    ],
    questions_in_review: 0,
    questions_derived: derivedKey ? 1 : 0,
  };
}

function enLaRuta() {
  // `StudentTestRunner` saca el identificador de la ruta (`/test/:id`), así que se monta dentro de
  // sus `Routes`: sin eso `useParams` devuelve vacío y la pantalla no pide nada.
  return (
    <Routes>
      <Route path="/test/:id" element={<StudentTestRunner />} />
    </Routes>
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('la marca «clave revisada automáticamente» en el test en curso', () => {
  it('se enseña cuando la clave de la pregunta es derivada', async () => {
    stubApi({
      '/api/v1/student/sessions/sesion-1/start': { body: carrera(true) },
      '/api/v1/student/sessions/sesion-1': { body: carrera(true) },
    });

    renderWithProviders(enLaRuta(), { route: '/test/sesion-1' });

    expect(await screen.findByText('clave revisada automáticamente')).toBeInTheDocument();
  });

  it('no se enseña cuando la clave no es derivada', async () => {
    stubApi({
      '/api/v1/student/sessions/sesion-1/start': { body: carrera(false) },
      '/api/v1/student/sessions/sesion-1': { body: carrera(false) },
    });

    renderWithProviders(enLaRuta(), { route: '/test/sesion-1' });

    // La pregunta se ha pintado (si no, la prueba pasaría por no haber nada en pantalla).
    expect(
      await screen.findByText('¿Cuál de estas opciones es la correcta?'),
    ).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.queryByText('clave revisada automáticamente')).not.toBeInTheDocument();
    });
  });
});
