import { useState } from 'react';

import type { AnswerKey, BulkRecalculation, OutdatedSessions } from '../../api/questions';
import { ErrorState } from '../../components/ErrorState';
import { LoadingState } from '../../components/LoadingState';
import { StatusBadge } from '../../components/StatusBadge';
import { keyStatusLabel, keyStatusTone } from './labels';
import { formatDateTime } from '../../lib/format';

export interface AnswerKeysPanelProps {
  keys: AnswerKey[];
  isPending: boolean;
  isError: boolean;
  busy: boolean;
  conflict: string | null;
  error: string | null;
  onRetry: () => void;
  onActivate: (keyId: string) => void;
  onSupersede: (keyId: string, supersededId: string) => void;
  /** Cuántas sesiones terminadas del conjunto no están corregidas con la plantilla activa. */
  outdated: OutdatedSessions | null;
  outdatedPending: boolean;
  outdatedError: string | null;
  onRecalculate: () => void;
  recalculating: boolean;
  recalculation: BulkRecalculation | null;
  recalculateError: string | null;
}

/**
 * Plantillas del conjunto (07_UI-UX §7 y contrato §9).
 *
 * Activar una plantilla **es aprobarla** (ADR-009), así que la confirmación lo dice con esas palabras y
 * avisa de que queda auditado con quién y cuándo. Los 409 del servidor se muestran con su motivo y se
 * dice que **nada cambió**: una clave oficial sin su plantilla oficial enlazada no se activa, y una
 * aprobación no la convierte en oficial.
 *
 * Y una consecuencia que no se puede dejar escondida (DEBT-013): activar una clave corregida **no**
 * cambia las notas ya puestas. Aquí se dice cuántas sesiones terminadas se quedan con la corrección
 * vieja y se ofrece recalcularlas de una vez, con el informe de qué cambió en cada una.
 */
