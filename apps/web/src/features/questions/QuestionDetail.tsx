import { useState } from 'react';

import type { Explanation, IssueKind, Question, QuestionEvidence, QuestionKind } from '../../api/questions';
import { ISSUE_KINDS, QUESTION_KINDS } from '../../api/questions';
import { apiBaseUrl } from '../../api/client';
import { ErrorState } from '../../components/ErrorState';
import { LoadingState } from '../../components/LoadingState';
import { StatusBadge } from '../../components/StatusBadge';
import {
  issueKindLabel,
  keyOutcomeLabel,
  keyOutcomeTone,
  kindLabel,
  originLabel,
  originTone,
  questionStatusLabel,
  questionStatusTone,
} from './labels';

export interface QuestionDetailProps {
  question: Question;
  evidence: QuestionEvidence[];
  evidenceIsPending: boolean;
  /** Explicaciones de la pregunta entera y de cada opción (S12.7). */
  explanations: Explanation[];
  explanationsIsPending: boolean;
  explanationsError: string | null;
  busy: boolean;
  conflict: string | null;
  error: string | null;
  onSetExplanation: (input: { text: string; optionStableKey: string | null }) => void;
  onPatch: (changes: {
    question_type: QuestionKind;
    position: number;
    is_reserve: boolean;
    reserve_order: number | null;
  }) => void;
  onCorrect: (input: { note: string; stem: string | null; options: string[] | null }) => void;
  onReportIssue: (input: { kind: IssueKind; detail: string }) => void;
}

/**
 * Ficha de una pregunta (07_UI-UX §7): los campos estructurados a un lado y **el original al otro**.
 *
 * El original es lo que se importó: el enunciado tal y como llegó y, cuando existe, la cita que lo
 * sostiene —con enlace para abrir el original en su página, que es lo que pedía DEBT-010: una cita que
 * se puede abrir—. Si la pregunta no tiene documento de origen adjunto, se dice —no se enseña un hueco
 * ni se inventa una cita—.
 *
 * Corregir una transcripción **no** se hace aquí con el editor: se hace con corrección local, que crea
 * versión nueva con motivo y no reescribe el original. La pantalla lo explica donde toca.
 */
