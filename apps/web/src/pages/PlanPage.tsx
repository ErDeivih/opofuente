/**
 * El plan entero, semana a semana (M4 de la fase 3).
 *
 * **«Hoy» enseña la semana en curso; esta pantalla, el calendario completo.** Se abre desde el enlace
 * del plan y **sigue ahí al recargar**: el plan no es una respuesta que se pinta una vez y se pierde,
 * es lo que el alumno acordó con la fecha de su examen.
 *
 * **Los temas que no caben se nombran**: un plan que dice «3 temas fuera» y no dice cuáles no se
 * puede discutir ni corregir. El modo —extensivo o intensivo— y los recortes por horas también se
 * enseñan, porque son decisiones que el alumno tiene que poder entender.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { Link } from 'react-router-dom';

import {
  fetchCalendario,
  fetchPlanGuardado,
  guardarPlan,
  type PlanGuardado,
  type Semana as SemanaDelPlan,
  type Tarea,
  type TipoDeTarea,
} from '../api/plan';
import { destinoDeTarea } from '../features/plan/destino';

/** Los días de la semana, con el índice que usa el servidor (0 es lunes). */
const DIAS = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo'];

const ETIQUETA: Record<TipoDeTarea, string> = {
  leer: 'Leer',
  test: 'Test',
  repaso: 'Repaso',
  supuesto: 'Supuesto',
  simulacro: 'Simulacro',
};

/** El formulario de la fecha, **el mismo con plan y sin él**. */
function FormularioPlan({ guardado }: { guardado: PlanGuardado }) {
  const cliente = useQueryClient();
  const [fecha, setFecha] = useState(guardado.exam_date ?? '');
  const [horas, setHoras] = useState(guardado.hours_per_week ?? 10);
  const [descanso, setDescanso] = useState(guardado.rest_days[0] ?? 6);

  const poner = useMutation({
    mutationFn: () => guardarPlan(fecha, horas, [descanso]),
    onSuccess: () => {
      void cliente.invalidateQueries({ queryKey: ['plan'] });
    },
  });

  return (
    <form
      className="hoy__formulario"
      onSubmit={(evento) => {
        evento.preventDefault();
        poner.mutate();
      }}
    >
      <label>
        Fecha del examen
        <input
          type="date"
          value={fecha}
          onChange={(evento) => setFecha(evento.target.value)}
          required
        />
      </label>
      <label>
        Horas por semana
        <input
          type="number"
          min={1}
          max={80}
          value={horas}
          onChange={(evento) => setHoras(Number(evento.target.value))}
        />
      </label>
      <label>
        Día de descanso
        <select value={descanso} onChange={(evento) => setDescanso(Number(evento.target.value))}>
          {DIAS.map((dia, indice) => (
            <option key={dia} value={indice}>
              {dia}
            </option>
          ))}
        </select>
      </label>
      <button type="submit" disabled={poner.isPending || fecha === ''}>
        {poner.isPending ? 'Calculando…' : 'Calcular el plan'}
      </button>
      {poner.isError && <p className="hoy__error">No se pudo calcular el plan.</p>}
    </form>
  );
}

function ListaDeTareas({ tareas }: { tareas: Tarea[] }) {
  if (tareas.length === 0) {
    return <p className="plan__vacia">Esta semana no tiene tareas: el plan cuenta con el descanso.</p>;
  }
  return (
    <ul className="plan__tareas">
      {tareas.map((tarea) => (
        <li key={`${tarea.tipo}-${tarea.codigo ?? tarea.titulo}`} className="plan__tarea">
          <span className="plan__tipo">{ETIQUETA[tarea.tipo]}</span>
          <Link to={destinoDeTarea(tarea)} className="plan__enlace">
            {tarea.titulo}
          </Link>
          <span className="plan__minutos">{tarea.minutos} min</span>
        </li>
      ))}
    </ul>
  );
}

