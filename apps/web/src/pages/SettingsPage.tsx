import { useState } from 'react';

import type { Backup } from '../api/maintenance';
import { PURGE_ACTIONS, type PurgeActionValue } from '../api/maintenance';
import { formatearNota } from '../lib/numeros';

/** Las tres acciones de retirada, en el orden en que se enseñan. */
const PURGE_ACTION_VALUES = Object.keys(PURGE_ACTIONS) as PurgeActionValue[];
import {
  useBackups,
  useCapabilities,
  useCreateBackup,
  useDiagnostic,
  useDiagnosticText,
  useExecuteRestore,
  useHousekeeping,
  useIndexHealth,
  usePurge,
  useReindex,
  useSettings,
  useValidateRestore,
  useVerifyBackup,
} from '../api/queries';
import { ErrorState } from '../components/ErrorState';
import { LoadingState } from '../components/LoadingState';
import { StatusBadge } from '../components/StatusBadge';
import { CapabilityList } from '../features/system/CapabilityList';
import {
  destinationLabel,
  describeError as describeFailure,
  formatBytes,
} from '../features/system/labels';

/**
 * Ajustes (07_UI-UX §11): ruta de datos y uso de disco, capacidades instaladas, privacidad explicada,
 * copia/restauración, exportación, higiene del almacén y diagnóstico con logs saneados.
 *
 * Tres decisiones que se ven en la pantalla:
 *
 * 1. **nada se hace sin enseñar antes lo que va a pasar**: la restauración se previsualiza (validación
 *    sin escribir) y la retirada de material enseña la lista con sus motivos y sus tamaños;
 * 2. **lo que no se sabe se dice**: un área que no se ha podido medir se muestra como no medible, y
 *    `unknown` en el destino de un proveedor se presenta como «no se puede determinar», nunca como
 *    «local»;
 * 3. **el diagnóstico se puede copiar tal cual**: el mismo texto que se enseña es el que se pega en
 *    una incidencia, ya saneado por el servidor.
 */
