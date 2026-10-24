import { useState } from 'react';
import { Link } from 'react-router-dom';

import {
  EXCLUSION_LABELS,
  KEY_STATUS_HELP,
  KEY_STATUS_LABELS,
  RELIABILITY_HELP,
  RELIABILITY_LABELS,
  materialHref,
  markedLetters,
  notesHref,
  optionLetters,
  QUESTION_STATUS_LABELS,
  type OptionLetter,
  type QuestionFile as QuestionFileView,
  type QuestionFileIncident,
  type QuestionFileKeyVersion,
  type QuestionFileNotes,
  type QuestionFileRepair,
  type QuestionFileVersion,
} from '../../api/questionFile';
import { INCIDENT_CATEGORY_LABELS, INCIDENT_STATUS_LABELS } from '../../api/notesIncidents';
import { StatusBadge, type StatusTone } from '../../components/StatusBadge';

/** El tono de la fiabilidad: verde cuando es fiable, aviso cuando está en duda, rojo cuando no. */
const TONO_FIABILIDAD: Record<string, StatusTone> = {
  fiable: 'ok',
  dudosa: 'warning',
  no_fiable: 'blocked',
};

/** El tono del estado de la plantilla: la que corrige es verde; la que no, informativa. */
const TONO_PLANTILLA: Record<string, StatusTone> = {
  active: 'ok',
  draft: 'warning',
  superseded: 'info',
  rejected: 'blocked',
};

const TONO_INCIDENCIA: Record<QuestionFileIncident['status'], StatusTone> = {
  open: 'warning',
  in_progress: 'info',
  reviewed: 'ok',
  dismissed: 'info',
};

/** Un día, sin la hora: en una ficha de texto largo la hora no cambia ninguna decisión. */
function dia(fecha: string | null | undefined): string {
  return fecha === null || fecha === undefined ? '—' : fecha.slice(0, 10);
}

function letras(cuales: string[]): string {
  return cuales.length === 0 ? '—' : cuales.map((cual) => cual.toUpperCase()).join(', ');
}

export interface QuestionFileProps {
  file: QuestionFileView;
  /** Hay una escritura en vuelo: los botones se apagan para que no se pisen dos decisiones. */
  busy: boolean;
  /** El rechazo del servidor con su motivo (409), ya traducido a texto. */
  conflict: string | null;
  /** Cualquier otro error de la escritura. */
  error: string | null;
  /** Lo último que se ha hecho, para que la pantalla lo diga sin recargar nada. */
  notice: string | null;
  onMarkCorrect: (input: { correctOptionKeys: string[]; note: string }) => void;
  onRepair: (input: { note: string }) => void;
}

/**
 * La ficha de una pregunta (F20, §4.2 del objetivo).
 *
 * **No es un visor**: es donde el propietario arregla una respuesta correcta y donde se ve qué se
 * está estudiando y con qué garantía. Seis bloques, y cada uno está por algo:
 *
 * 1. **la pregunta**, con sus opciones y **cuál está marcada hoy**;
 * 2. **de dónde sale esa respuesta**: la plantilla, su estado, el material del que salió con el
 *    estado de **su** versión, y el veredicto de fiabilidad del banco entero. Sin esto una letra no
 *    se puede juzgar;
 * 3. **qué dicen los apuntes**, con la frase que lo demuestra y el apartado exacto. Es la otra mitad
 *    de la comparación;
 * 4. **lo que ha señalado el sistema**, con su categoría;
 * 5. **fuera del temario**, cuando lo está, y por qué;
 * 6. **qué se puede hacer**: marcar la respuesta correcta (la anterior queda en el historial) y
 *    reparar lo que una regla pueda reparar. Lo que no se puede hacer se dice con el motivo, no con
 *    un botón apagado y sin explicación.
 *
 * Y debajo, los **dos historiales**: el de la pregunta y el de la plantilla, con la letra que cada
 * uno daba a esta pregunta. Es lo que hace que «no se pisa la anterior» sea un hecho comprobable y no
 * una promesa.
 *
 * Los textos que vienen del servidor —el enunciado, las opciones, el porqué de cada negativa, las
 * categorías del motor— van dentro de `data-contenido`: son datos, no frases de la interfaz.
 */
