import { useState } from 'react';

import { isApiError } from '../api/client';
import { CHANGE_STATUS_LABEL, SECTION_KIND_LABEL, changeSummary } from '../api/changes';
import {
  useChangeSets,
  useConfirmChangeSet,
  useDerivedArtifacts,
  useDiscardChangeSet,
  useResolveDerivedArtifact,
} from '../api/queries';
import { ErrorState } from '../components/ErrorState';
import { LoadingState } from '../components/LoadingState';
import { StatusBadge } from '../components/StatusBadge';

function describeError(error: unknown): string {
  return error instanceof Error ? error.message : 'Error desconocido';
}

const KIND_TONE: Record<string, 'ok' | 'warning' | 'info' | 'blocked'> = {
  changed: 'warning',
  removed: 'blocked',
  added: 'info',
  unchanged: 'ok',
};

/**
 * Cambios e invalidación (07_UI-UX §10 y RF-09).
 *
 * Tres cosas que la pantalla hace porque son la razón de ser del slice:
 *
 * 1. **enseña el diff antes de aplicar nada**: la propuesta se puede mirar entera —sección a sección y
 *    con los derivados que quedarían por revisar—, y confirmar es una decisión explícita;
 * 2. **dice qué no decide**: el aviso de que la aplicación no interpreta el efecto jurídico está en la
 *    propia tarjeta del cambio, no en un pie de página;
 * 3. **separa lo que se puede revisar de lo que no**: un resumen se marca y se revisa; una respuesta
 *    guardada se marca pero no se reescribe, y se dice.
 */
