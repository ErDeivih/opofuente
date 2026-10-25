/**
 * La pantalla de repaso (M3 de la fase 3).
 *
 * **Con teclado, porque es una pantalla de repetición**: espacio para dar la vuelta y 1 a 4 para
 * responder. **Un repaso con ratón es un repaso que se abandona**: son sesenta tarjetas y cada clic es
 * una decisión que no aporta nada.
 *
 * **La cita se enseña siempre**, también en la cara de la pregunta: es lo que hace que la tarjeta se
 * pueda comprobar contra los apuntes. **Una tarjeta sin cita es una afirmación sin fuente.**
 *
 * **Y el número de lo que queda va arriba**: sesenta tarjetas sin saber cuántas llevas es la forma más
 * rápida de dejarlo a la mitad.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import {
  answerCard,
  corregirFallo,
  fetchCola,
  type CorreccionDeFallo,
  type FalloVencido,
  type Respuesta,
  type Tarjeta,
} from '../api/cards';

/** Las cuatro respuestas con su tecla, en el orden en que se enseñan. */
const RESPUESTAS: readonly { tecla: string; respuesta: Respuesta; etiqueta: string; pista: string }[] = [
  { tecla: '1', respuesta: 'otra_vez', etiqueta: 'Otra vez', pista: 'no me salía' },
  { tecla: '2', respuesta: 'dificil', etiqueta: 'Difícil', pista: 'con esfuerzo' },
  { tecla: '3', respuesta: 'bien', etiqueta: 'Bien', pista: 'me salía' },
  { tecla: '4', respuesta: 'facil', etiqueta: 'Fácil', pista: 'sin pensar' },
];

/** Lo que se tarda en volver a verla, dicho como se dice en voz alta. */
function cuandoVuelve(tarjeta: Tarjeta): string {
  const dias = tarjeta.interval_days;
  if (dias === 0) return 'hoy otra vez';
  if (dias === 1) return 'mañana';
  return `en ${dias} días`;
}

/**
 * **Los fallos vencidos del día, como preguntas de test** (fase «lo que ve el alumno», punto 3).
 *
 * Se contestan una a una: se elige una opción y **entonces** llegan el acierto, la letra que valía y
 * la explicación con su cita. **Antes de contestar no se dice nada**, que es lo que hace un test.
 */
function FallosDelDia({ fallos }: { fallos: FalloVencido[] }) {
  const [indice, setIndice] = useState(0);
  const [elegida, setElegida] = useState<string | null>(null);
  const corregir = useMutation<CorreccionDeFallo, Error, string>({
    mutationFn: (letra: string) =>
      corregirFallo(fallos[indice]?.question_version_id ?? '', letra),
    onSuccess: () => {
      setElegida(null);
    },
  });
  const fallo = fallos[indice];
  if (fallo === undefined) {
    return null;
  }
  const resultado = corregir.data;
  return (
    <section className="tarjeta" aria-live="polite">
      <p className="tarjeta__pista">
        Fallo {indice + 1} de {fallos.length}
      </p>
      <p className="tarjeta__anverso">{fallo.stem}</p>
      <ul className="repaso__acciones">
        {fallo.options.map((opcion: { key: string; text: string }) => (
          <li key={opcion.key}>
            <button
              type="button"
              className="repaso__boton"
              disabled={corregir.isPending}
              onClick={() => {
                setElegida(opcion.key);
                corregir.mutate(opcion.key);
              }}
            >
              <kbd>{opcion.key}</kbd> {opcion.text}
            </button>
          </li>
        ))}
      </ul>
      {resultado != null && (
        <div className="tarjeta__cita">
          <p>
            {resultado.correct ? 'Bien.' : 'No.'} La respuesta era{' '}
            <strong>{resultado.correct_option_keys.join(', ')}</strong>
            {elegida !== null && !resultado.correct ? ` y elegiste «${elegida}»` : ''}.
          </p>
          {resultado.explanation !== null && <p>{resultado.explanation}</p>}
          {resultado.citation !== null && <p>{resultado.citation}</p>}
          {indice + 1 < fallos.length && (
            <button
              type="button"
              className="ui-button"
              onClick={() => {
                setIndice((n) => n + 1);
                corregir.reset();
              }}
            >
              Siguiente fallo
            </button>
          )}
        </div>
      )}
    </section>
  );
}

