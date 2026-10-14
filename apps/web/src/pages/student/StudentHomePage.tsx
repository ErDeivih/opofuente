import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';

import { getStudentOverview, type StudentBlockProgress } from '../../api/studentStudy';
import type { StudentSession } from '../../api/studentTests';
import { ErrorState } from '../../components/ErrorState';
import { LoadingState } from '../../components/LoadingState';
import { NotesStateChip } from '../../features/student/NotesStateChip';
import { describeError } from '../../features/system/labels';

/**
 * Inicio de la zona del alumno (F13).
 *
 * Enseña cuatro cosas, en el orden en que se necesitan al sentarse a estudiar:
 *
 * 1. **qué toca hacer**: seguir el test a medias —con por dónde iba— o empezar uno;
 * 2. **qué repasar**: los fallos vencidos, con su cifra;
 * 3. **cómo va**: una barra fina por bloque con el porcentaje **escrito**, porque una barra sin
 *    número es un adorno;
 * 4. **qué puede leer**: los temas con apuntes, con su estado y, cuando están publicados, la marca
 *    «Versión generada · en revisión» (decisión D2: el alumno lee y sabe qué está leyendo).
 *
 * Todo lo que se enseña es dato del servidor. «Sin empezar» no es un cero: es que no hay intentos, y
 * se dice con palabras en lugar de con un 0 % que parecería un suspenso.
 */
export function StudentHomePage() {
  const consulta = useQuery({ queryKey: ['student-overview'], queryFn: getStudentOverview });

  if (consulta.isPending) {
    return (
      <>
        <h1 className="pagina__titulo">Inicio</h1>
        <LoadingState label="Mirando por dónde ibas…" />
      </>
    );
  }
  if (consulta.isError) {
    return (
      <>
        <h1 className="pagina__titulo">Inicio</h1>
        <ErrorState
          title="No se pudo cargar tu Inicio"
          message={describeError(consulta.error)}
          onRetry={() => {
            void consulta.refetch();
          }}
        />
      </>
    );
  }

  const { opposition, in_progress, due_reviews, blocks, recent_tests } = consulta.data;
  const conApuntes = blocks
    .flatMap((bloque) => bloque.topics)
    .filter((tema) => tema.notes_state !== 'none');

  return (
    <>
      <header className="pagina__cabecera">
        <h1 className="pagina__titulo">Inicio</h1>
        <p className="pagina__entrada">{opposition.name}</p>
      </header>

      <section className="bloque" aria-labelledby="continuar">
        <h2 className="bloque__titulo" id="continuar">
          Continuar
        </h2>
        {in_progress === null ? (
          <p className="bloque__texto">
            {recent_tests.length === 0
              ? 'Aún no has hecho ningún test.'
              : 'No tienes ningún test a medias.'}
          </p>
        ) : (
          <p className="bloque__texto">
            {in_progress.title}: {in_progress.answered_questions} de {in_progress.total_questions}{' '}
            contestadas.
          </p>
        )}
        <p className="acciones">
          {in_progress !== null ? (
            <Link className="ui-button ui-button--primary" to={`/test/${in_progress.id}`}>
              Continuar el test
            </Link>
          ) : (
            <Link className="ui-button ui-button--primary" to="/tests">
              Empezar un test
            </Link>
          )}
          <Link className="ui-button ui-button--secondary" to="/tests?count=20">
            Test rápido de 20
          </Link>
          <Link className="ui-button ui-button--secondary" to="/simulacros">
            Simulacro
          </Link>
          <Link className="ui-button ui-button--secondary" to="/examenes">
            Examen oficial
          </Link>
        </p>
      </section>

      <section className="bloque" aria-labelledby="repasar">
        <h2 className="bloque__titulo" id="repasar">
          Repasar fallos
        </h2>
        {due_reviews === 0 ? (
          <p className="bloque__texto">No tienes fallos pendientes de repaso.</p>
        ) : (
          <p className="bloque__texto">
            {due_reviews} preguntas para repasar hoy, de las que has fallado y ya toca volver a ver.
          </p>
        )}
        {due_reviews > 0 && (
          <p className="acciones">
            <Link className="ui-button ui-button--secondary" to="/fallos">
              Repasar mis fallos
            </Link>
          </p>
        )}
      </section>

      <section className="bloque" aria-labelledby="tu-progreso">
        <h2 className="bloque__titulo" id="tu-progreso">
          Tu progreso
        </h2>
        <ul className="barras" aria-label="Progreso por bloque">
          {blocks.map((bloque) => (
            <li className="barras__fila" key={bloque.code}>
              <span className="barras__numeral">{bloque.code}</span>
              <span className="barras__titulo" data-contenido>
                {bloque.title}
              </span>
              <BarraDeBloque bloque={bloque} />
            </li>
          ))}
        </ul>
        <p className="acciones">
          <Link className="ui-button ui-button--secondary" to="/progreso">
            Ver mi progreso
          </Link>
        </p>
      </section>

      <section className="bloque" aria-labelledby="tus-apuntes">
        <h2 className="bloque__titulo" id="tus-apuntes">
          Tus apuntes
        </h2>
        {conApuntes.length === 0 ? (
          <p className="bloque__texto">Todavía no hay apuntes escritos de ningún tema.</p>
        ) : (
          <ul className="lista-temas" aria-label="Temas con apuntes">
            {conApuntes.map((tema) => (
              <li className="lista-temas__fila" key={tema.code}>
                <Link className="lista-temas__enlace" to={`/temario/${tema.code}`}>
                  <span className="lista-temas__codigo">{tema.code}</span>
                  <span data-contenido>{tema.title}</span>
                </Link>
                <NotesStateChip state={tema.notes_state} />
              </li>
            ))}
          </ul>
        )}
      </section>

      {recent_tests.length > 0 && (
        <section className="bloque" aria-labelledby="ultimos-tests">
          <h2 className="bloque__titulo" id="ultimos-tests">
            Últimos tests
          </h2>
          <ul className="lista-tests" aria-label="Últimos tests">
            {recent_tests.map((sesion) => (
              <li className="lista-tests__fila" key={sesion.id}>
                <Link className="lista-tests__enlace" to={`/test/${sesion.id}`}>
                  {sesion.title}
                </Link>
                <span className="lista-tests__cifra">{resumenDe(sesion)}</span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </>
  );
}

/** Una barra fina con el porcentaje escrito y, si no hay nada corregido, la verdad en palabras. */
function BarraDeBloque({ bloque }: { bloque: StudentBlockProgress }) {
  if (bloque.accuracy === null) {
    return <span className="barras__sin-datos">Sin empezar</span>;
  }
  const porcentaje = Math.round(bloque.accuracy * 100);
  return (
    <>
      <span className="barras__barra" aria-hidden="true">
        <span className="barras__relleno" style={{ width: `${String(porcentaje)}%` }} />
      </span>
      <span className="barras__cifra">{`${String(porcentaje)} %`}</span>
    </>
  );
}

/** El resumen de un test terminado: aciertos, fallos y blancos, sin juntar metadatos con puntos. */
function resumenDe(sesion: StudentSession): string {
  const resultado = sesion.result;
  if (resultado === null) {
    return 'Sin corregir';
  }
  return `${String(resultado.correct)} aciertos, ${String(resultado.wrong)} fallos, ${String(resultado.blank)} en blanco`;
}
