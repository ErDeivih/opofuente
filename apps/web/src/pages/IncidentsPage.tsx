import { useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import {
  INCIDENT_CATEGORIES,
  INCIDENT_CATEGORY_LABELS,
  INCIDENT_COUNT_FIELD,
  INCIDENT_STATUSES,
  INCIDENT_STATUS_HELP,
  INCIDENT_STATUS_LABELS,
  type IncidentCategory,
  type IncidentStatus,
} from '../api/notesIncidents';
import {
  useCurriculum,
  useNotesIncidents,
  useOppositions,
  useUpdateNotesIncident,
} from '../api/queries';
import { EmptyState } from '../components/EmptyState';
import { ErrorState } from '../components/ErrorState';
import { LoadingState } from '../components/LoadingState';
import { IncidentRow } from '../features/incidencias/IncidentRow';
import { groupByBlock, indexProgramme, topicLabel } from '../features/topicReview/programme';
import { describeError } from '../features/system/labels';

/** Los valores que existen, para no creerse lo que venga escrito en la dirección. */
function categoriaValida(valor: string | null): IncidentCategory | null {
  return INCIDENT_CATEGORIES.find((categoria) => categoria === valor) ?? null;
}

function estadoValido(valor: string | null): IncidentStatus | null {
  return INCIDENT_STATUSES.find((estado) => estado === valor) ?? null;
}

/**
 * La bandeja del motor (F18, §4.1 del objetivo: el bloque C del panel).
 *
 * **No es una lista de errores del alumno.** Es lo que el sistema no ha podido resolver solo mientras
 * escribía los apuntes: la norma que ha cambiado, la clave que los apuntes contradicen, el hueco para
 * el que no hay material y la pregunta que no se puede juzgar. Hasta ahora eso solo se veía abriendo
 * la API, y es lo que hace que un tema no llegue al 90 % o se quede en borrador.
 *
 * Lo que la pantalla hace, y nada más:
 *
 * 1. **enseña** cada incidencia con su categoría, su motivo, el porqué del dominio, la pregunta que
 *    la provoca y la frase verificada cuando la hay;
 * 2. **deja ir a mirarla**: el apartado de los apuntes por su ancla, la pregunta en el banco por su
 *    identificador y el material del que salió la clave. La pregunta que no se pudo situar en ninguna
 *    materia lo dice, en vez de mandar a un ancla que no está;
 * 3. **deja decidir**: los cuatro estados y la nota de lo que se ha decidido, por la ruta auditada
 *    (`PATCH /notes-incidents/{id}`), con su evento en la misma escritura;
 * 4. **cuenta en la base**: las cuatro cifras por categoría y las cuatro por estado salen del
 *    servidor, contadas con un `GROUP BY` sobre la bandeja entera. No son las de la página que se
 *    está mirando, y por eso el botón de «norma cambiada» dice 291 aunque se estén viendo 20.
 *
 * Los filtros viven en la **dirección** (`?categoria=norma_cambiada&estado=open&tema=I.2&q=clave`):
 * una bandeja se enlaza —«mira estas tres»— y volver a la pantalla devuelve lo que se estaba mirando.
 */
export function IncidentsPage() {
  const [params, setParams] = useSearchParams();
  const categoria = categoriaValida(params.get('categoria'));
  const estado = estadoValido(params.get('estado'));
  const tema = params.get('tema') ?? '';
  const q = params.get('q') ?? '';

  const incidencias = useNotesIncidents(categoria, estado, tema === '' ? null : tema, q);
  const despachar = useUpdateNotesIncident();

  const oppositions = useOppositions();
  const activa = oppositions.data?.find((oposicion) => oposicion.active) ?? null;
  const curriculum = useCurriculum(activa?.active_convocation?.id ?? null);
  const temas = useMemo(() => indexProgramme(curriculum.data?.nodes ?? []), [curriculum.data]);

  // El texto del buscador se escribe libre y se manda al enviar: la dirección no cambia con cada
  // tecla, que es lo que llenaría el historial de una palabra por letra.
  const [borrador, setBorrador] = useState<{ texto: string; para: string } | null>(null);
  const buscado = borrador !== null && borrador.para === q ? borrador.texto : q;

  function filtrar(cambios: {
    categoria?: string | null;
    estado?: string | null;
    tema?: string | null;
    q?: string | null;
  }) {
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

  const contadores = incidencias.data ?? null;
  const filas = incidencias.data?.incidents ?? [];
  const total = incidencias.data?.total ?? 0;
  const totales = incidencias.data?.totals_by_category ?? {};
  const totalCategorias = INCIDENT_CATEGORIES.reduce(
    (suma, cual) => suma + (totales[cual] ?? 0),
    0,
  );

  return (
    <>
      <header className="page__header">
        <h1>Incidencias del motor</h1>
        <p className="page__lead">
          Lo que <strong>el sistema no ha podido resolver solo</strong> mientras escribía los apuntes:
          una norma que ha cambiado, una respuesta correcta que los apuntes contradicen, un dato que no
          está escrito en ninguna parte y una pregunta que no se puede juzgar. No es una lista de
          errores de nadie: es lo que necesita tu criterio para que el tema se pueda cerrar. Cada
          decisión queda auditada.
        </p>
      </header>

      <section className="card" aria-labelledby="resumen-incidencias">
        <h2 id="resumen-incidencias">Qué espera tu criterio</h2>
        <p className="avisos__resumen">
          <strong>{contadores?.pending ?? 0}</strong> pendientes
          {contadores !== null && contadores.pending > 0
            ? ' — el motor las señaló y nadie ha decidido todavía'
            : ' — no espera nada tu criterio'}
          <span className="hint">
            {' '}
            · {contadores?.in_progress ?? 0} en curso · {contadores?.reviewed ?? 0} resueltas ·{' '}
            {contadores?.dismissed ?? 0} descartadas
          </span>
        </p>

        <h3 className="incidencias__titulo-filtro">Por categoría</h3>
        <div className="filtros" role="group" aria-label="Filtrar por categoría">
          <button
            className={categoria === null ? 'filtro filtro--activo' : 'filtro'}
            type="button"
            aria-pressed={categoria === null}
            onClick={() => {
              filtrar({ categoria: null });
            }}
          >
            Todas
            <span className="filtro__cuenta">{totalCategorias}</span>
          </button>
          {INCIDENT_CATEGORIES.map((cual) => (
            <button
              key={cual}
              className={categoria === cual ? 'filtro filtro--activo' : 'filtro'}
              type="button"
              aria-pressed={categoria === cual}
              onClick={() => {
                filtrar({ categoria: cual });
              }}
            >
              {/* El nombre de la categoría es el del dominio (§2.1.4 del objetivo) y viaja como
                  contenido, igual que los títulos del programa oficial del filtro de tema. */}
              <span data-contenido>{INCIDENT_CATEGORY_LABELS[cual]}</span>
              <span className="filtro__cuenta">{totales[cual] ?? 0}</span>
            </button>
          ))}
        </div>

        <h3 className="incidencias__titulo-filtro">Por estado</h3>
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
              {INCIDENT_STATUSES.reduce(
                (suma, cual) => suma + (contadores?.[INCIDENT_COUNT_FIELD[cual]] ?? 0),
                0,
              )}
            </span>
          </button>
          {INCIDENT_STATUSES.map((cual) => (
            <button
              key={cual}
              className={estado === cual ? 'filtro filtro--activo' : 'filtro'}
              type="button"
              aria-pressed={estado === cual}
              title={INCIDENT_STATUS_HELP[cual]}
              onClick={() => {
                filtrar({ estado: cual });
              }}
            >
              {INCIDENT_STATUS_LABELS[cual]}
              <span className="filtro__cuenta">
                {contadores?.[INCIDENT_COUNT_FIELD[cual]] ?? 0}
              </span>
            </button>
          ))}
        </div>

        <div className="form__row">
          <label className="form__label" htmlFor="incidencia-tema">
            Tema
          </label>
          {/*
            `data-contenido` en el selector: sus opciones son los **títulos del programa oficial**
            (`II.1 · Informática básica. Representación y comunicación de la información…`), el mismo
            material que la zona del alumno marca como contenido. Sin la marca, el detector de
            palabras prohibidas leería «representación» y «versiones» como jerga de la aplicación.
          */}
          <select
            id="incidencia-tema"
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
          aria-label="Buscar en las incidencias"
          onSubmit={(evento) => {
            evento.preventDefault();
            filtrar({ q: buscado.trim() });
          }}
        >
          <label className="form__label" htmlFor="incidencia-buscar">
            Buscar en la pregunta, el motivo y el apartado
          </label>
          <input
            id="incidencia-buscar"
            className="form__input"
            type="search"
            value={buscado}
            maxLength={200}
            placeholder="puerto, plazo, memoria virtual…"
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
          {q !== '' && ` Se están viendo ${String(total)} incidencia(s) con «${q}».`}
        </p>
      </section>

      {incidencias.isPending && <LoadingState label="Leyendo las incidencias del motor…" />}
      {incidencias.isError && (
        <ErrorState
          title="No se pudieron leer las incidencias"
          message={describeError(incidencias.error)}
          onRetry={() => {
            void incidencias.refetch();
          }}
        />
      )}
      {despachar.isError && (
        <ErrorState
          title="La decisión no se pudo guardar"
          message={describeError(despachar.error)}
          onRetry={() => {
            despachar.reset();
          }}
        />
      )}

      {incidencias.isSuccess && filas.length === 0 && (
        <EmptyState
          title={
            contadores !== null && totalCategorias > 0
              ? 'Ninguna incidencia con estos filtros'
              : 'Ninguna incidencia esperando'
          }
          description={
            contadores !== null && totalCategorias > 0
              ? 'Hay incidencias en la bandeja, pero no con la categoría, el estado, el tema o la búsqueda que has puesto. Quita algún filtro para verlas.'
              : 'Aquí aparecerá lo que el motor no pueda cerrar solo al comprobar un tema contra las preguntas de su banco: huecos sin material, respuestas correctas que no cuadran, normas cambiadas y preguntas que no se pueden juzgar.'
          }
        />
      )}

      {incidencias.isSuccess && filas.length > 0 && (
        <section className="card" aria-labelledby="lista-incidencias">
          <h2 id="lista-incidencias">
            Incidencias{' '}
            <span className="hint">· {total} con estos filtros, de la más nueva a la más vieja</span>
          </h2>
          <ul className="avisos" aria-label="Incidencias del motor">
            {filas.map((incidencia) => (
              <IncidentRow
                key={incidencia.id}
                incidencia={incidencia}
                busy={despachar.isPending}
                onDispatch={(nuevo, nota) => {
                  despachar.mutate({ id: incidencia.id, status: nuevo, note: nota });
                }}
              />
            ))}
          </ul>
        </section>
      )}
    </>
  );
}