export function QuestionDetail({
  question,
  evidence,
  evidenceIsPending,
  explanations,
  explanationsIsPending,
  explanationsError,
  busy,
  conflict,
  error,
  onSetExplanation,
  onPatch,
  onCorrect,
  onReportIssue,
}: QuestionDetailProps) {
  const [kind, setKind] = useState<QuestionKind>(question.question_type);
  const [position, setPosition] = useState(String(question.position));
  const [isReserve, setIsReserve] = useState(question.is_reserve);
  const [reserveOrder, setReserveOrder] = useState(
    question.reserve_order === null ? '' : String(question.reserve_order),
  );
  const [note, setNote] = useState('');
  const [stem, setStem] = useState('');
  const [options, setOptions] = useState(question.options.map((opcion) => opcion.text).join('\n'));
  const [issueKind, setIssueKind] = useState<IssueKind>('ambiguous');
  const [issueDetail, setIssueDetail] = useState('');
  // Qué hueco se está explicando: la pregunta entera (`null`) o una de sus opciones.
  const [hueco, setHueco] = useState<string>('');
  const [textoExplicacion, setTextoExplicacion] = useState('');

  const deLaPregunta = explanations.find((item) => item.option_stable_key === null) ?? null;
  const porOpcion = new Map(
    explanations
      .filter((item) => item.option_stable_key !== null)
      .map((item) => [item.option_stable_key as string, item]),
  );
  // Al elegir un hueco se trae lo que ya hubiera escrito ahí: explicar es corregir lo que hay, no
  // empezar de cero cada vez.
  const vigente = hueco === '' ? deLaPregunta : (porOpcion.get(hueco) ?? null);

  const correctas = new Set(question.correct_option_keys);
  const opcionesActuales = question.options.map((opcion) => opcion.text).join('\n');

  return (
    <>
      {conflict !== null && (
        <>
          <ErrorState title="El servidor rechazó la operación" message={conflict} />
          <p className="hint">Un conflicto no cambia nada: la pregunta se queda como estaba.</p>
        </>
      )}
      {error !== null && <ErrorState title="La operación no se aplicó" message={error} />}

      <div className="card">
        <h3>Pregunta {question.position}</h3>
        <p className="form__row">
          <StatusBadge tone={originTone(question.origin_type)}>
            {originLabel(question.origin_type)}
          </StatusBadge>{' '}
          <StatusBadge tone={questionStatusTone(question.status)}>
            {questionStatusLabel(question.status)}
          </StatusBadge>{' '}
          <StatusBadge tone={keyOutcomeTone(question.key_outcome)}>
            {keyOutcomeLabel(question.key_outcome)}
            {question.correct_option_keys.length > 0 &&
              `: ${question.correct_option_keys.join(', ')}`}
          </StatusBadge>{' '}
          <span className="hint">
            {kindLabel(question.question_type)}
            {question.is_reserve ? ' · reserva' : ''}
            {question.version_no > 1 ? ` · versión ${question.version_no}` : ''}
          </span>
        </p>

        <div className="tabs__panel">
          <section aria-labelledby="campos-estructurados">
            <h4 id="campos-estructurados">Campos estructurados</h4>
            <p>{question.stem}</p>
            <ol>
              {question.options.map((opcion) => (
                <li key={opcion.id}>
                  <span className="sample__path">{opcion.stable_key.toUpperCase()}</span>{' '}
                  {opcion.text}{' '}
                  {correctas.has(opcion.stable_key) && <StatusBadge tone="ok">correcta</StatusBadge>}
                </li>
              ))}
            </ol>
            {question.options.length === 0 && (
              <p className="hint">
                Esta pregunta no tiene opciones guardadas: está sin completar y el banco lo dice.
              </p>
            )}
          </section>

          <section aria-labelledby="original-pregunta">
            <h4 id="original-pregunta">Original</h4>
            <p className="hint">
              Así llegó el enunciado, antes de cualquier edición: no se reescribe nunca.
            </p>
            <blockquote className="reader">{question.stem}</blockquote>
            {evidenceIsPending ? (
              <LoadingState label="Cargando la evidencia…" />
            ) : evidence.length === 0 ? (
              <p className="hint">
                Esta pregunta no tiene documento de origen adjunto, así que no hay cita que abrir. La
                cita se crea al importar la pregunta <strong>desde un documento</strong>, desde la
                pestaña «Importar» de esta pantalla; no se rellena con una cita inventada.
              </p>
            ) : (
              <>
                <h5>Evidencia que la sostiene</h5>
                <ul>
                  {evidence.map((cita) => (
                    <li key={`${cita.span_id}-${cita.role}`}>
                      <StatusBadge tone={cita.status === 'accepted' ? 'ok' : 'warning'}>
                        {cita.role}
                      </StatusBadge>{' '}
                      {cita.citation_label ?? `página ${String(cita.page ?? 'sin página')}`}{' '}
                      <a
                        href={originalDeLaCita(cita)}
                        target="_blank"
                        rel="noreferrer"
                        aria-label={
                          cita.page === null || cita.page === undefined
                            ? 'abrir el original de la cita'
                            : `abrir el original de la cita en la página ${String(cita.page)}`
                        }
                      >
                        abrir el original
                        {cita.page === null || cita.page === undefined
                          ? ''
                          : ` (página ${String(cita.page)})`}
                      </a>
                      <blockquote className="reader">{cita.text}</blockquote>
                      {cita.claim !== null && cita.claim !== undefined && (
                        <p className="hint">sostiene: {cita.claim}</p>
                      )}
                    </li>
                  ))}
                </ul>
              </>
            )}
          </section>
          <section aria-labelledby="explicaciones-pregunta">
            <h4 id="explicaciones-pregunta">Explicaciones</h4>
            <p className="hint">
              Por qué cada opción es la correcta o no lo es (07_UI-UX §7). El texto es tuyo o viene del
              material; no se inventa ninguna explicación y una opción sin explicación se queda sin
              ella.
            </p>
            {explanationsIsPending && <LoadingState label="Cargando las explicaciones…" />}
            {explanationsError !== null && (
              <ErrorState title="No se pudieron leer las explicaciones" message={explanationsError} />
            )}
            {!explanationsIsPending && explanationsError === null && (
              <>
                {deLaPregunta === null ? (
                  <p className="hint">La pregunta no tiene explicación propia.</p>
                ) : (
                  <p>
                    <StatusBadge tone={deLaPregunta.origin === 'generated' ? 'warning' : 'info'}>
                      la pregunta entera
                    </StatusBadge>{' '}
                    {deLaPregunta.text}
                  </p>
                )}
                <ul>
                  {question.options.map((opcion) => {
                    const explicacion = porOpcion.get(opcion.stable_key);
                    return (
                      <li key={`explicacion-${opcion.id}`}>
                        <span className="sample__path">{opcion.stable_key.toUpperCase()}</span>{' '}
                        {explicacion === undefined ? (
                          <span className="hint">sin explicación</span>
                        ) : (
                          explicacion.text
                        )}
                      </li>
                    );
                  })}
                </ul>
                <div className="form__row">
                  <label className="form__label" htmlFor="explicacion-hueco">
                    Qué se explica
                  </label>
                  <select
                    id="explicacion-hueco"
                    className="selector__select"
                    value={hueco}
                    onChange={(event) => {
                      const elegido = event.target.value;
                      setHueco(elegido);
                      const actual =
                        elegido === ''
                          ? deLaPregunta
                          : (porOpcion.get(elegido) ?? null);
                      setTextoExplicacion(actual === null ? '' : actual.text);
                    }}
                  >
                    <option value="">La pregunta entera</option>
                    {question.options.map((opcion) => (
                      <option key={opcion.stable_key} value={opcion.stable_key}>
                        La opción {opcion.stable_key.toUpperCase()}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="form__row">
                  <label className="form__label" htmlFor="explicacion-texto">
                    Explicación
                  </label>
                  <textarea
                    id="explicacion-texto"
                    className="form__input"
                    rows={3}
                    value={textoExplicacion}
                    onChange={(event) => {
                      setTextoExplicacion(event.target.value);
                    }}
                  />
                  <button
                    className="button"
                    type="button"
                    disabled={busy || textoExplicacion.trim() === ''}
                    onClick={() => {
                      onSetExplanation({
                        text: textoExplicacion.trim(),
                        optionStableKey: hueco === '' ? null : hueco,
                      });
                    }}
                  >
                    {vigente === null ? 'Guardar la explicación' : 'Sustituir la explicación'}
                  </button>
                  <span className="hint">
                    Guardar en el mismo hueco <strong>sustituye</strong> lo que hubiera: una
                    explicación por opción, no un historial de versiones.
                  </span>
                </div>
              </>
            )}
          </section>
        </div>
      </div>

      <section className="card" aria-labelledby="editor-pregunta">
        <h3 id="editor-pregunta">Composición</h3>
        <p className="hint">
          Aquí se cambia cómo se presenta la pregunta (tipo, orden y si es reserva). El enunciado y las
          opciones de una pregunta oficial <strong>no</strong> se reescriben: se corrigen con
          corrección local.
        </p>
        <div className="form__row">
          <label className="form__label" htmlFor="editor-tipo">
            Tipo de pregunta
          </label>
          <select
            id="editor-tipo"
            className="selector__select"
            value={kind}
            onChange={(event) => {
              setKind(event.target.value as QuestionKind);
            }}
          >
            {QUESTION_KINDS.map((valor) => (
              <option key={valor} value={valor}>
                {kindLabel(valor)}
              </option>
            ))}
          </select>
          <label className="form__label" htmlFor="editor-posicion">
            Posición
          </label>
          <input
            id="editor-posicion"
            className="selector__select"
            type="number"
            min={1}
            value={position}
            onChange={(event) => {
              setPosition(event.target.value);
            }}
          />
          <label className="form__label" htmlFor="editor-reserva">
            <input
              id="editor-reserva"
              type="checkbox"
              checked={isReserve}
              onChange={(event) => {
                setIsReserve(event.target.checked);
              }}
            />{' '}
            es reserva
          </label>
          <label className="form__label" htmlFor="editor-orden">
            Orden de reserva
          </label>
          <input
            id="editor-orden"
            className="selector__select"
            type="number"
            min={1}
            value={reserveOrder}
            onChange={(event) => {
              setReserveOrder(event.target.value);
            }}
          />
          <button
            className="button"
            type="button"
            disabled={busy}
            aria-label="Guardar la composición de la pregunta"
            onClick={() => {
              onPatch({
                question_type: kind,
                position: Number(position),
                is_reserve: isReserve,
                reserve_order: reserveOrder === '' ? null : Number(reserveOrder),
              });
            }}
          >
            Guardar composición
          </button>
        </div>
      </section>

      <section className="card" aria-labelledby="correccion-local">
        <h3 id="correccion-local">Corrección local</h3>
        <p className="hint">
          Cambiar una transcripción oficial crea una{' '}
          <strong>versión nueva con su motivo</strong> y deja la anterior como sustituida: el original
          sigue ahí y se puede comparar.
        </p>
        <div className="form__row">
          <label className="form__label" htmlFor="correccion-motivo">
            Motivo (obligatorio)
          </label>
          <input
            id="correccion-motivo"
            className="selector__select"
            value={note}
            onChange={(event) => {
              setNote(event.target.value);
            }}
          />
        </div>
        <div className="form__row">
          <label className="form__label" htmlFor="correccion-enunciado">
            Enunciado corregido (opcional)
          </label>
          <textarea
            id="correccion-enunciado"
            className="reader"
            rows={3}
            value={stem}
            onChange={(event) => {
              setStem(event.target.value);
            }}
          />
          <label className="form__label" htmlFor="correccion-opciones">
            Opciones corregidas (una por línea, opcional)
          </label>
          <textarea
            id="correccion-opciones"
            className="reader"
            rows={4}
            value={options}
            onChange={(event) => {
              setOptions(event.target.value);
            }}
          />
          <p className="hint">
            Se guarda <strong>solo lo que cambies</strong>: con el enunciado en blanco y las opciones
            tal como están, la versión nueva conserva el texto y añade únicamente el motivo. El
            original no se toca en ningún caso.
          </p>
          <button
            className="button"
            type="button"
            disabled={busy || note.trim().length < 3}
            aria-label="Guardar la corrección local"
            onClick={() => {
              const lineas = options
                .split('\n')
                .map((linea) => linea.trim())
                .filter((linea) => linea !== '');
              onCorrect({
                note: note.trim(),
                stem: stem.trim() === '' ? null : stem.trim(),
                // Se envía solo lo que se ha cambiado: dejar las opciones como estaban no crea una
                // versión nueva de las opciones, sino una versión anotada del enunciado.
                options:
                  lineas.length === 0 || lineas.join('\n') === opcionesActuales ? null : lineas,
              });
            }}
          >
            Guardar corrección
          </button>
          {note.trim().length < 3 && (
            <p className="hint">
              El motivo es obligatorio: sin él no se puede corregir una transcripción oficial.
            </p>
          )}
        </div>
      </section>

      <section className="card" aria-labelledby="reportar-incidencia">
        <h3 id="reportar-incidencia">Reportar una incidencia</h3>
        <div className="form__row">
          <label className="form__label" htmlFor="incidencia-tipo">
            Qué pasa
          </label>
          <select
            id="incidencia-tipo"
            className="selector__select"
            value={issueKind}
            onChange={(event) => {
              setIssueKind(event.target.value as IssueKind);
            }}
          >
            {ISSUE_KINDS.map((valor) => (
              <option key={valor} value={valor}>
                {issueKindLabel(valor)}
              </option>
            ))}
          </select>
          <label className="form__label" htmlFor="incidencia-detalle">
            Detalle
          </label>
          <input
            id="incidencia-detalle"
            className="selector__select"
            value={issueDetail}
            onChange={(event) => {
              setIssueDetail(event.target.value);
            }}
          />
          <button
            className="button"
            type="button"
            disabled={busy || issueDetail.trim().length < 3}
            aria-label="Enviar la incidencia de la pregunta"
            onClick={() => {
              onReportIssue({ kind: issueKind, detail: issueDetail.trim() });
            }}
          >
            Reportar
          </button>
        </div>
      </section>
    </>
  );
}

/**
 * La URL del original de una cita, en su página cuando se sabe.
 *
 * El `#page=N` lo entiende el visor del navegador para los PDF; para un texto plano se abre el fichero
 * igual, sin salto. Se enlaza a la ruta del contrato (`GET /document-versions/{id}/original`), que es
 * la que sirve el fichero con `Content-Disposition: inline` para los tipos seguros.
 */
function originalDeLaCita(cita: QuestionEvidence): string {
  const base = `${apiBaseUrl()}/api/v1/document-versions/${encodeURIComponent(
    cita.document_version_id,
  )}/original`;
  return cita.page === null || cita.page === undefined ? base : `${base}#page=${String(cita.page)}`;
}
