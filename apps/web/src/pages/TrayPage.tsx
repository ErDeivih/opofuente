import { useState } from 'react';
import { Link } from 'react-router-dom';

import type { Issue, Inventory } from '../api/ingestion';
import { isActive } from '../api/ingestion';
import {
  useCancelBatch,
  useConfirmImport,
  useCreateInventory,
  useBatch,
  useBatchIssues,
  useBatchItems,
  useBatches,
  useJob,
  useRepresentations,
  useRetryBatch,
} from '../api/queries';
import { EmptyState } from '../components/EmptyState';
import { ErrorState } from '../components/ErrorState';
import { LoadingState } from '../components/LoadingState';
import { StatusBadge } from '../components/StatusBadge';
import type { StatusTone } from '../components/StatusBadge';
import { IntakeActions } from '../features/ingestion/IntakeActions';
import { TextViewer } from '../features/ingestion/TextViewer';

const STATUS_TONE: Record<string, StatusTone> = {
  queued: 'info',
  running: 'info',
  cancel_requested: 'warning',
  succeeded: 'ok',
  failed: 'blocked',
  cancelled: 'info',
};

const SEVERITY_TONE: Record<string, StatusTone> = {
  info: 'info',
  warning: 'warning',
  error: 'blocked',
};

/** Estados desde los que la API admite un reintento (los demás responden 409). */
const CAN_RETRY: ReadonlySet<string> = new Set(['failed', 'cancelled']);

function formatBytes(value: number): string {
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let size = value;
  let unit = 0;
  while (size >= 1024 && unit < units.length - 1) {
    size /= 1024;
    unit += 1;
  }
  return `${size.toFixed(unit === 0 ? 0 : 1)} ${units[unit] ?? 'B'}`;
}

function describeError(error: unknown): string {
  return error instanceof Error ? error.message : 'Error desconocido';
}

/**
 * Incidencias con su código, su severidad y la ruta relativa.
 *
 * Se muestran tanto en la vista previa (lo que se va a omitir y por qué) como en el lote ya
 * importado: omitir material en silencio sería mentir por omisión.
 */
function IssueList({ issues }: { issues: Issue[] }) {
  if (issues.length === 0) {
    return <p className="hint">Sin incidencias.</p>;
  }
  return (
    <ul className="issues">
      {issues.map((issue, index) => (
        <li key={`${issue.code}-${issue.relative_path ?? ''}-${index}`} className="issues__item">
          <StatusBadge tone={SEVERITY_TONE[issue.severity] ?? 'info'}>{issue.code}</StatusBadge>
          <span>{issue.safe_message}</span>
          {issue.relative_path !== null && issue.relative_path !== undefined && (
            <span className="hint sample__path">{issue.relative_path}</span>
          )}
        </li>
      ))}
    </ul>
  );
}

/**
 * Bandeja (07_UI-UX §4): inventariar una carpeta en lectura y, solo si el usuario lo confirma,
 * importar una copia.
 *
 * Las otras dos formas de entrada del MVP (ficheros sueltos, texto pegado y URL) viven en
 * `IntakeActions`: crean su propio lote, que esta pantalla selecciona para seguir su progreso. El
 * texto que deja la extracción se lee aquí mismo (`TextViewer`), con su calidad y sus avisos.
 */
