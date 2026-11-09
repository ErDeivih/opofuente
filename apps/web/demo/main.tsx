/**
 * Demo estática de OpoFuente para GitHub Pages.
 *
 * No hay servidor ni API: todo el contenido viene empaquetado en `data.json`, y el progreso se guarda
 * en `localStorage`. Es una demo de lectura y práctica, no la aplicación completa (esa vive en local
 * y usa SQLite). El aviso superior lo dice en todo momento.
 */

import { useEffect, useState, type ReactElement } from 'react';
import { createRoot } from 'react-dom/client';

import demoData from './data.json';
import { loadProgress, resetProgress, saveResult, scoreAnswers, type PracticeResult } from './practice';
import '../src/styles/global.css';
import './demo.css';

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

interface Topic {
  readonly path: string;
  readonly title: string;
  readonly apuntes: string;
  readonly practica: boolean;
}

interface Block {
  readonly path: string;
  readonly title: string;
  readonly temas: readonly Topic[];
}

interface DemoData {
  readonly title: string;
  readonly warning: string;
  readonly curriculum: { readonly code: string; readonly name: string; readonly blocks: readonly Block[] };
  readonly practices: readonly Practice[];
}

const data = demoData as DemoData;
const TOPICS = data.curriculum.blocks.flatMap((block) => block.temas);
const TOPIC_BY_PATH = new Map(TOPICS.map((topic) => [topic.path, topic]));
const PRACTICE_BY_SLUG = new Map(data.practices.map((practice) => [practice.slug, practice]));

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

function Apuntes({ text }: { text: string }) {
  if (text.trim() === '') {
    return <p className="hint">Este tema aún no tiene apuntes en la demo.</p>;
  }
  return (
    <div className="demo-apuntes">
      {text.split(/\n\n+/).map((paragraph, index) => (
        <p key={index}>
          {paragraph.split(/(\*\*[^*]+\*\*)/g).map((fragment, fragmentIndex) =>
            fragment.startsWith('**') && fragment.endsWith('**') ? (
              <strong key={fragmentIndex}>{fragment.slice(2, -2)}</strong>
            ) : (
              <span key={fragmentIndex}>{fragment}</span>
            ),
          )}
        </p>
      ))}
    </div>
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
          Una muestra del temario común de informática C1 y de dos prácticas por tema. Todo funciona
          en tu navegador: no hay servidor, no hay cuenta y no se envía nada.
        </p>
      </section>
      <div className="card">
        <h2>Qué puedes hacer aquí</h2>
        <ul>
          <li>Recorrer el temario (5 bloques, 40 temas) y leer los apuntes del tema I.1 y del II.13.</li>
          <li>Hacer dos prácticas de 10 preguntas cada una, con corrección y explicación al momento.</li>
          <li>Ver la ficha de cada pregunta con su respuesta y su explicación.</li>
        </ul>
        <p className="hint">
          El progreso se guarda en <code>localStorage</code> de este navegador. Si lo borras, se
          pierde; no hay cuenta ni sincronización.
        </p>
      </div>
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
          {data.curriculum.name}: {data.curriculum.blocks.length} bloques · {TOPICS.length} temas.
          Los temas marcados con «práctica» tienen preguntas en esta demo.
        </p>
      </section>
      {data.curriculum.blocks.map((block) => (
        <section className="card" key={block.path}>
          <h2>
            {block.path} · {block.title}
          </h2>
          <ul className="demo-topics">
            {block.temas.map((topic) => {
              const practice = data.practices.find((item) => item.tema_path === topic.path);
              return (
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
                    {practice !== undefined && <span className="demo-tag">práctica</span>}
                  </button>
                </li>
              );
            })}
          </ul>
        </section>
      ))}
    </>
  );
}

function Tema({ path }: { path: string }) {
  const topic = TOPIC_BY_PATH.get(path);
  const practice = data.practices.find((item) => item.tema_path === path);
  if (topic === undefined) {
    return <p className="hint">Ese tema no existe en la demo.</p>;
  }
  return (
    <>
      <section className="page__header">
        <p className="hint">
          <button className="button button--link" type="button" onClick={() => { go('temario'); }}>
            ← Volver al temario
          </button>
        </p>
        <h1>{topic.title}</h1>
        <p className="page__lead">Tema {topic.path} · temario común de informática C1</p>
      </section>
      <section className="card">
        <h2>Apuntes</h2>
        <Apuntes text={topic.apuntes} />
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
        <p className="hint">Este tema no tiene práctica en la demo; el temario completo sí está.</p>
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
          Dos prácticas de demostración, una por tema. Se corrigen al momento y guardan tu mejor
          resultado en este navegador.
        </p>
      </section>
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
          OpoFuente es una aplicación local. Esta página es una demo estática con datos empaquetados:
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
