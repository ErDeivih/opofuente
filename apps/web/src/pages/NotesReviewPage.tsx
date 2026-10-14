import { Link } from 'react-router-dom';

import {
  NOTES_STATE_CLASS,
  NOTES_STATE_HELP,
  NOTES_STATE_LABELS,
  REVIEW_DECISION_LABELS,
  coveragePercent,
  thresholdPercent,
  type NotesReviewTopic,
} from '../api/notesReview';
import { useNotesReview } from '../api/queries';
import { ErrorState } from '../components/ErrorState';
import { LoadingState } from '../components/LoadingState';
import { describeError } from '../features/system/labels';

/**
 * La revisión de los apuntes (F24, §4.3 del objetivo): la tabla de los temas.
 *
 * Es la pantalla que faltaba del punto (4) del objetivo. Lo que hace, y nada más:
 *
 * 1. **enseña los temas con su estado** y, en los que esperan una decisión, **el motivo con su
 *    cifra**: el servidor manda cada razón ya escrita (`reasons[].text`) con el número aparte
 *    (`figure`), y aquí no se compone ninguna frase ni se recalcula ningún porcentaje que no salga del
 *    par de números que viaja en `coverage`;
 * 2. **dice qué espera una decisión** y qué no: los borradores son los que se revisan, y un tema
 *    publicado no vuelve a la lista de pendientes aunque su cobertura baje (ya pasó las puertas);
 * 3. **lleva a la ficha** de cada tema, que es donde se lee apartado a apartado y donde se aprueba o
 *    se rechaza. La fila no decide nada: una decisión se toma con el texto delante.
 *
 * La tabla **no mide los temas publicados** a propósito (el servidor no los mide): medir los quince
 * publicados costaría la mitad de la página para repetir lo que ya dice su estado. Su ficha sí los
 * mide, y por eso el estado es un enlace y no una etiqueta muerta.
 */
export function NotesReviewPage() {
  const revision = useNotesReview();

  if (revision.isPending) {
    return (
      <LoadingState label="Leyendo los apuntes guardados de cada tema y midiendo los borradores…" />
    );
  }
  if (revision.isError) {
    return (
      <ErrorState
        title="No se pudieron leer los apuntes"
        message={describeError(revision.error)}
        onRetry={() => {
          void revision.refetch();
        }}
      />
    );
  }

  const contadores = revision.data.counters;
  const temas = revision.data.topics;
  const conApuntes = temas.filter((tema) => tema.state !== 'none');
  const sinApuntes = temas.filter((tema) => tema.state === 'none');

  return (
    <>
      <header className="page__header">
        <h1>Apuntes</h1>
        <p className="page__lead">
          Los temas del programa con <strong>lo que ha medido el motor</strong> y lo que queda por
          decidir. Un tema en borrador se lee entero —no está escondido— y aquí se ve{' '}
          <strong>por qué</strong> no está publicado, con su cifra. Aprobar un tema que cumple las dos
          puertas lo publica; rechazarlo guarda tu motivo. Cada decisión queda auditada.
        </p>      </header>

      <section className="card" aria-labelledby="resumen-apuntes">
        <h2 id="resumen-apuntes">Cómo están los apuntes</h2>
        <p className="avisos__resumen">
          <strong>{contadores.pending_decision}</strong> esperan tu decisión
          <span className="hint">
            {' '}
            · {contadores.with_notes} tema(s) con apuntes: {contadores.published} publicado(s) y{' '}
            {contadores.draft} en borrador · {contadores.approved} aprobado(s) ·{' '}
            {contadores.rejected} rechazado(s) · {contadores.without_notes} sin apuntes escritos
          </span>
        </p>
        <p className="hint">
          El listón del §2.3 es el <strong>90 %</strong> de las preguntas que se pueden corregir y{' '}
          <strong>no se toca</strong>: aprobar un tema no convierte un 82 % en un 90 %. Lo que sí hace
          una aprobación es publicar el tema cuando las dos puertas pasan.
        </p>
      </section>

      <section className="card" aria-labelledby="temas-con-apuntes">
        <h2 id="temas-con-apuntes">
          Temas con apuntes <span className="hint">· {conApuntes.length} de {temas.length}</span>
        </h2>
        <ul className="apuntes-revision" aria-label="Temas con apuntes">
          {conApuntes.map((tema) => (
            <Fila key={tema.code} tema={tema} />
          ))}
        </ul>
      </section>

      {sinApuntes.length > 0 && (
        <section className="card" aria-labelledby="temas-sin-apuntes">
          <h2 id="temas-sin-apuntes">
            Temas sin apuntes escritos{' '}
            <span className="hint">· {sinApuntes.length}, todavía sin texto que revisar</span>
          </h2>
          <p className="hint">
            {sinApuntes.map((tema) => tema.code).join(' · ')}
          </p>
        </section>
      )}
    </>
  );
}