export function AnswerKeysPanel({
  keys,
  isPending,
  isError,
  busy,
  conflict,
  error,
  onRetry,
  onActivate,
  onSupersede,
  outdated,
  outdatedPending,
  outdatedError,
  onRecalculate,
  recalculating,
  recalculation,
  recalculateError,
}: AnswerKeysPanelProps) {
  const [confirmando, setConfirmando] = useState<string | null>(null);
  const [sustituyendo, setSustituyendo] = useState<string | null>(null);
  const [sustituida, setSustituida] = useState('');

  if (isPending) {
    return <LoadingState label="Cargando las plantillas…" />;
  }

  if (isError) {
    return (
      <ErrorState
        title="No se pudieron cargar las plantillas"
        message="El conjunto no está disponible o el servidor no responde."
        onRetry={onRetry}
      />
    );
  }

  return (
    <>
      {conflict !== null && (
        <>
          <ErrorState title="El servidor no la activó" message={conflict} />
          <p className="hint">
            Un conflicto no cambia nada: la plantilla se queda como estaba y la que hubiera activa sigue
            activa.
          </p>
        </>
      )}
      {error !== null && <ErrorState title="La operación no se aplicó" message={error} />}

      {keys.length === 0 ? (
        <p className="hint">
          Este conjunto no tiene ninguna plantilla. Se crea importando una plantilla suelta en la
          pestaña «Importar» o trayendo la columna de la clave en un CSV.
        </p>
      ) : (
        <table className="table">
          <caption className="table__caption">{keys.length} plantillas del conjunto</caption>
          <thead>
            <tr>
              <th scope="col">Versión</th>
              <th scope="col">Estado</th>
              <th scope="col">Desenlaces</th>
              <th scope="col">Aprobada</th>
              <th scope="col">Sustituye a</th>
              <th scope="col">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {keys.map((clave) => {
              const otras = keys.filter((otra) => otra.id !== clave.id);
              return (
                <tr key={clave.id}>
                  <th scope="row">v{clave.version_no}</th>
                  <td>
                    <StatusBadge tone={keyStatusTone(clave.status)}>
                      {keyStatusLabel(clave.status)}
                    </StatusBadge>
                  </td>
                  <td className="hint">{clave.entries.length} preguntas con desenlace</td>
                  <td className="hint">
                    {clave.approved_at === null || clave.approved_at === undefined
                      ? 'sin aprobar'
                      : formatDateTime(clave.approved_at)}
                  </td>
                  <td className="hint">{clave.supersedes_id ?? 'a ninguna'}</td>
                  <td>
                    {clave.status !== 'active' && confirmando !== clave.id && (
                      <button
                        className="button"
                        type="button"
                        disabled={busy}
                        aria-label={`Activar la plantilla v${String(clave.version_no)}`}
                        onClick={() => {
                          setConfirmando(clave.id);
                        }}
                      >
                        Activar…
                      </button>
                    )}
                    {confirmando === clave.id && (
                      <div className="form__row">
                        <p className="hint">
                          ¿Activar la plantilla v{clave.version_no}? Activarla{' '}
                          <strong>es aprobarla</strong>: queda registrado quién y cuándo, y pasa a ser
                          la clave con la que se corrige el examen. La que estuviera activa se conserva
                          como sustituida.
                        </p>
                        <button
                          className="button"
                          type="button"
                          disabled={busy}
                          aria-label={`Confirmar la activación de la plantilla v${String(
                            clave.version_no,
                          )}`}
                          onClick={() => {
                            setConfirmando(null);
                            onActivate(clave.id);
                          }}
                        >
                          Sí, activar
                        </button>
                        <button
                          className="button"
                          type="button"
                          onClick={() => {
                            setConfirmando(null);
                          }}
                        >
                          Cancelar
                        </button>
                      </div>
                    )}

                    {otras.length > 0 && sustituyendo !== clave.id && (
                      <button
                        className="button"
                        type="button"
                        disabled={busy}
                        aria-label={`Marcar qué plantilla sustituye v${String(clave.version_no)}`}
                        onClick={() => {
                          setSustituyendo(clave.id);
                          setSustituida('');
                        }}
                      >
                        Marcar sustitución…
                      </button>
                    )}
                    {sustituyendo === clave.id && (
                      <div className="form__row">
                        <label className="form__label" htmlFor={`sustituida-${clave.id}`}>
                          ¿A qué plantilla sustituye la v{clave.version_no}?
                        </label>
                        <select
                          id={`sustituida-${clave.id}`}
                          className="selector__select"
                          value={sustituida}
                          onChange={(event) => {
                            setSustituida(event.target.value);
                          }}
                        >
                          <option value="">elige la plantilla</option>
                          {otras.map((otra) => (
                            <option key={otra.id} value={otra.id}>
                              v{otra.version_no} · {keyStatusLabel(otra.status)}
                            </option>
                          ))}
                        </select>
                        <button
                          className="button"
                          type="button"
                          disabled={busy || sustituida === ''}
                          aria-label={`Confirmar que la plantilla v${String(
                            clave.version_no,
                          )} sustituye a la elegida`}
                          onClick={() => {
                            setSustituyendo(null);
                            onSupersede(clave.id, sustituida);
                          }}
                        >
                          Sí, marcar la sustitución
                        </button>
                        <button
                          className="button"
                          type="button"
                          onClick={() => {
                            setSustituyendo(null);
                          }}
                        >
                          Cancelar
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}

      <section aria-labelledby="plantillas-sesiones">
        <h3 id="plantillas-sesiones">Sesiones ya corregidas</h3>
        {outdatedPending ? (
          <LoadingState label="Contando las sesiones del conjunto…" />
        ) : outdatedError !== null ? (
          <p className="hint">
            No se ha podido contar cuántas sesiones quedan sin corregir con la plantilla activa:{' '}
            {outdatedError}
          </p>
        ) : outdated === null ? (
          <p className="hint">
            Sin plantilla activa no se puede decir qué sesiones están al día: no hay con qué comparar.
          </p>
        ) : (
          <>
            <p>
              <StatusBadge tone={outdated.outdated > 0 ? 'warning' : 'ok'}>
                {outdated.outdated === 1
                  ? '1 sesión desactualizada'
                  : `${String(outdated.outdated)} sesiones desactualizadas`}
              </StatusBadge>{' '}
              {outdated.detail}
            </p>
            {outdated.outdated > 0 && (
              <div className="form__row">
                <button
                  className="button"
                  type="button"
                  disabled={recalculating}
                  aria-label={
                    outdated.outdated === 1
                      ? 'Recalcular la sesión desactualizada'
                      : `Recalcular las ${String(outdated.outdated)} sesiones desactualizadas`
                  }
                  onClick={onRecalculate}
                >
                  {recalculating
                    ? 'Recalculando…'
                    : outdated.outdated === 1
                      ? 'Recalcular esa sesión ahora'
                      : 'Recalcular esas sesiones ahora'}
                </button>
                <span className="hint">
                  Se corrigen con la plantilla v{String(outdated.key_version)} activa. Cada sesión
                  conserva su resultado anterior: recalcular no borra lo que se dijo entonces.
                </span>
              </div>
            )}
            {outdated.outdated_session_ids.length > 0 && (
              // Cuáles son, no solo cuántas: el servidor manda los identificadores para poder
              // señalarlas, y una cifra sin lista obliga a buscarlas sesión a sesión en el historial.
              <details>
                <summary>
                  {outdated.outdated_session_ids.length === 1
                    ? 'Ver la sesión desactualizada'
                    : `Ver las ${String(outdated.outdated_session_ids.length)} sesiones desactualizadas`}
                </summary>
                <ul className="hint">
                  {outdated.outdated_session_ids.map((sesionId) => (
                    <li key={sesionId}>
                      <span className="sample__path">{sesionId}</span>
                    </li>
                  ))}
                </ul>
              </details>
            )}
            {outdated.without_evaluation > 0 && (
              <p className="hint">
                {outdated.without_evaluation === 1
                  ? '1 sesión terminada no tiene ninguna corrección guardada'
                  : `${String(outdated.without_evaluation)} sesiones terminadas no tienen ninguna corrección guardada`}
                : no se pueden comparar con la plantilla, y no se cuentan como desactualizadas.
              </p>
            )}
            {recalculation !== null && (
              <div>
                <p role="status">
                  {recalculation.detail}
                  {recalculation.key_version > 0 &&
                    ` (plantilla v${String(recalculation.key_version)})`}
                </p>
                <ul>
                  {recalculation.sessions.map((cambio) => (
                    <li key={cambio.session_id} className="hint">
                      <span className="sample__path">{cambio.session_id}</span>:{' '}
                      {cambio.changed
                        ? `de ${cambio.previous_total} a ${cambio.new_total}`
                        : `sin cambios (${cambio.new_total})`}
                      {cambio.previous_key_label !== cambio.new_key_label &&
                        ` · ${cambio.previous_key_label || 'sin plantilla'} → ${
                          cambio.new_key_label || 'sin plantilla'
                        }`}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {recalculateError !== null && <p className="notice">{recalculateError}</p>}
          </>
        )}
      </section>
    </>
  );
}
