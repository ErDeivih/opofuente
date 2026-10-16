import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

import {
  getStudentSyllabus,
  getStudentTestPlan,
  type StudentBlockProgress,
  type StudentSyllabus,
  type StudentTopicProgress,
} from '../../api/studentStudy';
import {
  createStudentTest,
  type StudentFeedback,
  type StudentFilter,
} from '../../api/studentTests';
import { ErrorState } from '../../components/ErrorState';
import { LoadingState } from '../../components/LoadingState';
import { describeError } from '../../features/system/labels';
import { formatearPorcentaje } from '../../lib/numeros';

/**
 * La pantalla de Tests (F22): elegir y empezar.
 *
 * Es la que faltaba de la zona del alumno, y existe porque los enlaces ya estaban: Inicio manda aquí
 * su «Test rápido de 20» (`?count=20`), el Temario el test de un tema (`?tema=IV.1`) y la pestaña
 * «Preguntas» del tema hace lo mismo. Una pantalla que ignorara esos parámetros sería peor que la
 * pantalla que había: enseñaría el formulario en blanco después de haberle pedido algo concreto. Por
 * eso los dos se leen, y se leen **de la dirección**, no de un estado que se pierda al recargar.
 *
 * Lo que se elige aquí es lo que el alumno necesita decidir antes de empezar: **de qué temas**,
 * **cuántas preguntas**, **cuáles** (todas, las que no ha visto, las que falló o las que marcó
 * dudosas), **cómo se corrigen** (al responder o al terminar) y **si lleva el reloj del test**.
 *
 * Tres cosas que esta pantalla **no** hace, a propósito:
 *
 * 1. **no compone el test**: manda el formulario a `POST /student/tests` y el motor compone con la
 *    misma forma que en cualquier otra sesión;
 * 2. **no calcula el reloj**: los minutos de cada tamaño salen del plan del servidor, que es el mismo
 *    que después pone el límite de la sesión. Una regla escrita dos veces se separa;
 * 3. **no decide qué se puede preguntar**: los temas, sus preguntas disponibles y lo que ya se ha
 *    contestado en cada uno vienen del temario de la API. Un tema sin preguntas no se puede marcar, y
 *    se dice por qué en vez de dejar una casilla que no hace nada.
 */