export function SettingsPage() {
  const settings = useSettings();
  const capabilities = useCapabilities();
  const backups = useBackups();
  const housekeeping = useHousekeeping();
  const indexHealth = useIndexHealth();
  const diagnostic = useDiagnostic();

  const crear = useCreateBackup();
  const verificar = useVerifyBackup();
  const validar = useValidateRestore();
  const restaurar = useExecuteRestore();
  const limpiar = usePurge();
  const reindexar = useReindex();
  const texto = useDiagnosticText();

  const [nota, setNota] = useState('');
  const [aviso, setAviso] = useState<string | null>(null);
  const [backupAElegir, setBackupAElegir] = useState<string | null>(null);
  const [accionAConfirmar, setAccionAConfirmar] = useState<PurgeActionValue | null>(null);
  const [diagnosticoCopiado, setDiagnosticoCopiado] = useState<string | null>(null);

  const ocupado =
    crear.isPending ||
    verificar.isPending ||
    validar.isPending ||
    restaurar.isPending ||
    limpiar.isPending ||
    reindexar.isPending;

  if (settings.isPending) {
    return <LoadingState label="Leyendo la configuración…" />;
  }
  if (settings.isError) {
    return (
      <ErrorState
        title="No se pudo leer la configuración"
        message={describeFailure(settings.error)}
        onRetry={() => {
          void settings.refetch();
        }}
      />
    );
  }

  const datos = settings.data;
  // Una sección por consulta, y **cada una con su estado**: así una consulta que aún no ha llegado no
  // deja en blanco a las demás. Se comprueba el `data` de cada hook donde se usa (abajo), no un
  // agregado: mezclar «alguna consulta cargando» con «esta sección ya tiene datos» es la forma de que
  // una sección aparezca vacía sin que nada haya fallado.
  const informe = housekeeping.data ?? null;
  const copias: Backup[] = backups.data?.backups ?? [];
  const elegida = copias.find((copia) => copia.id === backupAElegir) ?? null;
  const previsualizacion = validar.data ?? null;

  return (
    <>
      <header className="page__header">
        <h1>Ajustes</h1>
        <p className="hint">
          Todo lo que la aplicación hace con tus datos, dicho sin adornos: dónde los guarda, qué
          capacidades hay de verdad, a dónde sale el contenido si configuras un proveedor, y cómo se
          copia y se restaura.
        </p>
      </header>

      {aviso !== null && (
        <p className="notice" role="status">
          {aviso}
        </p>
      )}

      <section className="card" aria-labelledby="ajustes-datos">
        <h2 id="ajustes-datos">Datos y disco</h2>
        <dl className="facts">
          <dt>Versión</dt>
          <dd>
            {datos.version} · esquema <span className="sample__path">{diagnostic.data?.schema_revision ?? '…'}</span>
          </dd>
          <dt>Ruta de datos</dt>
          <dd className="sample__path">{datos.data_dir}</dd>
          <dt>Base de datos</dt>
          <dd className="sample__path">{datos.database_file}</dd>
          <dt>Disco</dt>
          <dd>
            {formatBytes(datos.disk_free_bytes)} libres de {formatBytes(datos.disk_total_bytes)}
          </dd>
          <dt>Servidor</dt>
          <dd>
            {datos.host}:{datos.port} · registro {datos.log_level}
          </dd>
        </dl>
        <p className="hint">
          Los ajustes se editan en <span className="sample__path">.env</span> y en las variables de
          entorno: esta pantalla <strong>no</strong> escribe configuración, la lee y la explica.
        </p>
      </section>

      <section className="card" aria-labelledby="ajustes-uso">
        <h2 id="ajustes-uso">Uso del almacén</h2>
        {housekeeping.isPending ? (
          <LoadingState label="Midiendo el almacén…" />
        ) : informe === null ? (
          <p className="hint">No se ha podido medir el almacén.</p>
        ) : (
          <>
            <table className="table">
              <caption className="table__caption">
                Total {formatBytes(informe.total_bytes)} · recuperable{' '}
                {formatBytes(informe.reclaimable_bytes)}
              </caption>
              <thead>
                <tr>
                  <th scope="col">Área</th>
                  <th scope="col">Ficheros</th>
                  <th scope="col">Tamaño</th>
                </tr>
              </thead>
              <tbody>
                {informe.usage.map((area) => (
                  <tr key={area.area}>
                    <th scope="row">
                      {area.note ?? area.area}
                      {!area.readable && (
                        <>
                          {' '}
                          <StatusBadge tone="warning">no se ha podido medir</StatusBadge>
                        </>
                      )}
                    </th>
                    <td>{area.file_count}</td>
                    <td>{area.readable ? formatBytes(area.size_bytes) : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="hint">
              Aquí no se borra nada solo: cada bloque de abajo enseña lo que se puede retirar y su
              motivo, y hay que confirmarlo.
            </p>
          </>
        )}
      </section>

      {housekeeping.data !== undefined && housekeeping.data.candidates.length > 0 && (
        <section className="card" aria-labelledby="ajustes-limpieza">
          <h2 id="ajustes-limpieza">Qué se puede retirar</h2>
          <ul>
            {PURGE_ACTION_VALUES.map((accion) => {
              const candidatos = housekeeping.data.candidates.filter((c) => c.action === accion);
              if (candidatos.length === 0) {
                return null;
              }
              const bytes = candidatos.reduce((suma, c) => suma + c.size_bytes, 0);
              const etiqueta = PURGE_ACTIONS[accion].label;
              return (
                <li key={accion}>
                  <p>
                    <strong>{etiqueta}</strong>:{' '}
                    {candidatos.length === 1
                      ? '1 elemento'
                      : `${String(candidatos.length)} elementos`}
                    {bytes > 0 && ` · ${formatBytes(bytes)}`}
                  </p>
                  <p className="hint">{PURGE_ACTIONS[accion].why}</p>
                  <ul>
                    {candidatos.slice(0, 5).map((candidato) => (
                      <li key={candidato.reference} className="hint">
                        <span className="sample__path">{candidato.display}</span> —{' '}
                        {candidato.detail}
                      </li>
                    ))}
                  </ul>
                  {candidatos.length > 5 && (
                    <p className="hint">y {candidatos.length - 5} más de la misma clase.</p>
                  )}
                  {accionAConfirmar === accion ? (
                    <p className="form__row">
                      <span>
                        Se van a retirar {candidatos.length} elemento(s)
                        {bytes > 0 && ` (${formatBytes(bytes)})`}. Lo referenciado no se toca.
                      </span>
                      <button
                        className="button"
                        type="button"
                        disabled={ocupado}
                        onClick={() => {
                          limpiar.mutate(
                            { action: accion, references: null },
                            {
                              onSuccess: (resultado) => {
                                setAccionAConfirmar(null);
                                setAviso(
                                  `${resultado.detail}${resultado.skipped.length > 0 ? ` (${String(resultado.skipped.length)} sin poder retirar)` : ''}`,
                                );
                              },
                            },
                          );
                        }}
                      >
                        Sí, retirar
                      </button>
                      <button
                        className="button"
                        type="button"
                        onClick={() => {
                          setAccionAConfirmar(null);
                        }}
                      >
                        Cancelar
                      </button>
                    </p>
                  ) : (
                    <button
                      className="button"
                      type="button"
                      disabled={ocupado}
                      // El nombre accesible va explícito: el texto del botón lleva comillas angulares
                      // y una interpolación, y un nombre estable es lo que permite comprobarlo.
                      aria-label={`Retirar: ${etiqueta}`}
                      onClick={() => {
                        setAccionAConfirmar(accion);
                      }}
                    >
                      Retirar «{etiqueta}»
                    </button>
                  )}
                </li>
              );
            })}
          </ul>
          {limpiar.isError && <p className="notice">{describeFailure(limpiar.error)}</p>}
        </section>
      )}

      <section className="card" aria-labelledby="ajustes-capacidades">
        <h2 id="ajustes-capacidades">Capacidades instaladas</h2>
        {capabilities.isPending ? (
          <LoadingState label="Comprobando capacidades…" />
        ) : capabilities.data === undefined ? (
          <p className="hint">No se han podido leer las capacidades.</p>
        ) : (
          <CapabilityList capabilities={capabilities.data.capabilities} />
        )}
      </section>

      <section className="card" aria-labelledby="ajustes-privacidad">
        <h2 id="ajustes-privacidad">Privacidad: a dónde sale tu contenido</h2>
        <p className="hint">
          Se calcula sobre la dirección real de cada proveedor, no sobre su nombre. «No se puede
          determinar» cuenta como que sí sale: es la respuesta conservadora.
        </p>
        <dl className="facts">
          <dt>Modelo de lenguaje</dt>
          <dd>
            <StatusBadge tone={datos.llm.destination === 'remote' ? 'warning' : 'ok'}>
              {destinationLabel(datos.llm.destination)}
            </StatusBadge>{' '}
            <span className="hint">{datos.llm.destination_reason}</span>
          </dd>
          <dt>Embeddings</dt>
          <dd>
            <StatusBadge tone={datos.embeddings.destination === 'remote' ? 'warning' : 'ok'}>
              {destinationLabel(datos.embeddings.destination)}
            </StatusBadge>{' '}
            <span className="hint">{datos.embeddings.destination_reason}</span>
          </dd>
          <dt>Clave del proveedor</dt>
          <dd>
            {datos.llm.api_key_configured
              ? 'configurada (no se muestra ni se devuelve nunca)'
              : 'no hay clave configurada'}
          </dd>
        </dl>
      </section>

      <section className="card" aria-labelledby="ajustes-copias">
        <h2 id="ajustes-copias">Copia y restauración</h2>
        <div className="form__row">
          <label className="form__label" htmlFor="copia-nota">
            Nota de la copia (opcional)
          </label>
          <input
            id="copia-nota"
            className="selector__select"
            value={nota}
            onChange={(event) => {
              setNota(event.target.value);
            }}
          />
          <button
            className="button"
            type="button"
            disabled={ocupado}
            onClick={() => {
              crear.mutate(nota.trim() === '' ? null : nota.trim(), {
                onSuccess: (copia) => {
                  setNota('');
                  setAviso(`Copia hecha: ${copia.id} (${formatBytes(copia.size_bytes)}).`);
                },
              });
            }}
          >
            Hacer una copia ahora
          </button>
        </div>
        {crear.isError && <p className="notice">{describeFailure(crear.error)}</p>}

        {backups.isPending ? (
          <LoadingState label="Leyendo las copias…" />
        ) : copias.length === 0 ? (
          <p className="hint">
            Todavía no hay copias. Una copia incluye la base de datos, el material copiado y el texto
            extraído, con el hash de cada fichero.
          </p>
        ) : (
          <table className="table">
            <caption className="table__caption">Copias de seguridad</caption>
            <thead>
              <tr>
                <th scope="col">Copia</th>
                <th scope="col">Fecha</th>
                <th scope="col">Tamaño</th>
                <th scope="col">Se puede restaurar</th>
                <th scope="col">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {copias.map((copia) => (
                <tr key={copia.id} aria-selected={copia.id === backupAElegir}>
                  <th scope="row">
                    <span className="sample__path">{copia.id}</span>
                    {copia.note !== null && <p className="hint">{copia.note}</p>}
                  </th>
                  <td>{copia.created_at.replace('T', ' ').slice(0, 19)}</td>
                  <td>{formatBytes(copia.size_bytes)}</td>
                  <td>
                    <StatusBadge tone={copia.restorable ? 'ok' : 'warning'}>
                      {copia.restorable ? 'sí' : 'no'}
                    </StatusBadge>{' '}
                    <span className="hint">{copia.restorable_reason}</span>
                  </td>
                  <td>
                    <button
                      className="button"
                      type="button"
                      disabled={ocupado}
                      onClick={() => {
                        verificar.mutate(copia.id, {
                          onSuccess: (informeVerificacion) => {
                            setAviso(
                              informeVerificacion.verified
                                ? `La copia ${copia.id} está entera: ${String(informeVerificacion.backup.file_count)} fichero(s) con su hash correcto.`
                                : `La copia ${copia.id} tiene problemas: ${informeVerificacion.problems.join('; ')}`,
                            );
                          },
                        });
                      }}
                    >
                      Verificar
                    </button>{' '}
                    <button
                      className="button"
                      type="button"
                      disabled={ocupado || !copia.restorable}
                      onClick={() => {
                        setBackupAElegir(copia.id);
                        validar.mutate(copia.id, {
                          onSuccess: (vista) => {
                            setAviso(
                              vista.can_restore
                                ? 'La copia se puede restaurar. Revisa la previsualización antes de seguir.'
                                : `No se puede restaurar: ${vista.blockers.join('; ')}`,
                            );
                          },
                        });
                      }}
                    >
                      Previsualizar restauración
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {verificar.isError && <p className="notice">{describeFailure(verificar.error)}</p>}

        {previsualizacion !== null && elegida !== null && (
          <div className="card notice" aria-labelledby="ajustes-preview">
            <h3 id="ajustes-preview">Restaurar «{elegida.id}»</h3>
            <ul>
              <li>
                Se sustituirá: <span className="sample__path">{previsualizacion.targets.join(', ')}</span>
              </li>
              <li>
                Necesita {formatBytes(previsualizacion.needed_bytes)} y hay{' '}
                {previsualizacion.free_bytes < 0
                  ? 'espacio sin determinar'
                  : formatBytes(previsualizacion.free_bytes)}{' '}
                libres.
              </li>
              <li>{previsualizacion.previous_backup_note}</li>
              {previsualizacion.missing_scope.length > 0 && (
                <li>
                  La copia no trae todo el alcance habitual: faltan{' '}
                  {previsualizacion.missing_scope.join(', ')}.
                </li>
              )}
            </ul>
            {restaurar.data !== undefined ? (
              <p role="status">
                Restauración hecha: {String(restaurar.data.restored.length)} fichero(s).{' '}
                {restaurar.data.health_ok
                  ? restaurar.data.health_detail
                  : `Atención: ${restaurar.data.health_detail}`}
              </p>
            ) : (
              <p className="form__row">
                <button
                  className="button"
                  type="button"
                  disabled={ocupado || !previsualizacion.can_restore}
                  onClick={() => {
                    restaurar.mutate(elegida.id, {
                      onSuccess: (resultado) => {
                        setAviso(
                          resultado.health_ok
                            ? 'Restauración completada y comprobada.'
                            : 'La restauración se hizo, pero la comprobación posterior falló: mira el detalle.',
                        );
                      },
                    });
                  }}
                >
                  Restaurar esta copia
                </button>
                <button
                  className="button"
                  type="button"
                  onClick={() => {
                    setBackupAElegir(null);
                    validar.reset();
                  }}
                >
                  Cancelar
                </button>
              </p>
            )}
            {restaurar.isError && <p className="notice">{describeFailure(restaurar.error)}</p>}
          </div>
        )}
      </section>

      <section className="card" aria-labelledby="ajustes-indice">
        <h2 id="ajustes-indice">Índice de búsqueda</h2>
        {indexHealth.isPending ? (
          <LoadingState label="Comprobando el índice…" />
        ) : indexHealth.data === undefined ? (
          <p className="hint">No se ha podido comprobar el índice.</p>
        ) : (
          <>
            <p>
              <StatusBadge tone={indexHealth.data.healthy ? 'ok' : 'warning'}>
                {indexHealth.data.healthy ? 'completo' : 'incompleto'}
              </StatusBadge>{' '}
              {indexHealth.data.detail}
            </p>
            <div className="form__row">
              <button
                className="button"
                type="button"
                disabled={ocupado}
                onClick={() => {
                  reindexar.mutate(undefined, {
                    onSuccess: (resultado) => {
                      setAviso(
                        `${resultado.detail} (${formatearNota(resultado.took_seconds)} s; antes ${String(resultado.before)}, ahora ${String(resultado.after)})`,
                      );
                    },
                  });
                }}
              >
                Rehacer el índice
              </button>
            </div>
            <p className="hint">
              El índice es derivado: el texto de las evidencias es la verdad. Rehacerlo no puede
              perder nada y sirve para reparar un índice que se haya quedado atrás.
            </p>
            {reindexar.isError && <p className="notice">{describeFailure(reindexar.error)}</p>}
          </>
        )}
      </section>

      <section className="card" aria-labelledby="ajustes-exportacion">
        <h2 id="ajustes-exportacion">Exportación</h2>
        <p className="hint">
          Las exportaciones (Markdown/Obsidian y Anki CSV) se hacen desde{' '}
          <a href="/errores">Errores</a>, junto a la cola de repaso, porque es ahí donde se elige qué
          se lleva.
        </p>
      </section>

      <section className="card" aria-labelledby="ajustes-diagnostico">
        <h2 id="ajustes-diagnostico">Diagnóstico y registros saneados</h2>
        <div className="form__row">
          <button
            className="button"
            type="button"
            onClick={() => {
              texto.mutate(undefined, {
                onSuccess: (contenido) => {
                  setDiagnosticoCopiado(contenido);
                },
              });
            }}
          >
            Preparar el diagnóstico en texto
          </button>
        </div>
        <p className="hint">
          El diagnóstico no lleva contenido, ni claves, ni rutas completas: las rutas van abreviadas y
          el registro pasa por el saneado de secretos. Es lo que se puede pegar en una incidencia.
        </p>
        {diagnostic.data !== undefined && (
          <>
            <p className="hint">
              Última generación: {diagnostic.data.generated_at.replace('T', ' ').slice(0, 19)} ·{' '}
              {diagnostic.data.log_tail.length} línea(s) de registro
            </p>
            <ul className="hint">
              {Object.entries(diagnostic.data.counts).map(([clave, valor]) => (
                <li key={clave}>
                  {clave}: {valor}
                </li>
              ))}
            </ul>
          </>
        )}
        {diagnosticoCopiado !== null && (
          <textarea
            className="reader"
            rows={12}
            readOnly
            aria-label="Diagnóstico sanitizado"
            value={diagnosticoCopiado}
          />
        )}
        {texto.isError && <p className="notice">{describeFailure(texto.error)}</p>}
      </section>

      <section className="card" aria-labelledby="ajustes-limites">
        <h2 id="ajustes-limites">Límites en vigor</h2>
        <dl className="facts">
          <dt>Tamaño por fichero</dt>
          <dd>{formatBytes(datos.limits.max_file_bytes)}</dd>
          <dt>Entradas por lote</dt>
          <dd>{datos.limits.max_batch_entries}</dd>
          <dt>Descarga por URL</dt>
          <dd>
            {formatBytes(datos.limits.max_url_bytes)} · {datos.limits.max_url_redirects} redirección(es)
          </dd>
          <dt>Texto pegado</dt>
          <dd>{formatBytes(datos.limits.max_paste_bytes)}</dd>
          <dt>ZIP</dt>
          <dd>
            {datos.limits.max_zip_entries} entradas · {formatBytes(datos.limits.max_zip_uncompressed_bytes)}{' '}
            · ratio {datos.limits.max_zip_ratio} · profundidad {datos.limits.max_zip_depth}
          </dd>
          <dt>PDF</dt>
          <dd>{datos.limits.max_pdf_pages} páginas</dd>
          <dt>Worker</dt>
          <dd>
            sondeo cada {datos.limits.worker_poll_seconds} s · lease {datos.limits.job_lease_seconds} s
          </dd>
        </dl>
      </section>
    </>
  );
}
