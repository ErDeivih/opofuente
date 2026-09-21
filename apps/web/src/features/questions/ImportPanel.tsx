import { useState } from 'react';

import type { DocumentSummary } from '../../api/library';
import type {
  CsvMapping,
  ImportKind,
  QuestionImportReport,
  QuestionStatus,
} from '../../api/questions';
import { DEFAULT_CSV_MAPPING, rejectedRowsCsv } from '../../api/questions';
import { ErrorState } from '../../components/ErrorState';
import { LoadingState } from '../../components/LoadingState';
import { StatusBadge } from '../../components/StatusBadge';

export interface ImportPanelProps {
  onImport: (input: { kind: ImportKind; text: string; mapping: CsvMapping | null }) => void;
  /** Importa las preguntas de la versión **activa** de un documento de la biblioteca (DEBT-010). */
  onImportDocument: (documentVersionId: string) => void;
  /** Documentos de la biblioteca, para elegir de cuál salen las preguntas. */
  documents: DocumentSummary[];
  documentsIsPending: boolean;
  /** Si la biblioteca no se pudo leer: se dice, en lugar de enseñarla como vacía. */
  documentsError: string | null;
  report: QuestionImportReport | null;
  isPending: boolean;
  conflict: string | null;
  error: string | null;
}

const KIND_LABEL: Record<ImportKind, string> = {
  questions: 'preguntas de un texto',
  csv: 'un CSV con columnas',
  json: 'preguntas de un JSON',
  answer_key: 'una plantilla suelta',
  document: 'las preguntas de un documento',
};

/**
 * Importador del banco (04_INGESTION §10): texto, CSV con mapeo de columnas, JSON, plantilla suelta y
 * **desde un documento** de la biblioteca.
 *
 * Cuatro cosas que la pantalla no hace y son a propósito:
 *
 * 1. **no inventa columnas**: el mapeo enseña lo que va a leer y lo que falta se informa;
 * 2. **no esconde lo rechazado**: cada fila que no entró sale con su número y su causa, y se puede
 *    descargar en CSV para arreglarla;
 * 3. **no activa nada**: importar crea preguntas y, si vienen claves, una plantilla en borrador;
 * 4. **no inventa la cita**: importar desde un documento enlaza cada pregunta con el fragmento del
 *    que se leyó su enunciado, y solo se importa la versión **aceptada** del documento —una candidata
 *    no es la versión buena, así que sus preguntas citarían material sin aceptar—. Para importar otra
 *    versión, se acepta antes en la Biblioteca.
 */