function Semana({ semana }: { semana: SemanaDelPlan }) {
  return (
    <section className="plan__semana" aria-labelledby={`semana-${semana.numero}`}>
      <header className="plan__semana__cabecera">
        <h2 id={`semana-${semana.numero}`}>Semana {semana.numero}</h2>
        <span className="plan__fase">
          {semana.fase === 'fase-2' ? 'Repaso y simulacro' : 'Lectura'}
        </span>
        <span className="plan__empieza">empieza el {semana.empieza}</span>
      </header>
      {semana.recortes.map((recorte) => (
        <p key={recorte} className="plan__recorte">
          {recorte}
        </p>
      ))}
      <ListaDeTareas tareas={semana.tareas} />
    </section>
  );
}

export function PlanPage() {
  const guardado = useQuery({ queryKey: ['plan', 'guardado'], queryFn: fetchPlanGuardado });
  const calendario = useQuery({
    queryKey: ['plan', 'calendario'],
    queryFn: fetchCalendario,
    enabled: guardado.data?.exam_date != null,
    retry: false,
  });

  if (guardado.isPending) {
    return (
      <section className="plan">
        <h1>Plan</h1>
        <p className="hoy__vacio">Cargando el plan…</p>
      </section>
    );
  }

  if (guardado.isError) {
    return (
      <section className="plan">
        <h1>Plan</h1>
        <p className="hoy__error">No se pudo leer el plan. Reintenta en un momento.</p>
      </section>
    );
  }

  if (guardado.data.exam_date == null) {
    return (
      <section className="plan plan--sin-plan">
        <h1>Plan</h1>
        <p className="hoy__motivo">
          Para repartir los temas hace falta la fecha del examen. Elige una y el plan se calcula solo.
        </p>
        <FormularioPlan guardado={guardado.data} />
      </section>
    );
  }

  if (calendario.isPending) {
    return (
      <section className="plan">
        <h1>Plan</h1>
        <p className="hoy__vacio">Cargando el calendario…</p>
      </section>
    );
  }

  if (calendario.isError || calendario.data === undefined) {
    return (
      <section className="plan">
        <h1>Plan</h1>
        <p className="hoy__error">No se pudo leer el calendario. Reintenta en un momento.</p>
        <p>
          <Link to="/">Volver a Hoy</Link>
        </p>
      </section>
    );
  }

  const plan = calendario.data;

  return (
    <section className="plan">
      <header className="plan__cabecera">
        <div>
          <h1>Plan</h1>
          <p className="plan__resumen">
            Examen el {guardado.data.exam_date} · {guardado.data.hours_per_week ?? '—'} h por semana ·{' '}
            <strong>{plan.modo === 'extensivo' ? 'modo extensivo' : 'modo intensivo'}</strong>
          </p>
        </div>
        <Link to="/">Volver a Hoy</Link>
      </header>

      <p className="plan__cuenta">
        {plan.total_semanas} semanas: {plan.semanas_de_lectura} de lectura
        {plan.fase_2_desde != null && ' y el resto de repaso y simulacros'}.
      </p>

      {!plan.planificable && (
        <section className="plan__aviso" role="status">
          <h2>No cabe todo con ese ritmo</h2>
          <p>{plan.motivo}</p>
        </section>
      )}

      {plan.fuera_temas.length > 0 && (
        <section className="plan__fuera" aria-labelledby="plan-fuera">
          <h2 id="plan-fuera">Se quedan fuera del plan</h2>
          <p>
            No entran antes del examen. Se nombran para que puedas decidir si amplías las horas, mueves
            la fecha o los dejas para otra convocatoria.
          </p>
          <ul>
            {plan.fuera_temas.map((tema) => (
              <li key={tema.codigo}>
                <strong>{tema.codigo}</strong> · {tema.titulo}
                {tema.bloque_titulo !== '' && (
                  <span className="plan__bloque"> ({tema.bloque_titulo})</span>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}

      <div className="plan__semanas">
        {plan.semanas.map((semana) => (
          <Semana key={semana.numero} semana={semana} />
        ))}
      </div>

      <details className="plan__cambiar">
        <summary>Cambiar la fecha del examen o las horas</summary>
        <FormularioPlan guardado={guardado.data} />
      </details>
    </section>
  );
}
