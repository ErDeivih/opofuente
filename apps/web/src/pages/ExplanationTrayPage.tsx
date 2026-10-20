import { usePendingExplanations } from '../api/queries';

/**
 * La bandeja de explicaciones generadas (M1 de la fase 3).
 *
 * **Lo que enseña**: la cola de trabajo del propietario — las explicaciones que un modelo escribió y que
 * nadie ha revisado —, **con el enunciado de su pregunta y la cita literal de los apuntes**. El enunciado
 * viaja con cada fila para que se pueda decidir sin abrir otra pantalla; aprobar a ciegas es lo que esta
 * bandeja existe para evitar.
 *
 * **Lo que todavía no hace**: aprobar, editar ni regenerar. **Las tres necesitan sus rutas de escritura**
 * (`status`, el texto, una llamada al modelo) y **hoy solo existe la de lectura**. Están apuntadas en
 * `docs/hitos/M1.md` como lo que falta de este hito.
 *
 * **Y no filtra nada aquí**: las privadas y las oficiales no salen porque **el servidor no las manda**.
 * Esconderlas en el cliente sería tener dos sitios donde se decide lo mismo.
 */
export function ExplanationTrayPage() {
  const consulta = usePendingExplanations();

  if (consulta.isLoading) {
    return <p>Cargando la bandeja…</p>;
  }
  if (consulta.isError) {
    return <p>No se ha podido leer la bandeja. Vuelve a intentarlo.</p>;
  }

  const filas = consulta.data ?? [];
  if (filas.length === 0) {
    return <p>No hay explicaciones generadas esperando revisión.</p>;
  }

  return (
    <section>
      <h1>Bandeja de explicaciones</h1>
      <p>
        {filas.length === 1
          ? 'Una explicación generada espera revisión.'
          : `${String(filas.length)} explicaciones generadas esperan revisión.`}
      </p>
      <ol>
        {filas.map((fila) => (
          <li key={fila.explanation.id}>
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
