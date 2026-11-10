/**
 * Demo estática de OpoFuente para GitHub Pages.
 *
 * No hay servidor ni API: todo el contenido viene empaquetado en `data.json`, y el progreso se guarda
 * en `localStorage`. Cada tema declara el estado de sus apuntes (`completos`, `solo_resumen` o
 * `pendiente`) y de su práctica (`con_practica` o `pendiente`); el temario muestra ambos sellos y los
 * temas sin escribir dicen «Pendiente» en lugar de mostrar un párrafo vacío.
 */

import { useEffect, useState, type ReactElement } from 'react';
import { createRoot } from 'react-dom/client';

import demoData from './data.json';
import {
  clearResume,
  loadProgress,
  loadResume,
  resetProgress,
  saveResult,
  saveResume,
  scoreAnswers,
  type PracticeResult,
} from './practice';
import '../src/styles/global.css';
import './demo.css';

type ApuntesStatus = 'completos' | 'solo_resumen' | 'pendiente';
type PracticaStatus = 'con_practica' | 'pendiente';
type Filtro = 'todos' | 'apuntes' | 'practica';

interface Option {
  readonly key: string;
  readonly text: string;
}

interface DemoSource {
  readonly label: string;
  readonly url: string;
}

interface Question {
  readonly stem: string;
  readonly options: readonly Option[];
  readonly correct: string;
  readonly explanation: string;
  readonly source?: DemoSource;
}

interface Practice {
  readonly slug: string;
  readonly tema_path: string;
  readonly title: string;
  readonly source: DemoSource;
  readonly questions: readonly Question[];
}

interface DemoTable {
  readonly columns: readonly string[];
  readonly rows: readonly (readonly string[])[];
}

interface DemoSection {
  readonly heading: string;
  readonly body?: string;
  readonly table?: DemoTable;
}

interface TopicSummary {
  readonly path: string;
  readonly title: string;
  readonly apuntesStatus: ApuntesStatus;
  readonly practicaStatus: PracticaStatus;
  readonly sectionCount: number;
  readonly questionCount: number;
}

interface TopicContent {
  readonly path: string;
  readonly title: string;
  readonly apuntesStatus: ApuntesStatus;
  readonly practicaStatus: PracticaStatus;
  readonly source: DemoSource;
  readonly sections: readonly DemoSection[];
  readonly practiceSlug?: string;
}

interface Coverage {
  readonly total: number;
  readonly conApuntes: number;
  readonly soloResumen: number;
  readonly pendientes: number;
  readonly conPractica: number;
}

interface Block {
  readonly path: string;
  readonly title: string;
  readonly coverage: Coverage;
  readonly topics: readonly TopicSummary[];
}

interface Convocatoria {
  readonly code: string;
  readonly title: string;
  readonly administration: string;
  readonly territory: string;
  readonly status: string;
  readonly url: string;
}

interface DemoData {
  readonly title: string;
  readonly warning: string;
  readonly convocatorias: {
    readonly total: number;
    readonly draft: number;
    readonly archived: number;
    readonly items: readonly Convocatoria[];
  };
  readonly curriculum: {
    readonly code: string;
    readonly name: string;
    readonly blocks: readonly Block[];
  };
  readonly topics: Readonly<Record<string, TopicContent>>;
  readonly practices: readonly Practice[];
  readonly progress: {
    readonly total: number;
    readonly apuntesCompletos: number;
    readonly soloResumen: number;
    readonly pendientes: number;
    readonly conPractica: number;
    readonly sinPractica: number;
    readonly questions: number;
    readonly convocatorias: number;
  };
}

const data = demoData as DemoData;
const TOPIC_LIST = data.curriculum.blocks.flatMap((block) => block.topics);
const TOPIC_BY_PATH = new Map(TOPIC_LIST.map((topic) => [topic.path, topic]));
const PRACTICE_BY_SLUG = new Map(data.practices.map((practice) => [practice.slug, practice]));

const APUNTES_LABEL: Readonly<Record<ApuntesStatus, string>> = {
  completos: 'Apuntes completos',
  solo_resumen: 'Solo resumen',
  pendiente: 'Pendiente',
};

const PRACTICA_LABEL: Readonly<Record<PracticaStatus, string>> = {
  con_practica: 'Con práctica',
  pendiente: 'Práctica pendiente',
};

function pendientesTexto(n: number): string {
  return `${String(n)} ${n === 1 ? 'pendiente' : 'pendientes'}`;
}