export function TestsPage() {
  const navegar = useNavigate();
  const cliente = useQueryClient();
  const [parametros] = useSearchParams();

  const plan = useQuery({ queryKey: ['student-test-plan'], queryFn: getStudentTestPlan });
  const temario = useQuery({ queryKey: ['student-syllabus'], queryFn: getStudentSyllabus });

  // Lo que pide la dirección. Puede venir más de un tema (`?tema=IV.1&tema=IV.2`) y viene del
  // Temario, del propio tema y del atajo de Inicio; el `count`, solo de Inicio.
  const temasDeLaDireccion = parametros.getAll('tema').join(',');
  const cuentaDeLaDireccion = parametros.get('count');

  // La elección del alumno manda en cuanto la hace (`null` = todavía no ha tocado nada, así que vale
  // lo que diga la dirección). Se guarda el `null` y no una copia ya resuelta para que un temario que
  // llega después no pise lo que la persona acaba de marcar.
  const [elegidos, setElegidos] = useState<readonly string[] | null>(null);
  const [cuenta, setCuenta] = useState<number | null>(null);
  const [filtro, setFiltro] = useState<StudentFilter>('all');
  const [correccion, setCorreccion] = useState<StudentFeedback>('immediate');
  const [reloj, setReloj] = useState(false);

  const seleccion = useMemo(
    () => elegidos ?? codigosDeLaDireccion(temario.data, temasDeLaDireccion),
    [elegidos, temario.data, temasDeLaDireccion],
  );
  const cuentaElegida = useMemo(
    () => cuenta ?? cuentaInicial(cuentaDeLaDireccion, plan.data?.counts ?? []),
    [cuenta, cuentaDeLaDireccion, plan.data],
  );

  const empezar = useMutation({
    mutationFn: () =>
      createStudentTest({
        nodes: [...seleccion],
        count: cuentaElegida,
        filter: filtro,
        feedback: correccion,
        timed: reloj,
      }),
    onSuccess: (sesion) => {
      void cliente.invalidateQueries({ queryKey: ['student-overview'] });
      void navegar(`/test/${sesion.id}`);
    },
  });

  if (plan.isPending || temario.isPending) {
    return (
      <>
        <h1 className="pagina__titulo">Tests</h1>
        <LoadingState label="Mirando qué se puede preguntar…" />
      </>
    );
  }
  if (plan.isError || temario.isError) {
    const error = plan.error ?? temario.error;
    return (
      <>
        <h1 className="pagina__titulo">Tests</h1>
        <ErrorState
          title="No se pudo preparar el test"
          message={describeError(error)}
          onRetry={() => {
            void plan.refetch();
            void temario.refetch();
          }}
        />
      </>
    );
  }

  const bloques = temario.data.blocks;
  const temas = bloques.flatMap((bloque) => bloque.topics);
  const disponibles = temas
    .filter((tema) => seleccion.includes(tema.code))
    .reduce((total, tema) => total + tema.available_questions, 0);
  const minutosDelReloj =
    plan.data.counts.find((opcion) => opcion.questions === cuentaElegida)?.minutes ?? null;

  return (
    <>
      <header className="pagina__cabecera">
        <h1 className="pagina__titulo">Tests</h1>
        <p className="pagina__entrada">
          Tú eliges de qué temas, cuántas preguntas y cómo se corrigen. No es un examen: no hay nota.
        </p>
      </header>

      <section className="bloque" aria-labelledby="de-que">
        <h2 className="bloque__titulo" id="de-que">
          De qué temas
        </h2>
        <p className="bloque__texto">
          Marca uno o varios temas. Un test puede mezclar temas de bloques distintos.
        </p>
        <ul className="elegir-temas" aria-label="Temas de los que puede salir el test">
          {bloques.map((bloque) => (
            <BloqueElegible
              key={bloque.code}
              bloque={bloque}
              seleccion={seleccion}
              onCambiar={setElegidos}
            />
          ))}
        </ul>
      </section>

      <section className="bloque" aria-labelledby="cuantas">
        <h2 className="bloque__titulo" id="cuantas">
          Cuántas preguntas
        </h2>
        <div className="opciones" role="radiogroup" aria-labelledby="cuantas">
          {plan.data.counts.map((opcion) => (
            <div className="opcion" key={opcion.questions}>
              <input
                id={`cuenta-${String(opcion.questions)}`}
                type="radio"
                name="cuenta"
                value={opcion.questions}
                checked={cuentaElegida === opcion.questions}
                onChange={() => setCuenta(opcion.questions)}
              />
              <label className="opcion__texto" htmlFor={`cuenta-${String(opcion.questions)}`}>
                <span className="opcion__titulo">{`${String(opcion.questions)} preguntas`}</span>
                <span className="opcion__detalle">{`${String(opcion.minutes)} minutos con el reloj`}</span>
              </label>
            </div>
          ))}
        </div>
      </section>

      <section className="bloque" aria-labelledby="cuales">
        <h2 className="bloque__titulo" id="cuales">
          Qué preguntas
        </h2>
        <div className="opciones" role="radiogroup" aria-labelledby="cuales">
          {(Object.keys(ETIQUETA_FILTRO) as StudentFilter[]).map((cual) => (
            <div className="opcion" key={cual}>
              <input
                id={`filtro-${cual}`}
                type="radio"
                name="filtro"
                value={cual}
                checked={filtro === cual}
                onChange={() => setFiltro(cual)}
              />
              <label className="opcion__texto" htmlFor={`filtro-${cual}`}>
                <span className="opcion__titulo">{ETIQUETA_FILTRO[cual].titulo}</span>
                <span className="opcion__detalle">{ETIQUETA_FILTRO[cual].detalle}</span>
              </label>
            </div>
          ))}
        </div>
      </section>

      <section className="bloque" aria-labelledby="correccion">
        <h2 className="bloque__titulo" id="correccion">
          Cómo se corrigen
        </h2>
        <div className="opciones" role="radiogroup" aria-labelledby="correccion">
          {(Object.keys(ETIQUETA_CORRECCION) as StudentFeedback[]).map((modo) => (
            <div className="opcion" key={modo}>
              <input
                id={`correccion-${modo}`}
                type="radio"
                name="correccion"
                value={modo}
                checked={correccion === modo}
                onChange={() => setCorreccion(modo)}
              />
              <label className="opcion__texto" htmlFor={`correccion-${modo}`}>
                <span className="opcion__titulo">{ETIQUETA_CORRECCION[modo].titulo}</span>
                <span className="opcion__detalle">{ETIQUETA_CORRECCION[modo].detalle}</span>
              </label>
            </div>
          ))}
        </div>
      </section>

      <section className="bloque" aria-labelledby="reloj">
        <h2 className="bloque__titulo" id="reloj">
          El tiempo
        </h2>
        <div className="opciones">
          <div className="opcion">
            <input
              id="poner-reloj"
              type="checkbox"
              checked={reloj}
              onChange={(evento) => setReloj(evento.target.checked)}
            />
            <label className="opcion__texto" htmlFor="poner-reloj">
              <span className="opcion__titulo">Poner el reloj del test</span>
              <span className="opcion__detalle">
                {minutosDelReloj === null
                  ? 'El límite que corresponda a este tamaño.'
                  : `${String(minutosDelReloj)} minutos para ${String(cuentaElegida)} preguntas.`}
              </span>
            </label>
          </div>
        </div>
        {/* Lo que pasa **sin** el reloj no es «sin tiempo»: el test hereda el tiempo de la parte del
            examen con la que se corrige este material. Se dice con la cifra que trae el plan; si la
            convocatoria no lo publica, se dice que no está en lugar de suponer que no hay ninguno. */}
        {!reloj && (
          <p className="bloque__texto">
            {plan.data.convocation_minutes === null
              ? 'Sin el reloj del test, el examen tampoco publica un tiempo para este material.'
              : `Sin el reloj del test manda el tiempo del examen: ${String(plan.data.convocation_minutes)} minutos.`}
          </p>
        )}
        <p className="resultado__aviso">{plan.data.timed_note}</p>
      </section>

      <p className="resumen-test" role="status">
        {resumenDe(seleccion.length, disponibles, cuentaElegida)}
      </p>

      <p className="acciones">
        <button
          type="button"
          className="ui-button ui-button--primary"
          onClick={() => {
            empezar.mutate();
          }}
          disabled={seleccion.length === 0 || disponibles === 0 || empezar.isPending}
        >
          Empezar el test
        </button>
      </p>
      {empezar.isError && (
        <ErrorState title="No se pudo montar el test" message={describeError(empezar.error)} />
      )}
    </>
  );
}

