import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { getStudentMockExamPlan, type StudentMockExamVariant } from '../../api/studentStudy';
import { createStudentMockExam } from '../../api/studentTests';
import { ErrorState } from '../../components/ErrorState';
import { LoadingState } from '../../components/LoadingState';
import { describeError } from '../../features/system/labels';
import { renderInline } from '../../ui/inlineMarkdown';

/**
 * El simulacro, antes de montarlo (F14, paso 6 del §3 del objetivo).
 *
 * Esta pantalla existe para que se pueda elegir **sabiendo qué se elige**, y eso tiene dos
 * consecuencias que se ven en el código:
 *
 * 1. **nada de lo que se enseña está escrito aquí.** Las partes, sus preguntas, sus reservas, el
 *    tiempo, la banda de puntuación, el mínimo y la penalización salen del perfil del examen que
 *    sirve el servidor. Si la convocatoria no publica un dato, llega `null` y se dice que no está; no
 *    se rellena con lo que suele pasar;
 * 2. **el aviso de que no es un examen oficial sale del servidor y se enseña tal cual**, con su
 *    énfasis: es el mismo texto con el que el motor monta el simulacro, y reescribirlo aquí sería
 *    tener dos versiones de la misma advertencia (y una de ellas podría dejar de ser cierta).
 *
 * La variante corta es de la aplicación y lo dice: 40 preguntas y 48 minutos, sin supuesto.
 */
