/**
 * «Hoy»: lo que toca hacer, en tres a cinco tareas (M4 de la fase 3).
 *
 * **Sustituye a Inicio como pantalla principal.** Lo que enseña no es un resumen del progreso sino
 * **cosas concretas que hacer**, cada una con su botón a la pantalla que toca: leer un tema, hacer un
 * test, repasar tarjetas o un simulacro.
 *
 * **Si no hay plan, lo dice y pide la fecha**: no inventa tareas ni supone una fecha a seis meses. **Un
 * plan que aparece solo porque el servidor supuso algo es un plan que el alumno no acordó.**
 *
 * **Y el botón lleva a la pantalla correcta, no a una genérica**: una tarea de leer lleva a sus
 * apuntes, una de test al test de ese tema, y un simulacro a simulacros. Si el botón llevara a Inicio,
 * la tarea no se podría tachar «sola» —que es lo que el hito pide—.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { Link } from 'react-router-dom';

import { fetchHoy, fetchPlanGuardado, guardarPlan, type Tarea } from '../api/plan';

/** A dónde lleva cada tipo de tarea. */
function destino(tarea: Tarea): string {
  switch (tarea.tipo) {
    case 'leer':
      return `/temario/${tarea.codigo ?? ''}`;
    case 'test':
      return `/tests?tema=${encodeURIComponent(tarea.codigo ?? '')}`;
    case 'repaso':
      return '/repaso';
    case 'simulacro':
      return '/simulacros';
  }
}

/** Los días de la semana, con el índice que usa el servidor (0 es lunes). */
const DIAS = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo'];

export function HoyPage() {
  const cliente = useQueryClient();
  const guardado = useQuery({ queryKey: ['plan', 'guardado'], queryFn: fetchPlanGuardado });
  const hoy = useQuery({ queryKey: ['plan', 'hoy'], queryFn: fetchHoy, staleTime: 0 });

  const [fecha, setFecha] = useState('');
  const [horas, setHoras] = useState(10);
  const [descanso, setDescanso] = useState<number>(6);

  const poner = useMutation({
    mutationFn: () => guardarPlan(fecha, horas, [descanso]),
    onSuccess: () => {
      void cliente.invalidateQueries({ queryKey: ['plan'] });
    },
  });

  if (guardado.isPending || hoy.isPending) {
    return <p className="hoy__vacio">Cargando lo de hoy…</p>;
  }

  if (guardado.isError || hoy.isError) {
    return <p className="hoy__error">No se pudo leer el plan. Reintenta en un momento.</p>;
  }

  // **Sin fecha no hay plan**: se pide, y se dice por qué.
  if (guardado.data?.exam_date == null) {
    return (
      <section className="hoy hoy--sin-plan">
        <h1>Hoy</h1>
        <p className="hoy__motivo">
          Para saber qué toca hoy hace falta la fecha del examen. Elige una y el plan reparte los temas
          que quedan.
        </p>
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
        </form>
        {poner.isError && <p className="hoy__error">No se pudo calcular el plan.</p>}
      </section>
    );
  }

  const semana = hoy.data?.semana ?? null;
  const tareas = semana?.tareas ?? [];

  if (semana === null) {
    return (
      <section className="hoy hoy--vacio">
        <h1>Hoy</h1>
        {(hoy.data?.motivos ?? ['no hay nada que hacer hoy']).map((motivo) => (
          <p key={motivo} className="hoy__motivo">
            {motivo}
          </p>
        ))}
      </section>
    );
  }

  // **Tres a cinco tareas**: si la semana trae más —un día con dos cosas—, se enseñan las cinco
  // primeras y se dice cuántas quedan. Una pantalla con quince tareas no se empieza.
  const visibles = tareas.slice(0, 5);
  const restantes = tareas.length - visibles.length;

  return (
    <section className="hoy">
      <header className="hoy__cabecera">
        <h1>Hoy</h1>
        <p className="hoy__semana">
          Semana {semana.numero} · empieza el {semana.empieza}
        </p>
      </header>

      {visibles.length === 0 ? (
        <p className="hoy__motivo">
          Esta semana no tiene tareas. Descansa: el plan cuenta con ello.
        </p>
      ) : (
        <ol className="hoy__tareas">
          {visibles.map((tarea) => (
            <li key={`${tarea.tipo}-${tarea.titulo}`} className="hoy__tarea">
              <Link to={destino(tarea)} className="hoy__enlace">
                {tarea.titulo}
              </Link>
              <span className="hoy__minutos">{tarea.minutos} min</span>
            </li>
          ))}
        </ol>
      )}

      {restantes > 0 && (
        <p className="hoy__resto">
          y {restantes} más esta semana, en el <Link to="/">plan</Link>
        </p>
      )}
    </section>
  );
}
