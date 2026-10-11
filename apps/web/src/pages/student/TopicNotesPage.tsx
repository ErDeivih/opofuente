import { useQuery } from '@tanstack/react-query';
import { Link, useParams } from 'react-router-dom';

import { getStudentNotes, getStudentTopic, type StudentNoteSection } from '../../api/studentStudy';
import { ErrorState } from '../../components/ErrorState';
import { LoadingState } from '../../components/LoadingState';
import { NotesBody } from '../../features/student/NotesBody';
import { NotesStateChip } from '../../features/student/NotesStateChip';
import { ReportMistake } from '../../features/student/ReportMistake';
import { describeError } from '../../features/system/labels';

/**
 * Un tema con sus apuntes (F13): la pantalla de lectura.
 *
 * Es la pantalla para la que existe esta aplicación, así que está construida para leerse: tres
 * columnas como pide el diseño, con
 *
 * - el **índice de apartados** a la izquierda, pegajoso al hacer scroll y navegable: cada enlace
 *   lleva al ancla de su apartado;
 * - la **columna de lectura** en el centro, en Source Serif 4 a 68 caracteres por línea;
 * - la **nota al margen** a la derecha, dentro de su apartado (en el móvil cae debajo de su texto),
 *   con una cifra real: cuántas preguntas de este tema se contestan con ese apartado;
 * - y, en cada apartado, el botón **«Esto está mal»** (decisión D2), que guarda el aviso por su ruta
 *   auditada.
 *
 * Un tema **en borrador se lee entero** y lo dice con su marca. Un tema sin apuntes escritos lo dice
 * con una frase, sin ceros ni textos vacíos.
 *
 * Las pestañas son las del diseño (Apuntes · Preguntas · Mi progreso). «Apuntes» es lo que hay; las
 * otras dos llevan a la pantalla que les toca —el test del tema y el progreso—, que son del bloque
 * siguiente: un enlace que navega es honesto, una pestaña que no hace nada no lo sería.
 */
export function TopicNotesPage() {
  const { codigo = '' } = useParams();
  const tema = useQuery({
    queryKey: ['student-topic', codigo],
    queryFn: () => getStudentTopic(codigo),
  });
  const apuntes = useQuery({
    queryKey: ['student-notes', codigo],
    queryFn: () => getStudentNotes(codigo),
  });

  if (tema.isPending || apuntes.isPending) {
    return <LoadingState label="Cargando los apuntes…" />;
  }
  if (tema.isError || apuntes.isError) {
    const error = tema.error ?? apuntes.error;
    return (
      <ErrorState
        title="No se pudieron cargar los apuntes"
        message={describeError(error)}
        onRetry={() => {
          void tema.refetch();
          void apuntes.refetch();
        }}
      />
    );
  }

  const ficha = tema.data;
  const notas = apuntes.data;

  return (
    <>
      <header className="pagina__cabecera">
        <p className="tema__bloque">
          <Link to="/temario">Temario</Link>
          {` · ${ficha.block_code}: `}
          <span data-contenido>{ficha.block_title}</span>
        </p>
        <h1 className="pagina__titulo">
          <span className="tema__codigo">{`Tema ${ficha.code}`}</span>{' '}
          <span data-contenido>{ficha.title}</span>
        </h1>
        <p className="tema__estado">
          <NotesStateChip state={notas.state} />
          {ficha.progress !== null && (
            <span className="tema__preguntas">{`${String(ficha.progress.available_questions)} preguntas`}</span>
          )}
        </p>
      </header>

      <nav className="pestanas" aria-label="Secciones del tema">
        <span className="pestanas__pestana pestanas__pestana--activa" aria-current="page">
          Apuntes
        </span>
        <Link className="pestanas__pestana" to={`/tests?tema=${ficha.code}`}>
          Preguntas
        </Link>
        <Link className="pestanas__pestana" to="/progreso">
          Mi progreso
        </Link>
      </nav>

      {notas.state === 'none' || notas.sections.length === 0 ? (
        <p className="bloque__texto">
          Este tema todavía no tiene apuntes escritos. Cuando los tenga, se leerán aquí.
        </p>
      ) : (
        <div className="apuntes">
          <nav className="apuntes__indice" aria-label="Apartados">
            <h2 className="apuntes__indice-titulo">Apartados</h2>
            <ol className="apuntes__indice-lista">
              {notas.sections.map((apartado) => (
                <li key={apartado.key}>
                  <a className="apuntes__indice-enlace" href={`#apartado-${apartado.anchor}`}>
                    {/* El título del apartado es **contenido** (el material que se lee), así que va
                        marcado como tal: el detector de lenguaje interno de las capturas busca la
                        jerga de la aplicación en los menús, no las palabras del temario. */}
                    <span data-contenido>{`${String(apartado.number)}. ${apartado.title}`}</span>
                  </a>
                </li>
              ))}
            </ol>
          </nav>

          <div className="apuntes__lectura">
            {notas.sections.map((apartado) => (
              <Apartado
                key={apartado.key}
                apartado={apartado}
                codigo={ficha.code}
                tituloDelTema={ficha.title}
              />
            ))}
          </div>
        </div>
      )}
    </>
  );
}

/** Un apartado: su título, su texto, su nota al margen y el aviso de error. */
function Apartado({
  apartado,
  codigo,
}: {
  apartado: StudentNoteSection;
  codigo: string;
  tituloDelTema: string;
}) {
  return (
    <section
      className="apartado"
      id={`apartado-${apartado.anchor}`}
      aria-label={apartado.title}
      tabIndex={-1}
    >
      <h2 className="apartado__titulo">
        <span className="apartado__numero">{apartado.number}</span>{' '}
        <span data-contenido>{apartado.title}</span>
      </h2>
      <div className="apartado__cuerpo" data-contenido>
        <NotesBody markdown={apartado.body_markdown} />
      </div>
      <div className="apartado__lateral">
        {apartado.questions_covered > 0 && (
          <aside className="nota-margen" role="note" aria-label="Esto se pregunta">
            <p className="nota-margen__rotulo">Esto se pregunta</p>
            <p className="nota-margen__texto">
              {apartado.questions_covered === 1
                ? '1 pregunta de este tema se contesta en este apartado.'
                : `${String(apartado.questions_covered)} preguntas de este tema se contestan en este apartado.`}
            </p>
          </aside>
        )}
        <ReportMistake code={codigo} sectionKey={apartado.key} sectionTitle={apartado.title} />
      </div>
    </section>
  );
}