export function RepasoPage() {
  const cliente = useQueryClient();
  const [vuelta, setVuelta] = useState(false);
  const [hechas, setHechas] = useState(0);
  //: Cuántas vuelven mañana: es la mitad útil del resumen.
  const [manana, setManana] = useState(0);
  const [aviso, setAviso] = useState<string | null>(null);

  const cola = useQuery({ queryKey: ['cards', 'queue'], queryFn: fetchCola, staleTime: 0 });

  const responder = useMutation({
    mutationFn: ({ id, respuesta }: { id: string; respuesta: Respuesta }) =>
      answerCard(id, respuesta),
    onSuccess: (tarjeta) => {
      setAviso(`Vuelve ${cuandoVuelve(tarjeta)}`);
      setHechas((n) => n + 1);
      if (cuandoVuelve(tarjeta) === 'mañana') {
        setManana((n) => n + 1);
      }
      setVuelta(false);
      void cliente.invalidateQueries({ queryKey: ['cards'] });
    },
    onError: () => setAviso('no se pudo guardar la respuesta: vuelve a intentarlo'),
  });

  const tarjetas = cola.data?.tarjetas ?? [];
  const actual = tarjetas[0];

  const alPulsar = useCallback(
    (event: KeyboardEvent) => {
      if (actual === undefined) return;
      if (event.key === ' ') {
        event.preventDefault();
        setVuelta((v) => !v);
        return;
      }
      // **Las respuestas solo cuentan con la tarjeta dada la vuelta**: contestar sin haber visto el
      // reverso no es un repaso, es un test de adivinación.
      if (!vuelta) return;
      const elegida = RESPUESTAS.find((opcion) => opcion.tecla === event.key);
      if (elegida === undefined) return;
      event.preventDefault();
      responder.mutate({ id: actual.id, respuesta: elegida.respuesta });
    },
    [actual, vuelta, responder],
  );

  useEffect(() => {
    window.addEventListener('keydown', alPulsar);
    return () => window.removeEventListener('keydown', alPulsar);
  }, [alPulsar]);

  if (cola.isPending) {
    return <p className="repaso__vacio">Cargando…</p>;
  }

  if (cola.isError) {
    return <p className="repaso__error">No se pudo cargar la cola. Reintenta en un momento.</p>;
  }

  if (actual === undefined) {
    return (
      <section className="repaso repaso--hecho">
        <h1>Repaso</h1>
        {hechas > 0 ? (
          <>
            {/* **El resumen al terminar**: cuántas han sido, cuántas vuelven mañana y por dónde
                seguir. Una pantalla que solo dice «hecho» deja al alumno sin saber qué ha pasado. */}
            <p className="repaso__hecho__total">
              Has repasado <strong>{hechas}</strong>{' '}
              {hechas === 1 ? 'tarjeta' : 'tarjetas'}.
            </p>
            <p className="repaso__cuenta">
              {manana === 0
                ? 'Ninguna vuelve mañana.'
                : `${String(manana)} ${manana === 1 ? 'vuelve' : 'vuelven'} mañana.`}
            </p>
            <p>
              <Link to="/">Volver a Hoy</Link>
            </p>
          </>
        ) : (
          <p className="repaso__cuenta">
            No hay tarjetas que repasar hoy. Vuelve mañana o ponte un test.
          </p>
        )}
        {cola.data?.fallos !== undefined && cola.data.fallos.length > 0 && (
          <FallosDelDia fallos={cola.data.fallos} />
        )}
        {aviso !== null && <p className="repaso__aviso">{aviso}</p>}
      </section>
    );
  }

  return (
    <section className="repaso">
      <header className="repaso__cabecera">
        <h1>Repaso</h1>
        <p className="repaso__cuenta">
          Quedan <strong>{tarjetas.length}</strong> de {cola.data?.total ?? 0} · hechas {hechas}
        </p>
      </header>

      <article className="tarjeta" aria-live="polite">
        <p className="tarjeta__anverso">{actual.front}</p>
        {vuelta ? (
          <p className="tarjeta__reverso">{actual.back}</p>
        ) : (
          <>
            <p className="tarjeta__pista">
              Pulsa <kbd>espacio</kbd> para ver la respuesta
            </p>
            {/* **Y un botón**, no solo el teclado: quien repasa con el móvil no tiene espacio. */}
            <button
              type="button"
              className="ui-button repaso__ver"
              onClick={() => {
                setVuelta(true);
              }}
            >
              Ver la respuesta
            </button>
          </>
        )}
        {actual.citation !== null && <blockquote className="tarjeta__cita">{actual.citation}</blockquote>}
      </article>

      <div className="repaso__acciones">
        {RESPUESTAS.map((opcion) => (
          <button
            key={opcion.tecla}
            type="button"
            className="repaso__boton"
            disabled={!vuelta || responder.isPending}
            onClick={() => responder.mutate({ id: actual.id, respuesta: opcion.respuesta })}
          >
            <kbd>{opcion.tecla}</kbd> {opcion.etiqueta}
            <span className="repaso__pista">{opcion.pista}</span>
          </button>
        ))}
      </div>

      {aviso !== null && <p className="repaso__aviso">{aviso}</p>}
    </section>
  );
}