export function QuestionFile({
  file,
  busy,
  conflict,
  error,
  notice,
  onMarkCorrect,
  onRepair,
}: QuestionFileProps) {
  const letrasDisponibles = optionLetters(file);
  const marcadas = markedLetters(file);
  const [elegidas, setElegidas] = useState<string[]>(marcadas);
  const [notaClave, setNotaClave] = useState('');
  const [notaReparacion, setNotaReparacion] = useState('');
  const multiple = file.question_type === 'multi_mark_error';
  const hrefMaterial = materialHref(file);
  const puedeMarcar = !file.protection.protected && !busy && elegidas.length > 0;

  function alternar(letra: string) {
    setElegidas((antes) =>
      multiple
        ? antes.includes(letra)
          ? antes.filter((cual) => cual !== letra)
          : [...antes, letra].sort()
        : [letra],
    );
  }

  return (
    <>
      <header className="page__header">
        <h1>Ficha de la pregunta</h1>
        <p className="page__lead">
          La pregunta, la respuesta que se da por buena y <strong>de dónde sale</strong>. Aquí se
          arregla lo que no cuadra: cambiar la respuesta correcta —la anterior se conserva— y reparar
          el texto que se importó mal. Cada cambio queda auditado.
        </p>
        <p className="hint">
          <Link className="link" to="/admin/preguntas">
            Volver al banco de preguntas
          </Link>
          {' · '}
          <span data-contenido>{file.set_title}</span>
          {file.set_distribution === 'personal' ? ' · material tuyo' : ' · publicable'} · pregunta{' '}
          {file.position}
          {file.is_reserve ? ' (reserva)' : ''} · vista {file.version_no}
        </p>
      </header>

      {file.superseded_by !== null && (
        <div className="notice card">
          <h2>Esta vista está sustituida</h2>
          <p>
            Una vista posterior la reemplazó: lo que se está mirando es lo que decía antes. La que
            manda hoy es la otra.
          </p>
          <p>
            <Link className="link" to={`/admin/preguntas?pregunta=${file.superseded_by}`}>
              Abrir la vista que manda
            </Link>
          </p>
        </div>
      )}

      <section className="card" aria-labelledby="ficha-pregunta">
        <h2 id="ficha-pregunta">La pregunta</h2>
        <p className="hint">
          {QUESTION_STATUS_LABELS[file.status]} ·{' '}
          {file.question_type === 'multi_mark_error'
            ? 'hay que marcar más de una'
            : file.question_type === 'true_false'
              ? 'verdadero o falso'
              : file.question_type === 'free_text_reference'
                ? 'de referencia libre'
                : 'una sola respuesta'}{' '}
          · dada de alta el {dia(file.created_at)}
          {file.note === null ? '' : ' · con un arreglo anterior anotado'}
        </p>
        {file.note !== null && (
          <p className="nota-margen">
            <span className="nota-margen__rotulo">Por qué se cambió la última vez</span>
            <span className="nota-margen__texto" data-contenido>
              {file.note}
            </span>
          </p>
        )}
        <p className="resultado__enunciado" data-contenido>
          {file.stem}
        </p>
        <ul className="resultado__opciones">
          {file.options.map((opcion) => {
            const correcta = marcadas.includes(opcion.stable_key);
            return (
              <li
                key={opcion.stable_key}
                className={
                  correcta ? 'resultado__opcion resultado__opcion--correcta' : 'resultado__opcion'
                }
              >
                <span className="resultado__letra">{opcion.stable_key.toUpperCase()}</span>
                <span className="resultado__texto" data-contenido>
                  {opcion.text}
                </span>
                {correcta && <span className="resultado__marca">respuesta correcta</span>}
              </li>
            );
          })}
        </ul>
      </section>

      <section className="card" aria-labelledby="ficha-procedencia">
        <h2 id="ficha-procedencia">De dónde sale la respuesta correcta</h2>
        {file.key === null ? (
          <p className="hint">
            Esta pregunta <strong>no tiene</strong> respuesta correcta con la que se pueda corregir:
            ni su banco le ha dado una ni se ha marcado desde aquí. Se dice en vez de enseñar una
            letra que no le corresponde.
          </p>
        ) : (
          <>
            <p className="hint">
              <StatusBadge tone={TONO_PLANTILLA[file.key.status] ?? 'info'}>
                {KEY_STATUS_LABELS[file.key.status]}
              </StatusBadge>{' '}
              respuesta <strong>{letras(file.key.correct_option_keys)}</strong> · vista{' '}
              {file.key.version_no} de la lista de respuestas del banco
              {file.key.approved_at === null ? '' : ` · aprobada el ${dia(file.key.approved_at)}`}
              {file.key.outcome === 'annulled' ? ' · la pregunta está anulada' : ''}
            </p>
            <p className="hint">{KEY_STATUS_HELP[file.key.status]}</p>
            <dl className="facts">
              <dt>Material del que salió</dt>
              <dd data-contenido>
                {file.key.source_document_title === null ? (
                  'No consta: esta respuesta no se importó de ningún documento.'
                ) : (
                  <>
                    {file.key.source_document_title}
                    {file.key.source_version_label === null
                      ? ''
                      : ` · ${file.key.source_version_label}`}
                    {file.key.source_version_status === null
                      ? ''
                      : ` · ${estadoDeVersion(file.key.source_version_status)}`}
                  </>
                )}
              </dd>
            </dl>
            {hrefMaterial !== null && (
              <p>
                <Link className="link" to={hrefMaterial}>
                  Abrir el material en la biblioteca
                </Link>
              </p>
            )}
          </>
        )}

        <h3>Con qué garantía se estudia este banco</h3>
        {file.key_reliability === null ? (
          <p className="hint" data-contenido>
            {file.reliability_source}
          </p>
        ) : (
          <p className="hint">
            <StatusBadge tone={TONO_FIABILIDAD[file.key_reliability] ?? 'info'}>
              {RELIABILITY_LABELS[file.key_reliability] ?? file.key_reliability}
            </StatusBadge>{' '}
            {RELIABILITY_HELP[file.key_reliability] ?? ''}
          </p>
        )}
      </section>

      <section className="card" aria-labelledby="ficha-apuntes">
        <h2 id="ficha-apuntes">Qué dicen los apuntes</h2>
        {file.notes.length === 0 ? (
          <p className="hint">
            Esta pregunta no se ha comprobado contra ningún tema: no hay apuntes que la contesten, ni
            a favor ni en contra.
          </p>
        ) : (
          <ul className="avisos">
            {file.notes.map((contraste: QuestionFileNotes) => {
              const href = notesHref(contraste);
              return (
                <li className="avisos__fila" key={`${contraste.topic_code}-${contraste.anchor}`}>
                  <div className="avisos__cabecera">
                    <p className="avisos__origen">
                      <span className="avisos__tema">{contraste.topic_code}</span>
                      <span data-contenido>{contraste.topic_title}</span>
                    </p>
                    <StatusBadge tone={contraste.coincides ? 'ok' : 'warning'}>
                      {contraste.coincides ? 'coincide con la respuesta' : 'no coincide'}
                    </StatusBadge>
                  </div>
                  <p className="hint">
                    Los apuntes contestan con la letra{' '}
                    <strong>{contraste.answer_letter?.toUpperCase() ?? 'ninguna'}</strong> y la
                    respuesta correcta es <strong>{letras(contraste.expected_letters)}</strong>
                    {contraste.coincides
                      ? ': están de acuerdo, no hay nada que discutir.'
                      : ': aquí hay algo que decidir.'}
                  </p>
                  {contraste.phrase !== null && (
                    <p className="nota-margen">
                      <span className="nota-margen__rotulo">La frase de los apuntes que lo demuestra</span>
                      <span className="nota-margen__texto" data-contenido>
                        {contraste.phrase}
                      </span>
                    </p>
                  )}
                  <p className="hint">
                    {href === null ? (
                      'No se pudo situar en ningún apartado de los apuntes.'
                    ) : (
                      <>
                        <Link className="link" to={href}>
                          Ver el apartado
                        </Link>
                        {contraste.section_title === null ? (
                          ''
                        ) : (
                          <>
                            {' · '}
                            {/* El título del apartado es texto de los apuntes, no de la interfaz:
                                se marca para que la revisión de vocabulario no lo lea como jerga
                                nuestra (un apartado que se llame «versiones» es del temario). */}
                            <span data-contenido>{contraste.section_title}</span>
                          </>
                        )}
                      </>
                    )}
                  </p>
                </li>
              );
            })}
          </ul>
        )}
      </section>

      <section className="card" aria-labelledby="ficha-incidencias">
        <h2 id="ficha-incidencias">Lo que ha señalado el sistema</h2>
        {file.incidents.length === 0 ? (
          <p className="hint">
            Ninguna incidencia sobre esta pregunta: ni su forma, ni su respuesta correcta, ni los
            apuntes han dado motivo para revisarla.
          </p>
        ) : (
          <ul className="avisos">
            {file.incidents.map((incidencia) => (
              <li className="avisos__fila" key={incidencia.id}>
                <div className="avisos__cabecera">
                  <p className="avisos__origen">
                    <span className="incidencias__etiqueta" data-contenido>
                      {INCIDENT_CATEGORY_LABELS[incidencia.category]}
                    </span>
                    <span className="avisos__tema">{incidencia.topic_code}</span>
                  </p>
                  <StatusBadge tone={TONO_INCIDENCIA[incidencia.status]}>
                    {INCIDENT_STATUS_LABELS[incidencia.status]}
                  </StatusBadge>
                </div>
                <details className="incidencias__detalle">
                  <summary>Qué dijo el motor</summary>
                  <p data-contenido>{incidencia.detail}</p>
                </details>
                {incidencia.phrase !== null && (
                  <p className="nota-margen">
                    <span className="nota-margen__rotulo">La frase que lo demuestra</span>
                    <span className="nota-margen__texto" data-contenido>
                      {incidencia.phrase}
                    </span>
                  </p>
                )}
                {incidencia.resolution_note !== null && (
                  <p className="hint" data-contenido>
                    Lo que se hizo: {incidencia.resolution_note}
                  </p>
                )}
              </li>
            ))}
          </ul>
        )}
        <p className="hint">
          <Link className="link" to="/admin/incidencias">
            Ver todas las incidencias del motor
          </Link>
        </p>
      </section>

      {file.exclusion !== null && (
        <section className="card" aria-labelledby="ficha-exclusion">
          <h2 id="ficha-exclusion">Fuera del temario</h2>
          <p className="hint">
            Está marcada como <strong>{EXCLUSION_LABELS[file.exclusion.reason]}</strong> y no entra en
            ningún test ni en la comprobación de los apuntes. Lo decidió{' '}
            <span data-contenido>{file.exclusion.actor}</span> el {dia(file.exclusion.created_at)}.
          </p>
          {file.exclusion.note !== null && (
            <p className="hint" data-contenido>
              {file.exclusion.note}
            </p>
          )}
        </section>
      )}

      <section className="card" aria-labelledby="ficha-marcar">
        <h2 id="ficha-marcar">Marcar la respuesta correcta</h2>
        {file.protection.protected ? (
          <>
            <p className="hint" data-contenido>
              {file.protection.reason}.
            </p>
            <details>
              <summary>Qué bancos están protegidos y por qué ({file.protection.sets.length})</summary>
              <ul className="avisos">
                {file.protection.sets.map((conjunto) => (
                  <li className="avisos__fila" key={conjunto.id}>
                    <p data-contenido>{conjunto.title}</p>
                    <p className="hint" data-contenido>
                      {conjunto.reason}
                      {conjunto.source_document_title === null
                        ? ''
                        : ` · su plantilla: ${conjunto.source_document_title}`}
                    </p>
                  </li>
                ))}
              </ul>
            </details>
          </>
        ) : (
          <>
            <fieldset className="opciones">
              <legend>
                {multiple
                  ? 'Marca todas las respuestas que valen'
                  : 'Marca la respuesta que vale'}
              </legend>
              {file.options.map((opcion) => (
                <label className="opcion" key={opcion.stable_key}>
                  <input
                    type={multiple ? 'checkbox' : 'radio'}
                    name="respuesta-correcta"
                    value={opcion.stable_key}
                    checked={elegidas.includes(opcion.stable_key)}
                    disabled={busy}
                    onChange={() => {
                      alternar(opcion.stable_key);
                    }}
                  />
                  <span className="opcion__titulo">{opcion.stable_key.toUpperCase()}</span>
                  <span className="opcion__texto" data-contenido>
                    {opcion.text}
                  </span>
                </label>
              ))}
            </fieldset>
            <div className="form__row">
              <label className="form__label" htmlFor="nota-de-la-respuesta">
                Por qué (opcional)
              </label>
              <input
                id="nota-de-la-respuesta"
                className="form__input"
                type="text"
                maxLength={500}
                value={notaClave}
                placeholder="los apuntes lo contestan en el apartado de puertos"
                onChange={(evento) => {
                  setNotaClave(evento.target.value);
                }}
              />
            </div>
            <p>
              <button
                className="button"
                type="button"
                disabled={!puedeMarcar}
                aria-label="Guardar la respuesta correcta"
                onClick={() => {
                  onMarkCorrect({ correctOptionKeys: elegidas, note: notaClave });
                }}
              >
                Guardar la respuesta correcta
              </button>{' '}
              {elegidas.length === 0 && (
                <span className="hint">Marca al menos una respuesta.</span>
              )}
            </p>
            <p className="hint">
              Se guarda como una lista de respuestas nueva del banco: la de ahora pasa a{' '}
              <strong>sustituida</strong> y se conserva, así que el cambio se puede leer y deshacer.
              {letrasDisponibles.length > 0
                ? ` Esta pregunta tiene ${String(letrasDisponibles.length)} opción(es).`
                : ''}
            </p>
          </>
        )}
      </section>

      <section className="card" aria-labelledby="ficha-reparar">
        <h2 id="ficha-reparar">Reparar el texto importado</h2>
        {file.repair.reglas.length > 0 ? (
          <>
            <p className="hint">
              Hay <strong>{file.repair.reglas.length}</strong> arreglo(s) que una regla puede hacer sin
              inventarse nada:
            </p>
            <ul className="check-list">
              {file.repair.titulos.map((titulo, indice) => (
                <li className="check-list__item" key={file.repair.reglas[indice] ?? titulo}>
                  {titulo}
                </li>
              ))}
            </ul>
            <p className="hint" data-contenido>
              {file.repair.detalle}
            </p>
            {file.repair.stem !== null && (
              <>
                <h3>Cómo quedaría el enunciado</h3>
                <p className="resultado__enunciado" data-contenido>
                  {file.repair.stem}
                </p>
              </>
            )}
            {file.repair.opciones !== null && (
              <>
                <h3>Cómo quedarían las opciones ({file.repair.opciones.length})</h3>
                <ul className="resultado__opciones">
                  {file.repair.opciones.map((texto, indice) => (
                    <li className="resultado__opcion" key={`${String(indice)}-${texto.slice(0, 20)}`}>
                      <span className="resultado__letra">
                        {String.fromCharCode(65 + indice)}
                      </span>
                      <span className="resultado__texto" data-contenido>
                        {texto}
                      </span>
                    </li>
                  ))}
                </ul>
              </>
            )}
            <div className="form__row">
              <label className="form__label" htmlFor="nota-de-la-reparacion">
                Por qué se repara (obligatorio)
              </label>
              <input
                id="nota-de-la-reparacion"
                className="form__input"
                type="text"
                maxLength={500}
                value={notaReparacion}
                placeholder="la referencia del examen quedó pegada al enunciado"
                onChange={(evento) => {
                  setNotaReparacion(evento.target.value);
                }}
              />
            </div>
            <p>
              <button
                className="button"
                type="button"
                disabled={busy || notaReparacion.trim() === ''}
                aria-label="Reparar y guardar una vista nueva: reparar el texto de la pregunta"
                onClick={() => {
                  onRepair({ note: notaReparacion });
                }}
              >
                Reparar y guardar una vista nueva
              </button>{' '}
              {notaReparacion.trim() === '' && (
                <span className="hint">Escribe por qué antes de guardar.</span>
              )}
            </p>
            <p className="hint">
              El texto de ahora no se pisa: se añade una vista nueva y la de antes queda sustituida,
              con su motivo. Y el sitio de la pregunta —sus temas y sus apuntes— viaja con ella, así
              que no se sale de donde estaba.
            </p>
          </>
        ) : (
          <p className="hint" data-contenido>
            {file.repair.por_que_no ??
              'No hay ningún arreglo que una regla pueda hacer en esta pregunta: su texto se importó bien.'}
          </p>
        )}
      </section>

      <section className="card" aria-labelledby="ficha-historial">
        <h2 id="ficha-historial">Historial</h2>
        <h3>La pregunta</h3>
        <HistorialDeVersiones versiones={file.versions} actual={file.question_version_id} />
        <h3>La respuesta correcta de esta pregunta</h3>
        <HistorialDePlantillas claves={file.keys} />
      </section>

      {notice !== null && <p className="notice notice--inline">{notice}</p>}
      {conflict !== null && (
        <p className="notice notice--inline" role="alert">
          El servidor no lo ha permitido, y dice por qué: <span data-contenido>{conflict}</span>
        </p>
      )}
      {error !== null && (
        <p className="notice notice--inline" role="alert">
          El cambio no se ha podido guardar: {error}
        </p>
      )}
    </>
  );
}

