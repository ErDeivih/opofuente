import { useCapabilities, useReadiness, useSettings } from '../../api/queries';
import { ErrorState } from '../../components/ErrorState';
import { LoadingState } from '../../components/LoadingState';
import { StatusBadge } from '../../components/StatusBadge';
import { CapabilityList } from './CapabilityList';
import { describeError, formatBytes } from './labels';

/**
 * Estado real del sistema: salud, capacidades y almacenamiento.
 *
 * Todo lo que se muestra aquí viene de la API. Lo que no existe no se dibuja como si
 * existiera: se declara como pendiente con su slice.
 */
export function SystemStatus() {
  const readiness = useReadiness();
  const capabilities = useCapabilities();
  const settings = useSettings();

  return (
    <section className="card" aria-labelledby="estado-sistema">
      <h2 id="estado-sistema">Estado del sistema</h2>

      <div aria-live="polite" className="status-summary">
        {readiness.isPending && <LoadingState label="Comprobando la base de datos…" />}
        {readiness.isError && (
          <ErrorState
            title="No se pudo comprobar el estado"
            message={describeError(readiness.error)}
            onRetry={() => {
              void readiness.refetch();
            }}
          />
        )}
        {readiness.isSuccess &&
          (readiness.data.status === 'ready' ? (
            <StatusBadge tone="ok">listo para trabajar</StatusBadge>
          ) : (
            <StatusBadge tone="blocked">degradado</StatusBadge>
          ))}
      </div>

      {readiness.isSuccess && (
        <ul className="check-list">
          {readiness.data.checks.map((check) => (
            <li key={check.name} className="check-list__item">
              <StatusBadge tone={check.status === 'ok' ? 'ok' : 'blocked'}>{check.name}</StatusBadge>
              <span className="check-list__detail">{check.detail}</span>
            </li>
          ))}
        </ul>
      )}

      <h3>Capacidades</h3>
      {capabilities.isPending && <LoadingState label="Consultando capacidades…" />}
      {capabilities.isError && (
        <ErrorState
          title="No se pudieron consultar las capacidades"
          message={describeError(capabilities.error)}
          onRetry={() => {
            void capabilities.refetch();
          }}
        />
      )}
      {capabilities.isSuccess && <CapabilityList capabilities={capabilities.data.capabilities} />}

      {capabilities.isSuccess && capabilities.data.degradations.length > 0 && (
        <>
          <h3>Degradaciones declaradas</h3>
          <p className="hint">
            La aplicación funciona sin estas piezas. Se listan para que no haya funciones ausentes
            disfrazadas de correctas.
          </p>
          <ul className="degradation-list">
            {capabilities.data.degradations.map((degradation) => (
              <li key={degradation.code}>{degradation.message}</li>
            ))}
          </ul>
        </>
      )}

      <h3>Almacenamiento</h3>
      {settings.isPending && <LoadingState label="Consultando la configuración…" />}
      {settings.isError && (
        <ErrorState
          title="No se pudo leer la configuración"
          message={describeError(settings.error)}
          onRetry={() => {
            void settings.refetch();
          }}
        />
      )}
      {settings.isSuccess && (
        <dl className="facts">
          <dt>Directorio de datos</dt>
          <dd className="facts__path">{settings.data.data_dir}</dd>
          <dt>Espacio libre</dt>
          <dd>{formatBytes(settings.data.disk_free_bytes)}</dd>
          <dt>Proveedor de IA</dt>
          <dd>
            {settings.data.llm.provider}
            {settings.data.llm.sends_data_off_device ? ' (enviaría datos fuera)' : ' (todo local)'}
          </dd>
          <dt>OCR</dt>
          <dd>{settings.data.ocr.tesseract_available ? 'disponible' : 'no disponible'}</dd>
        </dl>
      )}
    </section>
  );
}