/**
 * Una fila de la tabla: el tema, su estado, sus cifras, su motivo y su decisión.
 *
 * El motivo va **como lista y en el orden en el que lo manda el servidor**: la primera razón es el
 * titular (por qué no está publicado) y las demás son el desglose de a quién le toca cada parte. Cada
 * una lleva su cifra aparte para que el número se lea sin leer la frase.
 */
function Fila({ tema }: { tema: NotesReviewTopic }) {
  const cobertura = coveragePercent(tema.coverage);
  const coberturaTodas = coveragePercent(tema.coverage_all_keys);
  // La decisión, normalizada una vez: el contrato la marca opcional y el resto de la fila no tiene
  // que defenderse de `undefined` en cada línea.
  const revision = tema.review ?? null;
  return (
    <li className="apuntes-revision__fila">
      <div className="apuntes-revision__cabecera">
        <h3 className="apuntes-revision__titulo">
          <Link to={`/admin/apuntes/${encodeURIComponent(tema.code)}`}>
            <span className="apuntes-revision__codigo">{tema.code}</span>{' '}
            {/* El título del tema es contenido del temario, no una frase nuestra. */}
            <span data-contenido>{tema.title}</span>
          </Link>
        </h3>
        <p className="apuntes-revision__estado">
          <span className={`marca ${NOTES_STATE_CLASS[tema.state]}`}>
            {NOTES_STATE_LABELS[tema.state]}
          </span>
          <span className="hint"> {NOTES_STATE_HELP[tema.state]}</span>
          {tema.state === 'none' && (
            <span className="hint"> · Todavía no tiene apartados escritos.</span>
          )}
        </p>
      </div>

      <dl className="apuntes-revision__cifras">
        <div>
          <dt>Apartados</dt>
          <dd>{tema.sections_written}</dd>
        </div>
        <div>
          <dt>Hechos</dt>
          <dd>{tema.facts}</dd>
        </div>
        <div>
          <dt>Comprobadas</dt>
          <dd>{tema.checks.total}</dd>
        </div>
        <div>
          <dt>Cobertura</dt>
          <dd>
            {cobertura === null ? (
              <span className="hint">sin medir en esta tabla</span>
            ) : (
              <>
                {tema.coverage?.[0]} de {tema.coverage?.[1]}{' '}
                <span className="hint">({cobertura})</span>
              </>
            )}
          </dd>
        </div>
        {coberturaTodas !== null && (
          <div>
            <dt>Sobre todas las preguntas</dt>
            <dd>{coberturaTodas}</dd>
          </div>
        )}
        <div>
          <dt>Incidencias</dt>
          <dd>
            {tema.incidents_open > 0 ? (
              <Link to={`/admin/incidencias?tema=${encodeURIComponent(tema.code)}`}>
                {tema.incidents_open} sin despachar
              </Link>
            ) : (
              <span className="hint">ninguna</span>
            )}
          </dd>
        </div>
      </dl>

      {tema.reasons.length > 0 && (
        <ul
          className="apuntes-revision__motivos"
          aria-label={`Motivo de ${tema.code}`}
          // El texto del motivo lo compone el **servidor** con las palabras del motor (y alguna de
          // ellas —«versión»— es jerga de la trastienda, no una frase de esta pantalla): va marcado
          // como contenido, igual que el detalle de una incidencia en la bandeja del motor.
          data-contenido
        >
          {tema.reasons.map((razon) => (
            <li key={razon.code}>
              {razon.figure !== null && razon.figure !== undefined && (
                <strong className="apuntes-revision__figura">{razon.figure}</strong>
              )}{' '}
              {razon.text}
            </li>
          ))}
        </ul>
      )}

      <p className="apuntes-revision__decision">
        {revision === null ? (
          <span className="hint">Sin decisión escrita sobre este tema.</span>
        ) : (
          <>
            <strong>{REVIEW_DECISION_LABELS[revision.decision]}</strong>
            {revision.note !== null && revision.note !== undefined && (
              <span> · «{revision.note}»</span>
            )}
            <span className="hint"> · por {revision.actor}</span>
          </>
        )}
        <Link className="apuntes-revision__enlace" to={`/admin/apuntes/${encodeURIComponent(tema.code)}`}>
          Leer y decidir
        </Link>
      </p>

      {tema.measured && cobertura !== null && (
        <p className="hint">
          Medido hoy sobre las comprobaciones guardadas (sin volver a pagar ninguna corrida); el
          listón es el {thresholdPercent(tema.coverage_threshold)}.
        </p>
      )}
    </li>
  );
}
