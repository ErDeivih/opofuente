import { useCallback, useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate, useParams } from 'react-router-dom';

import {
  answerStudentQuestion,
  finishStudentRun,
  getStudentRun,
  startStudentRun,
  type StudentRun,
} from '../../api/studentTests';
import { isApiError } from '../../api/client';
import { EmptyState } from '../../components/EmptyState';
import { LoadingState } from '../../components/LoadingState';
import { AnswerSheet } from './AnswerSheet';
import { LETRAS_POR_DEFECTO } from './answerSheetModel';

/**
 * El test en curso, con la hoja de respuestas (diseño v0, §1 de `DISENO-V0-Y-STITCH-2026-10.md`).
 *
 * Es **modo examen**: desaparece la navegación (esta pantalla se monta fuera del marco del alumno).
 * A la izquierda el enunciado y sus opciones; a la derecha la hoja de respuestas, que en móvil se
 * abre con un botón. Se contesta con el ratón o con el teclado (`A`–`D`, `1`–`4`, `Intro`, `M`).
 *
 * Lo que **no** hace, y es lo importante: no inventa la corrección. Si el test corrige al final y no
 * ha terminado, la respuesta del servidor no trae la solución y aquí no hay nada que enseñar; si
 * corrige al momento, se enseña lo que el servidor manda. La solución no vive en esta pantalla.
 */
export function StudentTestRunner() {
  const { id = '' } = useParams<{ id: string }>();
  const navegar = useNavigate();
  const cliente = useQueryClient();
  const [arrancado, setArrancado] = useState(false);
  const [hojaAbierta, setHojaAbierta] = useState(false);

  const run = useQuery({
    queryKey: ['student-run', id],
    queryFn: () => getStudentRun(id),
    enabled: id !== '',
  });

  // Un test recién montado está en borrador: se arranca al entrar, que es lo que espera quien pulsa
  // «Empezar». Arrancar uno que ya corre no cambia nada (la ruta es reintentable).
  const arrancar = useMutation({
    mutationFn: () => startStudentRun(id),
    onSuccess: (datos) => {
      cliente.setQueryData(['student-run', id], datos);
      setArrancado(true);
    },
  });
  useEffect(() => {
    if (run.data !== undefined && run.data.session.status === 'draft' && !arrancado) {
      arrancar.mutate();
    }
  }, [run.data, arrancado, arrancar]);

  const contestar = useMutation({
    mutationFn: (variables: { position: number; chosen: string[]; confidence: 'low' | null }) =>
      answerStudentQuestion(id, {
        position: variables.position,
        chosen: variables.chosen,
        elapsed_ms: 0,
        confidence: variables.confidence,
      }),
    onSuccess: (datos: StudentRun) => {
      cliente.setQueryData(['student-run', id], datos);
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

  const estado: StudentRun | undefined = run.data;
  const pregunta = estado?.question ?? null;
  const puedeCorregir = pregunta?.correction != null;

  const responder = useCallback(
    (letra: string, confidence: 'low' | null = null) => {
      if (pregunta === null) {
        return;
      }
      contestar.mutate({ position: pregunta.position, chosen: [letra], confidence });
    },
    [contestar, pregunta],
  );

  const letras = useMemo(
    () =>
      pregunta === null || pregunta.options.length === 0
        ? LETRAS_POR_DEFECTO
        : pregunta.options.map((opcion) => opcion.key),
    [pregunta],
  );

  // Teclado: `A`–`D` y `1`–`4` responden, `M` marca dudosa, `←`/`→` recorren la hoja e `Intro`
  // confirma. Se ignora lo que se teclea dentro de un campo de texto.
  useEffect(() => {
    function alPulsar(evento: KeyboardEvent) {
      if (pregunta === null || evento.metaKey || evento.ctrlKey || evento.altKey) {
        return;
      }
      const destino = evento.target as HTMLElement | null;
      if (destino !== null && ['INPUT', 'TEXTAREA', 'SELECT'].includes(destino.tagName)) {
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
  }, [letras, pregunta, responder]);

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
        <p className="test-cabecera__progreso">
          Pregunta {estado.position ?? estado.total} de {estado.total}
        </p>
        <p className="test-cabecera__titulo">{estado.session.title}</p>
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
          {estado.finished ? (
            <Link className="ui-button ui-button--secondary" to="/">
              Salir
            </Link>
          ) : (
            <button
              type="button"
              className="ui-button ui-button--primary"
              onClick={() => {
                cerrar.mutate();
              }}
              disabled={cerrar.isPending}
            >
              Terminar
            </button>
          )}
        </div>
      </header>

      <div className="test-cuerpo">
        <section className="test-pregunta" aria-label="Pregunta">
          {pregunta === null ? (
            <>
              <EmptyState
                title="No queda ninguna pregunta por contestar"
                description="Puedes terminar el test y ver el resultado."
              />
              {estado.finished ? null : (
                <button
                  type="button"
                  className="ui-button ui-button--primary"
                  onClick={() => {
                    cerrar.mutate();
                  }}
                >
                  Terminar y ver el resultado
                </button>
              )}
            </>
          ) : (
            <>
              <p className="test-pregunta__numero">
                {pregunta.is_reserve ? 'Reserva · ' : ''}
                {pregunta.position}
                {pregunta.key_in_review ? (
                  // La clave de esta pregunta está en revisión (§1): el conjunto discrepa de los
                  // apuntes entre el 15 % y el 30 %. Entra en el test, pero el alumno lo ve **antes**
                  // de fiarse de la corrección. El texto es el mismo que devuelve la API.
                  <span className="marca-clave-en-revision" title="clave en revisión">
                    clave en revisión
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
                Teclado: A–D o 1–4 para responder, M para marcarla como dudosa.
                {puedeCorregir ? null : ' La corrección de este test se ve al terminar.'}
              </p>
            </>
          )}
        </section>

        <aside
          className={`test-hoja${hojaAbierta ? ' test-hoja--abierta' : ''}`}
          aria-label="Hoja de respuestas"
        >
          <h2 className="test-hoja__titulo">Hoja</h2>
          <AnswerSheet filas={estado.sheet} actual={estado.position} letras={letras} />
        </aside>
      </div>
    </main>
  );
}