function porcentaje(parte: number, total: number): number {
  return total === 0 ? 0 : Math.round((parte / total) * 100);
}

function go(path: string): void {
  window.location.hash = `#/${path}`;
}

function useRoute(): string {
  const [route, setRoute] = useState(() => window.location.hash.replace(/^#\/?/, ''));
  useEffect(() => {
    const onChange = () => {
      setRoute(window.location.hash.replace(/^#\/?/, ''));
    };
    window.addEventListener('hashchange', onChange);
    return () => {
      window.removeEventListener('hashchange', onChange);
    };
  }, []);
  return route;
}

function normalized(text: string): string {
  return text
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '');
}

/** Texto con **negritas** y listas simples; no interpreta HTML. */
function RichText({ text }: { text: string }) {
  return (
    <>
      {text.split(/\n\n+/).map((paragraph, index) => {
        const lines = paragraph.split('\n').map((line) => line.trim());
        const withContent = lines.filter((line) => line !== '');
        const bullets = lines.filter((line) => line.startsWith('- '));
        if (bullets.length === withContent.length && bullets.length > 0) {
          return (
            <ul key={index}>
              {bullets.map((bullet, bulletIndex) => (
                <li key={bulletIndex}>{withBold(bullet.slice(2))}</li>
              ))}
            </ul>
          );
        }
        return <p key={index}>{withBold(paragraph)}</p>;
      })}
    </>
  );
}

function withBold(text: string): ReactElement[] {
  return text.split(/(\*\*[^*]+\*\*)/g).map((fragment, index) =>
    fragment.startsWith('**') && fragment.endsWith('**') ? (
      <strong key={index}>{fragment.slice(2, -2)}</strong>
    ) : (
      <span key={index}>{fragment}</span>
    ),
  );
}

function ApuntesBadge({ status }: { status: ApuntesStatus }) {
  return (
    <span className={`demo-status demo-status--apuntes-${status}`}>{APUNTES_LABEL[status]}</span>
  );
}

function PracticaBadge({ status }: { status: PracticaStatus }) {
  return (
    <span className={`demo-status demo-status--practica-${status}`}>{PRACTICA_LABEL[status]}</span>
  );
}

function SourceLine({ source, official = false }: { source: DemoSource; official?: boolean }) {
  if (source.label === '') {
    return null;
  }
  return (
    <p className="hint demo-source">
      {official
        ? source.url.includes('boe.es')
          ? 'Texto oficial (BOE): '
          : 'Fuente oficial: '
        : 'Fuente: '}
      {source.url !== '' ? (
        <a href={source.url} target="_blank" rel="noreferrer noopener">
          {source.label}
        </a>
      ) : (
        source.label
      )}
    </p>
  );
}

function ProgressCard() {
  const { total, apuntesCompletos, soloResumen, pendientes, conPractica, questions } = data.progress;
  const porcentaje = Math.round((apuntesCompletos / total) * 100);
  return (
    <section className="card demo-progress" aria-labelledby="progreso-contenido">
      <h2 id="progreso-contenido">Cobertura del temario</h2>
      <div className="demo-stats">
        <div>
          <strong>{apuntesCompletos}</strong>
          <span>apuntes completos</span>
        </div>
        <div>
          <strong>{soloResumen}</strong>
          <span>solo resumen</span>
        </div>
        <div>
          <strong>{pendientes}</strong>
          <span>pendientes</span>
        </div>
        <div>
          <strong>{conPractica}</strong>
          <span>con práctica</span>
        </div>
      </div>
      <div
        className="demo-bar"
        role="progressbar"
        aria-valuenow={porcentaje}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label="Temas con apuntes completos"
      >
        <span style={{ width: `${String(porcentaje)}%` }} />
      </div>
      <p className="hint">
        {questions} preguntas de test en total. Los apuntes completos incluyen apartados, tabla,
        ejemplo, fuente y práctica de 10 preguntas.
      </p>
    </section>
  );
}

function ConvocatoriasCard() {
  const { total, draft, archived, items } = data.convocatorias;
  return (
    <section className="card" aria-labelledby="convocatorias">
      <h2 id="convocatorias">Convocatorias a las que sirve</h2>
      <p>
        Un <strong>temario común</strong> para <strong>{total} convocatorias C1 de informática</strong>{' '}
        ({draft} por confirmar y {archived} cerradas) y el perfil TAI. No se copia el temario por
        convocatoria: se comparte y cada una aplica sus particularidades.
      </p>
      <details className="demo-details">
        <summary>Ver las {total} convocatorias</summary>
      <aside className="demo-convocatorias" aria-label="Convocatorias">
        <ul>
          {items.map((item) => (
            <li key={item.code}>
              <strong>{item.title}</strong>
              <span className="hint">
                {[item.administration, item.territory].filter((part) => part !== '').join(' · ')}
                {item.status === 'archived' ? ' · cerrada' : ' · por confirmar'}
              </span>
              {item.url !== '' && (
                <a href={item.url} target="_blank" rel="noreferrer noopener">
                  Bases de {item.title}
                </a>
              )}
            </li>
          ))}
        </ul>
      </aside>
      </details>
    </section>
  );
}

function Header() {
  return (
    <header className="demo-header">
      <a className="demo-brand" href="#/">
        OpoFuente <span className="demo-tag">demo estática</span>
      </a>
      <nav className="demo-nav" aria-label="Secciones de la demo">
        <button className="button" type="button" onClick={() => { go('temario'); }}>
          Temario
        </button>
        <button className="button" type="button" onClick={() => { go('cobertura'); }}>
          Cobertura
        </button>
        <button className="button" type="button" onClick={() => { go('practicas'); }}>
          Prácticas
        </button>
        <button className="button" type="button" onClick={() => { go('guia'); }}>
          Guía
        </button>
      </nav>
    </header>
  );
}

function ComoFunciona() {
  return (
    <>
      <section className="page__header">
        <h1>Cómo funciona</h1>
        <p className="page__lead">
          Es una demo estática: el temario va empaquetado y tu progreso se guarda en este navegador.
        </p>
      </section>
      <section className="card">
        <ol>
          <li>Elige un tema en <strong>Temario</strong> o una práctica en <strong>Prácticas</strong>.</li>
          <li>En la práctica, al elegir una opción se corrige al momento y verás la explicación.</li>
          <li>El progreso se guarda en <code>localStorage</code>; puedes continuar donde lo dejaste.</li>
          <li>Si borras los datos del sitio, se pierde el progreso. No hay cuenta ni servidor.</li>
        </ol>
        <div className="demo-actions">
          <button className="button" type="button" onClick={() => { go(''); }}>
            Volver a la portada
          </button>
        </div>
      </section>
    </>
  );
}

function BlockSummary() {
  return (
    <section className="card demo-block-summary">
      <h2>Avance por bloque</h2>
      <p className="demo-block-line">
        {data.curriculum.blocks
          .map(
            (block) =>
              `${block.path}: ${String(block.coverage.conApuntes)}/${String(block.coverage.total)} (${String(
                porcentaje(block.coverage.conApuntes, block.coverage.total),
              )}%)`,
          )
          .join(' · ')}
      </p>
      <p className="hint">Temas con apuntes completos sobre el total de cada bloque.</p>
    </section>
  );
}

function Home() {
  const progress = loadProgress();
  const resume = loadResume();
  const pendiente = data.practices.find((practice) => {
    const saved = progress[practice.slug];
    return saved !== undefined && saved.lastScore < saved.lastTotal;
  });
  const continuePractice =
    (resume !== null ? PRACTICE_BY_SLUG.get(resume.slug) : undefined) ??
    pendiente ??
    data.practices[0];
  const resumeQuestion =
    resume !== null && continuePractice !== undefined && resume.slug === continuePractice.slug
      ? Math.min(resume.index + 1, continuePractice.questions.length)
      : null;
  const siguientes =
    continuePractice === undefined
      ? data.practices.slice(0, 3)
      : data.practices.filter((practice) => practice.slug !== continuePractice.slug).slice(0, 3);

  return (
    <>
      <section className="page__header">
        <h1>OpoFuente — demo estática</h1>
        <p className="page__lead">
          Temario común de informática C1: {data.progress.apuntesCompletos} temas con apuntes completos
          y su práctica de 10 preguntas. Todo en tu navegador.
        </p>
      </section>
      <ProgressCard />
      <BlockSummary />
      {continuePractice !== undefined && (
        <section className="card demo-continue">
          <h2>Continuar</h2>
          <p>
            {resumeQuestion !== null
              ? `${continuePractice.tema_path} · pregunta ${String(resumeQuestion)} de ${String(continuePractice.questions.length)}`
              : `Empieza por ${continuePractice.tema_path}`}
          </p>
          <button
            className="button"
            type="button"
            onClick={() => {
              go(`practica/${continuePractice.slug}`);
            }}
          >
            Continuar donde lo dejé
          </button>
        </section>
      )}
      <section className="card">
        <h2>Siguientes prácticas</h2>
        <ul className="demo-next">
          {siguientes.map((practice) => (
            <li key={practice.slug}>
              <button
                className="button button--link"
                type="button"
                onClick={() => {
                  go(`practica/${practice.slug}`);
                }}
              >
                {practice.tema_path} · {practice.title.replace(/^Práctica · /, '')}
              </button>
            </li>
          ))}
        </ul>
        <button className="button button--link" type="button" onClick={() => { go('practicas'); }}>
          Ver todas las prácticas
        </button>
      </section>
      <ConvocatoriasCard />
    </>
  );
}

function Guia() {
  const progress = loadProgress();
  const hechas = data.practices
    .map((practice) => {
      const resultado = progress[practice.slug];
      if (resultado === undefined) {
        return null;
      }
      const porcentaje = resultado.lastTotal === 0
        ? 0
        : Math.round((resultado.lastScore / resultado.lastTotal) * 100);
      return { practice, resultado, porcentaje };
    })
    .filter((item): item is NonNullable<typeof item> => item !== null)
    .sort((a, b) => a.porcentaje - b.porcentaje);
  const flojas = hechas.filter((item) => item.porcentaje < 70);

  return (
    <>
      <section className="page__header">
        <h1>Guía de estudio</h1>
        <p className="page__lead">
          Orden recomendado de bloques y detección de los temas flojos a partir de tus prácticas.
        </p>
      </section>
      <section className="card">
        <h2>Orden recomendado</h2>
        <p>
          Primero la base normativa y técnica, después sistemas y redes, y al final datos y seguridad.
          Así reutilizas conceptos en lugar de memorizarlos aislados.
        </p>
        <ol className="demo-guide">
          {data.curriculum.blocks.map((block) => (
            <li key={block.path}>
              <strong>{block.path} · {block.title}</strong>{' '}
              <span className="hint">
                {block.coverage.conApuntes}/{block.coverage.total} con apuntes (
                {porcentaje(block.coverage.conApuntes, block.coverage.total)}%)
              </span>
            </li>
          ))}
        </ol>
      </section>
      <section className="card">
        <h2>Tus temas flojos</h2>
        {hechas.length === 0 ? (
          <p>
            Todavía no has hecho ninguna práctica. Empieza por una y aquí aparecerán los temas que
            conviene reforzar.
          </p>
        ) : flojas.length === 0 ? (
          <p>
            No hay temas por debajo del 70 % en tus últimas prácticas. Sigue así y repasa los temas
            pendientes del temario.
          </p>
        ) : (
          <>
            <p className="hint">
              Por debajo del 70 % en la última práctica. Refuerza el tema y repite la práctica.
            </p>
            <ul className="demo-guide">
              {flojas.map(({ practice, porcentaje: pct }) => (
                <li key={practice.slug}>
                  <strong>{practice.tema_path}</strong> · {pct} % ·{' '}
                  <button
                    className="button button--link"
                    type="button"
                    onClick={() => {
                      go(`tema/${practice.tema_path}`);
                    }}
                  >
                    Repasar tema
                  </button>{' '}
                  <button
                    className="button button--link"
                    type="button"
                    onClick={() => {
                      go(`practica/${practice.slug}`);
                    }}
                  >
                    Repetir práctica
                  </button>
                </li>
              ))}
            </ul>
          </>
        )}
        <div className="demo-actions">
          <button className="button" type="button" onClick={() => { go('temario'); }}>
            Ir al temario
          </button>
          <button className="button button--link" type="button" onClick={() => { go('practicas'); }}>
            Ver todas las prácticas
          </button>
        </div>
      </section>
    </>
  );
}

function Cobertura() {
  return (
    <>
      <section className="page__header">
        <h1>Mapa de cobertura</h1>
        <p className="page__lead">
          Estado de los 40 temas: apuntes completos, solo resumen o pendientes, y si tienen práctica.
          Solo cuenta el contenido publicado en esta demo.
        </p>
      </section>
      <ProgressCard />
      {data.curriculum.blocks.map((block) => (
        <section className="card" key={block.path}>
          <h2>
            {block.path} · {block.title}
          </h2>
          <p className="demo-block-progress">
            {block.path}: {block.coverage.conApuntes}/{block.coverage.total} (
            {porcentaje(block.coverage.conApuntes, block.coverage.total)}%) con apuntes ·{' '}
            {block.coverage.conPractica}/{block.coverage.total} con práctica
            {block.coverage.pendientes > 0 ? ` · ${pendientesTexto(block.coverage.pendientes)}` : ''}
          </p>
          <div className="table-wrap">
            <table className="table demo-cobertura">
              <thead>
                <tr>
                  <th scope="col">Tema</th>
                  <th scope="col">Apuntes</th>
                  <th scope="col">Práctica</th>
                </tr>
              </thead>
              <tbody>
                {block.topics.map((topic) => (
                  <tr key={topic.path}>
                    <td>
                      <button
                        className="button button--link"
                        type="button"
                        onClick={() => {
                          go(`tema/${topic.path}`);
                        }}
                      >
                        {topic.path} · {topic.title}
                      </button>
                    </td>
                    <td>
                      <ApuntesBadge status={topic.apuntesStatus} />
                    </td>
                    <td>
                      <PracticaBadge status={topic.practicaStatus} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ))}
    </>
  );
}

function Temario({ initialFiltro = 'todos' }: { readonly initialFiltro?: Filtro }) {
  const [query, setQuery] = useState('');
  const [filtro, setFiltro] = useState<Filtro>(initialFiltro);
  const search = normalized(query.trim());
  const blocks = data.curriculum.blocks
    .map((block) => ({
      ...block,
      topics: block.topics.filter((topic) => {
        const coincide = search === '' || normalized(`${topic.path} ${topic.title}`).includes(search);
        if (!coincide) {
          return false;
        }
        if (filtro === 'apuntes') {
          return topic.apuntesStatus === 'completos';
        }
        if (filtro === 'practica') {
          return topic.practicaStatus === 'con_practica';
        }
        return true;
      }),
    }))
    .filter((block) => block.topics.length > 0);
  const totalVisibles = blocks.reduce((total, block) => total + block.topics.length, 0);

  return (
    <>
      <section className="page__header">
        <h1>Temario</h1>
        <p className="page__lead">
          {data.curriculum.name}: {data.curriculum.blocks.length} bloques · {TOPIC_LIST.length} temas.
          Cada tema muestra el estado de sus apuntes y de su práctica.
        </p>
      </section>
      <ProgressCard />
      <section className="card demo-filters" aria-label="Buscar y filtrar el temario">
        <label className="demo-search">
          <span>Buscar por código o título</span>
          <input
            type="search"
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
            }}
            placeholder="I.1, Constitución, redes…"
          />
        </label>
        <div className="demo-filter-buttons">
          {(
            [
              ['todos', 'Todos'],
              ['apuntes', 'Con apuntes'],
              ['practica', 'Con práctica'],
            ] as const
          ).map(([value, label]) => (
            <button
              key={value}
              type="button"
              className={filtro === value ? 'button demo-filter--active' : 'button'}
              aria-pressed={filtro === value}
              onClick={() => {
                setFiltro(value);
              }}
            >
              {label}
            </button>
          ))}
        </div>
        <p className="hint">
          {totalVisibles} tema(s) visibles de {TOPIC_LIST.length}.
        </p>
      </section>
      {blocks.map((block) => (
        <section className="card" key={block.path}>
          <h2>
            {block.path} · {block.title}
          </h2>
          <p className="demo-block-progress">
            {block.path}: {block.coverage.conApuntes}/{block.coverage.total} (
            {porcentaje(block.coverage.conApuntes, block.coverage.total)}%) con apuntes ·{' '}
            {block.coverage.conPractica}/{block.coverage.total} con práctica
            {block.coverage.pendientes > 0 ? ` · ${pendientesTexto(block.coverage.pendientes)}` : ''}
          </p>
          <ul className="demo-topics">
            {block.topics.map((topic) => (
              <li key={topic.path}>
                <button
                  className="demo-topic"
                  type="button"
                  onClick={() => {
                    go(`tema/${topic.path}`);
                  }}
                >
                  <span className="demo-topic__path">{topic.path}</span>
                  <span className="demo-topic__title">{topic.title}</span>
                  <span className="demo-topic__badges">
                    <ApuntesBadge status={topic.apuntesStatus} />
                    <PracticaBadge status={topic.practicaStatus} />
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </section>
      ))}
      {blocks.length === 0 && (
        <section className="card">
          <p>No hay temas que coincidan con la búsqueda.</p>
        </section>
      )}
    </>
  );
}

function Breadcrumbs({ path }: { path: string }) {
  return (
    <nav className="demo-breadcrumbs" aria-label="Migas de pan">
      <button
        className="button button--link"
        type="button"
        onClick={() => {
          go('temario');
        }}
      >
        Temario
      </button>
      <span aria-hidden="true">›</span>
      <span aria-current="page">{path}</span>
    </nav>
  );
}

function PendingTopic({ topic, summary }: { topic: TopicContent; summary: TopicSummary }) {
  return (
    <>
      <section className="page__header">
        <Breadcrumbs path={summary.path} />
        <h1>{summary.title}</h1>
        <p className="page__lead">Tema {summary.path} · temario común de informática C1</p>
      </section>
      <section className="card demo-pending">
        <h2>Apuntes pendientes.</h2>
        <p>
          Este tema <strong>todavía no está redactado</strong>. No se muestra un párrafo vacío ni
          contenido de relleno: simplemente falta.
        </p>
        <p className="hint">
          Hay {data.progress.apuntesCompletos} de {data.progress.total} temas con apuntes completos y{' '}
          {data.progress.pendientes} pendientes.
        </p>
        <button
          className="button"
          type="button"
          onClick={() => {
            go('temario/apuntes');
          }}
        >
          Ver temas completos
        </button>
        {topic.source.label !== '' && <SourceLine source={topic.source} />}
      </section>
    </>
  );
}

function Tema({ path }: { path: string }) {
  const summary = TOPIC_BY_PATH.get(path);
  if (summary === undefined) {
    return <p className="hint">Ese tema no existe en la demo.</p>;
  }
  const topic: TopicContent = data.topics[path] ?? {
    path,
    title: summary.title,
    apuntesStatus: 'pendiente',
    practicaStatus: 'pendiente',
    source: { label: '', url: '' },
    sections: [],
  };
  if (topic.apuntesStatus === 'pendiente') {
    return <PendingTopic topic={topic} summary={summary} />;
  }
  const practice = data.practices.find((item) => item.tema_path === path);
  return (
    <>
      <section className="page__header">
        <Breadcrumbs path={topic.path} />
        <h1>{topic.title}</h1>
        <p className="page__lead demo-topic__badges">
          Tema {topic.path} · <ApuntesBadge status={topic.apuntesStatus} />{' '}
          <PracticaBadge status={topic.practicaStatus} />
        </p>
        <p className="hint">
          Forma parte del temario común de las {data.convocatorias.total} convocatorias C1.{' '}
          <button
            className="button button--link"
            type="button"
            onClick={() => {
              go('');
            }}
          >
            Ver convocatorias
          </button>
        </p>
      </section>
      {topic.sections.map((section) => (
        <section className="card" key={section.heading}>
          <h2>{section.heading}</h2>
          {section.body !== undefined && <RichText text={section.body} />}
          {section.table !== undefined && (
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    {section.table.columns.map((column) => (
                      <th scope="col" key={column}>{column}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {section.table.rows.map((row, index) => (
                    <tr key={index}>
                      {row.map((cell, cellIndex) => (
                        <td key={cellIndex}>{cell}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      ))}
      <section className="card">
        <h2>Fuente</h2>
        <SourceLine source={topic.source} />
        <p className="hint">
          Contenido propio de la demo a partir de la fuente citada; no reproduce texto de academias.
        </p>
      </section>
      {practice !== undefined ? (
        <section className="card">
          <h2>Práctica de este tema</h2>
          <p className="hint">
            {practice.questions.length} preguntas con corrección y explicación. Puedes ver cada
            pregunta antes de empezar.
          </p>
          <div className="demo-actions">
            <button
              className="button"
              type="button"
              onClick={() => {
                go(`practica/${practice.slug}`);
              }}
            >
              Empezar la práctica
            </button>
            <button
              className="button button--link"
              type="button"
              onClick={() => {
                go(`pregunta/${practice.slug}/0`);
              }}
            >
              Ver la primera pregunta
            </button>
          </div>
          <ol className="demo-questions">
            {practice.questions.map((question, index) => (
              <li key={question.stem}>
                <button
                  className="button button--link"
                  type="button"
                  onClick={() => {
                    go(`pregunta/${practice.slug}/${index}`);
                  }}
                >
                  {question.stem}
                </button>
              </li>
            ))}
          </ol>
        </section>
      ) : (
        <section className="card demo-pending">
          <h2>Práctica pendiente</h2>
          <p>Este tema todavía no tiene práctica publicada en la demo.</p>
        </section>
      )}
    </>
  );
}

function Practicas() {
  const progress = loadProgress();
  return (
    <>
      <section className="page__header">
        <h1>Prácticas</h1>
        <p className="page__lead">
          {data.practices.length} prácticas, una por tema con apuntes completos. Se corrigen al
          momento y guardan tu mejor resultado en este navegador.
        </p>
      </section>
      <ProgressCard />
      {data.practices.map((practice) => {
        const saved = progress[practice.slug];
        return (
          <section className="card" key={practice.slug}>
            <h2>{practice.title}</h2>
            <p className="hint">Tema {practice.tema_path} · {practice.questions.length} preguntas</p>
            {saved !== undefined && (
              <p className="hint">
                Mejor: <strong>{saved.best} %</strong> · último: {saved.lastScore}/{saved.lastTotal}
              </p>
            )}
            <div className="demo-actions">
              <button
                className="button"
                type="button"
                onClick={() => {
                  go(`practica/${practice.slug}`);
                }}
              >
                {saved !== undefined ? 'Repetir' : 'Empezar'}
              </button>
            </div>
          </section>
        );
      })}
      <p>
        <button
          className="button button--link"
          type="button"
          onClick={() => {
            resetProgress();
            window.location.reload();
          }}
        >
          Borrar mi progreso de esta demo
        </button>
      </p>
    </>
  );
}

function Pregunta({ slug, index }: { slug: string; index: number }) {
  const practice = PRACTICE_BY_SLUG.get(slug);
  const question = practice?.questions[index];
  if (practice === undefined || question === undefined) {
    return <p className="hint">Esa pregunta no existe en la demo.</p>;
  }
  return (
    <>
      <section className="page__header">
        <p className="hint">
          <button
            className="button button--link"
            type="button"
            onClick={() => {
              go(`tema/${practice.tema_path}`);
            }}
          >
            ← Volver al tema
          </button>
        </p>
        <h1>Ficha de pregunta</h1>
        <p className="page__lead">
          Pregunta {index + 1} de {practice.questions.length} · {practice.title}
        </p>
      </section>
      <section className="card">
        <h2>{question.stem}</h2>
        <ul className="demo-options">
          {question.options.map((option) => (
            <li
              key={option.key}
              className={option.key === question.correct ? 'demo-option demo-option--correct' : 'demo-option'}
            >
              <span className="demo-option__key">{option.key})</span> {option.text}
              {option.key === question.correct && <strong> · correcta</strong>}
            </li>
          ))}
        </ul>
        <h3>Por qué</h3>
        <p>{question.explanation}</p>
        {question.source !== undefined && <SourceLine source={question.source} official />}
      </section>
      <div className="demo-actions">
        {index > 0 && (
          <button className="button" type="button" onClick={() => { go(`pregunta/${slug}/${index - 1}`); }}>
            Anterior
          </button>
        )}
        {index + 1 < practice.questions.length && (
          <button className="button" type="button" onClick={() => { go(`pregunta/${slug}/${index + 1}`); }}>
            Siguiente
          </button>
        )}
      </div>
    </>
  );
}

function PracticeRunner({ practice }: { practice: Practice }) {
  const resumed = loadResume();
  const initialIndex =
    resumed !== null && resumed.slug === practice.slug
      ? Math.min(Math.max(resumed.index, 0), practice.questions.length - 1)
      : 0;
  const [index, setIndex] = useState(initialIndex);
  const [selected, setSelected] = useState<string | null>(null);
  const [answered, setAnswered] = useState(false);
  const [answers, setAnswers] = useState<Record<number, string>>(
    resumed !== null && resumed.slug === practice.slug ? resumed.answers : {},
  );
  const [result, setResult] = useState<PracticeResult | null>(null);

  useEffect(() => {
    if (result === null) {
      saveResume(practice.slug, index, answers);
    }
  }, [answers, index, practice.slug, result]);

  const question = practice.questions[index];

  if (result !== null) {
    return (
      <>
        <section className="page__header">
          <h1>Resultado</h1>
          <p className="page__lead">{practice.title}</p>
        </section>
        <section className="card">
          <h2>
            {result.lastScore} de {result.lastTotal} correctas
          </h2>
          <p>
            Mejor resultado guardado en este navegador: <strong>{result.best} %</strong> ·{' '}
            {result.attempts} intento(s).
          </p>
          <div className="demo-actions">
            <button
              className="button"
              type="button"
              onClick={() => {
                window.location.reload();
              }}
            >
              Repetir
            </button>
            <button
              className="button"
              type="button"
              onClick={() => {
                go(`tema/${practice.tema_path}`);
              }}
            >
              Volver a {practice.tema_path}
            </button>
            <button
              className="button"
              type="button"
              onClick={() => {
                go('practicas');
              }}
            >
              Ver todas las prácticas
            </button>
          </div>
        </section>
      </>
    );
  }

  if (question === undefined) {
    return <p className="hint">Esta práctica no tiene preguntas.</p>;
  }

  const isCorrect = selected === question.correct;
  const isLast = index + 1 === practice.questions.length;

  function finish(): void {
    clearResume();
    const score = scoreAnswers(answers, practice.questions);
    setResult(saveResult(practice.slug, score.correct, score.total));
  }

  function siguiente(): void {
    if (!answered) {
      return;
    }
    if (isLast) {
      finish();
      return;
    }
    const next = index + 1;
    setIndex(next);
    setSelected(null);
    setAnswered(false);
    saveResume(practice.slug, next, answers);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  return (
    <>
      <section className="page__header">
        <h1>{practice.title}</h1>
        <div className="demo-practice__top">
          <p className="page__lead">
            Pregunta {index + 1} de {practice.questions.length} · corrección al elegir
          </p>
          <button
            className="button button--link"
            type="button"
            onClick={() => {
              go(`tema/${practice.tema_path}`);
            }}
          >
            Volver a {practice.tema_path}
          </button>
        </div>
      </section>
      <section className="card">
        <h2>{question.stem}</h2>
        <ul className="demo-options">
          {question.options.map((option) => (
            <li key={option.key}>
              <label className="demo-option">
                <input
                  type="radio"
                  name="respuesta"
                  value={option.key}
                  checked={selected === option.key}
                  disabled={answered}
                  onChange={() => {
                    if (answered) {
                      return;
                    }
                    setSelected(option.key);
                    setAnswers((previous) => ({ ...previous, [index]: option.key }));
                    setAnswered(true);
                  }}
                />{' '}
                <span className="demo-option__key">{option.key})</span> {option.text}
              </label>
            </li>
          ))}
        </ul>
        {!answered ? (
          <p className="hint">Elige una opción: se corrige al momento.</p>
        ) : (
          <>
            <div className={isCorrect ? 'demo-feedback demo-feedback--ok' : 'demo-feedback demo-feedback--bad'}>
              <strong>{isCorrect ? 'Correcto.' : `Incorrecto: era ${question.correct}.`}</strong>{' '}
              {question.explanation}
            </div>
            {question.source !== undefined && <SourceLine source={question.source} official />}
            <div className="demo-actions">
              <button className="button" type="button" onClick={siguiente}>
                {isLast ? 'Ver resultado' : 'Siguiente pregunta'}
              </button>
            </div>
          </>
        )}
      </section>
    </>
  );
}

function App() {
  const route = useRoute();
  const parts = route.split('/').filter((part) => part !== '');

  let content: ReactElement;
  if (parts[0] === 'temario' && parts[1] === 'apuntes') {
    content = <Temario initialFiltro="apuntes" key="apuntes" />;
  } else if (parts[0] === 'temario') {
    content = <Temario />;
  } else if (parts[0] === 'como-funciona') {
    content = <ComoFunciona />;
  } else if (parts[0] === 'guia') {
    content = <Guia />;
  } else if (parts[0] === 'cobertura') {
    content = <Cobertura />;
  } else if (parts[0] === 'tema' && parts[1] !== undefined) {
    content = <Tema path={parts[1]} />;
  } else if (parts[0] === 'practicas') {
    content = <Practicas />;
  } else if (parts[0] === 'practica' && parts[1] !== undefined) {
    const practice = PRACTICE_BY_SLUG.get(parts[1]);
    content =
      practice === undefined ? <p className="hint">Esa práctica no existe.</p> : (
        <PracticeRunner practice={practice} key={practice.slug} />
      );
  } else if (parts[0] === 'pregunta' && parts[1] !== undefined && parts[2] !== undefined) {
    content = <Pregunta slug={parts[1]} index={Number(parts[2])} />;
  } else {
    content = <Home />;
  }

  return (
    <div className="demo-shell">
      <Header />
      <div className="demo-warning" role="note">
        <span>{data.warning}</span>{' '}
        <button
          className="button button--link"
          type="button"
          onClick={() => {
            go('como-funciona');
          }}
        >
          Cómo funciona
        </button>
      </div>
      <main className="demo-main">{content}</main>
      <footer className="demo-footer">
        <p>OpoFuente · demo estática · contenido propio</p>
      </footer>
    </div>
  );
}

const container = document.getElementById('root');
if (container === null) {
  throw new Error('falta #root en la página de demo');
}
createRoot(container).render(<App />);
