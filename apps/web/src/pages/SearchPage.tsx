import { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';

import { isApiError } from '../api/client';
import type {
  AnswerStyle,
  EvidenceSpan,
  RagAnswer,
  RagQuery,
  SearchResult,
  VersionMode,
} from '../api/search';
import { ANSWER_STYLES, VERSION_MODES, citationText, documentHref } from '../api/search';
import { useAskCorpus, useRetrieval, useSearchResults } from '../api/queries';
import { ErrorState } from '../components/ErrorState';
import { LoadingState } from '../components/LoadingState';
import { StatusBadge } from '../components/StatusBadge';

const STYLE_LABEL: Record<AnswerStyle, string> = {
  brief: 'breve',
  teach: 'explicada',
  compare: 'comparando fuentes',
};

const ANSWER_STATUS_LABEL: Record<RagAnswer['status'], string> = {
  supported: 'respaldada por el corpus',
  partial: 'respaldada solo en parte',
  insufficient: 'evidencia insuficiente',
};

const ANSWER_STATUS_TONE: Record<RagAnswer['status'], 'ok' | 'warning' | 'blocked'> = {
  supported: 'ok',
  partial: 'warning',
  insufficient: 'blocked',
};

const VERSION_LABEL: Record<VersionMode, string> = {
  current: 'solo lo vigente',
  explicit_historical: 'incluir también el histórico',
};

function describeError(error: unknown): string {
  return error instanceof Error ? error.message : 'Error desconocido';
}

/** Un fragmento entregado: su cita, su texto y el enlace para abrirlo en la Biblioteca. */
function Citation({ span }: { span: EvidenceSpan }) {
  const etiqueta = citationText(span);
  return (
    <>
      <span className="hint">
        <span className="sample__path">{etiqueta}</span>
        {etiqueta === span.document_title ? '' : ` · ${span.document_title}`} ·{' '}
        {span.version_status}
        {span.section_title === null ||
        span.section_title === undefined ||
        span.section_title === etiqueta
          ? ''
          : ` · ${span.section_title}`}
      </span>
      <blockquote className="reader">{span.text}</blockquote>
      {/* El enlace dice **a qué** cita lleva: dos «Abrir» iguales no distinguen nada al navegar
          con lector de pantalla, y aquí hay uno por fragmento. */}
      <Link
        className="button"
        to={documentHref(span)}
        aria-label={`Abrir en la Biblioteca: ${etiqueta} de ${span.document_title}`}
      >
        Abrir en la Biblioteca
      </Link>
    </>
  );
}

/**
 * Buscar y preguntar (07_UI-UX §2 —la búsqueda global de la cabecera— y 08_API-CONTRACT §8).
 *
 * Cuatro cosas que la pantalla hace porque son la razón de ser del slice:
 *
 * 1. **buscar no responde**: buscar devuelve fragmentos con su cita y la respuesta con afirmaciones
 *    citadas se pide a propósito. Así se puede mirar la evidencia antes de creerse una frase;
 * 2. **lo que no entra se ve**: la degradación (sin proveedor de embeddings) y lo que quedó fuera del
 *    corpus (versiones no publicadas) se enseñan con su motivo, en vez de devolver menos en silencio;
 * 3. **la falta de evidencia no se disfraza**: una respuesta `insufficient` se muestra como tal y con
 *    lo que no se ha podido sostener, en lugar de con un texto que parezca una respuesta;
 * 4. **todo se puede abrir y comprobar**: cada cita enlaza al documento y la recuperación completa
 *    (incluido lo que se descartó) está a un clic (§5, paso 9).
 */
export function SearchPage() {
  const [params, setParams] = useSearchParams();
  // Lo que se busca es lo que está en la dirección: una búsqueda se puede enlazar y repetir. El
  // campo enseña lo escrito **mientras** se escribe y, en cuanto la dirección cambia (por aquí o
  // por el buscador de la cabecera), vuelve a lo que se está buscando: no hay dos verdades.
  const q = params.get('q') ?? '';
  const [borrador, setBorrador] = useState<{ texto: string; para: string } | null>(null);
  const texto = borrador !== null && borrador.para === q ? borrador.texto : q;
  const [versionMode, setVersionMode] = useState<VersionMode>('current');
  const [style, setStyle] = useState<AnswerStyle>('brief');
  const [privadas, setPrivadas] = useState(true);

  const resultados = useSearchResults(
    q.trim() === ''
      ? null
      : { query: q, version_mode: versionMode, strategy: 'lexical', limit: 10 },
  );
  const preguntar = useAskCorpus();
  const pregunta = preguntar.data ?? null;

  const conflicto = isApiError(preguntar.error, 409) ? describeError(preguntar.error) : null;
  const error =
    preguntar.error === null || conflicto !== null ? null : describeError(preguntar.error);

  function escribir(valor: string): void {
    setBorrador({ texto: valor, para: q });
  }

  function buscar(): void {
    const termino = texto.trim();
    setParams(termino === '' ? {} : { q: termino });
    preguntar.reset();
  }

  return (
    <>
      <header className="page__header">
        <h1>Buscar y preguntar</h1>
        <p className="page__lead">
          La búsqueda va sobre el material publicado y vigente. Preguntar añade una respuesta con sus
          citas: cada afirmación dice de qué fragmento sale y, si el corpus no la sostiene, lo dice.
        </p>
      </header>

      <section className="card" aria-labelledby="busqueda">
        <h2 id="busqueda">Búsqueda</h2>
        <div className="form__row">
          <label className="form__label" htmlFor="busqueda-texto">
            Qué buscas
          </label>
          <input
            id="busqueda-texto"
            className="selector__select"
            value={texto}
            onChange={(event) => {
              escribir(event.target.value);
            }}
            onKeyDown={(event) => {
              if (event.key === 'Enter') {
                buscar();
              }
            }}
          />
          <label className="form__label" htmlFor="busqueda-version">
            Versiones
          </label>
          <select
            id="busqueda-version"
            className="selector__select"
            value={versionMode}
            onChange={(event) => {
              setVersionMode(event.target.value as VersionMode);
            }}
          >
            {VERSION_MODES.map((valor) => (
              <option key={valor} value={valor}>
                {VERSION_LABEL[valor]}
              </option>
            ))}
          </select>
          <button
            className="button"
            type="button"
            disabled={texto.trim() === ''}
            onClick={buscar}
          >
            Buscar
          </button>
        </div>
        <div className="form__row">
          <label className="form__label" htmlFor="busqueda-estilo">
            Respuesta
          </label>
          <select
            id="busqueda-estilo"
            className="selector__select"
            value={style}
            onChange={(event) => {
              setStyle(event.target.value as AnswerStyle);
            }}
          >
            {ANSWER_STYLES.map((valor) => (
              <option key={valor} value={valor}>
                {STYLE_LABEL[valor]}
              </option>
            ))}
          </select>
          <button
            className="button"
            type="button"
            aria-label="Preguntar al corpus"
            disabled={texto.trim() === '' || preguntar.isPending}
            onClick={() => {
              setParams({ q: texto });
              preguntar.mutate({
                query: texto,
                version_mode: versionMode,
                style,
                strategy: 'lexical',
                limit: 6,
                allow_private_sources: privadas,
              });
            }}
          >
            Preguntar
          </button>
          <label className="form__label" htmlFor="busqueda-privadas">
            <input
              id="busqueda-privadas"
              type="checkbox"
              checked={privadas}
              onChange={(event) => {
                setPrivadas(event.target.checked);
              }}
            />{' '}
            Incluir mi material privado
          </label>
          <span className="hint">
            Preguntar guarda la consulta y su recuperación: la respuesta queda auditable.
          </span>
        </div>
      </section>

      {resultados.isPending && <LoadingState label="Buscando en el corpus…" />}
      {resultados.isError && (
        <ErrorState
          title="La búsqueda no se pudo hacer"
          message={describeError(resultados.error)}
          onRetry={() => {
            void resultados.refetch();
          }}
        />
      )}
      {resultados.data !== undefined && <SearchResults results={resultados.data} />}

      {conflicto !== null && (
        <ErrorState title="El servidor rechazó la consulta" message={conflicto} />
      )}
      {error !== null && <ErrorState title="La pregunta no se pudo hacer" message={error} />}

      {preguntar.isPending && <LoadingState label="Recuperando evidencia y componiendo la respuesta…" />}
      {pregunta !== null && <AnswerPanel query={pregunta} />}
    </>
  );
}

const STRATEGY_LABELS: Readonly<Record<string, string>> = {
  lexical: 'léxica',
  semantic: 'semántica',
  hybrid: 'híbrida',
};

/** La estrategia de recuperación, en español; un valor nuevo se enseña tal cual, no se inventa. */
function strategyLabel(strategy: string): string {
  return STRATEGY_LABELS[strategy] ?? strategy;
}

function SearchResults({ results }: { results: SearchResult }) {
  return (    <section className="card" aria-labelledby="resultados-busqueda">
      <h2 id="resultados-busqueda">Resultados</h2>
      <p className="hint">
        {results.total} fragmentos · {results.version_mode === 'explicit_historical'
          ? 'con el histórico incluido'
          : 'solo versiones vigentes'}{' '}
        · recuperación <span className="sample__path">{strategyLabel(results.strategy)}</span>
      </p>

      {results.degradations.length > 0 && (
        <div className="notice">
          <h3>Lo que esta búsqueda no puede hacer</h3>
          <ul className="hint">
            {results.degradations.map((aviso) => (
              <li key={aviso}>{aviso}</li>
            ))}
          </ul>
        </div>
      )}

      {results.excluded.length > 0 && (
        <>
          <h3>Fuera del corpus</h3>
          <ul className="hint">
            {results.excluded.map((motivo) => (
              <li key={motivo}>{motivo}</li>
            ))}
          </ul>
        </>
      )}

      {results.hits.length === 0 ? (
        <p className="hint">
          Ningún fragmento publicado responde a esa búsqueda. Puede que el tema no esté importado, o
          que solo esté en material sin publicar.
        </p>
      ) : (
        <ol className="results">
          {results.hits.map((hit) => (
            <li key={hit.span.id}>
              <p>
                <strong>{hit.span.document_title}</strong>{' '}
                <StatusBadge tone={hit.span.version_status === 'accepted' ? 'ok' : 'warning'}>
                  {hit.span.version_status}
                </StatusBadge>{' '}
                <span className="hint">
                  {hit.matched_terms.length === 0
                    ? 'sin términos coincidentes declarados'
                    : `coincide en: ${hit.matched_terms.join(', ')}`}
                </span>
              </p>
              <ul className="evidence">
                <li>
                  <Citation span={hit.span} />
                </li>
              </ul>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}

/** La respuesta con sus citas. `insufficient` es un resultado, no un error: se enseña como tal. */
function AnswerPanel({ query }: { query: RagQuery }) {
  const answer = query.answer ?? null;
  return (
    <section className="card" aria-labelledby="respuesta-rag">
      <h2 id="respuesta-rag">Respuesta</h2>
      <p className="hint">
        «{query.question}» · {query.version_mode === 'explicit_historical'
          ? 'con el histórico incluido'
          : 'solo versiones vigentes'}{' '}
        · recuperación <span className="sample__path">{strategyLabel(query.strategy)}</span>
      </p>

      {answer === null ? (
        <p className="hint">
          El servidor ha guardado la consulta pero no ha devuelto respuesta: no hay nada que enseñar
          como si lo hubiera.
        </p>
      ) : (
        <>
          <p>
            <StatusBadge tone={ANSWER_STATUS_TONE[answer.status]}>
              {ANSWER_STATUS_LABEL[answer.status]}
            </StatusBadge>{' '}
            <span className="hint">
              redactada por <span className="sample__path">{answer.provider}</span>
              {answer.model === null || answer.model === undefined ? (
                ''
              ) : (
                <>
                  {' '}
                  · modelo <span className="sample__path">{answer.model}</span>
                </>
              )}
              {answer.prompt_template_version === null ||
              answer.prompt_template_version === undefined ? (
                ''
              ) : (
                <>
                  {' '}
                  · <span className="sample__path">{answer.prompt_template_version}</span>
                </>
              )}
            </span>
          </p>
          <p className="reader">{answer.short_answer}</p>
          {answer.explanation !== '' && <p>{answer.explanation}</p>}

          {answer.claims.length > 0 && (
            <>
              <h3>Afirmaciones y de dónde salen</h3>
              <ol className="results">
                {answer.claims.map((claim, indice) => (
                  <li key={`${String(indice)}-${claim.text.slice(0, 32)}`}>
                    <p>
                      {claim.text}{' '}
                      <StatusBadge tone={claim.support === 'direct' ? 'ok' : 'warning'}>
                        {claim.support === 'direct' ? 'literal del corpus' : 'inferida'}
                      </StatusBadge>
                    </p>
                    {claim.evidence.length === 0 ? (
                      <p className="hint">
                        Esta afirmación no cita ningún fragmento: no se puede comprobar.
                      </p>
                    ) : (
                      <ul className="evidence">
                        {claim.evidence.map((span) => (
                          <li key={span.id}>
                            <Citation span={span} />
                          </li>
                        ))}
                      </ul>
                    )}
                  </li>
                ))}
              </ol>
            </>
          )}

          {answer.uncertainties.length > 0 && (
            <>
              <h3>Lo que no se ha podido sostener</h3>
              <ul className="hint">
                {answer.uncertainties.map((texto) => (
                  <li key={texto}>{texto}</li>
                ))}
              </ul>
            </>
          )}

          {answer.suggested_followups.length > 0 && (
            <>
              <h3>Se puede mirar después</h3>
              <ul className="hint">
                {answer.suggested_followups.map((texto) => (
                  <li key={texto}>{texto}</li>
                ))}
              </ul>
            </>
          )}
        </>
      )}

      <RetrievalDetail queryId={query.id} />
    </section>
  );
}

/** Todo lo que se recuperó, se usara o no (05_RAG §5, paso 9): la respuesta no oculta sus descartes. */
function RetrievalDetail({ queryId }: { queryId: string }) {
  const [abierto, setAbierto] = useState(false);
  const recuperacion = useRetrieval(abierto ? queryId : null);

  return (
    <details
      onToggle={(event) => {
        setAbierto(event.currentTarget.open);
      }}
    >
      <summary>Ver todo lo que se recuperó, se usara o no</summary>
      {recuperacion.isPending && <LoadingState label="Leyendo la recuperación guardada…" />}
      {recuperacion.isError && (
        <ErrorState
          title="No se pudo leer la recuperación"
          message={describeError(recuperacion.error)}
          onRetry={() => {
            void recuperacion.refetch();
          }}
        />
      )}
      {recuperacion.data !== undefined && (
        <>
          <p className="hint">
            {recuperacion.data.hits.length} fragmentos recuperados ·{' '}
            {recuperacion.data.used_ids.length} usados en la respuesta · corpus{' '}
            <span className="sample__path">{recuperacion.data.corpus_revision}</span>
          </p>
          <ul className="evidence">
            {recuperacion.data.hits.map((hit) => (
              <li key={hit.span.id}>
                <span className="hint">
                  #{hit.rank} · {hit.strategy} ·{' '}
                  {hit.used ? 'usado en la respuesta' : 'recuperado y no usado'}
                </span>
                <Citation span={hit.span} />
              </li>
            ))}
          </ul>
        </>
      )}
    </details>
  );
}
