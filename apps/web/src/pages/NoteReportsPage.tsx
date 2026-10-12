import { useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import {
  NOTE_REPORT_COUNT_FIELD,
  NOTE_REPORT_STATUSES,
  NOTE_REPORT_STATUS_HELP,
  NOTE_REPORT_STATUS_LABELS,
  type NoteReportStatus,
} from '../api/notesReports';
import { useCurriculum, useNoteReports, useOppositions, useUpdateNoteReport } from '../api/queries';
import { EmptyState } from '../components/EmptyState';
import { ErrorState } from '../components/ErrorState';
import { LoadingState } from '../components/LoadingState';
import { NoteReportRow } from '../features/avisos/NoteReportRow';
import { groupByBlock, indexProgramme, topicLabel } from '../features/topicReview/programme';
import { describeError } from '../features/system/labels';

/** Los estados que existen, para no creerse lo que venga escrito en la dirección. */
function estadoValido(valor: string | null): NoteReportStatus | null {
  return NOTE_REPORT_STATUSES.find((estado) => estado === valor) ?? null;
}

/**
 * La bandeja de avisos del alumno (F16, decisión D2 del objetivo: el bloque C del panel).
 *
 * El botón «Esto está mal» de los apuntes guarda desde F13 un aviso por su ruta auditada, y hasta
 * ahora **no había dónde mirarlo**: el propietario estudiaba, marcaba lo que estaba mal y no podía
 * verlo. Esta pantalla es eso y nada más que eso:
 *
 * 1. **se ve lo que el alumno escribió**, con su tema, su apartado, su motivo y su fecha;
 * 2. **se puede ir al punto exacto**: el apartado enlaza a su ancla de los apuntes, así que se mira
 *    el texto del que habla sin buscarlo a mano. Si el apartado ya no existe —los apuntes se
 *    reescriben— se dice, y ese es el aviso que más hay que mirar;
 * 3. **se despacha**: los cuatro estados del dominio y la nota de lo que se ha hecho, por la ruta
 *    auditada (`PATCH /notes-reports/{id}`), con su evento en la misma escritura;
 * 4. **se encuentra**: filtros por estado y por tema, búsqueda por lo que dijo el alumno y el
 *    contador de pendientes, que es el mismo número que enseña el menú.
 *
 * Los filtros viven en la **dirección** (`?estado=open&tema=IV.7&q=puerto`): una bandeja se enlaza
 * —«mira estos tres avisos»— y volver a la pantalla devuelve lo que se estaba mirando.
 */
export function NoteReportsPage() {
  const [params, setParams] = useSearchParams();
  const estado = estadoValido(params.get('estado'));
  const tema = params.get('tema') ?? '';
  const q = params.get('q') ?? '';

  const avisos = useNoteReports(estado, tema === '' ? null : tema, q);
  const despachar = useUpdateNoteReport();

  const oppositions = useOppositions();
  const activa = oppositions.data?.find((oposicion) => oposicion.active) ?? null;
  const curriculum = useCurriculum(activa?.active_convocation?.id ?? null);
  const temas = useMemo(() => indexProgramme(curriculum.data?.nodes ?? []), [curriculum.data]);

  // El texto del buscador se escribe libre y se manda al enviar: la dirección no cambia con cada
  // tecla, que es lo que llenaría el historial de una palabra por letra.
  const [borrador, setBorrador] = useState<{ texto: string; para: string } | null>(null);
  const buscado = borrador !== null && borrador.para === q ? borrador.texto : q;

  function filtrar(cambios: { estado?: string | null; tema?: string | null; q?: string | null }) {
    const siguiente = new URLSearchParams(params);
    for (const [clave, valor] of Object.entries(cambios)) {
      if (valor === null || valor === '') {
        siguiente.delete(clave);
      } else {
        siguiente.set(clave, valor);
      }
    }
    setParams(siguiente);
  }

  const contadores = avisos.data ?? null;
  const filas = avisos.data?.reports ?? [];
  const total = avisos.data?.total ?? 0;

  return (
    <>
      <header className="page__header">
        <h1>Avisos de los apuntes</h1>
        <p className="page__lead">
          Lo que el alumno marca con «Esto está mal» mientras estudia. Cada aviso lleva el apartado
          del que habla: se puede abrir en los apuntes, dejarlo en curso, resolverlo o descartarlo, y
          decir en una línea qué se ha hecho. Cada cambio queda auditado.
        </p>
      </header>

      <section className="card" aria-labelledby="resumen-avisos">
        <h2 id="resumen-avisos">Cómo va la bandeja</h2>
        <p className="avisos__resumen">
          <strong>{contadores?.pending ?? 0}</strong> pendientes
          {contadores !== null && contadores.pending > 0
            ? ' — nadie los ha mirado todavía'
            : ' — no espera nada tu criterio'}
          <span className="hint">
            {' '}
            · {contadores?.in_progress ?? 0} en curso · {contadores?.reviewed ?? 0} resueltos ·{' '}
            {contadores?.dismissed ?? 0} descartados
          </span>
        </p>

        <div className="filtros" role="group" aria-label="Filtrar por estado">
          <button
            className={estado === null ? 'filtro filtro--activo' : 'filtro'}
            type="button"
            aria-pressed={estado === null}
            onClick={() => {
              filtrar({ estado: null });
            }}
          >
            Todos
            <span className="filtro__cuenta">
              {NOTE_REPORT_STATUSES.reduce(
                (suma, cual) => suma + (contadores?.[NOTE_REPORT_COUNT_FIELD[cual]] ?? 0),
                0,
              )}
            </span>
          </button>
          {NOTE_REPORT_STATUSES.map((cual) => (
            <button
              key={cual}
              className={estado === cual ? 'filtro filtro--activo' : 'filtro'}
              type="button"
              aria-pressed={estado === cual}
              title={NOTE_REPORT_STATUS_HELP[cual]}
              onClick={() => {
                filtrar({ estado: cual });
              }}
            >
              {NOTE_REPORT_STATUS_LABELS[cual]}
              <span className="filtro__cuenta">
                {contadores?.[NOTE_REPORT_COUNT_FIELD[cual]] ?? 0}
              </span>
            </button>
          ))}
        </div>

        <div className="form__row">
          <label className="form__label" htmlFor="aviso-tema">
            Tema
          </label>
          {/*
            `data-contenido` en el selector: sus opciones son los **títulos del programa oficial**
            (`II.1 · Informática básica. Representación y comunicación de la información…`), el mismo
            material que la zona del alumno marca como contenido. Sin la marca, el detector de
            palabras prohibidas leería «representación» y «versiones» como jerga de la aplicación, y
            lo que hace es marcar el temario —que es justo lo que el detector dice que no hay que
            hacer—. El rótulo «Tema» se queda fuera y sigue vigilado.
          */}
          <select
            id="aviso-tema"
            className="selector__select"
            data-contenido
            value={tema}
            onChange={(evento) => {
              filtrar({ tema: evento.target.value });
            }}
          >
            <option value="">Todos los temas</option>
            {groupByBlock(temas).map((grupo) => (
              <optgroup key={grupo.title} label={grupo.title}>
                {grupo.topics.map((opcion) => (
                  <option key={opcion.path} value={opcion.path}>
                    {topicLabel(opcion)}
                  </option>
                ))}
              </optgroup>
            ))}
          </select>
        </div>

        <form
          className="busqueda-panel"
          role="search"
          aria-label="Buscar en los avisos"
          onSubmit={(evento) => {
            evento.preventDefault();
            filtrar({ q: buscado.trim() });
          }}
        >
          <label className="form__label" htmlFor="aviso-buscar">
            Buscar en el motivo y en el apartado
          </label>
          <input
            id="aviso-buscar"
            className="form__input"
            type="search"
            value={buscado}
            maxLength={200}
            placeholder="puerto, tabla, plazo…"
            onChange={(evento) => {
              setBorrador({ texto: evento.target.value, para: q });
            }}
          />
          <button className="button" type="submit">
            Buscar
          </button>
          {q !== '' && (
            <button
              className="button button--secondary"
              type="button"
              onClick={() => {
                setBorrador(null);
                filtrar({ q: null });
              }}
            >
              Quitar la búsqueda
            </button>
          )}
        </form>
        <p className="hint">
          Busca en el texto tal cual está guardado: <strong>no</strong> iguala acentos.
          {q !== '' && ` Se están viendo ${String(total)} aviso(s) con «${q}».`}
        </p>
      </section>

      {avisos.isPending && <LoadingState label="Leyendo los avisos del alumno…" />}
      {avisos.isError && (
        <ErrorState
          title="No se pudieron leer los avisos"
          message={describeError(avisos.error)}
          onRetry={() => {
            void avisos.refetch();
          }}
        />
      )}
      {despachar.isError && (
        <ErrorState
          title="El cambio no se pudo guardar"
          message={describeError(despachar.error)}
          onRetry={() => {
            despachar.reset();
          }}
        />
      )}

      {avisos.isSuccess && filas.length === 0 && (
        <EmptyState
          title={
            contadores !== null && contadores.pending + contadores.in_progress > 0
              ? 'Ningún aviso con estos filtros'
              : 'Ningún aviso esperando'
          }
          description={
            contadores !== null && contadores.pending + contadores.in_progress > 0
              ? 'Hay avisos en la bandeja, pero no con el estado, el tema o la búsqueda que has puesto. Quita algún filtro para verlos.'
              : 'Aquí aparecerá lo que el alumno marque con «Esto está mal» en los apuntes, con el apartado del que habla.'
          }
        />
      )}

      {avisos.isSuccess && filas.length > 0 && (
        <section className="card" aria-labelledby="lista-avisos">
          <h2 id="lista-avisos">
            Avisos <span className="hint">· {total} con estos filtros, del más nuevo al más viejo</span>
          </h2>
          <ul className="avisos" aria-label="Avisos del alumno sobre los apuntes">
            {filas.map((aviso) => (
              <NoteReportRow
                key={aviso.id}
                aviso={aviso}
                busy={despachar.isPending}
                onDispatch={(nuevo, nota) => {
                  despachar.mutate({ id: aviso.id, status: nuevo, note: nota });
                }}
              />
            ))}
          </ul>
        </section>
      )}
    </>
  );
}
