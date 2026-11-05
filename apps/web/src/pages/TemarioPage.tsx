import { useMemo, useState } from 'react';

import { useTemarioDetail, useTemarioList, useTemarioProgress } from '../api/queries';
import { EmptyState } from '../components/EmptyState';
import { ErrorState } from '../components/ErrorState';
import { LoadingState } from '../components/LoadingState';
import { ProgressPanel } from '../features/temario/ProgressPanel';
import { TemarioTree } from '../features/temario/TemarioTree';
import { filterTemario, flattenTopics } from '../features/temario/search';

/**
 * Índice del temario común (ESPECIFICACION §9, pantalla 1).
 *
 * El árbol que se estudia —5 bloques y 40 temas— con búsqueda que perdona tildes, la marca de lo
 * estudiado y el avance. La pantalla no enseña fuentes, versiones ni rutas: eso es de
 * administración, no del alumno (O2).
 */
export function TemarioPage() {
  const [query, setQuery] = useState('');
  const lista = useTemarioList();
  // El código del temario común lo dice el servidor; la pantalla no lo lleva escrito a mano.
  const comun =
    lista.data?.find(
      (item) => item.active_version !== null && item.active_version !== undefined,
    ) ?? null;
  const code = comun?.code ?? null;
  const detalle = useTemarioDetail(code);
  const avance = useTemarioProgress(code);

  const nodos = detalle.data?.nodes;
  const filtrados = useMemo(() => filterTemario(nodos ?? [], query), [nodos, query]);
  const buscando = query.trim() !== '';
  const temasEncontrados = useMemo(() => flattenTopics(filtrados).length, [filtrados]);
  const resumen = !buscando
    ? ''
    : temasEncontrados === 0
      ? 'Ningún tema coincide con la búsqueda'
      : temasEncontrados === 1
        ? '1 tema'
        : `${String(temasEncontrados)} temas`;

  return (
    <>
      <header className="page__header">
        <h1>Temario</h1>
        {detalle.data !== undefined && (
          <p className="page__lead">
            <strong>{detalle.data.counts.block ?? 0}</strong> bloques ·{' '}
            <strong>{detalle.data.counts.topic ?? 0}</strong> temas
          </p>
        )}
      </header>

      {lista.isPending && (
        <section className="card">
          <LoadingState label="Cargando el temario…" />
        </section>
      )}
      {lista.isError && (
        <section className="card">
          <ErrorState
            title="No se pudo cargar el temario"
            message="Inténtalo de nuevo."
            onRetry={() => {
              void lista.refetch();
            }}
          />
        </section>
      )}
      {lista.isSuccess && comun === null && (
        <section className="card">
          <EmptyState
            title="Todavía no hay temario común"
            description="Cuando haya un temario activo aparecerá aquí."
          />
        </section>
      )}

      {code !== null && detalle.isPending && (
        <section className="card">
          <LoadingState label="Cargando el temario…" />
        </section>
      )}
      {code !== null && detalle.isError && (
        <section className="card">
          <ErrorState
            title="No se pudo cargar el temario"
            message="Inténtalo de nuevo."
            onRetry={() => {
              void detalle.refetch();
            }}
          />
        </section>
      )}
      {detalle.isSuccess && (
        <section className="card" aria-labelledby="temario-bloques">
          <h2 id="temario-bloques">Temas</h2>
          <div className="form">
            <label className="form__label" htmlFor="temario-busqueda">
              Buscar un tema
            </label>
            <div className="form__row">
              <input
                id="temario-busqueda"
                className="form__input"
                type="search"
                value={query}
                autoComplete="off"
                onChange={(event) => {
                  setQuery(event.target.value);
                }}
              />
            </div>
          </div>
          <p className="hint" role="status" aria-live="polite">
            {resumen}
          </p>

          {nodos === undefined || nodos.length === 0 ? (
            <EmptyState
              title="El temario todavía no tiene temas"
              description="Cuando se publique el temario, aparecerá aquí."
            />
          ) : filtrados.length === 0 ? (
            <EmptyState
              title="Sin resultados"
              description="Prueba con otra palabra o con el código del tema."
            />
          ) : (
            <TemarioTree nodes={filtrados} searching={buscando} />
          )}
        </section>
      )}

      {code !== null && avance.isPending && (
        <section className="card">
          <LoadingState label="Cargando el avance…" />
        </section>
      )}
      {code !== null && avance.isError && (
        <section className="card">
          <ErrorState
            title="No se pudo cargar el avance"
            message="Inténtalo de nuevo."
            onRetry={() => {
              void avance.refetch();
            }}
          />
        </section>
      )}
      {avance.isSuccess && <ProgressPanel progress={avance.data} />}
    </>
  );
}
