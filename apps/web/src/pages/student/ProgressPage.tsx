import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';

import {
  getStudentProgress,
  type StudentTopicProgress,
} from '../../api/studentStudy';
import { fetchStats, type Stats } from '../../api/stats';
import { ErrorState } from '../../components/ErrorState';
import { EsqueletoDeLista } from '../../components/Esqueleto';
import type { StudentSession } from '../../api/studentTests';
import { describeError } from '../../features/system/labels';
import { diaLegible } from '../../lib/fechas';
import { formatearPorcentaje } from '../../lib/numeros';
import { ProgressBar } from '../../ui/Progress';

/**
 * El progreso (F14, paso 6 del §3 del objetivo).
 *
 * Contesta a tres preguntas, en este orden: **cuánto llevo**, **por dónde voy** y **qué me falta**.
 * Tres decisiones que se ven en el código:
 *
 * 1. **el porcentaje va escrito**, en cada bloque y en cada tema. Es la lección de F13: una barra sin
 *    número obliga a adivinar, y con 33 temas eso importa;
 * 2. **lo que no se ha empezado no es un cero**: un tema sin contestar dice «Sin empezar», porque un
 *    `0 %` se lee como un suspenso y no es eso;
 * 3. **los tests hechos son los de verdad**, no los que caben en la lista: la cifra la cuenta el
 *    servidor sobre todos los tests terminados, y el historial enseña los últimos.
 *
 * «Qué te falta» no es una lista de reproches: son los temas sin empezar y los más flojos, con su
 * salida a los apuntes y a practicar.
 */
