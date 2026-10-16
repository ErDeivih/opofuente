import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, useLocation, useNavigate, useParams, useSearchParams } from 'react-router-dom';

import {
  getStudentNotes,
  getStudentTopic,
  type StudentNoteChapter,
  type StudentNoteSection,
} from '../../api/studentStudy';
import { ErrorState } from '../../components/ErrorState';
import { EsqueletoDeLista } from '../../components/Esqueleto';
import {
  anclaDeLaDireccion,
  capituloQueAbrir,
  capituloQueContiene,
  useApartadoALaVista,
} from '../../features/student/capitulos';
import { NotesBody } from '../../features/student/NotesBody';
import { NotesStateChip } from '../../features/student/NotesStateChip';
import { ReportMistake } from '../../features/student/ReportMistake';
import { describeError } from '../../features/system/labels';
import { Plegable } from '../../ui/Disclosure';

/**
 * Un tema con sus apuntes (F13): la pantalla de lectura, **un capítulo cada vez** (F35, §3.1).
 *
 * Es la pantalla para la que existe esta aplicación, así que está construida para leerse: tres
 * columnas como pide el diseño, con
 *
 * - el **índice de capítulos** a la izquierda, con **su propio scroll** y sin pasar del alto de la
 *   ventana, con el capítulo abierto y el apartado que se está leyendo marcados;
 * - la **columna de lectura** en el centro, en Source Serif 4 y con su medida de 68 caracteres, que es
 *   lo que el propietario pidió: antes el texto ocupaba 370 px en una pantalla de 1280;
 * - la **nota al margen** a la derecha —debajo del párrafo cuando la pantalla no da para las tres
 *   columnas— con una cifra real: cuántas preguntas de este tema se contestan con ese apartado;
 * - y, en cada apartado, el botón **«Esto está mal»** (decisión D2), que guarda el aviso por su ruta
 *   auditada.
 *
 * **Por qué un capítulo y no el tema entero.** Medido antes de este cambio: IV.7 medía 110.427 px de
 * alto y I.1 **314.402**, con el índice en 1.415 px `sticky` dentro de una ventana de 800 —su mitad de
 * abajo no se alcanzaba ni desplazándose—. Un capítulo es un **epígrafe oficial** del tema, así que la
 * página pasa a medir lo que mide un epígrafe y el índice cabe entero.
 *
 * Un tema **en borrador se lee entero** y lo dice con su marca. Un tema sin apuntes escritos lo dice
 * con una frase, sin ceros ni textos vacíos.
 *
 * Las pestañas son las del diseño (Apuntes · Preguntas · Mi progreso). «Apuntes» es lo que hay; las
 * otras dos llevan a la pantalla que les toca —el test del tema y el progreso—: un enlace que navega
 * es honesto, una pestaña que no hace nada no lo sería.
 */
export function TopicNotesPage() {
  const { codigo = '' } = useParams();
  const { hash, pathname } = useLocation();
  const navegar = useNavigate();
  const [parametros] = useSearchParams();
  const pedido = parametros.get('capitulo');

  const tema = useQuery({
    queryKey: ['student-topic', codigo],
    queryFn: () => getStudentTopic(codigo),
  });
  const apuntes = useQuery({
    queryKey: ['student-notes', codigo, pedido],
    queryFn: () => getStudentNotes(codigo, pedido ?? undefined),
  });

  const ancla = anclaDeLaDireccion(hash);
  const capitulos = apuntes.data?.chapters ?? [];
  const servido = apuntes.data?.chapter ?? null;
  // El capítulo que hay que abrir de verdad: el del anclaje manda, y si el pedido ya no existe se
  // corrige al que el servidor ha servido. Ver `capitulos.ts`.
  const abrir = capituloQueAbrir({
    pedido,
    servido,
    delAncla: capituloQueContiene(capitulos, ancla),
  });

  useEffect(() => {
    if (abrir === null) {
      return;
    }
    const siguientes = new URLSearchParams(parametros);
    siguientes.set('capitulo', abrir);
    // La dirección se escribe **entera**, con su almohadilla: `setSearchParams` navega a `?…`, y una
    // dirección relativa de solo consulta se resuelve contra la actual **sin el fragmento**, así que
    // corregir el capítulo borraba el `#apartado-…` y el efecto que baja al párrafo se quedaba sin
    // ancla que buscar. Medido: con `setSearchParams` el enlace acababa en
    // `/temario/IV.7?capitulo=IV.7.2` —sin `#`— y no bajaba.
    //
    // `replace`: corregir la dirección no es un paso más del recorrido del alumno, es la misma
    // pantalla diciendo dónde está. Con `push`, el botón de atrás volvería al capítulo equivocado.
    // `navigate` devuelve una promesa en el enrutador de React: se ignora a propósito, porque no hay
    // nada que hacer cuando termina —el estado de la pantalla es el de la propia dirección—.
    void navegar({ pathname, search: `?${siguientes.toString()}`, hash }, { replace: true });
  }, [abrir, parametros, navegar, pathname, hash]);

  if (tema.isPending || apuntes.isPending) {
    return <EsqueletoDeLista nombre="los apuntes" identificador="esqueleto-tema" filas={6} />;
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
  const indice = notas.chapters.findIndex((capitulo) => capitulo.code === notas.chapter);
  const actual: StudentNoteChapter | null = indice < 0 ? null : (notas.chapters[indice] ?? null);
  const anterior = indice > 0 ? (notas.chapters[indice - 1] ?? null) : null;
  const siguiente =
    indice >= 0 && indice + 1 < notas.chapters.length ? (notas.chapters[indice + 1] ?? null) : null;

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
          <IndiceDelTema codigo={ficha.code} capitulos={notas.chapters} servido={notas.chapter} />

          <div className="apuntes__lectura">
            {actual !== null && (
              <p className="apuntes__capitulo">
                <span className="apuntes__capitulo-codigo">{actual.code}</span>{' '}
                <span data-contenido>{actual.title}</span>
              </p>
            )}
            {notas.sections.map((apartado) => (
              <Apartado
                key={apartado.key}
                apartado={apartado}
                codigo={ficha.code}
                tituloDelTema={ficha.title}
              />
            ))}
            {(anterior !== null || siguiente !== null) && (
              <nav className="apuntes__paso" aria-label="Capítulos del tema">
                {anterior !== null && (
                  <Link
                    className="ui-button ui-button--secondary apuntes__paso-enlace"
                    to={`/temario/${ficha.code}?capitulo=${encodeURIComponent(anterior.code)}`}
                    title={anterior.title}
                  >
                    Anterior: {anterior.code}
                  </Link>
                )}
                {siguiente !== null && (
                  <Link
                    className="ui-button ui-button--secondary apuntes__paso-enlace"
                    to={`/temario/${ficha.code}?capitulo=${encodeURIComponent(siguiente.code)}`}
                    title={siguiente.title}
                  >
                    Siguiente: {siguiente.code}
                  </Link>
                )}
              </nav>
            )}
          </div>
        </div>
      )}
    </>
  );
}