export function TrayPage() {
  const [sourcePath, setSourcePath] = useState('');
  const [inventory, setInventory] = useState<Inventory | null>(null);
  const [batchId, setBatchId] = useState<string | null>(null);

  const createInventory = useCreateInventory();
  const confirmImport = useConfirmImport();
  const cancelBatch = useCancelBatch();
  const retryBatch = useRetryBatch();

  const batches = useBatches();
  const batch = useBatch(batchId);
  const items = useBatchItems(batchId);
  const issues = useBatchIssues(batchId);
  const job = useJob(batch.data?.batch.job_id);
  const representations = useRepresentations(batchId);

  const isWorking = isActive(batch.data?.batch);

  return (
    <>
      <header className="page__header">
        <h1>Bandeja</h1>
        <p className="page__lead">
          OpoFuente <strong>copia</strong>: nunca mueve, renombra ni borra tus originales. Primero
          inventaría la carpeta en modo lectura y solo después copia lo que confirmes.
        </p>
        {/* La revisión de la clasificación es la continuación natural de la bandeja (07_UI-UX §4):
            aquí entra el material, allí se confirma lo que la aplicación propone sobre él. */}
        <p className="form__row">
          <Link className="button" to="/revision">
            Revisar la clasificación del material
          </Link>
          <span className="hint">
            Lo importado se clasifica en propuestas: se confirman (o se rechazan) en Revisión.
          </span>
        </p>
      </header>

      <section className="card" aria-labelledby="entrada">
        <h2 id="entrada">Entrada</h2>
        <form
          className="form"
          onSubmit={(event) => {
            event.preventDefault();
            createInventory.mutate(sourcePath, {
              onSuccess: (result) => {
                setInventory(result);
                setBatchId(null);
              },
            });
          }}
        >
          <label className="form__label" htmlFor="ruta">
            Carpeta a inventariar (ruta absoluta)
          </label>
          <div className="form__row">
            <input
              id="ruta"
              className="form__input"
              type="text"
              value={sourcePath}
              placeholder="F:\EspacioCodigo\material-para-probar"
              onChange={(event) => {
                setSourcePath(event.target.value);
              }}
            />
            <button className="button" type="submit" disabled={createInventory.isPending}>
              {createInventory.isPending ? 'Inventariando…' : 'Inventariar (solo lectura)'}
            </button>
          </div>
        </form>
        {createInventory.isError && (
          <ErrorState
            title="No se pudo inventariar esa carpeta"
            message={describeError(createInventory.error)}
          />
        )}

        <p className="hint">
          Las tres formas de entrada del MVP están aquí: inventariar una carpeta, copiar ficheros
          sueltos, pegar texto y traer una URL. Ninguna mueve ni borra nada de su origen.
        </p>
      </section>

      <section className="card" aria-labelledby="entradas-directas">
        <h2 id="entradas-directas">Otras formas de entrada</h2>
        <IntakeActions
          onBatchCreated={(created) => {
            setInventory(null);
            setBatchId(created.id);
          }}
        />
      </section>

      {inventory !== null && (
        <section className="card" aria-labelledby="vista-previa">
          <h2 id="vista-previa">Vista previa del inventario</h2>
          <div className="status-summary">
            <StatusBadge tone="info">{inventory.batch.source_path_display}</StatusBadge>
            <span className="hint">{inventory.note}</span>
          </div>

          <dl className="facts">
            <dt>Ficheros a copiar</dt>
            <dd>{inventory.batch.counters.inventoried ?? 0}</dd>
            <dt>Tamaño</dt>
            <dd>{formatBytes(inventory.batch.counters.total_bytes ?? 0)}</dd>
            <dt>Directorios recorridos</dt>
            <dd>{inventory.batch.counters.directories ?? 0}</dd>
            <dt>Omitidos</dt>
            <dd>
              {(inventory.batch.counters.omitted_hidden ?? 0) +
                (inventory.batch.counters.omitted_temporary ?? 0) +
                (inventory.batch.counters.omitted_executable ?? 0) +
                (inventory.batch.counters.omitted_directory ?? 0) +
                (inventory.batch.counters.omitted_unsupported ?? 0)}{' '}
              <span className="hint">(ocultos, temporales, ejecutables, directorios y formatos sin extractor)</span>
            </dd>
            <dt>Enlaces fuera de la carpeta</dt>
            <dd>
              {inventory.batch.counters.linked_outside_root ?? 0}{' '}
              <span className="hint">(no se siguen)</span>
            </dd>
            <dt>Formatos</dt>
            <dd>
              {Object.entries(inventory.batch.formats ?? {})
                .map(([extension, count]) => `${extension} ×${count}`)
                .join(', ') || 'ninguno'}
            </dd>
          </dl>

          {inventory.sample.length > 0 && (
            <>
              <h3>Muestra</h3>
              <ul className="sample">
                {inventory.sample.map((entry) => (
                  <li key={entry.id}>
                    <span className="sample__path">{entry.relative_path}</span>
                    <span className="hint"> {formatBytes(entry.size_bytes)}</span>
                  </li>
                ))}
              </ul>
            </>
          )}

          <h3>Qué se omite y por qué</h3>
          <IssueList issues={inventory.issues} />

          <div className="form__row">
            <button
              className="button"
              type="button"
              disabled={confirmImport.isPending || (inventory.batch.counters.inventoried ?? 0) === 0}
              onClick={() => {
                confirmImport.mutate(inventory.batch.id, {
                  onSuccess: (created) => {
                    setBatchId(created.id);
                  },
                });
              }}
            >
              Importar una copia
            </button>
            <button
              className="button"
              type="button"
              onClick={() => {
                setInventory(null);
              }}
            >
              Cancelar
            </button>
          </div>
          {confirmImport.isError && (
            <ErrorState
              title="No se pudo confirmar la importación"
              message={describeError(confirmImport.error)}
            />
          )}
        </section>
      )}

      {batchId !== null && (
        <section className="card" aria-labelledby="lote">
          <h2 id="lote">Importación</h2>
          {batch.isPending && <LoadingState label="Consultando el lote…" />}
          {batch.isError && (
            <ErrorState
              title="No se pudo consultar el lote"
              message={describeError(batch.error)}
              onRetry={() => {
                void batch.refetch();
              }}
            />
          )}
          {batch.isSuccess && (
            <>
              <div className="status-summary" aria-live="polite">
                <StatusBadge tone={STATUS_TONE[batch.data.batch.status] ?? 'info'}>
                  {batch.data.batch.status}
                </StatusBadge>
                <span className="hint">
                  {job.data === undefined
                    ? 'trabajo en cola'
                    : `${Math.round(job.data.progress * 100)} % · ${job.data.step ?? 'en curso'}`}
                </span>
              </div>
              <p className="hint">
                El trabajo se ejecuta en el servidor local: cerrar esta pestaña no lo cancela.
              </p>

              <dl className="facts">
                <dt>Copiados</dt>
                <dd>
                  {batch.data.batch.counters.copied ?? 0} de {batch.data.batch.counters.total ?? 0}
                </dd>
                <dt>Pendientes</dt>
                <dd>{batch.data.batch.counters.pending ?? 0}</dd>
                <dt>Artefactos</dt>
                <dd>{batch.data.report.artifacts_total}</dd>
                <dt>Informe cuadra</dt>
                <dd>{batch.data.report.balanced ? 'sí' : 'no'}</dd>
              </dl>

              <div className="form__row">
                {isWorking && (
                  <button
                    className="button"
                    type="button"
                    disabled={cancelBatch.isPending}
                    onClick={() => {
                      cancelBatch.mutate(batch.data.batch.id);
                    }}
                  >
                    Cancelar
                  </button>
                )}
                {/* Solo se puede reintentar lo que está parado y a medias: la API responde 409 en
                    cualquier otro estado, así que no se ofrece un botón que fallaría. */}
                {CAN_RETRY.has(batch.data.batch.status) && (
                  <button
                    className="button"
                    type="button"
                    disabled={retryBatch.isPending}
                    onClick={() => {
                      retryBatch.mutate(batch.data.batch.id);
                    }}
                  >
                    Reintentar
                  </button>
                )}
              </div>
              {(retryBatch.isError || cancelBatch.isError) && (
                <ErrorState
                  title="No se pudo cambiar el estado del lote"
                  message={describeError(retryBatch.error ?? cancelBatch.error)}
                />
              )}
              {(batch.data.batch.counters.source_changed ?? 0) > 0 && (
                <p className="hint">
                  Hay {batch.data.batch.counters.source_changed} fichero(s) que cambiaron desde el
                  inventario: no se copian ni se reintentan con ese inventario. Inventaría la carpeta
                  otra vez para revisarlos.
                </p>
              )}
            </>
          )}
        </section>
      )}

      {batchId !== null && items.data !== undefined && items.data.entries.length > 0 && (
        <section className="card" aria-labelledby="entradas">
          <h2 id="entradas">Entradas del lote</h2>
          <table className="table">
            <caption className="table__caption">{items.data.total} entradas</caption>
            <thead>
              <tr>
                <th scope="col">Fichero</th>
                <th scope="col">Estado</th>
                <th scope="col">Tamaño</th>
                <th scope="col">Detalle</th>
              </tr>
            </thead>
            <tbody>
              {items.data.entries.slice(0, 50).map((entry) => (
                <tr key={entry.id}>
                  <th scope="row" className="sample__path">
                    {entry.relative_path}
                  </th>
                  <td>
                    <StatusBadge tone={entry.status === 'hashed' ? 'ok' : entry.status === 'failed' ? 'blocked' : 'info'}>
                      {entry.status}
                    </StatusBadge>
                  </td>
                  <td>{formatBytes(entry.size_bytes)}</td>
                  <td className="hint">{entry.detail ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {batchId !== null && issues.data !== undefined && (
        <section className="card" aria-labelledby="incidencias">
          <h2 id="incidencias">Incidencias del lote</h2>
          <IssueList issues={issues.data.issues} />
        </section>
      )}

      {batchId !== null && (
        <section className="card" aria-labelledby="texto-extraido">
          <h2 id="texto-extraido">Texto extraído</h2>
          {representations.isPending && <LoadingState label="Consultando el texto extraído…" />}
          {representations.isSuccess && (
            <TextViewer representations={representations.data} />
          )}
        </section>
      )}

      <section className="card" aria-labelledby="historial">
        <h2 id="historial">Lotes recientes</h2>
        {batches.isPending && <LoadingState label="Cargando lotes…" />}
        {batches.isError && (
          <ErrorState
            title="No se pudieron cargar los lotes"
            message={describeError(batches.error)}
            onRetry={() => {
              void batches.refetch();
            }}
          />
        )}
        {batches.isSuccess && batches.data.length === 0 && (
          <EmptyState
            title="Todavía no hay lotes"
            description="Cuando inventaríes una carpeta aparecerá aquí, con su informe."
          />
        )}
        {batches.isSuccess && batches.data.length > 0 && (
          <ul className="sample">
            {batches.data.map((row) => (
              <li key={row.id}>
                <button
                  className="button button--link"
                  type="button"
                  onClick={() => {
                    setInventory(null);
                    setBatchId(row.id);
                  }}
                >
                  {row.kind} · {row.source_path_display}
                </button>
                <StatusBadge tone={STATUS_TONE[row.status] ?? 'info'}>{row.status}</StatusBadge>
                <span className="hint"> {row.total_items} entradas</span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </>
  );
}
