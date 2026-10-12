import { useMemo, useState } from 'react';

import { EXCLUSION_LABELS, type ExclusionReason } from '../api/topicReview';
import { useExcludedQuestions } from '../api/queries';
import { EmptyState } from '../components/EmptyState';
import { ErrorState } from '../components/ErrorState';
import { LoadingState } from '../components/LoadingState';
import { describeError } from '../features/system/labels';

/** Los dos motivos, en el orden en que se miran: primero lo que hay que arreglar. */
const MOTIVOS: readonly ExclusionReason[] = ['enunciado_roto', 'otra_administracion'];

/** Qué significa cada motivo, dicho para poder juzgar la marca sin abrir la pregunta. */
const MOTIVO_AYUDA: Record<ExclusionReason, string> = {
  enunciado_roto:
    'El enunciado no es una pregunta contestable: es un trozo de norma, una cabecera de tabla o un ' +
    'texto sin las opciones. No entra en tests, simulacros ni comprobaciones de apuntes.',
  otra_administracion:
    'Es normativa u organización de otra administración (Zaragoza, Murcia, Pontevedra, Barcelona…). ' +
    'No es materia de este programa, pero se queda en la base por si su informática sirve.',
};

/**
 * «No son preguntas» (F16, decisión D6): lo que el motor dejó fuera, con su motivo.
 *
 * El propietario decidió que los enunciados rotos y las preguntas de otra administración **no se
 * tiran**: no entran en ningún test, simulacro ni comprobación de apuntes, pero se quedan en la base
 * y aquí se pueden mirar. Esta pantalla existe para eso y **solo** para eso:
 *
 * - **enseña**: la pregunta, el motivo por el que está fuera, quién lo decidió y cuándo;
 * - **busca**: por el texto del enunciado, que es lo único que permite encontrar una entre cientos;
 * - y **no toca nada**: no hay botón de borrar ni de editar. Devolver una pregunta al temario es
 *   asignarle un tema, y eso se hace en Clasificación, que es donde está la marca y su auditoría.
 *
 * Las cifras de cada motivo salen del servidor (`totals_by_reason`), contadas en la base: sumar a
 * mano las filas de la página que se está mirando daría un número que miente.
 */
export function NoSonPreguntasPage() {
  const [motivo, setMotivo] = useState<ExclusionReason>('enunciado_roto');
  const [buscado, setBuscado] = useState('');
  const [q, setQ] = useState('');
  const marcas = useExcludedQuestions(motivo, q);

  const totales = marcas.data?.totals_by_reason ?? {};
  const total = marcas.data?.total ?? 0;

  const texto = useMemo(() => {
    if (marcas.data === undefined) {
      return '';
    }
    const filas = marcas.data.exclusions.length;
    if (filas === 0) {
      return '';
    }
    return total > filas
      ? `Se enseñan las ${String(filas)} más recientes de ${String(total)}.`
      : `${String(total)} en total.`;
  }, [marcas.data, total]);

  return (
    <>
      <header className="page__header">
        <h1>No son preguntas</h1>
        <p className="page__lead">
          Enunciados que no se pueden contestar y preguntas de otras administraciones. No entran en
          ningún test, simulacro ni comprobación de apuntes, pero <strong>siguen en la base</strong>:
          aquí se miran sin tocarlos, por si alguno se puede rescatar.
        </p>
      </header>

      <section className="card" aria-labelledby="filtros-excluidas">
        <h2 id="filtros-excluidas">Lo que está fuera</h2>
        <div className="filtros" role="group" aria-label="Motivo por el que está fuera">
          {MOTIVOS.map((cual) => (
            <button
              key={cual}
              className={cual === motivo ? 'filtro filtro--activo' : 'filtro'}
              type="button"
              aria-pressed={cual === motivo}
              onClick={() => {
                setMotivo(cual);
              }}
            >
              {EXCLUSION_LABELS[cual]}
              <span className="filtro__cuenta">{totales[cual] ?? 0}</span>
            </button>
          ))}
        </div>
        <p className="hint">{MOTIVO_AYUDA[motivo]}</p>

        <form
          className="busqueda-panel"
          role="search"
          aria-label="Buscar en los enunciados que están fuera"
          onSubmit={(evento) => {
            evento.preventDefault();
            setQ(buscado.trim());
          }}
        >
          <label className="form__label" htmlFor="buscar-excluidas">
            Buscar en el enunciado
          </label>
          <input
            id="buscar-excluidas"
            className="form__input"
            type="search"
            value={buscado}
            maxLength={200}
            placeholder="puerto, plazo, ley…"
            onChange={(evento) => {
              setBuscado(evento.target.value);
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
                setBuscado('');
                setQ('');
              }}
            >
              Quitar la búsqueda
            </button>
          )}
        </form>
        <p className="hint">
          Busca en el texto tal cual está guardado: <strong>no</strong> iguala acentos («gestion» no
          encuentra «gestión»).
        </p>
      </section>

      {marcas.isPending && <LoadingState label="Leyendo lo que está fuera…" />}
      {marcas.isError && (
        <ErrorState
          title="No se pudieron leer las preguntas excluidas"
          message={describeError(marcas.error)}
          onRetry={() => {
            void marcas.refetch();
          }}
        />
      )}

      {marcas.isSuccess && marcas.data.exclusions.length === 0 && (
        <EmptyState
          title={
            q === ''
              ? `Ninguna pregunta fuera por «${EXCLUSION_LABELS[motivo].toLowerCase()}»`
              : 'Ningún enunciado coincide con la búsqueda'
          }
          description={
            q === ''
              ? 'Cuando el clasificador declare una pregunta fuera del programa, saldrá aquí con su motivo y con quién lo decidió.'
              : 'Prueba con otra palabra, o quita la búsqueda para ver el motivo entero.'
          }
        />
      )}

      {marcas.isSuccess && marcas.data.exclusions.length > 0 && (
        <section className="card" aria-labelledby="lista-excluidas">
          <h2 id="lista-excluidas">
            {EXCLUSION_LABELS[motivo]} <span className="hint">· {texto}</span>
          </h2>
          <ul className="excluidas" aria-label="Preguntas que no son preguntas">
            {marcas.data.exclusions.map((marca) => (
              <li key={marca.question_version_id} className="excluidas__fila">
                <p className="excluidas__enunciado" data-contenido>
                  {marca.stem ?? 'Enunciado no disponible'}
                </p>
                <p className="excluidas__meta">
                  <span>{EXCLUSION_LABELS[marca.reason]}</span>
                  {marca.note !== null && marca.note !== undefined && (
                    <span className="hint"> · {marca.note}</span>
                  )}
                  <span className="hint">
                    {' '}
                    · lo decidió {marca.actor}
                    {marca.created_at !== null && marca.created_at !== undefined
                      ? ` el ${marca.created_at.slice(0, 10)}`
                      : ''}
                  </span>
                </p>
              </li>
            ))}
          </ul>
        </section>
      )}
    </>
  );
}
