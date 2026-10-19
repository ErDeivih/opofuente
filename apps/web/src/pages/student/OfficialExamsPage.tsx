import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';

import { getStudentOfficialExams, type StudentOfficialExam } from '../../api/studentStudy';
import { createStudentOfficialExam } from '../../api/studentTests';
import { ErrorState } from '../../components/ErrorState';
import { LoadingState } from '../../components/LoadingState';
import { describeError } from '../../features/system/labels';
import { diaLegible } from '../../lib/fechas';

/**
 * Los exámenes oficiales importados (F14, paso 6 del §3 del objetivo; D10 para el INAP).
 *
 * La lista sale de la base y no de una lista escrita aquí: los exámenes del INAP se importan con su
 * cuestionario y su plantilla oficial (bloque D10), y lo que se ve es **lo que hay importado**. Las
 * tres cosas que esta pantalla **no** hace, y por las que está escrita así:
 *
 * 1. **no rellena la lista con lo que se le parezca.** No enseña bancos de práctica ni tests ya
 *    hechos con el nombre de «examen oficial»: una lista vacía con su explicación es más útil que una
 *    lista con otra cosa dentro;
 * 2. **no deja la pantalla en blanco**: cuando no hay ninguno, lo dice con esas palabras y explica de
 *    dónde saldrán;
 * 3. **no ofrece un examen que no se puede corregir**: el que está a medio importar (sin plantilla
 *    activa) sale, pero con su motivo en vez de un botón que fallaría.
 *
 * Y enseña **de dónde sale cada uno** (`origin_scope`, D10) y **cuántas preguntas tiene**, que es lo
 * que el alumno necesita para saber qué está practicando. El examen se pide **por su sitio en la
 * lista**, no por un identificador: del conjunto no viaja el identificador, solo su procedencia.
 */
export function OfficialExamsPage() {
  const navegar = useNavigate();
  const cliente = useQueryClient();

  const consulta = useQuery({
    queryKey: ['student-official-exams'],
    queryFn: getStudentOfficialExams,
  });

  const montar = useMutation({
    mutationFn: (position: number) => createStudentOfficialExam(position),
    onSuccess: (sesion) => {
      void cliente.invalidateQueries({ queryKey: ['student-overview'] });
      void navegar(`/test/${sesion.id}`);
    },
  });

  if (consulta.isPending) {
    return (
      <>
        <h1 className="pagina__titulo">Exámenes oficiales</h1>
        <LoadingState label="Mirando qué exámenes hay…" />
      </>
    );
  }
  if (consulta.isError) {
    return (
      <>
        <h1 className="pagina__titulo">Exámenes oficiales</h1>
        <ErrorState
          title="No se pudo cargar la lista de exámenes"
          message={describeError(consulta.error)}
          onRetry={() => {
            void consulta.refetch();
          }}
        />
      </>
    );
  }

  const examenes = consulta.data.exams;

  return (
    <>
      <header className="pagina__cabecera">
        <h1 className="pagina__titulo">Exámenes oficiales</h1>
        <p className="pagina__entrada">
          Los exámenes de años anteriores, hechos como el día del examen: mismas preguntas, mismo
          tiempo y misma penalización.
        </p>
      </header>

      {examenes.length === 0 ? (
        <section className="bloque" aria-labelledby="sin-examenes">
          <h2 className="bloque__titulo" id="sin-examenes">
            Todavía no hay exámenes oficiales importados
          </h2>
          <p className="bloque__texto">
            Los exámenes de años anteriores se descargan de la web del organismo y se importan en la
            aplicación; hasta que eso no se haga, no hay ninguno que hacer aquí. Cuando estén, saldrán
            en esta lista con su fecha y su número de preguntas.
          </p>
          <p className="bloque__texto">
            Mientras tanto, puedes estudiar con el temario y con los simulacros, que tienen el mismo
            número de preguntas, el mismo tiempo y la misma penalización.
          </p>
        </section>
      ) : (
        <section className="bloque" aria-labelledby="lista-examenes">
          <h2 className="bloque__titulo" id="lista-examenes">
            Los que hay
          </h2>
          <ul className="examenes" aria-label="Exámenes oficiales">
            {examenes.map((examen) => (
              <li className="examenes__fila" key={examen.position}>
                <span className="examenes__titulo" data-contenido>
                  {examen.title}
                </span>
                <span className="examenes__procedencia">{procedenciaDe(examen)}</span>
                <span className="examenes__datos">{datosDe(examen)}</span>
                {examen.ready ? (
                  <button
                    type="button"
                    className="ui-button ui-button--primary"
                    onClick={() => {
                      montar.mutate(examen.position);
                    }}
                    disabled={montar.isPending}
                  >
                    Hacer este examen
                  </button>
                ) : (
                  <span className="examenes__espera">{motivoDeEspera(examen)}</span>
                )}              </li>
            ))}
          </ul>
        </section>
      )}

      {montar.isError && (
        <ErrorState title="No se pudo montar el examen" message={describeError(montar.error)} />
      )}
    </>
  );
}