export function MockExamPage() {
  const navegar = useNavigate();
  const cliente = useQueryClient();
  const [variante, setVariante] = useState<'full' | 'short'>('full');
  const [bloque, setBloque] = useState<'III' | 'IV'>('IV');

  const consulta = useQuery({ queryKey: ['student-mock-plan'], queryFn: getStudentMockExamPlan });

  const montar = useMutation({
    mutationFn: () => createStudentMockExam({ variant: variante, case_block: bloque }),
    onSuccess: (sesion) => {
      void cliente.invalidateQueries({ queryKey: ['student-overview'] });
      void navegar(`/test/${sesion.id}`);
    },
  });

  if (consulta.isPending) {
    return (
      <>
        <h1 className="pagina__titulo">Simulacros</h1>
        <LoadingState label="Leyendo el perfil del examen…" />
      </>
    );
  }
  if (consulta.isError) {
    return (
      <>
        <h1 className="pagina__titulo">Simulacros</h1>
        <ErrorState
          title="No se pudo cargar el simulacro"
          message={describeError(consulta.error)}
          onRetry={() => {
            void consulta.refetch();
          }}
        />
      </>
    );
  }

  const plan = consulta.data;
  const elegida = variante === 'full' ? plan.full : plan.short;

  return (
    <>
      <header className="pagina__cabecera">
        <h1 className="pagina__titulo">Simulacros</h1>
      </header>

      <section className="bloque" aria-labelledby="variante">
        <h2 className="bloque__titulo" id="variante">
          Qué simulacro quieres
        </h2>
        <div className="opciones" role="radiogroup" aria-labelledby="variante">
          {[plan.full, plan.short].map((opcion) => (
            <div className="opcion" key={opcion.variant}>
              <input
                id={`variante-${opcion.variant}`}
                type="radio"
                name="variante"
                value={opcion.variant}
                checked={variante === opcion.variant}
                onChange={() => {
                  setVariante(opcion.variant);
                }}
              />
              <label className="opcion__texto" htmlFor={`variante-${opcion.variant}`}>
                <span className="opcion__titulo">{opcion.title}</span>
                <span className="opcion__detalle">{resumenDe(opcion)}</span>
              </label>
            </div>
          ))}
        </div>
      </section>

      <section className="bloque" aria-labelledby="que-cae">
        <h2 className="bloque__titulo" id="que-cae">
          Qué va a caer
        </h2>
        {elegida.parts.length === 0 ? (
          <p className="bloque__texto">
            El perfil de este examen no publica sus partes, así que no se puede decir qué va a caer. No
            se inventa: lo que se sepa estará en la convocatoria.
          </p>
        ) : (
          <ul className="simulacro__partes" aria-label="Partes del simulacro">
            {elegida.parts.map((parte) => (
              <li className="simulacro__parte" key={parte.code}>
                <p className="simulacro__parte-nombre">{parte.name}</p>
                <p className="simulacro__parte-datos">
                  {parte.ordinary_items === null
                    ? 'El perfil no publica cuántas preguntas tiene'
                    : `${String(parte.ordinary_items)} preguntas`}
                  {parte.reserve_items === null
                    ? ''
                    : ` más ${String(parte.reserve_items)} de reserva`}
                  {elegida.time_limit_minutes === null
                    ? ''
                    : ` · ${String(elegida.time_limit_minutes)} minutos`}
                </p>
                <p className="simulacro__parte-reglas">
                  {parte.score_max === null
                    ? 'Sin banda de puntuación publicada'
                    : `De 0 a ${String(parte.score_max)}`}
                  {parte.pass_score === null ? '' : ` · mínimo ${String(parte.pass_score)}`}
                  {parte.penalty === null
                    ? ''
                    : ` · cada error descuenta ${parte.penalty} de una pregunta`}
                </p>
              </li>
            ))}
          </ul>
        )}
        {elegida.note === null ? null : (
          <p className="resultado__aviso">{renderInline(elegida.note)}</p>
        )}
      </section>

      {variante === 'full' && plan.case_blocks.length > 0 && (
        <section className="bloque" aria-labelledby="supuesto">
          <h2 className="bloque__titulo" id="supuesto">
            El supuesto práctico
          </h2>
          {/*
            Se elige el supuesto y **no se despliegan sus temas**: eran nueve filas con su título y
            sus preguntas disponibles debajo de una decisión de dos opciones, y lo que hay que
            decidir aquí es III o IV. Lo que cae en cada bloque se lee en el temario, y lo que
            contesta el simulacro lo dice el servidor al montarlo.
          */}
          <div className="opciones" role="radiogroup" aria-labelledby="supuesto">
            {plan.case_blocks.map((opcion) => (
              <div className="opcion" key={opcion.code}>
                <input
                  id={`supuesto-${opcion.code}`}
                  type="radio"
                  name="supuesto"
                  value={opcion.code}
                  checked={bloque === opcion.code}
                  onChange={() => {
                    setBloque(opcion.code as 'III' | 'IV');
                  }}
                />
                <label className="opcion__texto" htmlFor={`supuesto-${opcion.code}`}>
                  <span className="opcion__titulo">{`Bloque ${opcion.code}`}</span>
                  <span className="opcion__detalle" data-contenido>
                    {opcion.title}
                  </span>
                </label>
              </div>
            ))}
          </div>
        </section>
      )}

      <p className="acciones">
        <button
          type="button"
          className="ui-button ui-button--primary"
          onClick={() => {
            montar.mutate();
          }}
          disabled={montar.isPending}
        >
          {montar.isPending ? 'Preparando tu simulacro…' : 'Empezar el simulacro'}
        </button>
      </p>
      {montar.isPending ? (
        // El montaje recorre el banco entero de los temas del simulacro y no es instantáneo: mientras
        // dura, la pantalla **lo dice** y el botón se queda ocupado. No es una barra de progreso
        // inventada —el servidor no publica en qué va—, es la frase que evita que parezca un cuelgue.
        <p className="simulacro__preparando" role="status" aria-live="polite">
          Estamos eligiendo las preguntas de tu simulacro. Puede tardar unos segundos.
        </p>
      ) : null}
      {montar.isError && <ErrorState title="No se pudo montar" message={describeError(montar.error)} />}
    </>
  );
}

/**
 * El resumen de una variante para su opción: cuántas preguntas se contestan y cuánto dura.
 *
 * Las de **reserva** van aparte y en su propio paréntesis: «100 preguntas (+10 de reserva) · 120
 * min». Sumarlas daba «110 preguntas», y eso no es lo que uno se encuentra al empezar: son cien las
 * que se contestan y diez las que están por si falla alguna. El propietario lo leyó como un error y
 * lo era de cuenta, no de datos.
 *
 * «min» y no «minutos» porque es una cifra en una línea de opción, no una frase; el dato completo
 * —con su tiempo por parte— sigue en «Qué va a caer».
 */
function resumenDe(variante: StudentMockExamVariant): string {
  const ordinarias = variante.parts.reduce((total, parte) => total + (parte.ordinary_items ?? 0), 0);
  const reserva = variante.parts.reduce((total, parte) => total + (parte.reserve_items ?? 0), 0);
  const duracion =
    variante.time_limit_minutes === null ? 'sin tiempo' : `${String(variante.time_limit_minutes)} min`;
  const preguntas =
    reserva === 0
      ? `${String(ordinarias)} preguntas`
      : `${String(ordinarias)} preguntas (+${String(reserva)} de reserva)`;
  return `${preguntas} · ${duracion}`;
}
