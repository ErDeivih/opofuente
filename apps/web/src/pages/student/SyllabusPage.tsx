import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';

import {
  getStudentMistakes,
  getStudentSyllabus,
  type StudentBlockProgress,
  type StudentMistakeTopic,
  type StudentTopicProgress,
} from '../../api/studentStudy';
import { ErrorState } from '../../components/ErrorState';
import { EsqueletoDeLista } from '../../components/Esqueleto';
import {
  estadoDeEstudio,
  etiquetaDeEstudio,
  type EstadoDeEstudio,
} from '../../features/student/estadoDeEstudio';
import { NotesStateChip } from '../../features/student/NotesStateChip';
import { describeError } from '../../features/system/labels';
import { formatearPorcentaje } from '../../lib/numeros';

/**
 * El temario del alumno (F13), como el índice de un programa oficial.
 *
 * El número romano del bloque va en el margen y los temas debajo, numerados, con su barra de acierto
 * —fina, con el porcentaje escrito—, el número de preguntas, su estado de estudio y las salidas de
 * cada tema: sus apuntes, su test y, si tiene, sus fallos.
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
  // Los fallos por tema (O2) son una segunda lectura, y **no puede tumbar el índice**: si falla, el
  // temario se lee igual y solo se deja de ofrecer el atajo a los fallos de cada tema.
  const fallos = useQuery({
    queryKey: ['student-mistakes'],
    queryFn: getStudentMistakes,
    retry: false,
    staleTime: 60_000,
  });

  const fallosPorTema = useMemo(() => {
    const mapa = new Map<string, StudentMistakeTopic>();
    for (const tema of fallos.data?.topics ?? []) {
      mapa.set(tema.code, tema);
    }
    return mapa;
  }, [fallos.data]);

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
        <EsqueletoDeLista nombre="el temario" identificador="esqueleto-temario" filas={5} />
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
        <p className="pagina__entrada">
          {consulta.data.opposition.name}{' '}
          <Link
            className="pagina__enlace"
            to={`/cuerpo/${consulta.data.opposition.code}`}
            aria-label={`Ficha del cuerpo ${consulta.data.opposition.code}`}
          >
            Ver la ficha del cuerpo
          </Link>
        </p>
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
                    <TemaFila key={tema.code} tema={tema} fallos={fallosPorTema.get(tema.code)} />
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

/**
 * Un tema del índice: título, preguntas, acierto, estado de los apuntes y sus salidas.
 *
 * La etiqueta de estado es de interfaz, no una nota: la calcula `estadoDeEstudio` en un solo sitio
 * para que el índice y cualquier otra pantalla no digan cosas distintas del mismo tema. Los fallos
 * solo aparecen cuando hay alguno: un cero en cada fila sería ruido.
 */
function TemaFila({ tema, fallos }: { tema: StudentTopicProgress; fallos?: StudentMistakeTopic }) {
  const estado: EstadoDeEstudio = estadoDeEstudio(tema);
  return (
    <li className="tema-fila" data-codigo={tema.code} aria-label={`Tema ${tema.code}`}>
      <p className="tema-fila__titulo">
        <span className="tema-fila__codigo">{tema.code}</span>{' '}
        <span data-contenido>{tema.title}</span>
      </p>
      <p className="tema-fila__datos">
        <span>{`${String(tema.available_questions)} preguntas`}</span>
        {tema.accuracy === null ? (
          <span className="tema-fila__sin-datos">{etiquetaDeEstudio(estado)}</span>
        ) : (
          <>
            <span className="tema-fila__cifra">{formatearPorcentaje(tema.accuracy)}</span>
            <span className="tema-fila__estado" data-estado={estado}>
              {etiquetaDeEstudio(estado)}
            </span>
          </>
        )}
        <NotesStateChip state={tema.notes_state} />
        {fallos !== undefined && fallos.failed > 0 && (
          <Link
            className="tema-fila__fallos"
            to={`/fallos?tema=${encodeURIComponent(tema.code)}`}
            aria-label={`Fallos de ${tema.code}`}
          >
            {`${String(fallos.failed)} ${fallos.failed === 1 ? 'fallo' : 'fallos'}`}
          </Link>
        )}
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
      <span className="barras__cifra">{formatearPorcentaje(bloque.accuracy)}</span>
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