export function ProgressPage() {
  const consulta = useQuery({ queryKey: ['student-progress'], queryFn: getStudentProgress });
  const stats = useQuery({ queryKey: ['stats'], queryFn: fetchStats });

  if (consulta.isPending) {
    return (
      <>
        <h1 className="pagina__titulo">Progreso</h1>
        <EsqueletoDeLista nombre="el progreso" identificador="esqueleto-progreso" filas={3} />
      </>
    );
  }
  if (consulta.isError) {
    return (
      <>
        <h1 className="pagina__titulo">Progreso</h1>
        <ErrorState
          title="No se pudo cargar tu progreso"
          message={describeError(consulta.error)}
          onRetry={() => {
            void consulta.refetch();
          }}
        />
      </>
    );
  }

  const { blocks, weakest_topics, history, tests_finished } = consulta.data;
  const temas = blocks.flatMap((bloque) => bloque.topics);
  const sinEmpezar = temas.filter((tema) => tema.answered === 0);
  const aciertos = temas.reduce((total, tema) => total + tema.correct, 0);

  return (
    <>
      <header className="pagina__cabecera">
        <h1 className="pagina__titulo">Progreso</h1>
        <p className="pagina__entrada">
          {`${String(tests_finished)} ${tests_finished === 1 ? 'test hecho' : 'tests hechos'} · ${String(aciertos)} ${aciertos === 1 ? 'acierto' : 'aciertos'} en total`}
        </p>
      </header>

      <section className="bloque" aria-labelledby="por-bloque">
        <h2 className="bloque__titulo" id="por-bloque">
          Por bloque
        </h2>
        <ul className="progreso__bloques" aria-label="Progreso por bloque">
          {blocks.map((bloque) => (
            <li className="progreso__bloque" key={bloque.code}>
              <span className="progreso__bloque-codigo">{bloque.code}</span>
              <span className="progreso__bloque-titulo" data-contenido>
                {bloque.title}
              </span>
              <BarraDeProgreso accuracy={bloque.accuracy} etiqueta={`Bloque ${bloque.code}`} />
              <span className="progreso__bloque-cifras">
                {`${String(bloque.correct)} de ${String(bloque.answered)} contestadas`}
              </span>
            </li>
          ))}
        </ul>
      </section>

      <section className="bloque" aria-labelledby="por-tema">
        <h2 className="bloque__titulo" id="por-tema">
          Por tema
        </h2>
        <ul className="progreso__temas" aria-label="Progreso por tema">
          {temas.map((tema) => (
            <FilaDeTema key={tema.code} tema={tema} />
          ))}
        </ul>
      </section>

      {weakest_topics.length > 0 && (
        <section className="bloque" aria-labelledby="mas-flojos">
          <h2 className="bloque__titulo" id="mas-flojos">
            Lo que hay que repasar
          </h2>
          <ul className="progreso__flojos" aria-label="Temas más flojos">
            {weakest_topics.map((tema) => (
              <li className="progreso__flojo" key={tema.code}>
                <span className="progreso__tema-codigo">{tema.code}</span>
                <span className="progreso__flojo-titulo" data-contenido>
                  {tema.title}
                </span>
                <span className="progreso__tema-porcentaje">{porcentaje(tema.accuracy)}</span>
                <Link className="ui-button ui-button--secondary" to={`/temario/${tema.code}`}>
                  Repasar {tema.code}
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}

      {sinEmpezar.length > 0 && (
        <section className="bloque" aria-labelledby="sin-empezar">
          <h2 className="bloque__titulo" id="sin-empezar">
            Lo que no has empezado
          </h2>
          <p className="bloque__texto">
            {`${String(sinEmpezar.length)} de ${String(temas.length)} temas no tienen ninguna pregunta contestada todavía.`}
          </p>
          <ul className="progreso__sin-empezar" aria-label="Temas sin empezar">
            {sinEmpezar.map((tema) => (
              <li className="progreso__sin-empezar-fila" key={tema.code}>
                <Link className="progreso__tema-enlace" to={`/temario/${tema.code}`}>
                  <span className="progreso__tema-codigo">{tema.code}</span>
                  <span data-contenido>{tema.title}</span>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/*
        **Lo que responde a «¿que estudio ahora?»** (M6): la nota con su intervalo, los temas donde
        falla con su boton, y el tiempo. **La frase la compone el servidor**: la pantalla no reescribe
        cifras, y si no hay margen no lo inventa.
      */}
      {stats.data !== undefined && <QueEstudiar stats={stats.data} />}

      <section className="bloque" aria-labelledby="evolucion">
        <h2 className="bloque__titulo" id="evolucion">
          Cómo evolucionas
        </h2>
        {history.length === 0 ? (
          <p className="bloque__texto">Todavía no has terminado ningún test.</p>
        ) : (
          <ul className="progreso__historial" aria-label="Evolución">
            {history.map((sesion) => (
              <li className="progreso__test" key={sesion.id}>
                <span className="progreso__test-fecha">
                  {diaLegible(sesion.finished_at ?? sesion.created_at)}
                </span>
                <span className="progreso__test-titulo">{sesion.title}</span>
                <span className="progreso__test-cifra">{resumenDe(sesion)}</span>
                <Link className="progreso__test-enlace" to={`/resultado/${sesion.id}`}>
                  Ver el resultado
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </>
  );
}

/** Un tema: su porcentaje escrito, sus aciertos y —si no se ha tocado— la verdad en palabras. */
function FilaDeTema({ tema }: { tema: StudentTopicProgress }) {
  return (
    <li className="progreso__tema">
      <Link className="progreso__tema-enlace" to={`/temario/${tema.code}`}>
        <span className="progreso__tema-codigo">{tema.code}</span>
        <span data-contenido>{tema.title}</span>
      </Link>
      <BarraDeProgreso accuracy={tema.accuracy} etiqueta={`Tema ${tema.code}`} />
      <span className="progreso__tema-cifras">{`${String(tema.correct)} de ${String(tema.answered)}`}</span>
    </li>
  );
}

/** La barra con su porcentaje escrito, o «Sin empezar» cuando no hay nada corregido. */
function BarraDeProgreso({ accuracy, etiqueta }: { accuracy: number | null; etiqueta: string }) {
  if (accuracy === null) {
    return <span className="progreso__sin-datos">Sin empezar</span>;
  }
  return <ProgressBar percent={accuracy * 100} label={etiqueta} />;
}

/** El porcentaje de acierto, escrito. */
function porcentaje(accuracy: number | null): string {
  return accuracy === null ? 'Sin empezar' : formatearPorcentaje(accuracy);
}

/** El resumen de un test terminado: aciertos, fallos y blancos. */
function resumenDe(sesion: StudentSession): string {
  const resultado = sesion.result;
  if (resultado === null) {
    return 'Sin corregir';
  }
  return `${String(resultado.correct)} aciertos · ${String(resultado.wrong)} fallos · ${String(resultado.blank)} en blanco`;
}

/**
 * «Que estudio ahora»: la nota, los flojos y el tiempo (M6).
 *
 * **La nota va con su intervalo o sin el**, y el servidor ya decidio cual: con menos de dos intentos no
 * hay dispersion con la que dar un margen, y un `+-0` seria una precision inventada.
 *
 * **Cada flojo lleva su boton a practicar ese tema**, que es lo que el hito pide para darse por hecho.
 */
function QueEstudiar({ stats }: { stats: Stats }) {
  return (
    <section className="bloque" aria-labelledby="que-estudiar">
      <h2 className="bloque__titulo" id="que-estudiar">
        Que estudiar ahora
      </h2>

      {stats.nota === null ? (
        <p className="bloque__texto">
          Todavia no hay intentos suficientes para estimar una nota. Haz un test y vuelve.
        </p>
      ) : (
        <p className="progreso__nota">{stats.nota.frase}</p>
      )}

      {stats.flojos.length > 0 && (
        <ul className="progreso__flojos" aria-label="Temas donde fallas">
          {stats.flojos.map((tema) => (
            <li className="progreso__flojo" key={tema.codigo}>
              <span className="progreso__tema-codigo">{tema.codigo}</span>
              <span className="progreso__flojo-titulo" data-contenido>
                {tema.titulo}
              </span>
              <span className="progreso__tema-porcentaje">{tema.frase}</span>
              <Link
                className="ui-button ui-button--secondary"
                to={`/tests?tema=${encodeURIComponent(tema.codigo)}`}
              >
                Practicar {tema.codigo}
              </Link>
            </li>
          ))}
        </ul>
      )}

      {stats.comparacion_del_tiempo !== null && (
        <p className="bloque__texto">{stats.comparacion_del_tiempo}</p>
      )}

      {stats.semanas.length > 0 && (
        <ul className="progreso__semanas" aria-label="Acierto por semana">
          {stats.semanas.map((semana) => (
            <li className="progreso__semana" key={semana.empieza}>
              <span className="progreso__semana-fecha">{semana.empieza}</span>
              <span className="progreso__semana-cifra">
                {`${String(Math.round(semana.acierto * 100))} % en ${String(semana.intentos)} ${semana.intentos === 1 ? 'intento' : 'intentos'}`}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