/**
 * El índice: los capítulos del tema y, bajo el que se está leyendo, sus apartados.
 *
 * Se lista **solo el capítulo abierto** por sus apartados —los de los demás ya están dentro de su
 * capítulo, a un clic— y el capítulo abierto va marcado con `aria-current="page"`. El apartado que se
 * está leyendo se marca con `aria-current="location"`, y se sabe por el scroll (`useApartadoALaVista`).
 */
function IndiceDelTema({
  codigo,
  capitulos,
  servido,
}: {
  codigo: string;
  capitulos: readonly StudentNoteChapter[];
  servido: string | null;
}) {
  const actual = capitulos.find((capitulo) => capitulo.code === servido);
  const enPantalla = useApartadoALaVista(
    (actual?.sections ?? []).map((apartado) => apartado.anchor),
  );

  return (
    <nav className="apuntes__indice" aria-label="Apartados">
      <h2 className="apuntes__indice-titulo">Apartados</h2>
      {/* El scroll vive aquí y no en el `nav`: así el título «Apartados» no se va con el desplazamiento
          y el índice nunca es más alto que la ventana. */}
      <div className="apuntes__indice-lista-marco">
        <ol className="apuntes__indice-lista">
          {capitulos.map((capitulo) => (
            <li className="apuntes__indice-capitulo" key={capitulo.code}>
              <Link
                className="apuntes__indice-capitulo-enlace"
                to={`/temario/${codigo}?capitulo=${encodeURIComponent(capitulo.code)}`}
                aria-current={capitulo.code === servido ? 'page' : undefined}
                title={capitulo.title}
              >
                <span className="apuntes__indice-capitulo-codigo">{capitulo.code}</span>{' '}
                {/* El título del epígrafe es **contenido** (el material que se lee), así que va
                    marcado como tal: el detector de lenguaje interno de las capturas busca la jerga
                    de la aplicación en los menús, no las palabras del temario. */}
                <span data-contenido>{capitulo.title}</span>
              </Link>
              {capitulo.code === servido && (
                <ol className="apuntes__indice-apartados">
                  {capitulo.sections.map((apartado) => (
                    <li key={apartado.key}>
                      <a
                        className="apuntes__indice-enlace"
                        href={`#apartado-${apartado.anchor}`}
                        aria-current={apartado.anchor === enPantalla ? 'location' : undefined}
                      >
                        <span data-contenido>{`${String(apartado.number)}. ${apartado.title}`}</span>
                      </a>
                    </li>
                  ))}
                </ol>
              )}
            </li>
          ))}
        </ol>
      </div>
    </nav>
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
  const cuenta = apartado.questions_covered;
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
        {cuenta > 0 && (
          // El rótulo se ve siempre —es lo que avisa de que ese párrafo es el que se pregunta— y la
          // frase que lo explica está **plegada**: la regla de la zona del alumno es que ningún
          // párrafo explicativo esté visible por defecto (la misma que el Resultado con su
          // «¿Por qué estimada?»).
          <Plegable titulo="Esto se pregunta">
            <p className="nota-margen__texto">
              {cuenta === 1
                ? '1 pregunta de este tema se contesta en este apartado.'
                : `${String(cuenta)} preguntas de este tema se contestan en este apartado.`}
            </p>
          </Plegable>
        )}
        <ReportMistake code={codigo} sectionKey={apartado.key} sectionTitle={apartado.title} />
      </div>
    </section>
  );
}