/**
 * «22 nov 2025 · 85 preguntas», y cuando el origen solo declara el año, «Ejercicio de 2025».
 *
 * Las tres formas son las tres cosas que se pueden afirmar, y se distinguen a propósito: una fecha
 * completa se enseña tal cual; un año se dice como año —los cuestionarios del INAP rotulan «2025 -
 * TAI-L (MODELO A)» y no publican el día, y poner un 1 de enero sería inventarse el día y el mes—;
 * y un examen sin ninguna de las dos **dice por qué**, en vez de dejar el hueco o de rellenarlo con
 * una fecha que nadie ha publicado.
 *
 * Y el número de preguntas es el del **examen**, no el del conjunto: 85 y no 135, que es lo que el
 * alumno se va a encontrar al abrirlo.
 */
function datosDe(examen: StudentOfficialExam): string {
  const fecha =
    examen.held_at !== null
      ? diaLegible(examen.held_at)
      : examen.held_year !== null
        ? `Ejercicio de ${String(examen.held_year)}`
        : 'Sin fecha publicada: el documento de origen no la declara';
  return `${fecha} · ${String(examen.questions)} preguntas`;
}

/**
 * De dónde sale el examen (`origin_scope`, D10), en las palabras del alumno.
 *
 * Tres valores y los tres se dicen: `age` es la Administración General del Estado —el INAP y la
 * Guardia Civil, que es el examen que se está preparando—, `otra_administracion` es material de otra
 * administración y `desconocida` es lo que no se puede afirmar. Un vocabulario se cierra en la base
 * (`CHECK`) y se traduce aquí una sola vez: escribir «AGE» a pelo en la pantalla dejaría dos verdades
 * sobre el mismo dato.
 */
function procedenciaDe(examen: StudentOfficialExam): string {
  if (examen.origin_scope === 'age') {
    return 'Administración General del Estado';
  }
  if (examen.origin_scope === 'otra_administracion') {
    return 'Otra administración';
  }
  return 'Procedencia sin declarar';
}

/**
 * Por qué un examen no se puede hacer todavía, con el motivo que le corresponde.
 *
 * Los dos motivos son distintos y no se pueden decir con la misma frase: **faltan sus respuestas**
 * es un examen que está a medio importar (sin plantilla activa con la que corregir) y **faltan
 * preguntas** es un examen que tiene menos de las que la convocatoria pide —los seis de promoción
 * interna traen 74 para una parte de 80—. El servidor manda el motivo en `blocked_reason` y aquí
 * solo se traduce: adivinarlo por el número de preguntas dejaría dos verdades sobre lo mismo.
 */
function motivoDeEspera(examen: StudentOfficialExam): string {
  if (examen.blocked_reason === 'faltan_preguntas') {
    return 'Todavía no se puede hacer: tiene menos preguntas de las que pide la convocatoria.';
  }
  if (examen.blocked_reason === 'faltan_respuestas') {
    return 'Todavía no se puede hacer: faltan sus respuestas.';
  }
  if (examen.questions === 0) {
    return 'Todavía no se puede hacer: no tiene preguntas.';
  }
  return 'Todavía no se puede hacer.';
}