export function ChangesPage() {
  const [seleccionado, setSeleccionado] = useState<string | null>(null);
  const cambios = useChangeSets();
  const pendientes = useDerivedArtifacts(true);
  const confirmar = useConfirmChangeSet();
  const descartar = useDiscardChangeSet();
  const resolver = useResolveDerivedArtifact();

  const conflictoConfirmar = isApiError(confirmar.error, 409) ? describeError(confirmar.error) : null;
  const errorConfirmar =
    confirmar.error === null || conflictoConfirmar !== null ? null : describeError(confirmar.error);
  const conflictoDescartar = isApiError(descartar.error, 409) ? describeError(descartar.error) : null;
  const errorDescartar =
    descartar.error === null || conflictoDescartar !== null ? null : describeError(descartar.error);

  const cambio = cambios.data?.find((item) => item.id === seleccionado) ?? cambios.data?.[0] ?? null;

  return (
    <>
      <header className="page__header">
        <h1>Cambios</h1>
        <p className="page__lead">
          Cuando llega una versión nueva de un material, OpoFuente compara las dos y dice qué depende
          de lo que ha cambiado. Nada se aplica hasta que lo confirmas, y lo que cambió de texto no
          decide por ti si algo sigue valiendo.
        </p>
      </header>

      {cambios.isPending && <LoadingState label="Leyendo los cambios…" />}
      {cambios.isError && (
        <ErrorState
          title="No se pudieron leer los cambios"
          message="La API no responde o la base de datos no está migrada."
          onRetry={() => {
            void cambios.refetch();
          }}
        />
      )}

      {cambios.data !== undefined && cambios.data.length === 0 && (
        <section className="card" aria-labelledby="sin-cambios">
          <h2 id="sin-cambios">Sin cambios</h2>
          <p className="hint">
            No hay ninguna versión nueva pendiente de revisar. Un cambio aparece cuando promocionas
            una segunda versión de un documento que ya tenía una aceptada: entonces se compara y se
            dice qué derivados dependen de lo que cambió.
          </p>
        </section>
      )}

      {cambios.data !== undefined && cambios.data.length > 0 && (
        <section className="card" aria-labelledby="lista-cambios">
          <h2 id="lista-cambios">Propuestas y cambios</h2>
          <ul className="sample" aria-label="Cambios de versión">
            {cambios.data.map((item) => (
              <li key={item.id}>
                <button
                  className="button button--link"
                  type="button"
                  aria-pressed={item.id === cambio?.id}
                  onClick={() => {
                    setSeleccionado(item.id);
                  }}
                >
                  {item.document_title}: {item.previous_version_label ?? item.previous_version_id} →{' '}
                  {item.new_version_label ?? item.new_version_id}
                </button>{' '}
                <StatusBadge tone={item.status === 'proposed' ? 'warning' : 'info'}>
                  {CHANGE_STATUS_LABEL[item.status]}
                </StatusBadge>{' '}
                <span className="hint">
                  {item.created_at.slice(0, 10)} · {changeSummary(item)}
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {cambio !== null && (
        <section className="card" aria-labelledby="detalle-cambio">
          <h2 id="detalle-cambio">Qué ha cambiado</h2>
          <p className="hint">{cambio.document_title}</p>
          <table className="table" aria-label="Diff por sección">
            <thead>
              <tr>
                <th scope="col">Sección</th>
                <th scope="col">Qué le ha pasado</th>
                <th scope="col">Antes</th>
                <th scope="col">Después</th>
              </tr>
            </thead>
            <tbody>
              {cambio.sections.map((seccion) => (
                <tr key={seccion.label}>
                  <th scope="row">{seccion.label}</th>
                  <td>
                    <StatusBadge tone={KIND_TONE[seccion.kind] ?? 'info'}>
                      {SECTION_KIND_LABEL[seccion.kind]}
                    </StatusBadge>
                  </td>
                  <td>
                    {seccion.left === null || seccion.left === undefined ? (
                      <span className="hint">—</span>
                    ) : (
                      <pre className="reader">{seccion.left}</pre>
                    )}
                  </td>
                  <td>
                    {seccion.right === null || seccion.right === undefined ? (
                      <span className="hint">—</span>
                    ) : (
                      <pre className="reader">{seccion.right}</pre>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="notice">
            <h3>Qué depende de lo que ha cambiado</h3>
            {cambio.affected.length === 0 ? (
              <p className="hint">
                Ningún derivado depende de las secciones que han cambiado: confirmar el cambio no
                obliga a revisar nada de lo que hay guardado.
              </p>
            ) : (
              <ul className="evidence" aria-label="Derivados afectados">
                {cambio.affected.map((item) => (
                  <li key={`${item.kind}-${item.id}`}>
                    <StatusBadge tone={item.reviewable ? 'warning' : 'info'}>
                      {item.reviewable ? 'por revisar' : 'no se revisa'}
                    </StatusBadge>{' '}
                    <strong>{item.title}</strong> <span className="hint">· {item.reason}</span>
                  </li>
                ))}
              </ul>
            )}
            <p className="hint">{cambio.effect_note}</p>
            {cambio.notes.map((nota) => (
              <p className="hint" key={nota}>
                {nota}
              </p>
            ))}
          </div>

          {cambio.status === 'proposed' ? (
            <div className="form__row">
              <button
                className="button"
                type="button"
                disabled={confirmar.isPending || descartar.isPending}
                onClick={() => {
                  confirmar.mutate(cambio.id);
                }}
              >
                Confirmar el cambio
              </button>
              <button
                className="button"
                type="button"
                disabled={confirmar.isPending || descartar.isPending}
                onClick={() => {
                  descartar.mutate(cambio.id);
                }}
              >
                Descartar la propuesta
              </button>
              <span className="hint">
                Confirmar acepta la versión nueva, sustituye la anterior (que se conserva como
                histórica) y marca los derivados afectados. Descartar no toca nada.
              </span>
            </div>
          ) : (
            <p className="hint">
              Este cambio está {CHANGE_STATUS_LABEL[cambio.status]} desde el{' '}
              {(cambio.confirmed_at ?? cambio.discarded_at ?? cambio.created_at).slice(0, 10)}.
            </p>
          )}

          {conflictoConfirmar !== null && (
            <p className="hint" role="alert">
              {conflictoConfirmar}
            </p>
          )}
          {errorConfirmar !== null && (
            <p className="hint" role="alert">
              {errorConfirmar}
            </p>
          )}
          {confirmar.data !== undefined && (
            <p className="hint" role="status">
              {confirmar.data.applied
                ? `Cambio aplicado: la versión anterior queda como histórica y ${String(confirmar.data.marked.length)} derivado(s) han quedado pendientes de revisar.`
                : `No se ha aplicado: ${confirmar.data.reason ?? 'sin motivo declarado'}`}
            </p>
          )}
          {descartar.data !== undefined && (
            <p className="hint" role="status">
              {descartar.data.reason ?? 'Propuesta descartada.'}
            </p>
          )}
          {conflictoDescartar !== null && (
            <p className="hint" role="alert">
              {conflictoDescartar}
            </p>
          )}
          {errorDescartar !== null && (
            <p className="hint" role="alert">
              {errorDescartar}
            </p>
          )}
        </section>
      )}

      <section className="card" aria-labelledby="resumenes">
        <h2 id="resumenes">Resúmenes del material</h2>
        <p className="hint">
          Los resúmenes son extractivos: texto del corpus con su cita, sin modelo. Un resumen depende
          de las secciones de las que sale, así que un cambio en ellas lo deja pendiente de revisar.
          Se crean desde el lector de la Biblioteca, en la sección que interesa.
        </p>
        {pendientes.isPending && <LoadingState label="Leyendo los resúmenes…" />}
        {pendientes.isError && (
          <ErrorState
            title="No se pudieron leer los resúmenes"
            message="El servidor no ha devuelto los derivados."
            onRetry={() => {
              void pendientes.refetch();
            }}
          />
        )}
        {pendientes.data !== undefined && pendientes.data.length === 0 && (
          <p className="hint">
            No hay ningún resumen pendiente de revisar. Si un cambio afecta a uno, aparecerá aquí con
            su motivo.
          </p>
        )}
        {pendientes.data !== undefined && pendientes.data.length > 0 && (
          <ul className="results" aria-label="Resúmenes pendientes de revisar">
            {pendientes.data.map((resumen) => (
              <li key={resumen.id}>
                <p>
                  <strong>{resumen.title}</strong>{' '}
                  <StatusBadge tone="warning">pendiente de revisar</StatusBadge>{' '}
                  <span className="hint">
                    {resumen.document_title} · secciones: {resumen.sections.join(', ') || 'sin declarar'}
                  </span>
                </p>
                <p className="hint">{resumen.needs_review_reason}</p>
                <pre className="reader">{resumen.content}</pre>
                <div className="form__row">
                  <button
                    className="button"
                    type="button"
                    disabled={resolver.isPending}
                    aria-label={`Marcar que el resumen sigue valiendo: ${resumen.title}`}
                    onClick={() => {
                      resolver.mutate({ artifactId: resumen.id, resolution: 'reviewed' });
                    }}
                  >
                    Sigue valiendo
                  </button>
                  <button
                    className="button"
                    type="button"
                    disabled={resolver.isPending}
                    aria-label={`Descartar el resumen: ${resumen.title}`}
                    onClick={() => {
                      resolver.mutate({ artifactId: resumen.id, resolution: 'discarded' });
                    }}
                  >
                    Descartarlo
                  </button>
                  <span className="hint">
                    Descartar no borra: aparta el resumen para que deje de usarse.
                  </span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </>
  );
}
