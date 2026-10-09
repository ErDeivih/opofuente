import type { DossierNoteSection, DossierNotes } from '../../api/dossier';
import { notesSummary, sectionReviewText } from '../../api/dossier';
import { StatusBadge } from '../../components/StatusBadge';
import { NotesMarkdown } from './NotesMarkdown';
import { revisionMarks } from './notesMarkdownParser';

export interface TopicNotesProps {
  notes: DossierNotes;
}

/**
 * Los apuntes redactados de un tema: los que se escriben a partir de sus preguntas y se comprueban con
 * ellas (pasos B-E del plan de apuntes).
 *
 * Tres cosas que esta pantalla dice y no puede callarse:
 *
 * 1. **de dónde salen**: no son un resumen del material, son los hechos que hay que saber para
 *    contestar las preguntas del tema, comprobados uno a uno. La cabecera lo dice con los números que
 *    devolvió la comprobación, no con una promesa;
 * 2. **qué hay que revisar**: los apartados escritos sin material de apoyo y las preguntas que no
 *    quedaron cubiertas llevan su etiqueta. Unos apuntes con huecos se enseñan con los huecos;
 * 3. **qué preguntas cubre cada apartado**, con su cifra: es el rastro que permite ir de la pregunta
 *    al párrafo (el identificador de la pregunta no se enseña aquí, pero el recuento sí).
 */
export function TopicNotes({ notes }: TopicNotesProps) {
  return (
    <section aria-labelledby="dossier-apuntes">
      <h3 id="dossier-apuntes">Apuntes redactados del tema</h3>
      <p className="hint">{notesSummary(notes)}</p>
      {notes.doubtful > 0 && (
        <p>
          <StatusBadge tone="warning">revisar</StatusBadge>{' '}
          <span className="hint">
            {String(notes.doubtful)}{' '}
            {notes.doubtful === 1 ? 'pregunta no quedó cubierta' : 'preguntas no quedaron cubiertas'}:
            están señaladas para que las mires, no se dan por buenas.
          </span>
        </p>
      )}
      {notes.sections.map((apartado) => (
        <NoteSectionBlock key={apartado.key} section={apartado} />
      ))}
    </section>
  );
}

/** Un apartado: su título, lo que cubre, su texto y lo que hay que revisar de él. */
function NoteSectionBlock({ section }: { section: DossierNoteSection }) {
  const marcas = revisionMarks(section.body_markdown);
  const aviso = sectionReviewText(section);
  const cubiertas = section.covered;
  const noCubiertas = section.gaps + section.doubtful;

  return (
    <article className="notes__section" aria-label={section.title}>
      <h4 className="notes__title">{section.title}</h4>
      <p className="hint">
        {section.epigraph_code}
        {' · '}
        {cubiertas === 1 ? '1 pregunta cubierta' : `${String(cubiertas)} preguntas cubiertas`}
        {noCubiertas > 0 && ` · ${String(noCubiertas)} sin cubrir`}
        {` · ${String(section.facts_total)} ${section.facts_total === 1 ? 'hecho' : 'hechos'}`}
      </p>
      {aviso !== null && (
        <p>
          <StatusBadge tone="warning">revisar</StatusBadge>{' '}
          <span className="hint">{aviso}</span>
        </p>
      )}
      <NotesMarkdown markdown={section.body_markdown} />
      {marcas.length > 0 && (
        <p className="hint">
          Párrafos marcados por el redactor (lo dice él mismo en el texto): {marcas.join('; ')}.
        </p>
      )}
    </article>
  );
}
