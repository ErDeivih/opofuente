import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate, useParams } from 'react-router-dom';

import { isApiError } from '../../api/client';
import {
  createStudentTest,
  getStudentResult,
  type StudentResultOutcome,
  type StudentResultQuestion,
  type StudentSessionResult,
} from '../../api/studentTests';
import { EmptyState } from '../../components/EmptyState';
import { LoadingState } from '../../components/LoadingState';
import { fechaLegible } from '../../lib/fechas';
import { renderInline } from '../../ui/inlineMarkdown';

/**
 * El resultado de un test terminado (F14, paso 3 del §3 del objetivo).
 *
 * Es la pantalla que contesta a la única pregunta que importa después de un test —**qué he fallado y
 * por dónde lo repaso**— y por eso no es una lista de números: cada pregunta lleva su tema, el
 * desglose va por tema y cada tema tiene su salida a los apuntes.
 *
 * Tres decisiones que se ven en el código:
 *
 * 1. **la nota es la que se guardó** al cerrar el test; esta pantalla no recalcula nada. El resultado
 *    se lee de la sesión (`GET …/result`), así que se puede recargar sin volver a cerrar nada;
 * 2. **el aviso de que la nota es una estimación sale del servidor**, no se escribe aquí: es el mismo
 *    texto que usa el motor, y reescribirlo sería tener dos versiones de la misma advertencia;
 * 3. una pregunta que la plantilla **no corrige** no cuenta como fallo: se dice que no se corrige.
 *    Meterla en los fallos sería culpar al alumno de un problema del material.
 */
