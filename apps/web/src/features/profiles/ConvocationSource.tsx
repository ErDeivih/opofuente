import type { ConvocationDetail } from '../../api/profiles';

export interface ConvocationSourceProps {
  convocation: ConvocationDetail;
}

/**
 * Procedencia de los datos: enlace oficial, fecha de publicación y referencia del acto.
 * Es obligatorio mostrarlo (07_UI-UX §6 y 09_SECURITY-PRIVACY-AND-RIGHTS §8: atribución, URL,
 * fecha y licencia) y también aclarar que OpoFuente no es una publicación oficial.
 */
export function ConvocationSource({ convocation }: ConvocationSourceProps) {
  return (
    <section className="card" aria-labelledby="procedencia">
      <h2 id="procedencia">Procedencia oficial</h2>
      <p className="source__title">{convocation.title}</p>
      <dl className="facts">
        <dt>Publicación</dt>
        <dd>
          <time dateTime={convocation.published_at}>{convocation.published_at}</time>
        </dd>
        <dt>Fuente</dt>
        <dd>
          <a href={convocation.official_url} target="_blank" rel="noreferrer noopener">
            {convocation.source_reference ?? convocation.official_url}
          </a>
        </dd>
        <dt>Fecha del examen</dt>
        <dd>
          {convocation.exam_date === null || convocation.exam_date === undefined ? (
            <span className="hint">No consta en la convocatoria</span>
          ) : (
            <time dateTime={convocation.exam_date}>{convocation.exam_date}</time>
          )}
        </dd>
      </dl>
      {convocation.exam_date_note != null && convocation.exam_date_note.length > 0 && (
        // La nota explica de dónde sale la fecha —o por qué no hay ninguna—: «no consta» a secas se
        // lee igual cuando falta el dato que cuando la convocatoria lo deja para otra resolución.
        <p className="hint">{convocation.exam_date_note}</p>
      )}
      <p className="hint">
        Los datos se extraen de la publicación oficial. OpoFuente no es un organismo oficial y esta
        pantalla no sustituye a la convocatoria: ante cualquier duda, prevalece el texto publicado.
      </p>
    </section>
  );
}