/** El estado de una versión de material, en palabras corrientes. */
function estadoDeVersion(status: string): string {
  const conocidos: Record<string, string> = {
    candidate: 'sin aceptar',
    accepted: 'aceptada',
    outdated: 'desactualizada',
    superseded: 'sustituida',
    withdrawn: 'retirada',
    rejected: 'rechazada',
  };
  return conocidos[status] ?? status;
}

function HistorialDeVersiones({
  versiones,
  actual,
}: {
  versiones: QuestionFileVersion[];
  actual: string;
}) {
  return (
    <div className="apuntes__tabla-marco">
      <table className="table">
        <caption className="table__caption">
          Lo que decía cada vez que se cambió, de la más nueva a la más vieja
        </caption>
        <thead>
          <tr>
            <th scope="col">Vista</th>
            <th scope="col">Estado</th>
            <th scope="col">Opciones</th>
            <th scope="col">Respuesta que tenía</th>
            <th scope="col">Fecha</th>
            <th scope="col">Motivo</th>
          </tr>
        </thead>
        <tbody>
          {versiones.map((version) => (
            <tr key={version.id}>
              <th scope="row">
                {version.version_no}
                {version.id === actual ? ' · la que estás viendo' : ''}
              </th>
              <td>{QUESTION_STATUS_LABELS[version.status]}</td>
              <td>{version.option_count}</td>
              <td>{letras(version.correct_option_keys)}</td>
              <td>{dia(version.created_at)}</td>
              <td data-contenido>{version.note ?? '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function HistorialDePlantillas({ claves }: { claves: QuestionFileKeyVersion[] }) {
  return (
    <div className="apuntes__tabla-marco">
      <table className="table">
        <caption className="table__caption">
          Las listas de respuestas del banco, con lo que cada una decía de esta pregunta
        </caption>
        <thead>
          <tr>
            <th scope="col">Lista</th>
            <th scope="col">Estado</th>
            <th scope="col">Respuesta de esta pregunta</th>
            <th scope="col">Material</th>
            <th scope="col">Aprobada</th>
          </tr>
        </thead>
        <tbody>
          {claves.map((clave) => (
            <tr key={clave.id}>
              <th scope="row">{clave.version_no}</th>
              <td>
                <StatusBadge tone={TONO_PLANTILLA[clave.status] ?? 'info'}>
                  {KEY_STATUS_LABELS[clave.status]}
                </StatusBadge>
              </td>
              <td>{letras(clave.correct_option_keys)}</td>
              <td data-contenido>{clave.source_document_title ?? '—'}</td>
              <td>{dia(clave.approved_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** Las letras que el usuario puede marcar, para las pruebas y para el contrato. */
export type { OptionLetter, QuestionFileRepair };
