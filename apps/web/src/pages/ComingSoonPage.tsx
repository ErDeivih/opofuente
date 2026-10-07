import { Card, EmptyState } from '../ui/Card';

export interface ComingSoonPageProps {
  /** El nombre de la sección, tal como se lee en la barra. */
  title: string;
  /** Qué hará esta pantalla, en una frase. */
  summary: string;
}

/**
 * Una sección del alumno que todavía no está construida (F1 del rediseño).
 *
 * Enseña lo justo y verdadero: qué se llamará esta pantalla, qué va a hacer y que todavía no está.
 * Nada de «slice», de ficheros del plan ni de estados simulados: el alumno no tiene por qué saber
 * cómo se construye la aplicación, y una pantalla vacía con jerga dentro se lee como un error.
 */
export function ComingSoonPage({ title, summary }: ComingSoonPageProps) {
  return (
    <>
      <header className="page__header">
        <h1>{title}</h1>
      </header>

      <Card title="Todavía no está">
        <EmptyState message={`${summary} Llega en la siguiente fase.`} />
      </Card>
    </>
  );
}
