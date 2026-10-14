import { useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import {
  NOTES_STATE_CLASS,
  NOTES_STATE_HELP,
  NOTES_STATE_LABELS,
  REVIEW_BLOCK_LABELS,
  REVIEW_DECISION_LABELS,
  coveragePercent,
  orderSections,
  thresholdPercent,
  type NotesReviewResult,
  type NotesReviewSection,
  type NotesReviewTopic,
} from '../api/notesReview';
import { useDecideNotesReview, useNotesReviewFile } from '../api/queries';
import { ErrorState } from '../components/ErrorState';
import { LoadingState } from '../components/LoadingState';
import { NotesBody } from '../features/student/NotesBody';
import { describeError } from '../features/system/labels';

/** El tope de la nota: el mismo que exige el servidor (una línea de bandeja). */
const MAX_NOTA = 300;

/**
 * La ficha de un tema para revisarlo (F24, §4.3 del objetivo).
 *
 * Es la pantalla donde el propietario **lee un borrador dentro del panel** y lo decide. Lo que hace y
 * lo que garantiza:
 *
 * 1. **el motivo, con su cifra y el primero**: qué le pasa al tema (sin apuntes, publicado, a las
 *    puertas, sin llegar al listón, con la forma rota) y después el desglose de a quién le toca cada
 *    parte. Las frases las compone el servidor: aquí no se recalcula ningún número;
 * 2. **el texto apartado a apartado, tal como se leerá en la zona del alumno**: se pinta con el
 *    **mismo** lector que la pantalla del alumno (`NotesBody`), así que las tablas, los títulos y la
 *    prosa salen igual que allí. Y cada apartado lleva sus cifras (hechos, palabras, cubiertas,
 *    huecos, dudosas, conflictos) y su aviso si el motor lo dejó marcado;
 * 3. **los peores primero**, cuando se piden: «peor» es lo que queda sin resolver en ese apartado
 *    (en conflicto, dudoso o sin frase), que es la cifra que manda el servidor en `worst`. Con el
 *    orden natural se lee el tema entero; con el otro se va directo a lo que hay que mirar, que es lo
 *    que evita releer sesenta páginas;
 * 4. **aprobar o rechazar con nota, por la ruta auditada**: una sola llamada por decisión
 *    (`POST /notes-review/{codigo}/decision`), con su evento en la misma transacción. Rechazar exige
 *    motivo —no se puede enviar sin él, y el servidor también lo comprueba— y al aprobar se dice si
 *    eso ha **publicado** el tema o qué puerta lo ha frenado.
 */
export function NotesReviewTopicPage() {
  const { codigo = '' } = useParams();
  const ficha = useNotesReviewFile(codigo);
  const decidir = useDecideNotesReview(codigo);

  const [peoresPrimero, setPeoresPrimero] = useState(false);
  const [nota, setNota] = useState('');
  const [resultado, setResultado] = useState<NotesReviewResult | null>(null);

  const secciones = useMemo(
    () => orderSections(ficha.data?.sections ?? [], peoresPrimero),
    [ficha.data, peoresPrimero],
  );

  if (ficha.isPending) {
    return <LoadingState label="Leyendo los apuntes del tema y midiéndolos…" />;
  }
  if (ficha.isError) {
    return (
      <ErrorState
        title="No se pudieron leer los apuntes del tema"
        message={describeError(ficha.error)}
        onRetry={() => {
          void ficha.refetch();
        }}
      />
    );
  }

  const tema = ficha.data.topic;
  // El contrato marca los campos que pueden no venir como opcionales; se normalizan **una vez** aquí
  // para que el resto de la pantalla no tenga que defenderse de `undefined` en cada línea.
  const razones = tema.reasons ?? [];
  const revision = tema.review ?? null;
  const cobertura = tema.coverage ?? null;
  const coberturaTodas = tema.coverage_all_keys ?? null;
  const conTexto = tema.state !== 'none';
  const notaLista = nota.trim();
  const puedeRechazar = notaLista !== '' && !decidir.isPending;

  function decidirCon(decision: 'approved' | 'rejected') {
    decidir.mutate(
      { decision, note: notaLista === '' ? null : notaLista },
      {
        onSuccess: (datos) => {
          setResultado(datos);
          setNota('');
        },
      },
    );
  }

  return (
    <>
      <header className="page__header">
        <p className="hint">
          <Link className="link" to="/admin/apuntes">
            Volver a los apuntes
          </Link>
          {` · ${tema.block_code}: `}
          <span data-contenido>{tema.block_title}</span>
        </p>
        <h1>
          <span className="apuntes-revision__codigo">{tema.code}</span>{' '}
          <span data-contenido>{tema.title}</span>
        </h1>
        <p className="apuntes-revision__estado">
          <span className={`marca ${NOTES_STATE_CLASS[tema.state]}`}>
            {NOTES_STATE_LABELS[tema.state]}
          </span>
          <span className="hint"> {NOTES_STATE_HELP[tema.state]}</span>
        </p>
      </header>

      {razones.length > 0 && (
        <section className="card" aria-labelledby="motivo-del-tema">
          <h2 id="motivo-del-tema">Por qué está así</h2>
          <ul className="apuntes-revision__motivos" aria-label="Motivo del tema" data-contenido>
            {razones.map((razon) => (
              <li key={razon.code}>
                {razon.figure !== null && razon.figure !== undefined && (
                  <strong className="apuntes-revision__figura">{razon.figure}</strong>
                )}{' '}
                {razon.text}
              </li>
            ))}
          </ul>
          {tema.measured && cobertura !== null && (
            <p className="hint">
              Cobertura medida hoy: {cobertura[0]} de {cobertura[1]} preguntas que se pueden corregir
              ({coveragePercent(cobertura)}); el listón es el{' '}
              {thresholdPercent(tema.coverage_threshold)}. Sobre todas las que tienen respuesta
              correcta: {coberturaTodas?.[0]} de {coberturaTodas?.[1]} (
              {coveragePercent(coberturaTodas)}). Medir no llama a ningún modelo: se lee de las
              comprobaciones guardadas.
            </p>
          )}
        </section>
      )}

      <Decision
        revision={revision}
        nota={nota}
        onNota={setNota}
        puedeRechazar={puedeRechazar}
        ocupado={decidir.isPending}
        conTexto={conTexto}
        error={decidir.isError ? describeError(decidir.error) : null}
        resultado={resultado}
        onDecidir={decidirCon}
        onCerrarResultado={() => {
          setResultado(null);
        }}
      />

      {!conTexto ? (
        <p className="bloque__texto">
          Este tema todavía no tiene apartados escritos: no hay nada que leer ni que decidir.
        </p>
      ) : (
        <section className="card" aria-labelledby="apartados-del-tema">
          <h2 id="apartados-del-tema">
            Los apuntes, apartado a apartado{' '}
            <span className="hint">· {secciones.length} apartado(s)</span>
          </h2>
          <div className="form__row">
            <button
              className="button button--secondary"
              type="button"
              aria-pressed={peoresPrimero}
              onClick={() => {
                setPeoresPrimero((previo) => !previo);
              }}
            >
              {peoresPrimero ? 'Leer en orden' : 'Los peores primero'}
            </button>
            <span className="hint">
              {peoresPrimero
                ? 'Los apartados con más preguntas sin resolver van primero; dentro de cada uno, el orden de lectura.'
                : 'El orden de lectura: así es como lo lee el alumno.'}
            </span>
          </div>
          <div className="apuntes__lectura">
            {secciones.map((apartado) => (
              <Apartado key={apartado.key} apartado={apartado} />
            ))}
          </div>
        </section>
      )}
    </>
  );
}

/** El bloque de la decisión: aprobar, rechazar con motivo y qué ha pasado después. */
function Decision({
  revision,
  nota,
  onNota,
  puedeRechazar,
  ocupado,
  conTexto,
  error,
  resultado,
  onDecidir,
  onCerrarResultado,
}: {
  revision: NotesReviewTopic['review'] | null;
  nota: string;
  onNota: (valor: string) => void;
  puedeRechazar: boolean;
  ocupado: boolean;
  conTexto: boolean;
  error: string | null;
  resultado: NotesReviewResult | null;
  onDecidir: (decision: 'approved' | 'rejected') => void;
  onCerrarResultado: () => void;
}) {
  const loDecidido = revision ?? null;
  const revisionDelResultado = resultado === null ? null : (resultado.topic.review ?? null);
  return (
    <section className="card" aria-labelledby="decision-del-tema">
      <h2 id="decision-del-tema">Tu decisión</h2>
      {loDecidido !== null && (
        <p className="apuntes-revision__decision">
          <strong>{REVIEW_DECISION_LABELS[loDecidido.decision]}</strong>
          {loDecidido.note !== null && loDecidido.note !== undefined && (
            <span> · «{loDecidido.note}»</span>
          )}
          <span className="hint"> · por {loDecidido.actor}</span>
        </p>
      )}
      <p className="hint">
        Aprobar <strong>publica el tema</strong> si cumple las dos puertas del §2.3; si no las cumple,
        queda aprobado y sin publicar, y se te dice qué puerta lo frena. Rechazar exige el motivo: sin
        él, el borrador se queda donde estaba y sin saber por qué.
      </p>
      <div className="form__row">
        <label className="form__label" htmlFor="nota-decision">
          Qué has decidido (una línea)
        </label>
        <input
          id="nota-decision"
          className="form__input"
          type="text"
          value={nota}
          maxLength={MAX_NOTA}
          placeholder="leído el 14 de octubre: el texto contesta lo que se pregunta"
          onChange={(evento) => {
            onNota(evento.target.value);
          }}
        />
      </div>
      <div className="form__row">
        <button
          className="button"
          type="button"
          disabled={!conTexto || ocupado}
          onClick={() => {
            onDecidir('approved');
          }}
        >
          {ocupado ? 'Guardando…' : 'Aprobar los apuntes'}
        </button>
        <button
          className="button button--secondary"
          type="button"
          disabled={!conTexto || !puedeRechazar}
          title={
            puedeRechazar
              ? undefined
              : 'Para rechazar hace falta el motivo: es lo que deja el borrador con su porqué'
          }
          onClick={() => {
            onDecidir('rejected');
          }}
        >
          Rechazar con este motivo
        </button>
        {!conTexto && <span className="hint">Un tema sin apuntes no se puede aprobar.</span>}
      </div>

      {error !== null && <ErrorState title="La decisión no se pudo guardar" message={error} />}

      {resultado !== null && (
        <div className="apuntes-revision__resultado" role="status">
          <p>
            <strong>
              {revisionDelResultado === null
                ? 'Decisión guardada'
                : REVIEW_DECISION_LABELS[revisionDelResultado.decision]}
            </strong>
            {resultado.published ? (
              <> · el tema ha quedado <strong>publicado</strong>.</>
            ) : (
              <> · el tema <strong>no se ha publicado</strong>.</>
            )}
            {resultado.blocked_by !== null && resultado.blocked_by !== undefined && (
              <> Lo frena: {REVIEW_BLOCK_LABELS[resultado.blocked_by]}.</>
            )}
          </p>
          <button className="button button--secondary" type="button" onClick={onCerrarResultado}>
            Entendido
          </button>
        </div>
      )}
    </section>
  );
}

/**
 * Un apartado: sus cifras, su aviso y su texto tal como se lee en la zona del alumno.
 *
 * El número es el de **lectura** (`position`), no el de la lista: cuando se ordenan los peores
 * primero, el apartado sigue diciendo qué número ocupa en el tema, que es lo que el alumno ve.
 */
function Apartado({ apartado }: { apartado: NotesReviewSection }) {
  const sinResolver = apartado.conflicts + apartado.doubtful + apartado.gaps;
  return (
    <article className="apartado" id={`apartado-${apartado.anchor}`}>
      <h3 className="apartado__titulo">
        <span className="apartado__numero">{apartado.position}.</span>{' '}
        <span data-contenido>{apartado.title}</span>
      </h3>
      <div className="apartado__cuerpo">
        {/* El mismo lector que la pantalla del alumno: la promesa de esta ficha es que aquí se lee
            como se leerá allí, y con un segundo lector eso dejaría de ser verdad. */}
        <NotesBody markdown={apartado.body_markdown} />
      </div>
      <div className="apartado__lateral">
        <p className="hint">
          {apartado.facts_total} hecho(s) · {apartado.words} palabra(s)
        </p>
        <p className="hint">
          {apartado.covered} cubierta(s) · {apartado.gaps} sin frase · {apartado.doubtful} dudosa(s)
          · {apartado.conflicts} en conflicto
        </p>
        {sinResolver > 0 && (
          <p className="hint">
            <strong>{sinResolver}</strong> sin resolver en este apartado.
          </p>
        )}
        {apartado.needs_review_reason !== null && apartado.needs_review_reason !== undefined && (
          <p className="hint" data-contenido>
            El motor lo dejó marcado: {apartado.needs_review_reason}
          </p>
        )}
      </div>
    </article>
  );
}
