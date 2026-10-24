import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate, useParams } from 'react-router-dom';

import {
  abandonStudentRun,
  answerStudentQuestion,
  finishStudentRun,
  getStudentRun,
  startStudentRun,
  type StudentRun,
} from '../../api/studentTests';
import { isApiError } from '../../api/client';
import { EmptyState } from '../../components/EmptyState';
import { LoadingState } from '../../components/LoadingState';
import { describeError } from '../system/labels';
import { AnswerSheet } from './AnswerSheet';
import { LETRAS_POR_DEFECTO } from './answerSheetModel';
import { SessionClock } from './TestClock';

/**
 * El test en curso, con la hoja de respuestas (diseño v0, §1 de `DISENO-V0-Y-STITCH-2026-10.md`).
 *
 * Es **modo examen**: desaparece la navegación (esta pantalla se monta fuera del marco del alumno).
 * A la izquierda el enunciado y sus opciones; a la derecha la hoja de respuestas, que en móvil se
 * abre con un botón. Se contesta con el ratón o con el teclado (`A`–`D`, `1`–`4`, `←`/`→` para
 * recorrer la hoja, `M`).
 *
 * Lo que **no** hace, y es lo importante: no inventa la corrección. Si el test corrige al final y no
 * ha terminado, la respuesta del servidor no trae la solución y aquí no hay nada que enseñar; si
 * corrige al momento, se enseña lo que el servidor manda. La solución no vive en esta pantalla.
 *
 * `posicion` es **la fila de la hoja que se está mirando**, y es lo que convierte la hoja en algo
 * que se usa y no solo se mira: `null` significa «la que toca» (la primera sin contestar, que decide
 * el servidor) y un número es una fila elegida —pulsando su número o con las flechas—. Volver a una
 * pregunta ya contestada es el defecto 5 del recorrido (§3.2 del encargo F36).
 */
