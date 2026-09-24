import type { DossierVersion } from '../../api/dossier';
import { EmptyState } from '../../components/EmptyState';
import { ErrorState } from '../../components/ErrorState';
import { LoadingState } from '../../components/LoadingState';

export interface DossierVersionListProps {
  versions: DossierVersion[];
  isPending: boolean;
  isError: boolean;
  onRetry: () => void;
  /** Lee una versión anterior tal como se leyó. */
  onOpen: (versionId: string) => void;
  /** Vuelve a la lectura de hoy (el dossier calculado, no una guardada). */
  onShowToday: () => void;
  /** La versión que se está leyendo ahora mismo, si es una guardada. */
  openVersionId?: string | null;
}

/**
 * Las versiones guardadas del dossier de un tema (S13).
 *
 * Se enseña **cuándo se leyó** y qué tamaño tenía. Sin los recuentos, una lista de fechas no dice si
 * el tema creció o se quedó igual, que es la única razón por la que alguien guarda versiones de lo que
 * sabe.
 */
export function DossierVersionList({
  versions,
  isPending,
  isError,
  onRetry,
  onOpen,
  onShowToday,
  openVersionId = null,
}: DossierVersionListProps) {
  if (isPending) {
    return <LoadingState label="Cargando las versiones guardadas…" />;
  }
  if (isError) {
    return (
      <ErrorState
        title="No se pudieron cargar las versiones"
        message="La API no responde o el tema ya no existe."
        onRetry={onRetry}
      />
    );
  }
  if (versions.length === 0) {
    return (
      <EmptyState
        title="Todavía no hay ninguna versión guardada de este tema"
        description="Guardar una lectura deja lo que el tema dice hoy, para poder compararlo con lo que diga mañana."
        hint="Se guarda aquí mismo, con «Guardar esta lectura»."
      />
    );
  }

  return (
    <>
      <ol className="dossier__versions" aria-label="Versiones guardadas">
        {versions.map((version) => (
          <li key={version.id}>
            <button
              type="button"
              className={
                version.id === openVersionId ? 'link dossier__version--open' : 'link'
              }
              aria-current={version.id === openVersionId ? 'true' : undefined}
              onClick={() => {
                onOpen(version.id);
              }}
            >
              {version.built_at.slice(0, 19).replace('T', ' ')}
            </button>{' '}
            <span className="hint">
              {String(version.sources_count)}{' '}
              {version.sources_count === 1 ? 'fuente' : 'fuentes'} ·{' '}
              {String(version.passages_count)}{' '}
              {version.passages_count === 1 ? 'pasaje' : 'pasajes'}
            </span>
          </li>
        ))}
      </ol>
      {openVersionId !== null && (
        <p>
          <button type="button" className="button" onClick={onShowToday}>
            Volver a la lectura de hoy
          </button>
        </p>
      )}
    </>
  );
}
