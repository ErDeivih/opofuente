import { useState } from 'react';

import type { AnswerKey } from '../../api/questions';
import { ErrorState } from '../../components/ErrorState';
import { LoadingState } from '../../components/LoadingState';
import { StatusBadge } from '../../components/StatusBadge';
import { keyStatusLabel, keyStatusTone } from './labels';

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
}

/**
 * Plantillas del conjunto (07_UI-UX §7 y contrato §9).
 *
 * Activar una plantilla **es aprobarla** (ADR-009), así que la confirmación lo dice con esas palabras y
 * avisa de que queda auditado con quién y cuándo. Los 409 del servidor se muestran con su motivo y se
 * dice que **nada cambió**: una clave oficial sin su plantilla oficial enlazada no se activa, y una
 * aprobación no la convierte en oficial.
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
                      : clave.approved_at}
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
    </>
  );
}
