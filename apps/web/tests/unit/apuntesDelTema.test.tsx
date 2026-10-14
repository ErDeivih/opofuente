import { screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { NotesMarkdown } from '../../src/features/dossier/NotesMarkdown';
import { notesBlocks, revisionMarks, tableCells } from '../../src/features/dossier/notesMarkdownParser';
import { TopicNotes } from '../../src/features/dossier/TopicNotes';
import { dossierNotesFixture, renderWithProviders } from './testUtils';

/**
 * Los apuntes redactados en la ficha del tema: lo que se enseña y, sobre todo, lo que **no** se
 * esconde (lo que falta y lo que hay que revisar).
 */
describe('apuntes redactados del tema (pasos B-E)', () => {
  it('enseña la cabecera con lo que se comprobó, no con una promesa', () => {
    const notes = dossierNotesFixture.notes;
    expect(notes).toBeDefined();
    renderWithProviders(<TopicNotes notes={notes!} />);

    expect(
      screen.getByRole('heading', { name: 'Apuntes redactados del tema' }),
    ).toBeInTheDocument();
    expect(screen.getByText(/2 apartados · 2 de 3 preguntas cubiertas · 1 para revisar/)).toBeInTheDocument();
    expect(screen.getByText(/escritos con deepseek-flash/)).toBeInTheDocument();
  });

  it('dice cuántas preguntas cubre cada apartado y cuáles hay que mirar', () => {
    const notes = dossierNotesFixture.notes;
    renderWithProviders(<TopicNotes notes={notes!} />);

    expect(screen.getByRole('heading', { name: 'La Constitución Española de 1978' })).toBeInTheDocument();
    expect(screen.getByText(/I\.1\.1 · 2 preguntas cubiertas · 4 hechos/)).toBeInTheDocument();
    // El apartado sin material de apoyo lo dice, y no se presenta como si estuviera revisado.
    expect(screen.getByText('sin material de apoyo')).toBeInTheDocument();
    expect(screen.getByText(/1 pregunta no quedó cubierta/)).toBeInTheDocument();
  });

  it('el texto se lee: títulos, tablas y el aviso del propio redactor', () => {
    const notes = dossierNotesFixture.notes;
    renderWithProviders(<TopicNotes notes={notes!} />);

    expect(screen.getByRole('heading', { name: 'Qué es' })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: 'Órgano' })).toBeInTheDocument();
    expect(screen.getByRole('cell', { name: 'Legislar' })).toBeInTheDocument();
    expect(screen.getByText(/Párrafos marcados por el redactor/)).toBeInTheDocument();
    // La marca de revisión no se enseña cruda dentro del párrafo: se cuenta aparte.
    expect(screen.queryByText(/<!--/)).not.toBeInTheDocument();
  });

  it('las preguntas en conflicto con su clave no se cuentan como cubiertas', () => {
    // Una letra distinta de la clave es lo que el propietario encontró en 96 preguntas de los
    // pilotos: se enseña como conflicto, aparte de las cubiertas y de las dudosas.
    const notes = dossierNotesFixture.notes!;
    const conConflicto = {
      ...notes,
      questions_total: 4,
      conflicts: 1,
      sections: notes.sections.map((apartado, indice) =>
        indice === 0
          ? { ...apartado, conflicts: 1, conflict_question_ids: ['q-4'] }
          : apartado,
      ),
    };
    renderWithProviders(<TopicNotes notes={conConflicto} />);

    expect(screen.getByText(/1 en conflicto con la clave/)).toBeInTheDocument();
    expect(screen.getByText('conflicto')).toBeInTheDocument();
    expect(
      screen.getByText(/pregunta la contestan los apuntes con una letra distinta de su clave/),
    ).toBeInTheDocument();
    // El apartado del conflicto cuenta esa pregunta entre las que no quedan cubiertas.
    expect(screen.getAllByText(/1 sin cubrir/).length).toBeGreaterThan(0);
  });
});

describe('lector mínimo de markdown de los apuntes', () => {
  it('las marcas de revisión se extraen y no quedan dentro del texto', () => {
    const texto = 'Un párrafo. <!-- revisar: sin material de apoyo -->\n\nOtro.';
    expect(revisionMarks(texto)).toEqual(['sin material de apoyo']);
    expect(notesBlocks(texto)).toHaveLength(2);
  });

  it('separa títulos, listas, tablas y párrafos', () => {
    const bloques = notesBlocks(
      '## Título\n\n- uno\n- dos\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\nUn párrafo\npartido.',
    );
    expect(bloques.map((bloque) => bloque.kind)).toEqual([
      'heading',
      'list',
      'table',
      'paragraph',
    ]);
  });

  it('parte las celdas de una tabla sin las barras de los extremos', () => {
    expect(tableCells('| NTP | 123 |')).toEqual(['NTP', '123']);
  });

  it('el énfasis y el código se dibujan, y lo que no se entiende sale tal cual', () => {
    renderWithProviders(
      <NotesMarkdown markdown={'La **norma** suprema y `TCP` con *cursiva*.'} />,
    );
    expect(screen.getByText('norma').tagName).toBe('STRONG');
    expect(screen.getByText('TCP').tagName).toBe('CODE');
    expect(screen.getByText('cursiva').tagName).toBe('EM');
  });

  it('un texto con ángulos se enseña como texto, no como código', () => {
    renderWithProviders(<NotesMarkdown markdown={'Ojo con <script>alert(1)</script> aquí.'} />);
    expect(screen.getByText(/<script>alert\(1\)<\/script>/)).toBeInTheDocument();
  });
});
