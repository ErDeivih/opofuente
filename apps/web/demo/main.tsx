/**
 * Demo estática de OpoFuente para GitHub Pages.
 *
 * No hay servidor ni API: todo el contenido viene empaquetado en `data.json`, y el progreso se guarda
 * en `localStorage`. Cada tema declara su estado (`completo`, `con_preguntas` o `pendiente`) y la
 * demo lo dice: los temas sin escribir se marcan «en preparación» en lugar de mostrar un párrafo vacío.
 */

import { useEffect, useState, type ReactElement } from 'react';
import { createRoot } from 'react-dom/client';

import demoData from './data.json';
import { loadProgress, resetProgress, saveResult, scoreAnswers, type PracticeResult } from './practice';
import '../src/styles/global.css';
import './demo.css';

type TopicStatus = 'completo' | 'con_preguntas' | 'pendiente';

interface Option {
  readonly key: string;
  readonly text: string;
}

interface Question {
  readonly stem: string;
  readonly options: readonly Option[];
  readonly correct: string;
  readonly explanation: string;
}

interface Practice {
  readonly slug: string;
  readonly tema_path: string;
  readonly title: string;
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

interface DemoSource {
  readonly label: string;
  readonly url: string;
}

interface TopicSummary {
  readonly path: string;
  readonly title: string;
  readonly status: TopicStatus;
  readonly sectionCount: number;
  readonly questionCount: number;
}

interface TopicContent {
  readonly path: string;
  readonly title: string;
  readonly status: TopicStatus;
  readonly source: DemoSource;
  readonly sections: readonly DemoSection[];
  readonly practiceSlug?: string;
}

interface Block {
  readonly path: string;
  readonly title: string;
  readonly topics: readonly TopicSummary[];
}

interface DemoData {
  readonly title: string;
  readonly warning: string;
  readonly curriculum: {
    readonly code: string;
    readonly name: string;
    readonly blocks: readonly Block[];
  };
  readonly topics: Readonly<Record<string, TopicContent>>;
  readonly practices: readonly Practice[];
  readonly progress: {
    readonly total: number;
    readonly complete: number;
    readonly withQuestions: number;
    readonly pending: number;
    readonly questions: number;
  };
}

const data = demoData as DemoData;
const TOPIC_LIST = data.curriculum.blocks.flatMap((block) => block.topics);
const TOPIC_BY_PATH = new Map(TOPIC_LIST.map((topic) => [topic.path, topic]));
const PRACTICE_BY_SLUG = new Map(data.practices.map((practice) => [practice.slug, practice]));

const STATUS_LABEL: Readonly<Record<TopicStatus, string>> = {
  completo: 'Completo',
  con_preguntas: 'Con preguntas',
  pendiente: 'En preparación',
};

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

/** Texto con **negritas** y listas simples; no interpreta HTML. */
function RichText({ text }: { text: string }) {
  return (
    <>
      {text.split(/\n\n+/).map((paragraph, index) => {
        const lines = paragraph.split('\n').map((line) => line.trim());
        const bullets = lines.filter((line) => line.startsWith('- '));
        if (bullets.length === lines.filter((line) => line !== '').length && bullets.length > 0) {
          return (
            <ul key={index}>
              {bullets.map((bullet, bulletIndex) => (
                <li key={bulletIndex}>
                  {withBold(bullet.slice(2))}
                </li>
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

function StatusBadge({ status }: { status: TopicStatus }) {
  return <span className={`demo-status demo-status--${status}`}>{STATUS_LABEL[status]}</span>;
}

function ProgressCard() {
  const { total, complete, withQuestions, pending, questions } = data.progress;
  const porcentaje = Math.round((complete / total) * 100);
  return (
    <section className="card demo-progress" aria-labelledby="progreso-contenido">
      <h2 id="progreso-contenido">Contenido de esta demo</h2>
      <p>
        <strong>{complete}</strong> temas completos · <strong>{withQuestions}</strong> con preguntas ·{' '}
        <strong>{pending}</strong> en preparación (de {total})
      </p>
      <div className="demo-bar" role="progressbar" aria-valuenow={porcentaje} aria-valuemin={0} aria-valuemax={100} aria-label="Temas completos">
        <span style={{ width: `${String(porcentaje)}%` }} />
      </div>
      <p className="hint">
        {questions} preguntas de test en total. Los {complete} temas completos incluyen su práctica;
        los {pending} pendientes aún no están escritos y se marcan «en preparación». Un tema completo
        lleva apartados, tabla, ejemplo, fuente y 10 preguntas.
      </p>
    </section>
  );
}

function SourceLine({ source }: { source: DemoSource }) {
  return (
    <p className="hint demo-source">
      Fuente: {source.url !== '' ? (
        <a href={source.url} target="_blank" rel="noreferrer noopener">
          {source.label}
        </a>
      ) : (
        source.label
      )}
    </p>
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
        <button className="button" type="button" onClick={() => { go('practicas'); }}>
          Prácticas
        </button>
      </nav>
    </header>
  );
}

function Home() {
  const progress = loadProgress();
  return (
    <>
      <section className="page__header">
        <h1>OpoFuente — demo estática</h1>
        <p className="page__lead">
          Una muestra del temario común de informática C1: {data.progress.complete} temas redactados
          con apartados, tablas, ejemplos, fuente y 10 preguntas cada uno. Todo funciona en tu
          navegador, sin cuenta y sin servidor.
        </p>
      </section>
      <ProgressCard />
      <section className="card">
        <h2>Qué puedes hacer aquí</h2>
        <ul>
          <li>Recorrer los 40 temas y ver cuáles están completos y cuáles en preparación.</li>
          <li>Estudiar los temas redactados y hacer su práctica de 10 preguntas con explicación.</li>
          <li>Ver la ficha de cada pregunta con su respuesta razonada.</li>
        </ul>
        <p className="hint">
          El progreso se guarda en <code>localStorage</code> de este navegador. Si lo borras, se
          pierde; no hay cuenta ni sincronización.
        </p>
      </section>
      <div className="demo-grid">
        {data.practices.map((practice) => {
          const saved = progress[practice.slug];
          return (
            <section className="card demo-card" key={practice.slug}>
              <h2>{practice.title}</h2>
              <p className="hint">
                {practice.questions.length} preguntas · tema {practice.tema_path}
              </p>
              {saved !== undefined ? (
                <p className="hint">
                  Mejor resultado: <strong>{saved.best} %</strong> · {saved.attempts} intento(s)
                </p>
              ) : (
                <p className="hint">Todavía no la has hecho.</p>
              )}
              <button
                className="button"
                type="button"
                onClick={() => {
                  go(`practica/${practice.slug}`);
                }}
              >
                Empezar la práctica
              </button>
            </section>
          );
        })}
      </div>
    </>
  );
}

function Temario() {
  return (
    <>
      <section className="page__header">
        <h1>Temario</h1>
        <p className="page__lead">
          {data.curriculum.name}: {data.curriculum.blocks.length} bloques · {TOPIC_LIST.length} temas.
          El estado de cada tema se ve en su insignia.
        </p>
      </section>
      <ProgressCard />
      {data.curriculum.blocks.map((block) => (
        <section className="card" key={block.path}>
          <h2>
            {block.path} · {block.title}
          </h2>
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
                  <StatusBadge status={topic.status} />
                </button>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </>
  );
}

function PendingTopic({ topic, summary }: { topic: TopicContent; summary: TopicSummary }) {
  return (
    <>
      <section className="page__header">
        <p className="hint">
          <button className="button button--link" type="button" onClick={() => { go('temario'); }}>
            ← Volver al temario
          </button>
        </p>
        <h1>{summary.title}</h1>
        <p className="page__lead">Tema {summary.path} · temario común de informática C1</p>
      </section>
      <section className="card demo-pending">
        <h2>En preparación</h2>
        <p>
          Este tema <strong>todavía no está redactado en la demo</strong>. No se muestra un párrafo
          vacío ni contenido de relleno: simplemente falta.
        </p>
        <p className="hint">
          Hay {data.progress.complete} de {data.progress.total} temas completos y{' '}
          {data.progress.pending} en preparación. La aplicación completa mantiene el temario común con
          sus 40 temas y el contenido se irá publicando aquí.
        </p>
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
    status: 'pendiente',
    source: { label: '', url: '' },
    sections: [],
  };
  if (topic.status === 'pendiente') {
    return <PendingTopic topic={topic} summary={summary} />;
  }
  const practice = data.practices.find((item) => item.tema_path === path);
  return (
    <>
      <section className="page__header">
        <p className="hint">
          <button className="button button--link" type="button" onClick={() => { go('temario'); }}>
            ← Volver al temario
          </button>
        </p>
        <h1>{topic.title}</h1>
        <p className="page__lead">
          Tema {topic.path} · <StatusBadge status={topic.status} /> · {topic.sections.length}{' '}
          apartados
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
      {practice !== undefined && (
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
          {data.practices.length} prácticas de demostración, una por tema redactado. Se corrigen al
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
  const [index, setIndex] = useState(0);
  const [selected, setSelected] = useState<string | null>(null);
  const [checked, setChecked] = useState(false);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [result, setResult] = useState<PracticeResult | null>(null);

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
    if (selected === null) {
      return;
    }
    const respuestas = { ...answers, [index]: selected };
    const score = scoreAnswers(respuestas, practice.questions);
    setResult(saveResult(practice.slug, score.correct, score.total));
  }

  return (
    <>
      <section className="page__header">
        <h1>{practice.title}</h1>
        <p className="page__lead">
          Pregunta {index + 1} de {practice.questions.length} · corrección al momento
        </p>
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
                  disabled={checked}
                  onChange={() => {
                    setSelected(option.key);
                  }}
                />{' '}
                <span className="demo-option__key">{option.key})</span> {option.text}
              </label>
            </li>
          ))}
        </ul>
        {!checked ? (
          <div className="demo-actions">
            <button
              className="button"
              type="button"
              disabled={selected === null}
              onClick={() => {
                setChecked(true);
                if (selected !== null) {
                  setAnswers((previous) => ({ ...previous, [index]: selected }));
                }
              }}
            >
              Comprobar
            </button>
          </div>
        ) : (
          <>
            <div className={isCorrect ? 'demo-feedback demo-feedback--ok' : 'demo-feedback demo-feedback--bad'}>
              <strong>{isCorrect ? 'Correcto.' : `Incorrecto: era ${question.correct}.`}</strong>{' '}
              {question.explanation}
            </div>
            <div className="demo-actions">
              <button
                className="button"
                type="button"
                onClick={() => {
                  if (isLast) {
                    finish();
                    return;
                  }
                  setIndex(index + 1);
                  setSelected(null);
                  setChecked(false);
                }}
              >
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
  if (parts[0] === 'temario') {
    content = <Temario />;
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
        <strong>Demo.</strong> {data.warning}
      </div>
      <main className="demo-main">{content}</main>
      <footer className="demo-footer">
        <p>
          OpoFuente es una aplicación local. Esta página es una demo estática con contenido propio:
          no incluye Guardia Civil, ni tu corpus, ni guarda nada fuera de este navegador.
        </p>
      </footer>
    </div>
  );
}

const container = document.getElementById('root');
if (container === null) {
  throw new Error('falta #root en la página de demo');
}
createRoot(container).render(<App />);
