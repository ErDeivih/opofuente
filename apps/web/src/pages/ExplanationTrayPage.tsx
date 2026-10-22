import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useCallback, useEffect, useState } from 'react';

import { decideExplanation, regenerateExplanation, type ExplanationDecision } from '../api/explanations';
import { usePendingExplanations } from '../api/queries';
import { setExplanation } from '../api/questions';

/**
 * La bandeja de explicaciones generadas (M1 de la fase 3).
 *
 * **Lo que enseña**: la cola de trabajo del propietario — las explicaciones que un modelo escribió y que
 * nadie ha revisado —, **con el enunciado de su pregunta y la cita literal de los apuntes**. El enunciado
 * viaja con cada fila para que se pueda decidir sin abrir otra pantalla; aprobar a ciegas es lo que esta
 * bandeja existe para evitar.
 *
 * **El teclado, con las guardas de `TopicReviewPage`**: no roba las teclas dentro de un campo —al editar,
 * las teclas son del campo—, ni en las listas anidadas, y los dígitos no son letras. **`j`/`k` mueven,
 * `a` aprueba, `r` rechaza y `e` abre el campo de editar.**
 *
 * **Editar empieza por el texto que ya hay**: el propietario corrige una explicación, no la escribe otra
 * vez. **Regenerar sí está** —la tecla g— y **es la única que gasta**: una llamada al modelo por
 * explicación, ~0,000024 $ con los datos de esta fase.
 *
 * **Y no filtra nada aquí**: las privadas y las oficiales no salen porque **el servidor no las manda**.
 * Esconderlas en el cliente sería tener dos sitios donde se decide lo mismo.
 */
export function ExplanationTrayPage() {
  const consulta = usePendingExplanations();
  const cliente = useQueryClient();
  const [cursor, setCursor] = useState(0);
  const [editando, setEditando] = useState<{ id: string; texto: string } | null>(null);

  const decidir = useMutation({
    mutationFn: ({ id, decision }: { id: string; decision: ExplanationDecision }) =>
      decideExplanation(id, decision),
    // La lista se vuelve a pedir al decidir: treinta segundos de `staleTime` no bastan para ver que la
    // fila se ha ido, y una bandeja que sigue enseñando lo aprobado no es una bandeja.
    onSuccess: () => {
      void cliente.invalidateQueries({ queryKey: ['explanations', 'pending'] });
      setCursor(0);
    },
  });

  const regenerar = useMutation({
    mutationFn: (id: string) => regenerateExplanation(id),
    // La fila cambia de texto al regenerar, así que se vuelve a pedir la cola: un `staleTime` de
    // treinta segundos enseñaría la versión vieja justo cuando el propietario acaba de pedir la nueva.
    onSuccess: () => {
      void cliente.invalidateQueries({ queryKey: ['explanations', 'pending'] });
    },
  });

  const guardar = useMutation({
    mutationFn: ({ questionId, texto }: { questionId: string; texto: string }) =>
      setExplanation(questionId, { text: texto, optionStableKey: null }),
    onSuccess: () => {
      void cliente.invalidateQueries({ queryKey: ['explanations', 'pending'] });
      setEditando(null);
    },
  });

  const filas = consulta.data ?? [];
  const actual = filas[cursor];

  const alPulsar = useCallback(
    (event: KeyboardEvent) => {
      const objetivo = event.target;
      // Guarda 1: dentro de un campo, las teclas son del campo.
      if (
        objetivo instanceof HTMLElement &&
        objetivo.closest('input, textarea, select, [contenteditable="true"]') !== null
      ) {
        return;
      }
      const tecla = event.key.toLowerCase();
      const mover = (destino: number) => {
        event.preventDefault();
        setCursor(Math.min(Math.max(destino, 0), Math.max(filas.length - 1, 0)));
      };
      if (tecla === 'j' || tecla === 'arrowdown') {
        mover(cursor + 1);
        return;
      }
      if (tecla === 'k' || tecla === 'arrowup') {
        mover(cursor - 1);
        return;
      }
      if (actual === undefined) {
        return;
      }
      if (tecla === 'a') {
        event.preventDefault();
        decidir.mutate({ id: actual.explanation.id, decision: 'reviewed' });
        return;
      }
      if (tecla === 'r') {
        event.preventDefault();
        decidir.mutate({ id: actual.explanation.id, decision: 'rejected' });
        return;
      }
      if (tecla === 'g') {
        // **Gasta**: una llamada al modelo. El aviso va en la pantalla, no aquí.
        event.preventDefault();
        regenerar.mutate(actual.explanation.id);
        return;
      }
      if (tecla === 'e') {
        event.preventDefault();
        setEditando({ id: actual.question_version_id, texto: actual.explanation.text });
      }
    },
    [actual, cursor, decidir, filas.length, regenerar],
  );

  useEffect(() => {
    window.addEventListener('keydown', alPulsar);
    return () => window.removeEventListener('keydown', alPulsar);
  }, [alPulsar]);

  if (consulta.isLoading) {
    return <p>Cargando la bandeja…</p>;
  }
  if (consulta.isError) {
    return <p>No se ha podido leer la bandeja. Vuelve a intentarlo.</p>;
  }
  if (filas.length === 0) {
    return <p>No hay explicaciones generadas esperando revisión.</p>;
  }

  return (
    <section>
      <h1>Bandeja de explicaciones</h1>
      <p>
        {filas.length === 1
          ? 'Una explicación generada espera revisión.'
          : `${String(filas.length)} explicaciones generadas esperan revisión.`}{' '}
        <span className="hint">
          j y k se mueven · a aprueba · r rechaza · e edita · g regenera (gasta)
        </span>
      </p>
      {editando !== null && (
        <form
          onSubmit={(evento) => {
            evento.preventDefault();
            guardar.mutate({ questionId: editando.id, texto: editando.texto });
          }}
        >
          <label htmlFor="explicacion-editada">La explicación, corregida</label>
          <textarea
            id="explicacion-editada"
            value={editando.texto}
            rows={4}
            onChange={(evento) => setEditando({ id: editando.id, texto: evento.target.value })}
          />
          <button type="submit" disabled={guardar.isPending}>
            Guardar
          </button>
          <button type="button" onClick={() => setEditando(null)}>
            Cancelar
          </button>
        </form>
      )}
      <ol>
        {filas.map((fila, indice) => (
          <li
            key={fila.explanation.id}
            className={indice === cursor ? 'resultado__pregunta' : undefined}
            data-en-el-cursor={indice === cursor ? 'si' : undefined}
          >
            <p>
              <strong>{fila.stem}</strong>
            </p>
            <p>{fila.explanation.text}</p>
            {fila.explanation.citation !== null && fila.explanation.citation !== undefined && (
              <blockquote>«{fila.explanation.citation}»</blockquote>
            )}
          </li>
        ))}
      </ol>
    </section>
  );
}