export function ResultPage() {
  const { id = '' } = useParams<{ id: string }>();
  const navegar = useNavigate();
  const cliente = useQueryClient();

  const consulta = useQuery({
    queryKey: ['student-result', id],
    queryFn: () => getStudentResult(id),
    enabled: id !== '',
  });

  const repetir = useMutation({
    mutationFn: (resultado: StudentSessionResult) =>
      createStudentTest({
        nodes: resultado.topics.map((tema) => tema.code),
        count: resultado.questions.length,
        filter: 'all',
        feedback: 'immediate',
      }),
    onSuccess: (sesion) => {
      void cliente.invalidateQueries({ queryKey: ['student-overview'] });
      void navegar(`/test/${sesion.id}`);
    },
  });

  if (id === '') {
    return (
      <>
        <h1 className="pagina__titulo">Resultado</h1>
        <EmptyState
          title="Esta dirección no lleva a ningún resultado"
          description="Abre un test desde Inicio o desde el temario y, al terminarlo, verás aquí su resultado."
        />
      </>
    );
  }
  if (consulta.isPending) {
    return (
      <>
        <h1 className="pagina__titulo">Resultado</h1>
        <LoadingState label="Mirando cómo fue…" />
      </>
    );
  }
  if (consulta.isError) {
    const sinTerminar = isApiError(consulta.error, 409);
    return (
      <>
        <h1 className="pagina__titulo">Resultado</h1>
        <EmptyState
          title={sinTerminar ? 'Ese test no está terminado' : 'No se pudo cargar el resultado'}
          description={
            sinTerminar
              ? 'El resultado se calcula al terminar el test: ábrelo y termínalo para verlo entero.'
              : 'La aplicación no responde. Arráncala con scripts\\api.ps1 y vuelve a intentarlo.'
          }
        />
        {sinTerminar && (
          <p className="acciones">
            <Link className="ui-button ui-button--primary" to={`/test/${id}`}>
              Volver al test
            </Link>
          </p>
        )}
      </>
    );
  }

  const resultado = consulta.data;
  const temas = resultado.topics;
  const primerTema = temas[0];
  const aciertos = resultado.total.correct;
  const fallos = resultado.total.wrong;
  const blancos = resultado.total.blank;

  return (
    <>
      <header className="pagina__cabecera">
        <h1 className="pagina__titulo">Resultado</h1>
        <p className="pagina__entrada">
          {resultado.session.title}
          {resultado.session.finished_at === null
            ? null
            : ` · ${fechaLegible(resultado.session.finished_at)}`}
          {resultado.duration_seconds === null
            ? null
            : ` · ${duracionLegible(resultado.duration_seconds)}`}
        </p>
      </header>

      <section className="bloque" aria-labelledby="tu-nota">
        <h2 className="bloque__titulo" id="tu-nota">
          Tu nota
        </h2>
        <p className="resultado__cifras">
          {aciertos} {aciertos === 1 ? 'acierto' : 'aciertos'} · {fallos}{' '}
          {fallos === 1 ? 'fallo' : 'fallos'} · {blancos} en blanco
        </p>
        <p className="resultado__puntos">
          <strong>{resultado.total.score_decimal}</strong>
          {resultado.total.score_max === null
            ? null
            : ` sobre ${String(resultado.total.score_max)}`}
        </p>
        {resultado.total.verdict_note === null ? null : (
          <p className="resultado__aviso">{renderInline(resultado.total.verdict_note)}</p>
        )}
        {resultado.official_note === null ? null : (
          <p className="resultado__aviso">{renderInline(resultado.official_note)}</p>
        )}

        {resultado.parts.length > 0 && (
          <ul className="resultado__partes" aria-label="Nota por parte">
            {resultado.parts.map((parte) => (
              <li className="resultado__parte" key={parte.part_code ?? 'unica'}>
                <p className="resultado__parte-nombre">{parte.part_name ?? 'Parte'}</p>
                <p className="resultado__parte-nota">
                  {parte.score_decimal}
                  {parte.score_max === null ? null : ` sobre ${String(parte.score_max)}`}
                  {parte.pass_score === null
                    ? null
                    : ` · mínimo ${String(parte.pass_score)}`}
                </p>
                <p className="resultado__parte-cifras">
                  {parte.correct} de {parte.correct + parte.wrong + parte.blank} corregidas
                </p>
                {parte.verdict_note === null ? null : (
                  <p className="resultado__aviso">{renderInline(parte.verdict_note)}</p>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="bloque" aria-labelledby="por-tema">
        <h2 className="bloque__titulo" id="por-tema">
          Por tema
        </h2>
        {temas.length === 0 ? (
          <p className="bloque__texto">
            Las preguntas de este test no están catalogadas en ningún tema del programa, así que no hay
            desglose por tema. El propietario las tiene en su bandeja para asignarlas.
          </p>
        ) : (
          <ul className="resultado__temas" aria-label="Por tema">
            {temas.map((tema) => (
              <li className="resultado__tema" key={tema.code}>
                <span className="resultado__tema-codigo">{tema.code}</span>
                <span className="resultado__tema-titulo" data-contenido>
                  {tema.title}
                </span>
                <span className="resultado__tema-cifras">
                  {tema.correct} de {tema.graded}
                </span>
                <span className="resultado__tema-porcentaje">{porcentaje(tema.accuracy)}</span>
                <Link className="ui-button ui-button--secondary" to={`/temario/${tema.code}`}>
                  Repasar {tema.code}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="bloque" aria-labelledby="pregunta-a-pregunta">
        <h2 className="bloque__titulo" id="pregunta-a-pregunta">
          Pregunta a pregunta
        </h2>
        <ul className="resultado__preguntas" aria-label="Pregunta a pregunta">
          {resultado.questions.map((pregunta) => (
            <PreguntaCorregida key={pregunta.position} pregunta={pregunta} />
          ))}
        </ul>
      </section>

      <p className="acciones">
        <button
          type="button"
          className="ui-button ui-button--primary"
          onClick={() => {
            repetir.mutate(resultado);
          }}
          disabled={repetir.isPending || temas.length === 0}
        >
          Repetir este test
        </button>
        {primerTema === undefined ? (
          <Link className="ui-button ui-button--secondary" to="/temario">
            Volver al temario
          </Link>
        ) : (
          <Link className="ui-button ui-button--secondary" to={`/temario/${primerTema.code}`}>
            Volver al tema {primerTema.code}
          </Link>
        )}
      </p>
    </>
  );
}

/** Una pregunta ya corregida: sus opciones, lo que se marcó y de qué tema era. */
function PreguntaCorregida({ pregunta }: { pregunta: StudentResultQuestion }) {
  const desenlace = textoDelDesenlace(pregunta.outcome);
  return (
    <li className="resultado__pregunta">
      <p className="resultado__pregunta-cabecera">
        <span className="resultado__posicion">
          {pregunta.is_reserve ? 'Reserva · ' : ''}
          {pregunta.position}
        </span>
        {pregunta.key_in_review ? (
          // En el resultado importa más que en el test: si la clave no es de fiar, un fallo puede ser
          // de la clave y no del alumno (§1), y eso hay que poder verlo justo al mirar qué se falló.
          <span className="marca-clave-en-revision" title="clave en revisión">
            clave en revisión
          </span>
        ) : null}
        {pregunta.topics.map((tema) => (
          <Link
            className="resultado__etiqueta-tema"
            key={tema.code}
            to={`/temario/${tema.code}`}
            title={tema.title}
          >
            {tema.code}
          </Link>
        ))}
        <span className={`resultado__desenlace resultado__desenlace--${pregunta.outcome}`}>
          {desenlace}
        </span>
        {pregunta.elapsed_ms === null ? null : (
          <span className="resultado__tiempo">{segundosLegibles(pregunta.elapsed_ms)}</span>
        )}
      </p>
      <p className="resultado__enunciado" data-contenido>
        {pregunta.stem}
      </p>
      <ul className="resultado__opciones" data-contenido>
        {pregunta.options.map((opcion) => {
          const elegida = pregunta.chosen.includes(opcion.key);
          const correcta = pregunta.correct.includes(opcion.key);
          return (
            <li
              className={`resultado__opcion${
                correcta ? ' resultado__opcion--correcta' : elegida ? ' resultado__opcion--fallada' : ''
              }`}
              key={opcion.key}
            >
              <span className="resultado__letra">{opcion.key.toUpperCase()}</span>
              <span className="resultado__texto">{opcion.text}</span>
              {elegida && <span className="resultado__marca">Tu respuesta</span>}
              {correcta && <span className="resultado__marca">Correcta</span>}
            </li>
          );
        })}
      </ul>
    </li>
  );
}

/** El desenlace, en las palabras de la pantalla. */
function textoDelDesenlace(desenlace: StudentResultOutcome): string {
  if (desenlace === 'correct') {
    return 'Acertada';
  }
  if (desenlace === 'wrong') {
    return 'Fallada';
  }
  if (desenlace === 'blank') {
    return 'En blanco';
  }
  return 'No se corrige';
}

/** El porcentaje de acierto, escrito. Sin nada corregido se dice que no hay nada que medir. */
function porcentaje(accuracy: number | null): string {
  return accuracy === null ? '—' : `${String(Math.round(accuracy * 100))} %`;
}

/** «12 min 30 s»: el tiempo que se ha tardado, con las unidades que se leen. */
function duracionLegible(segundos: number): string {
  const minutos = Math.floor(segundos / 60);
  const resto = segundos % 60;
  if (minutos === 0) {
    return `${String(resto)} s`;
  }
  if (resto === 0) {
    return `${String(minutos)} min`;
  }
  return `${String(minutos)} min ${String(resto)} s`;
}

/** El tiempo de una pregunta: en segundos mientras quepa, y si no, en minutos. */
function segundosLegibles(milisegundos: number): string {
  const segundos = Math.round(milisegundos / 1000);
  if (segundos < 60) {
    return `${String(segundos)} s`;
  }
  return duracionLegible(segundos);
}