/**
 * Un bloque del temario con sus temas, cada uno con lo que se puede preguntar y lo que ya se ha
 * contestado. La casilla del bloque marca y desmarca todos sus temas con preguntas.
 */
function BloqueElegible({
  bloque,
  seleccion,
  onCambiar,
}: {
  bloque: StudentBlockProgress;
  seleccion: readonly string[];
  onCambiar: (codigos: readonly string[]) => void;
}) {
  const elegibles = bloque.topics.filter((tema) => tema.available_questions > 0);
  const marcados = elegibles.filter((tema) => seleccion.includes(tema.code));
  const todos = elegibles.length > 0 && marcados.length === elegibles.length;
  const casilla = useRef<HTMLInputElement>(null);

  // Media marca (`indeterminate`) no se puede poner por atributo: es una propiedad del elemento, y
  // sin ella un bloque con un tema de tres marcado se leería como «vacío».
  useEffect(() => {
    if (casilla.current !== null) {
      casilla.current.indeterminate = marcados.length > 0 && !todos;
    }
  }, [marcados.length, todos]);

  const alternarBloque = (): void => {
    const codigos = new Set(seleccion);
    for (const tema of elegibles) {
      if (todos) {
        codigos.delete(tema.code);
      } else {
        codigos.add(tema.code);
      }
    }
    onCambiar([...codigos]);
  };

  return (
    <li className="elegir-temas__bloque" data-bloque={bloque.code}>
      <div className="elegir-temas__cabecera">
        <p className="elegir-temas__romano" aria-hidden="true">
          {bloque.code}
        </p>
        <h3 className="elegir-temas__titulo-bloque" data-contenido>
          {bloque.title}
        </h3>
      </div>
      <div className="elegir-temas__marcar-todo">
        <input
          id={`bloque-${bloque.code}`}
          ref={casilla}
          type="checkbox"
          checked={todos}
          disabled={elegibles.length === 0}
          onChange={alternarBloque}
        />
        <label htmlFor={`bloque-${bloque.code}`}>
          {elegibles.length === 0
            ? 'Este bloque todavía no tiene preguntas'
            : `Todo el bloque (${String(elegibles.length)} temas)`}
        </label>
      </div>
      <ul className="elegir-temas__lista">
        {bloque.topics.map((tema) => (
          <FilaDeTema
            key={tema.code}
            tema={tema}
            marcado={seleccion.includes(tema.code)}
            onCambiar={onCambiar}
            seleccion={seleccion}
          />
        ))}
      </ul>
    </li>
  );
}

/** Un tema: casilla, título, lo que hay para preguntar y lo que ya se ha contestado. */
function FilaDeTema({
  tema,
  marcado,
  seleccion,
  onCambiar,
}: {
  tema: StudentTopicProgress;
  marcado: boolean;
  seleccion: readonly string[];
  onCambiar: (codigos: readonly string[]) => void;
}) {
  const sinPreguntas = tema.available_questions === 0;
  const identificador = `tema-${tema.code}`;

  return (
    <li className="elegir-temas__fila">
      <input
        id={identificador}
        type="checkbox"
        checked={marcado}
        disabled={sinPreguntas}
        onChange={() => {
          onCambiar(
            marcado
              ? seleccion.filter((codigo) => codigo !== tema.code)
              : [...seleccion, tema.code],
          );
        }}
      />
      <label className="elegir-temas__texto" htmlFor={identificador}>
        <span className="elegir-temas__titulo">
          <span className="elegir-temas__codigo">{tema.code}</span>{' '}
          <span data-contenido>{tema.title}</span>
        </span>
        <span className="elegir-temas__datos">
          <span>
            {sinPreguntas
              ? 'Sin preguntas todavía'
              : `${String(tema.available_questions)} preguntas disponibles`}
          </span>
          <span>{contestadoDe(tema)}</span>
        </span>
      </label>
    </li>
  );
}

