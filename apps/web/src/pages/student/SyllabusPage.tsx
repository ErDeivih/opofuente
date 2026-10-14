import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';

import {
  getStudentSyllabus,
  type StudentBlockProgress,
  type StudentTopicProgress,
} from '../../api/studentStudy';
import { ErrorState } from '../../components/ErrorState';
import { LoadingState } from '../../components/LoadingState';
import { NotesStateChip } from '../../features/student/NotesStateChip';
import { describeError } from '../../features/system/labels';

/**
 * El temario del alumno (F13), como el índice de un programa oficial.
 *
 * El número romano del bloque va en el margen y los temas debajo, numerados, con su barra de acierto
 * —fina, con el porcentaje escrito—, el número de preguntas y las dos salidas de cada tema: sus
 * apuntes y su test.
 *
 * **El orden no se toca aquí**: viene en orden numérico de la API (`IV.1` antes de `IV.10`), y
 * reordenar en la pantalla sería tener dos órdenes que pueden divergir.
 *
 * Los temas **en borrador se ven y se leen igual** que los publicados: llevan su marca, que es lo
 * que el alumno necesita saber, y esconderlos sería decidir por él. Un tema sin apuntes escritos no
 * ofrece la salida a los apuntes, porque no hay nada que leer.
 *
 * La búsqueda filtra por título **y por código**, sin acentos y sin distinguir mayúsculas: quien
 * escribe `iv.7` o `tcp` quiere el mismo tema.
 */
export function SyllabusPage() {
  const [busqueda, setBusqueda] = useState('');
  const consulta = useQuery({ queryKey: ['student-syllabus'], queryFn: getStudentSyllabus });

  const bloques = useMemo(() => {
    const datos = consulta.data?.blocks ?? [];
    const buscado = normalizar(busqueda.trim());
    if (buscado.length === 0) {
      return datos;
    }
    return datos
      .map((bloque) => ({
        ...bloque,
        topics: bloque.topics.filter(
          (tema) =>
            normalizar(tema.title).includes(buscado) ||
            // El código se compara por **prefijo**, no por trozo: buscar `IV.10` no puede dejar
            // `IV.1` en la lista (y `iv.1` está dentro de `iv.10`, que es justo la trampa).
            normalizar(tema.code).startsWith(buscado),
        ),
      }))
      .filter((bloque) => bloque.topics.length > 0);
  }, [consulta.data, busqueda]);

  if (consulta.isPending) {
    return (
      <>
        <h1 className="pagina__titulo">Temario</h1>
        <LoadingState label="Cargando el temario…" />
      </>
    );
  }
  if (consulta.isError) {
    return (
      <>
        <h1 className="pagina__titulo">Temario</h1>
        <ErrorState
          title="No se pudo cargar el temario"
          message={describeError(consulta.error)}
          onRetry={() => {
            void consulta.refetch();
          }}
        />
      </>
    );
  }

  return (
    <>
      <header className="pagina__cabecera">
        <h1 className="pagina__titulo">Temario</h1>
        <p className="pagina__entrada">{consulta.data.opposition.name}</p>
      </header>

      <form className="buscador" role="search" onSubmit={(evento) => evento.preventDefault()}>
        <label className="buscador__etiqueta" htmlFor="buscar-tema">
          Buscar en el temario
        </label>
        <input
          id="buscar-tema"
          className="buscador__campo"
          type="search"
          value={busqueda}
          onChange={(evento) => setBusqueda(evento.target.value)}
          placeholder="Un tema, una palabra o IV.7"
        />
      </form>

      {bloques.length === 0 ? (
        <p className="bloque__texto">No hay ningún tema que coincida con esa búsqueda.</p>
      ) : (
        <ul className="temario" aria-label="Temario">
          {bloques.map((bloque) => (
            <li className="temario__bloque" key={bloque.code} aria-label={`Bloque ${bloque.code}`}>
              <p className="temario__romano" aria-hidden="true">
                {bloque.code}
              </p>
              <div className="temario__cuerpo">
                <h2 className="temario__titulo-bloque" data-contenido>
                  {bloque.title}
                </h2>
                <ul className="temario__temas">
                  {bloque.topics.map((tema) => (
                    <TemaFila key={tema.code} tema={tema} />
                  ))}
                </ul>
                <BarraDeBloque bloque={bloque} />
              </div>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}

/** Un tema del índice: título, preguntas, acierto, estado de los apuntes y sus dos salidas. */
function TemaFila({ tema }: { tema: StudentTopicProgress }) {
  return (
    <li className="tema-fila" data-codigo={tema.code} aria-label={`Tema ${tema.code}`}>
      <p className="tema-fila__titulo">
        <span className="tema-fila__codigo">{tema.code}</span>{' '}
        <span data-contenido>{tema.title}</span>
      </p>
      <p className="tema-fila__datos">
        <span>{`${String(tema.available_questions)} preguntas`}</span>
        {tema.accuracy === null ? (
          <span className="tema-fila__sin-datos">Sin empezar</span>
        ) : (
          <span className="tema-fila__cifra">{`${String(Math.round(tema.accuracy * 100))} %`}</span>
        )}
        <NotesStateChip state={tema.notes_state} />
      </p>
      <p className="tema-fila__acciones">
        {/* Un tema sin apuntes escritos no ofrece la salida a los apuntes: el estado ya lo dice, y
            repetirlo dos veces en la misma fila solo añade ruido. */}
        {tema.notes_state !== 'none' && (
          <Link
            className="ui-button ui-button--secondary"
            to={`/temario/${tema.code}`}
            aria-label={`Apuntes de ${tema.code}`}
          >
            Apuntes
          </Link>
        )}
        <Link
          className="ui-button ui-button--secondary"
          to={`/tests?tema=${tema.code}`}
          aria-label={`Test de ${tema.code}`}
        >
          Test
        </Link>
      </p>
    </li>
  );
}

/** La barra del bloque: fina y con la cifra escrita, o la verdad en palabras si no hay datos. */
function BarraDeBloque({ bloque }: { bloque: StudentBlockProgress }) {
  if (bloque.accuracy === null) {
    return <p className="barras__sin-datos">Sin preguntas corregidas todavía.</p>;
  }
  const porcentaje = Math.round(bloque.accuracy * 100);
  return (
    <p className="barras barras--bloque">
      <span className="barras__barra" aria-hidden="true">
        <span className="barras__relleno" style={{ width: `${String(porcentaje)}%` }} />
      </span>
      <span className="barras__cifra">{`${String(porcentaje)} %`}</span>
    </p>
  );
}

/** Sin acentos y en minúsculas: `IV.7`, `iv-7` y `Tcp` buscan lo mismo. */
function normalizar(texto: string): string {
  return texto
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[\s-]/g, '');
}
