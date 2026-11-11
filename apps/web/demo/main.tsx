/**
 * Demo estática de OpoFuente para GitHub Pages.
 *
 * No hay servidor ni API: todo el contenido viene empaquetado en `data.json`, y el progreso se guarda
 * en `localStorage`. Cada tema declara el estado de sus apuntes (`completos`, `solo_resumen` o
 * `pendiente`) y de su práctica (`con_practica` o `pendiente`); el temario muestra ambos sellos y los
 * temas sin escribir dicen «Pendiente» en lugar de mostrar un párrafo vacío.
 */

import { useEffect, useRef, useState, type ReactElement } from 'react';
import { createRoot } from 'react-dom/client';

import demoData from './data.json';
import {
  clearResume,
  loadAttempts,
  loadErratas,
  loadProgress,
  saveErrata,
  saveAttempt,
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

interface ExamQuestion extends Question {
  readonly topic: string;
}

interface CaseEntry {
  readonly slug: string;
  readonly tema_path: string;
  readonly block: string;
  readonly title: string;
  readonly scenario: string;
  readonly source: DemoSource;
  readonly questions: readonly Question[];
}

interface Practice {
  readonly slug: string;
  readonly tema_path: string;
  readonly title: string;
  readonly source: DemoSource;
  readonly questions: readonly Question[];
  readonly kind?: 'practice' | 'case';
  readonly scenario?: string;
}

interface DemoTable {
  readonly columns: readonly string[];
  readonly rows: readonly (readonly string[])[];
}

interface DemoSection {
  readonly heading: string;
  readonly body?: string;
  readonly table?: DemoTable;
  readonly svg?: string;
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
  readonly reviewedAt: string;
  readonly longSections?: readonly DemoSection[];
  readonly memorizar: readonly string[];
  readonly errores: readonly string[];
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

interface ExamRule {
  readonly code: string;
  readonly name: string;
  readonly questions: number;
  readonly minutes: number;
  readonly penalty: number;
  readonly note: string;
}

interface DemoData {
  readonly title: string;
  readonly warning: string;
  readonly examRules: {
    readonly tai: ExamRule;
    readonly local: ExamRule;
  };
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
  readonly cases: readonly CaseEntry[];
  readonly progress: {
    readonly total: number;
    readonly apuntesCompletos: number;
    readonly soloResumen: number;
    readonly pendientes: number;
    readonly conPractica: number;
    readonly sinPractica: number;
    readonly questions: number;
    readonly cases: number;
    readonly caseQuestions: number;
    readonly convocatorias: number;
  };
}

const data = demoData as DemoData;
const TOPIC_LIST = data.curriculum.blocks.flatMap((block) => block.topics);
const TOPIC_BY_PATH = new Map(TOPIC_LIST.map((topic) => [topic.path, topic]));
const PRACTICE_BY_SLUG = new Map(data.practices.map((practice) => [practice.slug, practice]));
const CASE_BY_SLUG = new Map(data.cases.map((caso) => [caso.slug, caso]));

function blockForTopic(path: string): Block | undefined {
  return data.curriculum.blocks.find((block) =>
    block.topics.some((topic) => topic.path === path),
  );
}

function shuffle<T>(items: readonly T[]): T[] {
  const copy = [...items];
  for (let i = copy.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    const temporal = copy[i] as T;
    copy[i] = copy[j] as T;
    copy[j] = temporal;
  }
  return copy;
}

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
        <button className="button" type="button" onClick={() => { go('examen'); }}>
          Examen
        </button>
        <button className="button" type="button" onClick={() => { go('estadisticas'); }}>
          Estadísticas
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

type ExamPhase = 'setup' | 'running' | 'result';

function formatoTiempo(segundos: number): string {
  const minutos = Math.floor(segundos / 60);
  const resto = segundos % 60;
  return `${String(minutos).padStart(2, '0')}:${String(resto).padStart(2, '0')}`;
}

function penalizacionTexto(penalizacion: number): string {
  return Math.abs(penalizacion - 1 / 3) < 0.001 ? '1/3' : String(penalizacion);
}

function fechaCorta(iso: string): string {
  if (iso === '') {
    return '—';
  }
  return new Date(iso).toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

const BLOQUE_TODOS = 'TODOS';

function preguntasDelBloque(path: string): ExamQuestion[] {
  const practices =
    path === BLOQUE_TODOS
      ? data.practices
      : data.practices.filter((practice) => blockForTopic(practice.tema_path)?.path === path);
  return practices.flatMap((practice) =>
    practice.questions.map((question) => ({ ...question, topic: practice.tema_path })),
  );
}

function Examen({ initialBlock }: { readonly initialBlock?: string | undefined }) {
  const [block, setBlock] = useState(initialBlock ?? data.curriculum.blocks[0]?.path ?? 'I');
  const [convocatoria, setConvocatoria] = useState('tai');
  const [count, setCount] = useState(initialBlock === BLOQUE_TODOS ? 100 : 10);
  const [phase, setPhase] = useState<ExamPhase>('setup');
  const [questions, setQuestions] = useState<ExamQuestion[]>([]);
  const [index, setIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [selected, setSelected] = useState<string | null>(null);
  const [timeLeft, setTimeLeft] = useState(0);
  const saved = useRef(false);
  const rule = convocatoria === 'tai' ? data.examRules.tai : data.examRules.local;
  const convocatoriaName =
    convocatoria === 'tai'
      ? data.examRules.tai.name
      : data.convocatorias.items.find((item) => item.code === convocatoria)?.title ?? 'C1 local';
  const esCompleto = block === BLOQUE_TODOS;
  const pool = preguntasDelBloque(block);
  const disponibles = Math.min(count, pool.length);

  useEffect(() => {
    if (phase !== 'running') {
      return;
    }
    if (timeLeft <= 0) {
      const fin = window.setTimeout(() => { setPhase('result'); }, 0);
      return () => { window.clearTimeout(fin); };
    }
    const temporizador = window.setTimeout(() => {
      setTimeLeft((segundos) => segundos - 1);
    }, 1000);
    return () => { window.clearTimeout(temporizador); };
  }, [phase, timeLeft]);

  useEffect(() => {
    if (phase !== 'result' || saved.current) {
      return;
    }
    saved.current = true;
    const aciertos = questions.filter(
      (question, posicion) => answers[posicion] === question.correct,
    ).length;
    const fallos = questions.filter(
      (question, posicion) => answers[posicion] !== undefined && answers[posicion] !== question.correct,
    ).length;
    const neto = aciertos - fallos * rule.penalty;
    const porcentaje = questions.length === 0 ? 0 : Math.max(0, Math.round((neto / questions.length) * 100));
    saveAttempt({
      type: 'exam',
      block: esCompleto ? BLOQUE_TODOS : block,
      topic: block,
      label: esCompleto ? 'Examen completo' : `Examen ${block}`,
      correct: aciertos,
      total: questions.length,
      percent: porcentaje,
      timeSeconds: Math.max(1, rule.minutes * 60 - timeLeft),
      convocatoria: convocatoriaName,
    });
  }, [answers, block, convocatoriaName, esCompleto, phase, questions, rule.minutes, rule.penalty, timeLeft]);

  function empezar(): void {
    const elegidas = shuffle(pool).slice(0, disponibles);
    setQuestions(elegidas);
    setAnswers({});
    setIndex(0);
    setSelected(null);
    setTimeLeft(rule.minutes * 60);
    saved.current = false;
    setPhase('running');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  if (phase === 'running') {
    const question = questions[index];
    if (question === undefined) {
      return <p className="hint">Este bloque no tiene preguntas.</p>;
    }
    const esUltima = index + 1 === questions.length;
    return (
      <>
        <section className="page__header">
          <h1>{esCompleto ? 'Examen completo' : `Examen · Bloque ${block}`}</h1>
          <p className="page__lead">
            {convocatoriaName} · pregunta {index + 1} de {questions.length} · sin corrección hasta el final
          </p>
          <p className="demo-exam-clock" aria-live="polite">
            Tiempo restante: <strong>{formatoTiempo(timeLeft)}</strong> · error −{penalizacionTexto(rule.penalty)}
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
                    name="examen"
                    value={option.key}
                    checked={selected === option.key}
                    onChange={() => {
                      setSelected(option.key);
                      setAnswers((previous) => ({ ...previous, [index]: option.key }));
                    }}
                  />{' '}
                  <span className="demo-option__key">{option.key})</span> {option.text}
                </label>
              </li>
            ))}
          </ul>
          <p className="hint">Elige una opción. La explicación aparece al terminar el examen.</p>
          <div className="demo-actions">
            <button
              className="button"
              type="button"
              disabled={selected === null}
              onClick={() => {
                if (esUltima) {
                  setPhase('result');
                  return;
                }
                setIndex(index + 1);
                setSelected(answers[index + 1] ?? null);
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }}
            >
              {esUltima ? 'Ver resultado' : 'Siguiente pregunta'}
            </button>
            <button className="button button--link" type="button" onClick={() => { setPhase('setup'); }}>
              Abandonar
            </button>
          </div>
        </section>
      </>
    );
  }

  if (phase === 'result') {
    const aciertos = questions.filter(
      (question, posicion) => answers[posicion] === question.correct,
    ).length;
    const fallos = questions.filter(
      (question, posicion) => answers[posicion] !== undefined && answers[posicion] !== question.correct,
    ).length;
    const blancos = questions.length - aciertos - fallos;
    const neto = aciertos - fallos * rule.penalty;
    const nota = questions.length === 0 ? 0 : Math.max(0, Math.round((neto / questions.length) * 100));
    const fallosDetalle = questions
      .map((question, posicion) => ({ question, elegida: answers[posicion] }))
      .filter((item) => item.elegida !== undefined && item.elegida !== item.question.correct);
    return (
      <>
        <section className="page__header">
          <h1>{esCompleto ? 'Resultado del examen completo' : 'Resultado del examen'}</h1>
          <p className="page__lead">
            {esCompleto ? 'Todos los bloques' : `Bloque ${block}`} · {convocatoriaName} · {aciertos} aciertos · {fallos} fallos · {blancos} en blanco
          </p>
        </section>
        <section className="card">
          <h2>Nota: {nota} %</h2>
          <ul className="demo-result-stats">
            <li><span>Nota</span><strong>{nota} %</strong></li>
            <li><span>Tiempo</span><strong>{formatoTiempo(rule.minutes * 60 - timeLeft)}</strong></li>
            <li><span>Aciertos</span><strong>{aciertos}</strong></li>
            <li><span>Fallos</span><strong>{fallos}</strong></li>
            <li><span>En blanco</span><strong>{blancos}</strong></li>
          </ul>
          <p>
            Puntuación directa: <strong>{neto.toFixed(2)}</strong> sobre {questions.length}. Penalización
            aplicada: {fallos} × {penalizacionTexto(rule.penalty)}.
          </p>
          <p className="hint">
            Tiempo: {formatoTiempo(rule.minutes * 60 - timeLeft)} de {rule.minutes} minutos. La nota de
            corte de la demo es 50 %; la calificación oficial depende de los baremos de la convocatoria.
          </p>
          <div className="demo-actions">
            <button
              className="button"
              type="button"
              onClick={() => { document.getElementById('revision-fallos')?.scrollIntoView({ behavior: 'smooth' }); }}
            >
              Revisar mis errores
            </button>
            <button className="button button--link" type="button" onClick={empezar}>
              Repetir examen
            </button>
            <button className="button button--link" type="button" onClick={() => { setPhase('setup'); }}>
              Cambiar de bloque o convocatoria
            </button>
          </div>
        </section>
        <section className="card" id="revision-fallos">
          <h2>Revisión de fallos</h2>
          {fallosDetalle.length === 0 ? (
            <p>Sin fallos. Puedes subir el número de preguntas o cambiar de bloque.</p>
          ) : (
            <ol className="demo-fallos">
              {fallosDetalle.map(({ question, elegida }) => (
                <li key={question.stem}>
                  <p><strong>{question.stem}</strong></p>
                  <p className="hint">Tema {question.topic} · tu respuesta: {elegida ?? 'sin responder'} · correcta: {question.correct}</p>
                  <p>{question.explanation}</p>
                  {question.source !== undefined && <SourceLine source={question.source} official />}
                  <button className="button button--link" type="button" onClick={() => { go(`tema/${question.topic}`); }}>
                    Repasar tema {question.topic}
                  </button>
                </li>
              ))}
            </ol>
          )}
        </section>
      </>
    );
  }

  return (
    <>
      <section className="page__header">
        <h1>{esCompleto ? 'Examen completo' : 'Examen por bloque'} <span className="demo-status demo-status--apuntes-pendiente">Simulación</span></h1>
        <p className="page__lead">
          Formato de examen real: tiempo límite y penalización por fallo según la convocatoria. Sin
          corrección hasta el final. <strong>Simulación no oficial:</strong> no sustituye a la convocatoria.
          {esCompleto ? ' Mezcla preguntas de los cinco bloques.' : ''}
        </p>
      </section>
      <section className="card">
        <h2>Convocatoria y formato</h2>
        <label className="demo-search">
          <span>Convocatoria</span>
          <select value={convocatoria} onChange={(event) => { setConvocatoria(event.target.value); }}>
            <option value="tai">TAI AGE 2025 · formato oficial</option>
            {data.convocatorias.items.map((item) => (
              <option key={item.code} value={item.code}>{item.title}</option>
            ))}
          </select>
        </label>
        <p className="hint">
          {rule.name}: {rule.questions} preguntas · {rule.minutes} minutos · error −
          {penalizacionTexto(rule.penalty)} · blanco 0.
        </p>
        <p className="hint">{rule.note}</p>
      </section>
      <section className="card">
        <h2>Bloque y número de preguntas</h2>
        <div className="demo-filter-buttons">
          <button
            type="button"
            className={esCompleto ? 'button demo-filter--active' : 'button'}
            aria-pressed={esCompleto}
            onClick={() => { setBlock(BLOQUE_TODOS); setCount(100); }}
          >
            Todos · 40/40
          </button>
          {data.curriculum.blocks.map((item) => (
            <button
              key={item.path}
              type="button"
              className={block === item.path ? 'button demo-filter--active' : 'button'}
              aria-pressed={block === item.path}
              onClick={() => { setBlock(item.path); }}
            >
              {item.path} · {item.coverage.conApuntes}/{item.coverage.total}
            </button>
          ))}
        </div>
        <p className="hint">
          {esCompleto ? 'Todos los bloques' : `Bloque ${block}`}: {pool.length} preguntas disponibles.
          Entrarán {disponibles}.
        </p>
        <div className="demo-filter-buttons">
          {[10, 20, 100, 999].map((numero) => (
            <button
              key={numero}
              type="button"
              className={count === numero ? 'button demo-filter--active' : 'button'}
              onClick={() => { setCount(numero); }}
            >
              {numero === 999 ? 'Todas' : String(numero)}
            </button>
          ))}
        </div>
        <div className="demo-actions">
          <button className="button" type="button" onClick={empezar} disabled={pool.length === 0}>
            Empezar examen
          </button>
          <button className="button button--link" type="button" onClick={() => { go('estadisticas'); }}>
            Ver estadísticas
          </button>
        </div>
      </section>
    </>
  );
}

function Estadisticas() {
  const progress = loadProgress();
  const attempts = loadAttempts();
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
    .filter((item): item is NonNullable<typeof item> => item !== null);
  const porBloque = data.curriculum.blocks.map((block) => {
    const items = hechas.filter((item) => blockForTopic(item.practice.tema_path)?.path === block.path);
    const totalCorrect = items.reduce((sum, item) => sum + item.resultado.lastScore, 0);
    const totalPreguntas = items.reduce((sum, item) => sum + item.resultado.lastTotal, 0);
    const porcentaje = totalPreguntas === 0 ? 0 : Math.round((totalCorrect / totalPreguntas) * 100);
    return { block, items, porcentaje };
  });
  const flojos = [...hechas].sort((a, b) => a.porcentaje - b.porcentaje).slice(0, 5);

  return (
    <>
      <section className="page__header">
        <h1>Estadísticas</h1>
        <p className="page__lead">
          Acierto por tema y bloque en tus prácticas, y historial de intentos de práctica y examen.
        </p>
      </section>
      <section className="card">
        <h2>Estadísticas de prácticas</h2>
        {hechas.length === 0 ? (
          <>
            <p>Todavía no hay prácticas hechas. Empieza por una práctica corta o por un simulacro completo.</p>
            <div className="demo-actions">
              <button className="button" type="button" onClick={() => { go('practicas'); }}>
                Hacer práctica
              </button>
              <button className="button button--link" type="button" onClick={() => { go('examen'); }}>
                Empezar simulacro
              </button>
            </div>
          </>
        ) : (
          <>
            {porBloque.map(({ block, items, porcentaje }) => (
              <p key={block.path} className="demo-block-line">
                {block.path}: <strong>{porcentaje} %</strong> ({items.length} tema(s) practicado(s))
              </p>
            ))}
            <h3>Temas más flojos</h3>
            <ol className="demo-weak">
              {flojos.map(({ practice, porcentaje }) => (
                <li key={practice.slug}>
                  <strong>{practice.tema_path}</strong> · {porcentaje} % ·{' '}
                  <button className="button button--link" type="button" onClick={() => { go(`practica/${practice.slug}`); }}>
                    Practicar
                  </button>{' '}
                  <button className="button button--link" type="button" onClick={() => { go(`tema/${practice.tema_path}`); }}>
                    Repasar
                  </button>
                </li>
              ))}
            </ol>
            <h3>Acierto por tema</h3>
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr><th scope="col">Tema</th><th scope="col">Último</th><th scope="col">Mejor</th><th scope="col">Intentos</th></tr>
                </thead>
                <tbody>
                  {[...hechas].sort((a, b) => a.porcentaje - b.porcentaje).map(({ practice, resultado, porcentaje }) => (
                    <tr key={practice.slug}>
                      <td>{practice.tema_path}</td>
                      <td>{porcentaje} %</td>
                      <td>{resultado.best} %</td>
                      <td>{resultado.attempts}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </section>
      <section className="card">
        <h2>Historial de intentos</h2>
        <p className="hint">Prácticas y exámenes guardados en este navegador.</p>
        {attempts.length === 0 ? (
          <>
            <p>Todavía no hay intentos registrados.</p>
            <div className="demo-actions">
              <button className="button" type="button" onClick={() => { go('practicas'); }}>
                Hacer práctica
              </button>
              <button className="button button--link" type="button" onClick={() => { go('examen'); }}>
                Empezar simulacro
              </button>
            </div>
          </>
        ) : (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th scope="col">Tipo</th>
                  <th scope="col">Bloque</th>
                  <th scope="col">Detalle</th>
                  <th scope="col">Fecha</th>
                  <th scope="col">Aciertos</th>
                  <th scope="col">Tiempo</th>
                  <th scope="col">Nota</th>
                </tr>
              </thead>
              <tbody>
                {attempts.map((attempt) => (
                  <tr key={attempt.id}>
                    <td data-label="Tipo">{attempt.type === 'exam' ? 'Examen' : attempt.type === 'case' ? 'Caso' : 'Práctica'}</td>
                    <td data-label="Bloque">{attempt.block === 'TODOS' ? 'Todos' : attempt.block}</td>
                    <td data-label="Detalle">{attempt.convocatoria ?? attempt.topic}</td>
                    <td data-label="Fecha">{fechaCorta(attempt.date)}</td>
                    <td data-label="Aciertos">{attempt.correct} / {attempt.total}</td>
                    <td data-label="Tiempo">{attempt.timeSeconds === undefined ? '—' : formatoTiempo(attempt.timeSeconds)}</td>
                    <td data-label="Nota">{attempt.percent} %</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
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
  const [comentario, setComentario] = useState('');
  const [aviso, setAviso] = useState('');
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
    reviewedAt: '',
    memorizar: [],
    errores: [],
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
      {(topic.longSections ?? topic.sections).map((section) => (
        <section className="card" key={section.heading}>
          <h2>{section.heading}</h2>
          {section.body !== undefined && <RichText text={section.body} />}
          {section.svg !== undefined && (
            <div className="demo-diagram" dangerouslySetInnerHTML={{ __html: section.svg }} />
          )}
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
        <h2>Revisión y fuente</h2>
        <p className="hint">
          Última actualización: <strong>{topic.reviewedAt.split('-').reverse().join('/')}</strong>
        </p>
        <SourceLine source={topic.source} />
        <p className="hint">
          Contenido propio de la demo a partir de la norma citada; no reproduce texto de academias.
        </p>
      </section>
      <section className="card demo-errata">
        <h2>¿Has visto una errata?</h2>
        <label className="demo-search">
          <span>Describe la errata (tema, apartado, qué corregir)</span>
          <textarea
            rows={3}
            value={comentario}
            onChange={(event) => { setComentario(event.target.value); }}
            placeholder="Ej.: en el apartado 2, el artículo citado no es el 21 sino el 22…"
          />
        </label>
        <div className="demo-actions">
          <button
            className="button"
            type="button"
            disabled={comentario.trim() === ''}
            onClick={() => {
              saveErrata({
                topic: topic.path,
                title: topic.title,
                source: topic.source.label,
                reviewedAt: topic.reviewedAt,
                comment: comentario.trim(),
              });
              const blob = new Blob([JSON.stringify(loadErratas(), null, 2)], {
                type: 'application/json',
              });
              const url = URL.createObjectURL(blob);
              const enlace = document.createElement('a');
              enlace.href = url;
              enlace.download = `errata-${topic.path.replace('.', '-')}.json`;
              enlace.click();
              URL.revokeObjectURL(url);
              setComentario('');
              setAviso('Constancia guardada en este navegador y descargada como fichero JSON.');
            }}
          >
            Descargar constancia de errata
          </button>
        </div>
        {aviso !== '' && <p className="hint" role="status">{aviso}</p>}
        <p className="hint">
          La demo no tiene servidor: la constancia se guarda en el navegador y se descarga en un fichero
          para que puedas enviarla. No se publica nada automáticamente.
        </p>
      </section>
      <section className="card">
        <h2>Lo que hay que memorizar</h2>
        <ul className="demo-memorizar">
          {topic.memorizar.map((punto) => (
            <li key={punto}>{punto}</li>
          ))}
        </ul>
      </section>
      <section className="card">
        <h2>Errores típicos</h2>
        <ul className="demo-memorizar">
          {topic.errores.map((error) => (
            <li key={error}>{error}</li>
          ))}
        </ul>
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
            {data.cases.filter((caso) => caso.tema_path === topic.path).map((caso) => (
              <button
                key={caso.slug}
                className="button button--link"
                type="button"
                onClick={() => { go(`caso/${caso.slug}`); }}
              >
                Caso práctico
              </button>
            ))}
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
      <section className="card">
        <h2>Casos prácticos</h2>
        <p className="hint">
          {data.cases.length} casos con 10 preguntas cada uno, centrados en los temas con menos preguntas
          de los bloques II y III.
        </p>
        {data.cases.map((caso) => (
          <div key={caso.slug} className="demo-case">
            <h3>{caso.title}</h3>
            <p className="hint">Tema {caso.tema_path} · bloque {caso.block} · 10 preguntas</p>
            <p>{caso.scenario}</p>
            <button className="button" type="button" onClick={() => { go(`caso/${caso.slug}`); }}>
              Empezar caso
            </button>
          </div>
        ))}
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
  const startedAt = useRef(0);
  useEffect(() => {
    startedAt.current = Date.now();
  }, []);
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
          {practice.scenario !== undefined && <p className="hint">{practice.scenario}</p>}
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
    const porcentaje = score.total === 0 ? 0 : Math.round((score.correct / score.total) * 100);
    saveAttempt({
      type: practice.kind === 'case' ? 'case' : 'practice',
      block: blockForTopic(practice.tema_path)?.path ?? '—',
      topic: practice.tema_path,
      label: practice.kind === 'case' ? `Caso ${practice.title}` : `Práctica ${practice.tema_path}`,
      correct: score.correct,
      total: score.total,
      percent: porcentaje,
      timeSeconds: Math.max(1, Math.round((Date.now() - startedAt.current) / 1000)),
    });
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
        {practice.scenario !== undefined && <p className="hint">{practice.scenario}</p>}
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
  } else if (parts[0] === 'examen') {
    content = <Examen key={parts[1] ?? 'inicio'} initialBlock={parts[1]} />;
  } else if (parts[0] === 'estadisticas') {
    content = <Estadisticas />;
  } else if (parts[0] === 'cobertura') {
    content = <Cobertura />;
  } else if (parts[0] === 'tema' && parts[1] !== undefined) {
    content = <Tema path={parts[1]} />;
  } else if (parts[0] === 'practicas') {
    content = <Practicas />;
  } else if (parts[0] === 'caso' && parts[1] !== undefined) {
    const caso = CASE_BY_SLUG.get(parts[1]);
    content =
      caso === undefined ? (
        <p className="hint">Ese caso práctico no existe.</p>
      ) : (
        <PracticeRunner
          practice={{
            slug: caso.slug,
            tema_path: caso.tema_path,
            title: caso.title,
            source: caso.source,
            questions: caso.questions,
            kind: 'case',
            scenario: caso.scenario,
          }}
          key={caso.slug}
        />
      );
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