/** Los nombres del formulario. El vocabulario del servidor no se traduce a otro: se explica. */
const ETIQUETA_FILTRO: Record<StudentFilter, { titulo: string; detalle: string }> = {
  all: { titulo: 'Todas', detalle: 'Todo lo que hay en los temas elegidos.' },
  unseen: { titulo: 'Las que no he visto', detalle: 'Solo lo que no ha salido en ningún test.' },
  failed: { titulo: 'Las que he fallado', detalle: 'Lo que fallaste la última vez que lo viste.' },
  flagged: {
    titulo: 'Las que marqué dudosas',
    detalle: 'Lo que dejaste marcado como dudoso al contestarlo.',
  },
};

const ETIQUETA_CORRECCION: Record<StudentFeedback, { titulo: string; detalle: string }> = {
  immediate: { titulo: 'Al responder', detalle: 'Ves lo que has acertado nada más contestar.' },
  at_end: { titulo: 'Al terminar', detalle: 'No ves la corrección hasta que cierras el test.' },
};

/**
 * Los temas que pide la dirección, en el orden del temario y sin repetir.
 *
 * Un código que no existe se queda fuera: el temario es la lista de lo que hay, y marcar un tema que
 * no está sería prometer un test que no se puede montar. Se acepta `IV-10` además de `IV.10`, que es
 * como escribe el código media aplicación.
 */
function codigosDeLaDireccion(temario: StudentSyllabus | undefined, crudos: string): string[] {
  if (temario === undefined || crudos.trim() === '') {
    return [];
  }
  const pedidos = new Set(
    crudos
      .split(',')
      .map((codigo) => codigo.trim().toUpperCase())
      .filter((codigo) => codigo !== '')
      .map((codigo) => codigo.replace('-', '.')),
  );
  return temario.blocks
    .flatMap((bloque) => bloque.topics)
    .filter((tema) => pedidos.has(tema.code.toUpperCase()))
    .map((tema) => tema.code);
}

/**
 * El tamaño inicial: el de la dirección si es uno de los que se ofrecen, y si no, 25.
 *
 * No se recorta ni se redondea lo que pide la dirección: si `?count=37` no es un tamaño ofrecido, se
 * empieza por el de por defecto en lugar de montar en silencio un test de otra cosa. Los tamaños que
 * se ofrecen los publica el servidor; aquí no se inventa ninguno.
 */
function cuentaInicial(pedida: string | null, ofrecidas: readonly { questions: number }[]): number {
  const numeros = ofrecidas.map((opcion) => opcion.questions);
  const solicitada = Number(pedida);
  if (pedida !== null && numeros.includes(solicitada)) {
    return solicitada;
  }
  return numeros.includes(25) ? 25 : (numeros[0] ?? 20);
}

/** Lo que ya se ha contestado en un tema, con la cifra escrita o la verdad en palabras. */
function contestadoDe(tema: StudentTopicProgress): string {
  if (tema.answered === 0) {
    return 'Sin contestar todavía';
  }
  if (tema.accuracy === null) {
    return `Contestadas ${String(tema.answered)}`;
  }
  return `${String(tema.answered)} contestadas · ${formatearPorcentaje(tema.accuracy)} de acierto`;
}

/** El resumen de lo que se va a montar, con lo que de verdad hay. */
function resumenDe(temas: number, disponibles: number, cuenta: number): string {
  if (temas === 0) {
    return 'Elige al menos un tema para poder empezar.';
  }
  if (disponibles === 0) {
    return 'Los temas elegidos no tienen preguntas todavía: elige otros o espera a que se importen.';
  }
  const cabeza = `Test de ${String(cuenta)} preguntas de ${String(temas)} ${
    temas === 1 ? 'tema' : 'temas'
  }`;
  // Si no hay tantas como se piden, el motor monta el test con las que haya: se dice **antes** de
  // empezar, no después de ver un test más corto de lo pedido.
  return disponibles < cuenta
    ? `${cabeza}: solo hay ${String(disponibles)} disponibles, así que tendrá ${String(disponibles)}.`
    : `${cabeza}.`;
}