export function ImportPanel({
  onImport,
  onImportDocument,
  documents,
  documentsIsPending,
  documentsError,
  report,
  isPending,
  conflict,
  error,
}: ImportPanelProps) {
  const [kind, setKind] = useState<ImportKind>('questions');
  const [text, setText] = useState('');
  const [mapping, setMapping] = useState<CsvMapping>(DEFAULT_CSV_MAPPING);
  const [documento, setDocumento] = useState('');

  /** El documento elegido y su versión **aceptada**: lo que se manda es la versión, no el título. */
  const elegido = documents.find((candidato) => candidato.id === documento) ?? null;
  const versionAceptada =
    elegido?.active_version?.is_accepted === true ? elegido.active_version.id : null;

  function enviar(): void {
    onImport({
      kind,
      text,
      mapping: kind === 'csv' ? mapping : null,
    });
  }

  return (
    <>
      <div className="form__row">
        <label className="form__label" htmlFor="importar-tipo">
          Qué se importa
        </label>
        <select
          id="importar-tipo"
          className="selector__select"
          value={kind}
          onChange={(event) => {
            setKind(event.target.value as ImportKind);
          }}
        >
          {(Object.keys(KIND_LABEL) as ImportKind[]).map((valor) => (
            <option key={valor} value={valor}>
              {KIND_LABEL[valor]}
            </option>
          ))}
        </select>
      </div>

      {kind === 'csv' && (
        <fieldset className="card">
          <legend>Mapeo de columnas</legend>
          <p className="hint">
            El enunciado y al menos dos opciones son imprescindibles; el resto son opcionales. Si una
            columna que se pide no está en el fichero, el informe lo dice y la importación sigue.
          </p>
          <div className="form__row">
            <label className="form__label" htmlFor="mapeo-stem">
              Columna del enunciado
            </label>
            <input
              id="mapeo-stem"
              className="selector__select"
              value={mapping.stem}
              onChange={(event) => {
                setMapping({ ...mapping, stem: event.target.value });
              }}
            />
            <label className="form__label" htmlFor="mapeo-opciones">
              Columnas de opciones (separadas por comas)
            </label>
            <input
              id="mapeo-opciones"
              className="selector__select"
              value={(mapping.options ?? []).join(', ')}
              onChange={(event) => {
                setMapping({
                  ...mapping,
                  options: event.target.value
                    .split(',')
                    .map((columna) => columna.trim())
                    .filter((columna) => columna !== ''),
                });
              }}
            />
          </div>
          <div className="form__row">
            <label className="form__label" htmlFor="mapeo-correct">
              Columna de la clave
            </label>
            <input
              id="mapeo-correct"
              className="selector__select"
              value={mapping.correct ?? ''}
              onChange={(event) => {
                setMapping({
                  ...mapping,
                  correct: event.target.value === '' ? null : event.target.value,
                });
              }}
            />
            <label className="form__label" htmlFor="mapeo-explanation">
              Columna de la explicación
            </label>
            <input
              id="mapeo-explanation"
              className="selector__select"
              value={mapping.explanation ?? ''}
              onChange={(event) => {
                setMapping({
                  ...mapping,
                  explanation: event.target.value === '' ? null : event.target.value,
                });
              }}
            />
            <label className="form__label" htmlFor="mapeo-topic">
              Columna del tema
            </label>
            <input
              id="mapeo-topic"
              className="selector__select"
              value={mapping.topic ?? ''}
              onChange={(event) => {
                setMapping({
                  ...mapping,
                  topic: event.target.value === '' ? null : event.target.value,
                });
              }}
            />
          </div>
        </fieldset>
      )}

      {kind === 'json' && (
        <p className="hint">
          Cada pregunta necesita <code>stem</code> y al menos dos <code>options</code>. Son
          opcionales <code>correct</code> (la letra, la posición o el texto de la opción),{' '}
          <code>explanation</code>, <code>topic</code>, <code>number</code>, <code>reserve</code>,{' '}
          <code>reserve_order</code> y <code>type</code>. Una pregunta mala no aborta el lote: se
          informa con su motivo y el resto entra.
        </p>
      )}

      {kind === 'document' ? (
        <div className="form__row">
          <label className="form__label" htmlFor="importar-documento">
            Documento del que salen las preguntas
          </label>
          {documentsIsPending ? (
            <LoadingState label="Leyendo la biblioteca…" />
          ) : documentsError !== null ? (
            <p className="hint">
              No se ha podido leer la biblioteca, así que no se puede elegir de qué documento salen
              las preguntas: {documentsError}
            </p>
          ) : documents.length === 0 ? (
            <p className="hint">
              La biblioteca todavía no tiene documentos. Un documento nace al promocionar material
              copiado en la Bandeja.
            </p>
          ) : (
            <>
              <select
                id="importar-documento"
                className="selector__select"
                value={documento}
                onChange={(event) => {
                  setDocumento(event.target.value);
                }}
              >
                <option value="">elige un documento</option>
                {documents.map((candidato) => (
                  <option key={candidato.id} value={candidato.id}>
                    {candidato.canonical_title}
                    {candidato.active_version === null ||
                    candidato.active_version === undefined
                      ? ' · sin ninguna versión'
                      : candidato.active_version.is_accepted
                        ? ''
                        : ' · versión sin aceptar'}
                  </option>
                ))}
              </select>
              <button
                className="button"
                type="button"
                disabled={isPending || versionAceptada === null}
                aria-label="Importar las preguntas del documento"
                onClick={() => {
                  if (versionAceptada !== null) {
                    onImportDocument(versionAceptada);
                  }
                }}
              >
                Importar del documento
              </button>
              <p className="hint">
                {elegido === null
                  ? 'Se importan las preguntas de la versión aceptada del documento, y cada una queda con la cita del fragmento del que salió.'
                  : elegido.active_version === null || elegido.active_version === undefined
                    ? `«${elegido.canonical_title}» no tiene ninguna versión: promociona su material en la Bandeja y vuelve aquí.`
                    : !elegido.active_version.is_accepted
                      ? `«${elegido.canonical_title}» tiene una versión sin aceptar: una candidata no es la versión buena, así que sus preguntas citarían material que todavía no se ha aceptado. Acéptala en la Biblioteca y vuelve aquí.`
                      : `Se importa la versión aceptada de «${elegido.canonical_title}», y cada pregunta queda con la cita del fragmento del que salió.`}
              </p>
            </>
          )}
        </div>
      ) : (
        <div className="form__row">
          <label className="form__label" htmlFor="importar-texto">
            {kind === 'csv'
              ? 'Contenido del CSV (con su cabecera)'
              : kind === 'json'
                ? 'Contenido del JSON (lista de preguntas, o un objeto con «questions»)'
                : 'Texto a importar'}
          </label>
          <textarea
            id="importar-texto"
            className="reader"
            rows={10}
            value={text}
            onChange={(event) => {
              setText(event.target.value);
            }}
          />
          <button
            className="button"
            type="button"
            disabled={isPending || text.trim() === ''}
            aria-label="Importar en el conjunto"
            onClick={enviar}
          >
            Importar
          </button>
        </div>
      )}

      {isPending && <LoadingState label="Importando…" />}
      {conflict !== null && (
        <ErrorState title="El servidor rechazó la importación" message={conflict} />
      )}
      {error !== null && <ErrorState title="La importación no se aplicó" message={error} />}

      {report !== null && (
        <section className="card" aria-labelledby="informe-importacion">
          <h3 id="informe-importacion">Qué ha pasado con lo importado</h3>
          <dl className="facts">
            <dt>Creadas</dt>
            <dd>{report.created}</dd>
            <dt>Ya estaban</dt>
            <dd>{report.existing}</dd>
            <dt>Incompletas</dt>
            <dd>{report.incomplete}</dd>
            <dt>Claves guardadas</dt>
            <dd>{report.key_entries}</dd>
            <dt>Claves en conflicto</dt>
            <dd>
              {report.keys_in_conflict}
              {report.keys_in_conflict > 0 && (
                <>
                  {' '}
                  <StatusBadge tone="blocked">no se fusionan solas</StatusBadge>
                </>
              )}
            </dd>
            {report.model_code_detected !== null && report.model_code_detected !== undefined && (
              <>
                <dt>Modelo detectado</dt>
                <dd>{report.model_code_detected}</dd>
              </>
            )}
          </dl>

          {report.evidence_links > 0 && (
            <p className="hint">
              <strong>{report.evidence_links}</strong>{' '}
              {report.evidence_links === 1 ? 'cita creada' : 'citas creadas'}: cada pregunta queda
              enlazada con el fragmento del que se leyó su enunciado, y la ficha puede abrir el
              original en esa página.
            </p>
          )}
          {(report.parts_detected ?? []).length > 0 && (
            <p className="hint">
              El material trae rótulos de parte:{' '}
              <span className="sample__path">{(report.parts_detected ?? []).join(', ')}</span>.{' '}
              <strong>No se guardan</strong> por pregunta: el modelo no tiene dónde, y emparejarlos
              con las partes de la convocatoria sería adivinar (ADR-014). Se dicen aquí en lugar de
              perderse.
            </p>
          )}
          {report.missing_columns.length > 0 && (
            <p className="hint">
              El mapeo pedía columnas que el fichero no trae:{' '}
              <span className="sample__path">{report.missing_columns.join(', ')}</span>. Se ha
              importado sin ellas.
            </p>
          )}
          {report.ignored_columns.length > 0 && (
            <p className="hint">
              Columnas que se leyeron y <strong>no se guardan</strong> todavía:{' '}
              <span className="sample__path">{report.ignored_columns.join(', ')}</span> (deuda
              registrada).
            </p>
          )}
          {report.unmatched_positions.length > 0 && (
            <p className="hint">
              Posiciones de la plantilla sin pregunta a la que pertenecer:{' '}
              <span className="sample__path">{report.unmatched_positions.join(', ')}</span>. No se ha
              inventado ninguna.
            </p>
          )}

          {report.issues.length > 0 && (
            <>
              <h4>Avisos del parser</h4>
              <ul>
                {report.issues.map((aviso) => (
                  <li key={`${String(aviso.line)}-${aviso.code}`} className="hint">
                    línea {aviso.line}: {aviso.code} — {aviso.detail}
                  </li>
                ))}
              </ul>
            </>
          )}

          {report.rejected.length > 0 ? (
            <>
              <h4>Filas rechazadas</h4>
              <p className="hint">
                Una fila mala no aborta el lote: se queda fuera con su causa y se puede arreglar y
                volver a importar.
              </p>
              <table className="table">
                <caption className="table__caption">
                  {report.rejected.length} filas rechazadas con su causa
                </caption>
                <thead>
                  <tr>
                    <th scope="col">Fila</th>
                    <th scope="col">Causa</th>
                    <th scope="col">Detalle</th>
                  </tr>
                </thead>
                <tbody>
                  {report.rejected.map((fila) => (
                    <tr key={`${String(fila.row_number)}-${fila.cause}`}>
                      <th scope="row">{fila.row_number}</th>
                      <td>
                        <span className="sample__path">{fila.cause}</span>
                      </td>
                      <td className="hint">{fila.detail}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <a
                className="button"
                download="filas-rechazadas.csv"
                href={`data:text/csv;charset=utf-8,${encodeURIComponent(
                  rejectedRowsCsv(report.rejected),
                )}`}
              >
                Descargar las filas rechazadas (CSV)
              </a>
            </>
          ) : (
            <p className="hint">No se rechazó ninguna fila.</p>
          )}

          {report.duplicates.length > 0 && (
            <>
              <h4>Duplicados detectados</h4>
              <ul>
                {report.duplicates.map((grupo) => (
                  <li key={grupo.members.join('-')} className="hint">
                    {grupo.members.length} preguntas ({grupo.kind}
                    {grupo.conflicting_keys ? ', claves en conflicto' : ''}):{' '}
                    {grupo.conflicting_keys
                      ? 'no se pueden fusionar sin decidir cuál es la buena'
                      : 'se pueden relacionar'}
                  </li>
                ))}
              </ul>
            </>
          )}
        </section>
      )}
    </>
  );
}

/** Ayuda para quien lee el código: los estados que puede traer una pregunta importada. */
export type ImportedQuestionStatus = QuestionStatus;