export function StudentTestRunner() {
  const { id = '' } = useParams<{ id: string }>();
  const navegar = useNavigate();
  const cliente = useQueryClient();
  const [hojaAbierta, setHojaAbierta] = useState(false);
  const [posicion, setPosicion] = useState<number | null>(null);
  // La frase que devuelve el servidor al abandonar: qué queda de lo contestado. Se enseña hasta que
  // se sale de la pantalla, porque es la respuesta a la pregunta que acaba de hacer el alumno.
  const [avisoAbandono, setAvisoAbandono] = useState<string | null>(null);


  const run = useQuery({
    queryKey: ['student-run', id, posicion],
    queryFn: () => getStudentRun(id, posicion ?? undefined),
    enabled: id !== '',
    // Al saltar de una fila a otra —pulsando su número o con las flechas— se **conserva** la pregunta
    // que se estaba viendo hasta que llega la nueva: sin esto, moverse por la hoja parpadeaba con la
    // pantalla de «Abriendo el test…» en cada pulsación.
    placeholderData: keepPreviousData,
  });

  // Un test recién montado está en borrador: se arranca al entrar, que es lo que espera quien pulsa
  // «Empezar». Arrancar uno que ya corre no cambia nada (la ruta es reintentable).
  //
  // El arranque es **uno y solo uno**, y por eso la guarda es un `ref` que se levanta **antes** de
  // pedirlo y las dependencias del efecto son estables. Antes era un `useState` que se levantaba en
  // el `onSuccess` y el objeto entero de la mutación en las dependencias: como ese objeto cambia de
  // identidad en cada render, el efecto se volvía a ejecutar en cada uno y **cada render mandaba otro
  // `POST /start`** mientras el primero no hubiera vuelto. Medido en el recorrido del 16-oct-2026:
  // 4, 4, 4, 6 y hasta 12 peticiones por test abierto. No se tapa con un `debounce` ni con un `if` a
  // la defensiva: se arregla donde estaba, en que el efecto se repita.
  const arranqueHecho = useRef(false);
  const arrancar = useMutation({
    mutationFn: () => startStudentRun(id),
    onSuccess: (datos) => {
      cliente.setQueryData(['student-run', id, null], datos);
    },
  });
  const pedirArranque = arrancar.mutate;
  useEffect(() => {
    if (arranqueHecho.current) {
      return;
    }
    if (run.data === undefined || run.data.session.status !== 'draft') {
      return;
    }
    arranqueHecho.current = true;
    pedirArranque();
  }, [run.data, pedirArranque]);

  const contestar = useMutation({
    mutationFn: (variables: {
      position: number;
      chosen: string[];
      confidence: 'low' | null;
      /** Si esa pregunta ya estaba contestada: cambiar una respuesta **no** mueve la pantalla. */
      cambiaba: boolean;
    }) =>
      answerStudentQuestion(id, {
        position: variables.position,
        chosen: variables.chosen,
        elapsed_ms: 0,
        confidence: variables.confidence,
      }),
    onSuccess: (datos: StudentRun, variables) => {
      cliente.setQueryData(['student-run', id, posicion], datos);
      if (variables.cambiaba) {
        // Se cambió una respuesta: el alumno se queda donde está, mirando la pregunta que acaba de
        // corregir. Saltar a otra fila aquí sería quitarle de delante lo que está leyendo.
        return;
      }
      // Y al contestar una pregunta por primera vez, el test avanza solo a la primera sin contestar
      // —que es el avance de siempre—, pero lo decide la pantalla y no el servidor: el servidor
      // devuelve la fila que se acaba de contestar (§3.2 del encargo F36).
      const pendiente = datos.sheet.find((fila) => !fila.answered);
      if (pendiente !== undefined) {
        setPosicion(pendiente.position);
      }
    },
  });

  const cerrar = useMutation({
    mutationFn: () => finishStudentRun(id),
    onSuccess: () => {
      void cliente.invalidateQueries({ queryKey: ['student-run', id] });
      // Terminar lleva a la pantalla de resultado, que lo lee entero de la sesión (F14): lo que hay
      // que poder ver es cada pregunta con su tema, y eso es otra pantalla.
      void navegar(`/resultado/${id}`);
    },
  });

  // Abandonar es la salida que faltaba (§3.4): sin ella, el único modo de dejar un simulacro a
  // medias era cerrar la pestaña, y la sesión se quedaba «en curso» para siempre. El servidor dice
  // qué ha quedado de lo contestado y aquí solo se repite.
  const abandonar = useMutation({
    mutationFn: () => abandonStudentRun(id),
    onSuccess: (hecho) => {
      setAvisoAbandono(hecho.detail);
      void cliente.invalidateQueries({ queryKey: ['student-run', id] });
    },
  });

  const estado: StudentRun | undefined = run.data;
  const pregunta = estado?.question ?? null;
  const puedeCorregir = pregunta?.correction != null;
  const abandonado = estado?.session.status === 'abandoned';
  const terminado = estado?.finished === true;
  // Con el test terminado o abandonado no se contesta: el servidor tampoco lo admite, y ofrecer una
  // opción que va a fallar es peor que no ofrecerla.
  const puedeContestar = estado !== undefined && !terminado && !abandonado;
  // El reloj se para cuando el test ya no corre: seguir contando después de terminar sería contar
  // algo que ya no pasa.
  // La base del reloj es **cuándo llegó la última lectura del servidor** (`dataUpdatedAt` de react
  // query, que es el reloj del navegador en ese momento): lo único que se mide con el reloj local es
  // lo que pasa desde ahí, así que un equipo con la hora mal puesta no inventa horas de examen. `0`
  // es «no lo sé» —una lectura hecha antes de tener respuesta— y el reloj lo dice en lugar de
  // inventarse una hora: no se llama a `Date.now()` aquí porque una pantalla no puede depender del
  // reloj al pintarse (una medida impura dentro del render da resultados que cambian solos).
  const baseDelReloj = run.dataUpdatedAt;

  const responder = useCallback(
    (letra: string, confidence: 'low' | null = null) => {
      if (pregunta === null || !puedeContestar) {
        return;
      }
      contestar.mutate({
        position: pregunta.position,
        chosen: [letra],
        confidence,
        cambiaba: pregunta.answered,
      });
    },
    [contestar, pregunta, puedeContestar],
  );

  /** Ir a una fila de la hoja: es lo que hace la hoja usable (pulsar su número o las flechas). */
  const irA = useCallback((destino: number) => {
    setPosicion(destino);
  }, []);

  const letras = useMemo(
    () =>
      pregunta === null || pregunta.options.length === 0
        ? LETRAS_POR_DEFECTO
        : pregunta.options.map((opcion) => opcion.key),
    [pregunta],
  );

  // Teclado: `A`–`D` y `1`–`4` responden, `M` marca dudosa y `←`/`→` recorren la hoja. Se ignora lo
  // que se teclea dentro de un campo de texto.
  //
  // Las flechas no existían: la ayuda del test las prometía desde el diseño v0 y no estaban
  // implementadas (§3.2 del encargo F36, defecto 5 del recorrido). Ahora están, y la ayuda de la
  // pantalla lo dice, para que la promesa y el código digan lo mismo.
  useEffect(() => {
    function alPulsar(evento: KeyboardEvent) {
      if (pregunta === null || evento.metaKey || evento.ctrlKey || evento.altKey) {
        return;
      }
      const destino = evento.target as HTMLElement | null;
      if (destino !== null && ['INPUT', 'TEXTAREA', 'SELECT'].includes(destino.tagName)) {
        return;
      }
      if (evento.key === 'ArrowLeft' || evento.key === 'ArrowRight') {
        const paso = evento.key === 'ArrowLeft' ? -1 : 1;
        const total = estado?.total ?? 0;
        const objetivo = pregunta.position + paso;
        if (objetivo < 1 || objetivo > total) {
          return;
        }
        evento.preventDefault();
        irA(objetivo);
        return;
      }
      const tecla = evento.key.toLowerCase();
      const indice = letras.indexOf(tecla) >= 0 ? letras.indexOf(tecla) : Number(tecla) - 1;
      const elegida = indice >= 0 && indice < letras.length ? letras[indice] : undefined;
      if (elegida !== undefined) {
        evento.preventDefault();
        responder(elegida);
        return;
      }
      if (tecla === 'm') {
        evento.preventDefault();
        responder(pregunta.chosen[0] ?? letras[0] ?? 'a', 'low');
      }
    }
    window.addEventListener('keydown', alPulsar);
    return () => {
      window.removeEventListener('keydown', alPulsar);
    };
  }, [estado?.total, irA, letras, pregunta, responder]);

  if (id === '') {
    return (
      <main className="test-marco">
        <EmptyState
          title="Esta dirección no lleva a ningún test"
          description="Abre un test desde Inicio o desde el temario."
        />
      </main>
    );
  }
  if (run.isPending) {
    return (
      <main className="test-marco">
        <LoadingState label="Abriendo el test…" />
      </main>
    );
  }
  if (run.isError) {
    return (
      <main className="test-marco">
        <EmptyState
          title={isApiError(run.error, 404) ? 'Ese test no existe' : 'No se pudo abrir el test'}
          description={
            isApiError(run.error, 404)
              ? 'Puede que lo hayas descartado. Vuelve a Inicio y monta otro.'
              : 'La aplicación no responde. Arráncala con scripts\\api.ps1 y vuelve a intentarlo.'
          }
        />
      </main>
    );
  }
  if (estado === undefined) {
    return (
      <main className="test-marco">
        <EmptyState title="Ese test no existe" description="Vuelve a Inicio y monta otro." />
      </main>
    );
  }

  return (
    <main className="test-marco">
      <header className="test-cabecera">
        <div className="test-cabecera__datos">
          <p className="test-cabecera__progreso">
            Pregunta {estado.position ?? estado.total} de {estado.total}
          </p>
          <p className="test-cabecera__titulo">{estado.session.title}</p>
          <SessionClock
            // Una lectura nueva del servidor vuelve a montar el reloj: su arranque es el instante de
            // esa lectura, y así no puede quedarse contando desde una respuesta anterior.
            key={`reloj-${String(baseDelReloj)}`}
            startedAt={estado.session.started_at}
            timeLimitMinutes={estado.session.time_limit_minutes}
            serverNow={estado.session.server_now}
            leidoEnMs={baseDelReloj}
            detenido={terminado || abandonado}
          />
        </div>
        <div className="test-cabecera__acciones">
          <button
            type="button"
            className="ui-button ui-button--secondary test-cabecera__hoja-boton"
            onClick={() => {
              setHojaAbierta((abierta) => !abierta);
            }}
            aria-expanded={hojaAbierta}
          >
            Hoja
          </button>
          {terminado || abandonado ? (
            <Link className="ui-button ui-button--secondary" to="/">
              Salir
            </Link>
          ) : (
            <>
              <button
                type="button"
                className="ui-button ui-button--secondary"
                onClick={() => {
                  const nombre = estado.session.title;
                  const mensaje =
                    estado.answered === 0
                      ? `¿Abandonar «${nombre}»? No has contestado nada: el test se descarta.`
                      : `¿Abandonar «${nombre}»? Llevas ${String(estado.answered)} de ` +
                        `${String(estado.total)} contestadas: se conservan para repasar, pero el ` +
                        'test no contará como hecho.';
                  if (typeof window !== 'undefined' && !window.confirm(mensaje)) {
                    return;
                  }
                  abandonar.mutate();
                }}
                disabled={abandonar.isPending || cerrar.isPending}
              >
                Abandonar
              </button>
              <button
                type="button"
                className="ui-button ui-button--primary"
                onClick={() => {
                  cerrar.mutate();
                }}
                disabled={cerrar.isPending || abandonar.isPending}
              >
                Terminar
              </button>
            </>
          )}
        </div>
      </header>

      {avisoAbandono === null ? null : (
        <p className="test-aviso" role="status">
          {avisoAbandono}
        </p>
      )}
      {abandonado ? (
        <p className="test-aviso test-aviso--abandonado" role="status">
          Este test está abandonado: lo que contestaste se conserva para repasar y no cuenta como
          test hecho. Para seguir estudiando, monta otro desde Inicio.
        </p>
      ) : null}

      <div className="test-cuerpo">
        <section className="test-pregunta" aria-label="Pregunta">
          {pregunta === null ? (
            <>
              <EmptyState
                title="No queda ninguna pregunta por contestar"
                description="Puedes terminar el test y ver el resultado."
              />
              {puedeContestar ? (
                <button
                  type="button"
                  className="ui-button ui-button--primary"
                  onClick={() => {
                    cerrar.mutate();
                  }}
                  disabled={cerrar.isPending}
                >
                  Terminar y ver el resultado
                </button>
              ) : null}
            </>
          ) : (
            <>
              {estado.session.practical_case_statement ? (
                // **El caso, con la pregunta**: sus veinticinco preguntas dicen «con los datos del
                // caso, conteste», y sin el enunciado delante no se pueden contestar (remate,
                // punto 4).
                <aside className="test-supuesto" aria-label="Enunciado del supuesto práctico">
                  <h2 className="test-supuesto__titulo">Supuesto práctico</h2>
                  <p className="test-supuesto__texto" data-contenido>
                    {estado.session.practical_case_statement}
                  </p>
                </aside>
              ) : null}
              <p className="test-pregunta__numero">
                {pregunta.is_reserve ? 'Reserva · ' : ''}
                {pregunta.position}
                {pregunta.in_review && !pregunta.derived_key ? (
                  // La clave de esta pregunta está en revisión (§1): el conjunto discrepa de los
                  // apuntes entre el 15 % y el 30 %. Entra en el test, pero el alumno lo ve **antes**
                  // de fiarse de la corrección. El texto es el mismo que devuelve la API. Si su clave
                  // es derivada manda la otra marca: es más específica y decir las dos confunde.
                  <span className="marca marca-clave-en-revision" title="clave en revisión">
                    clave en revisión
                  </span>
                ) : null}
                {pregunta.derived_key ? (
                  // Y esta otra dice de dónde sale la letra (§1 del encargo F29): la clave es
                  // derivada —los apuntes, con su cita verificada, y el modelo preguntado sin
                  // apuntes dicen lo mismo—, así que no es la plantilla del conjunto.
                  <span
                    className="marca marca-clave-derivada"
                    title="clave revisada automáticamente"
                  >
                    clave revisada automáticamente
                  </span>
                ) : null}
              </p>
              <h1 className="test-pregunta__enunciado" data-contenido>
                {pregunta.stem}
              </h1>
              <ul className="test-opciones" data-contenido>
                {pregunta.options.map((opcion, indice) => {
                  const elegida = pregunta.chosen.includes(opcion.key);
                  const correcta =
                    puedeCorregir && (pregunta.correction?.correct.includes(opcion.key) ?? false);
                  const estadoOpcion = correcta
                    ? 'correcta'
                    : elegida && puedeCorregir
                      ? 'fallada'
                      : elegida
                        ? 'elegida'
                        : 'normal';
                  return (
                    <li key={opcion.key}>
                      <button
                        type="button"
                        className={`test-opcion test-opcion--${estadoOpcion}`}
                        onClick={() => {
                          responder(opcion.key);
                        }}
                        disabled={!puedeContestar}
                        aria-pressed={elegida}
                      >
                        <span className="test-opcion__letra">{opcion.key.toUpperCase()}</span>
                        <span className="test-opcion__texto">{opcion.text}</span>
                        <span className="test-opcion__tecla">{indice + 1}</span>
                      </button>
                      {elegida && <p className="test-opcion__marca">Tu respuesta</p>}
                      {correcta && !elegida && <p className="test-opcion__marca">Correcta</p>}
                    </li>
                  );
                })}
              </ul>
              <p className="test-ayuda">
                {puedeContestar
                  ? 'Teclado: A–D o 1–4 para responder, M para marcarla como dudosa y ← / → para recorrer la hoja. Se puede volver a cualquier pregunta desde la hoja y cambiar la respuesta mientras el test no haya terminado.'
                  : 'Este test ya no admite respuestas.'}
                {puedeCorregir ? null : ' La corrección de este test se ve al terminar.'}
              </p>
              {contestar.error !== null && (
                // Una respuesta que el servidor no acepta se **dice**. El fallo medido en el
                // recorrido era este: el alumno pulsaba otra opción, la máquina de estados la
                // rechazaba y en la pantalla no pasaba nada —ni un aviso, ni un cambio—, que es la
                // peor forma de contar algo. El texto es el del servidor, que es el que sabe por qué
                // (con el test terminado, las respuestas están congeladas).
                <section className="card notice notice--inline" role="alert">
                  <h4>La respuesta no se ha guardado</h4>
                  <p>{describeError(contestar.error)}</p>
                </section>
              )}
            </>
          )}
        </section>

        <aside
          className={`test-hoja${hojaAbierta ? ' test-hoja--abierta' : ''}`}
          aria-label="Hoja de respuestas"
        >
          <h2 className="test-hoja__titulo">Hoja</h2>
          <AnswerSheet
            filas={estado.sheet}
            actual={estado.position}
            letras={letras}
            onIr={irA}
          />
        </aside>
      </div>
    </main>
  );
}
