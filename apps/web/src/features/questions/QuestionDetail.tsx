import { useState } from 'react';

import type { IssueKind, Question, QuestionEvidence, QuestionKind } from '../../api/questions';
import { ISSUE_KINDS, QUESTION_KINDS } from '../../api/questions';
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
  busy: boolean;
  conflict: string | null;
  error: string | null;
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
 * sostiene. Si la pregunta no tiene documento de origen adjunto, se dice —no se enseña un hueco ni se
 * inventa una cita—.
 *
 * Corregir una transcripción **no** se hace aquí con el editor: se hace con corrección local, que crea
 * versión nueva con motivo y no reescribe el original. La pantalla lo explica donde toca.
 */
export function QuestionDetail({
  question,
  evidence,
  evidenceIsPending,
  busy,
  conflict,
  error,
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
                cita se crea al importar la pregunta <strong>desde un documento</strong> (deuda
                registrada, DEBT-010); no se rellena con una cita inventada.
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
                      {cita.citation_label ?? `página ${String(cita.page ?? 'sin página')}`}
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
