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
  loadReadingPosition,
  saveReadingPosition,
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
  readonly pages?: string;
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

interface SupuestoQuestion {
  readonly stem: string;
  readonly options: readonly Option[];
  readonly correct: string;
  readonly justification: string;
}

interface Supuesto {
  readonly slug: string;
  readonly year: number;
  readonly conv: string;
  readonly block: string;
  readonly title: string;
  readonly difficulty: string;
  readonly official: boolean;
  readonly estimatedMinutes: number;
  readonly statement: string;
  readonly steps: readonly string[];
  readonly topics: readonly string[];
  readonly source: DemoSource;
  readonly questions: readonly SupuestoQuestion[];
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
  readonly formato?: 'esquema' | 'desarrollado';
  readonly longWords?: number;
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
  readonly supuestos: readonly Supuesto[];
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
    readonly supuestos: number;
    readonly supuestoQuestions: number;
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

function FormatoBadge({ formato, words }: { readonly formato?: 'esquema' | 'desarrollado'; readonly words?: number }) {
  if (formato === 'desarrollado') {
    return (
      <span className="demo-status demo-status--formato">
        Desarrollado · {words ?? 0} palabras
      </span>
    );
  }
  return <span className="demo-status demo-status--formato-esquema">Esquema · {words ?? 0} palabras</span>;
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
        <button className="button" type="button" onClick={() => { go('supuestos'); }}>
          Supuestos
        </button>
        <button className="button" type="button" onClick={() => { go('simulacro'); }}>
          Simulacro
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
                    <td data-label="Tipo">{attempt.type === 'exam' ? 'Examen' : attempt.type === 'case' ? 'Caso' : attempt.type === 'supuesto' ? 'Supuesto' : attempt.type === 'simulacro' ? 'Simulacro' : 'Práctica'}</td>
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

function Supuestos() {
  const [year, setYear] = useState<'todos' | number>('todos');
  const [block, setBlock] = useState<'todos' | 'III' | 'IV'>('todos');
  const years = [...new Set(data.supuestos.map((supuesto) => supuesto.year))].sort((a, b) => b - a);
  const filtrados = data.supuestos.filter(
    (supuesto) =>
      (year === 'todos' || supuesto.year === year) &&
      (block === 'todos' || supuesto.block === block),
  );
  return (
    <>
      <section className="page__header">
        <h1>Supuestos</h1>
        <p className="page__lead">
          Casos prácticos de los bloques III y IV con 20 preguntas y resolución razonada. Primero los
          oficiales del INAP, después los propios.
        </p>
      </section>
      <section className="card">
        <h2>Filtros</h2>
        <div className="demo-filter-buttons">
          <button className={year === 'todos' ? 'button demo-filter--active' : 'button'} type="button" onClick={() => { setYear('todos'); }}>
            Todos los años
          </button>
          {years.map((item) => (
            <button
              key={item}
              className={year === item ? 'button demo-filter--active' : 'button'}
              type="button"
              onClick={() => { setYear(item); }}
            >
              {item}
            </button>
          ))}
        </div>
        <div className="demo-filter-buttons">
          <button className={block === 'todos' ? 'button demo-filter--active' : 'button'} type="button" onClick={() => { setBlock('todos'); }}>
            Todos los bloques
          </button>
          <button className={block === 'III' ? 'button demo-filter--active' : 'button'} type="button" onClick={() => { setBlock('III'); }}>
            Bloque III
          </button>
          <button className={block === 'IV' ? 'button demo-filter--active' : 'button'} type="button" onClick={() => { setBlock('IV'); }}>
            Bloque IV
          </button>
        </div>
        <p className="hint">{filtrados.length} supuesto(s) · 20 preguntas cada uno · sin corrección hasta el final.</p>
      </section>
      {filtrados.length === 0 ? (
        <section className="card"><p>No hay supuestos con esos filtros.</p></section>
      ) : (
        filtrados.map((supuesto) => (
          <section className="card" key={supuesto.slug}>
            <h2>{supuesto.title}</h2>
            <p className="hint">
              {supuesto.year} · {supuesto.conv} · Bloque {supuesto.block} · Dificultad {supuesto.difficulty} ·{' '}
              {supuesto.estimatedMinutes} min · {supuesto.official ? 'Oficial INAP' : 'Propio'}
            </p>
            <p>{supuesto.statement.replace(/\*\*/g, '').slice(0, 240)}…</p>
            <p className="hint">Temas: {supuesto.topics.join(' · ')}</p>
            <div className="demo-actions">
              <button className="button" type="button" onClick={() => { go(`supuesto/${supuesto.slug}`); }}>
                Ver enunciado y resolución
              </button>
              <button className="button button--link" type="button" onClick={() => { go(`resolver-supuesto/${supuesto.slug}`); }}>
                Resolver como examen
              </button>
            </div>
          </section>
        ))
      )}
    </>
  );
}

function SupuestoDetalle({ slug }: { readonly slug: string }) {
  const supuesto = data.supuestos.find((item) => item.slug === slug);
  if (supuesto === undefined) {
    return <p className="hint">Ese supuesto no existe.</p>;
  }
  return (
    <>
      <section className="page__header">
        <p className="hint">
          <button className="button button--link" type="button" onClick={() => { go('supuestos'); }}>
            ← Volver a supuestos
          </button>
        </p>
        <h1>{supuesto.title}</h1>
        <p className="page__lead">
          {supuesto.year} · {supuesto.conv} · Bloque {supuesto.block} · {supuesto.difficulty} ·{' '}
          {supuesto.estimatedMinutes} min · {supuesto.official ? 'Oficial INAP' : 'Propio'}
        </p>
      </section>
      <section className="card">
        <h2>Enunciado</h2>
        <RichText text={supuesto.statement} />
        <p className="hint">Fuente: <a href={supuesto.source.url} target="_blank" rel="noreferrer">{supuesto.source.label}</a> · {supuesto.source.pages}</p>
      </section>
      <section className="card">
        <h2>Resolución paso a paso</h2>
        <ol>
          {supuesto.steps.map((paso) => <li key={paso}>{paso}</li>)}
        </ol>
      </section>
      <section className="card">
        <h2>Temas que toca</h2>
        <div className="demo-filter-buttons">
          {supuesto.topics.map((path) => (
            <button key={path} className="button button--link" type="button" onClick={() => { go(`tema/${path}`); }}>
              {path}
            </button>
          ))}
        </div>
        <div className="demo-actions">
          <button className="button" type="button" onClick={() => { go(`resolver-supuesto/${supuesto.slug}`); }}>
            Resolver como examen (20 preguntas)
          </button>
        </div>
        <p className="hint">Sin corrección hasta el final; al terminar verás la puntuación y la justificación de cada respuesta.</p>
      </section>
    </>
  );
}

function SupuestoRunner({ slug }: { readonly slug: string }) {
  const supuesto = data.supuestos.find((item) => item.slug === slug);
  const [index, setIndex] = useState(0);
  const [selected, setSelected] = useState<string | null>(null);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [finished, setFinished] = useState(false);
  if (supuesto === undefined) {
    return <p className="hint">Ese supuesto no existe.</p>;
  }
  const question = supuesto.questions[index];
  if (question === undefined) {
    return <p className="hint">Este supuesto no tiene preguntas.</p>;
  }
  if (finished) {
    const puntuables = supuesto.questions.filter((item) => item.correct !== 'ANULADA');
    const aciertos = puntuables.filter(
      (item) => answers[supuesto.questions.indexOf(item)] === item.correct,
    ).length;
    const nota = puntuables.length === 0 ? 0 : Math.round((aciertos / puntuables.length) * 100);
    return (
      <>
        <section className="page__header">
          <h1>Resultado del supuesto</h1>
          <p className="page__lead">
            {supuesto.title} · {aciertos} de {puntuables.length} puntuables · nota {nota} %
          </p>
        </section>
        <section className="card">
          <h2>Resolución paso a paso</h2>
          <ol>{supuesto.steps.map((paso) => <li key={paso}>{paso}</li>)}</ol>
          <div className="demo-actions">
            <button className="button" type="button" onClick={() => { setIndex(0); setAnswers({}); setSelected(null); setFinished(false); }}>
              Repetir supuesto
            </button>
            <button className="button button--link" type="button" onClick={() => { go('supuestos'); }}>
              Volver a supuestos
            </button>
          </div>
        </section>
        <section className="card">
          <h2>Revisión de las 20 preguntas</h2>
          <ol className="demo-fallos">
            {supuesto.questions.map((item, posicion) => {
              const elegida = answers[posicion];
              const anulada = item.correct === 'ANULADA';
              const correcta = elegida === item.correct;
              return (
                <li key={item.stem}>
                  <p><strong>{posicion + 1}. {item.stem}</strong></p>
                  <p className="hint">
                    Tu respuesta: {elegida ?? 'en blanco'} · {anulada ? 'ANULADA por el tribunal' : `correcta: ${item.correct}`}
                    {anulada ? '' : correcta ? ' · correcto' : ' · fallo'}
                  </p>
                  <p>{item.justification}</p>
                </li>
              );
            })}
          </ol>
        </section>
      </>
    );
  }
  const esUltima = index + 1 === supuesto.questions.length;
  return (
    <>
      <section className="page__header">
        <h1>{supuesto.title}</h1>
        <p className="page__lead">
          Pregunta {index + 1} de 20 · {supuesto.estimatedMinutes} min estimados · sin corrección hasta el final
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
                  name="supuesto"
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
        <div className="demo-actions">
          <button
            className="button"
            type="button"
            disabled={selected === null}
            onClick={() => {
              if (esUltima) {
                const puntuables = supuesto.questions.filter((item) => item.correct !== 'ANULADA');
                const aciertos = puntuables.filter(
                  (item) => answers[supuesto.questions.indexOf(item)] === item.correct,
                ).length;
                saveAttempt({
                  type: 'supuesto',
                  block: supuesto.block,
                  topic: supuesto.slug,
                  label: `Supuesto ${supuesto.title}`,
                  correct: aciertos,
                  total: puntuables.length,
                  percent: puntuables.length === 0 ? 0 : Math.round((aciertos / puntuables.length) * 100),
                });
                setFinished(true);
                return;
              }
              setIndex(index + 1);
              setSelected(answers[index + 1] ?? null);
              window.scrollTo({ top: 0, behavior: 'smooth' });
            }}
          >
            {esUltima ? 'Terminar y ver resultado' : 'Siguiente pregunta'}
          </button>
          <button className="button button--link" type="button" onClick={() => { go(`supuesto/${supuesto.slug}`); }}>
            Abandonar
          </button>
        </div>
      </section>
    </>
  );
}

function Simulacro() {
  const [phase, setPhase] = useState<'setup' | 'running' | 'result'>('setup');
  const [questions, setQuestions] = useState<ExamQuestion[]>([]);
  const [index, setIndex] = useState(0);
  const [selected, setSelected] = useState<string | null>(null);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [timeLeft, setTimeLeft] = useState(120 * 60);
  const saved = useRef(false);

  useEffect(() => {
    if (phase !== 'running') {
      return;
    }
    if (timeLeft <= 0) {
      const fin = window.setTimeout(() => { setPhase('result'); }, 0);
      return () => { window.clearTimeout(fin); };
    }
    const temporizador = window.setTimeout(() => { setTimeLeft((segundos) => segundos - 1); }, 1000);
    return () => { window.clearTimeout(temporizador); };
  }, [phase, timeLeft]);

  useEffect(() => {
    if (phase !== 'result' || saved.current) {
      return;
    }
    saved.current = true;
    const parte1 = questions.slice(0, 80);
    const parte2 = questions.slice(80);
    const aciertos = questions.filter((item, posicion) => answers[posicion] === item.correct).length;
    saveAttempt({
      type: 'simulacro',
      block: 'TAI',
      topic: 'simulacro',
      label: 'Simulacro TAI 80+20',
      correct: aciertos,
      total: questions.length,
      percent: questions.length === 0 ? 0 : Math.round((aciertos / questions.length) * 100),
    });
    void parte1;
    void parte2;
  }, [answers, phase, questions]);

  function empezar(): void {
    const todos = data.practices.flatMap((practice) =>
      practice.questions.map((question) => ({ ...question, topic: practice.tema_path })),
    );
    const barajadas = shuffle(todos);
    const primera = barajadas.slice(0, 80);
    const usadas = new Set(primera.map((item) => item.stem));
    const segunda = shuffle(
      todos.filter(
        (question) =>
          !usadas.has(question.stem) &&
          ['III', 'IV'].includes(blockForTopic(question.topic)?.path ?? ''),
      ),
    ).slice(0, 20);
    setQuestions([...primera, ...segunda]);
    setAnswers({});
    setIndex(0);
    setSelected(null);
    setTimeLeft(120 * 60);
    saved.current = false;
    setPhase('running');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  if (phase === 'running') {
    const question = questions[index];
    if (question === undefined) {
      return <p className="hint">El simulacro no tiene preguntas.</p>;
    }
    return (
      <>
        <section className="page__header">
          <h1>Simulacro TAI</h1>
          <p className="page__lead">
            {index < 80 ? 'Parte 1 · cuestionario' : 'Parte 2 · supuesto'} · pregunta {index + 1} de 100
          </p>
          <p className="demo-exam-clock" aria-live="polite">
            Tiempo restante: <strong>{formatoTiempo(timeLeft)}</strong> · error −1/3 · mínimo 25/50 por parte
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
                    name="simulacro"
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
          <p className="hint">Sin corrección hasta el final. Puedes abandonar y volver a empezar.</p>
          <div className="demo-actions">
            <button
              className="button"
              type="button"
              disabled={selected === null}
              onClick={() => {
                if (index + 1 === questions.length) {
                  setPhase('result');
                  return;
                }
                setIndex(index + 1);
                setSelected(answers[index + 1] ?? null);
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }}
            >
              {index + 1 === questions.length ? 'Terminar y ver nota' : 'Siguiente pregunta'}
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
    const partes = [questions.slice(0, 80), questions.slice(80)];
    const notas = partes.map((parte, posicion) => {
      const inicio = posicion === 0 ? 0 : 80;
      const aciertos = parte.filter((item, i) => answers[inicio + i] === item.correct).length;
      const fallos = parte.filter((item, i) => {
        const respuesta = answers[inicio + i];
        return respuesta !== undefined && respuesta !== item.correct;
      }).length;
      const bruto = aciertos - fallos / 3;
      return {
        aciertos,
        fallos,
        nota: Math.max(0, Number(((bruto / parte.length) * 50).toFixed(2))),
      };
    });
    const n1 = notas[0] ?? { aciertos: 0, fallos: 0, nota: 0 };
    const n2 = notas[1] ?? { aciertos: 0, fallos: 0, nota: 0 };
    const apto = notas.every((parte) => parte.nota >= 25);
    return (
      <>
        <section className="page__header">
          <h1>Resultado del simulacro TAI</h1>
          <p className="page__lead">
            {apto ? 'Apto' : 'No apto'} · Parte 1: {n1.nota}/50 · Parte 2: {n2.nota}/50
          </p>
        </section>
        <section className="card">
          <h2>Nota con penalización</h2>
          <ul className="demo-result-stats">
            <li><span>Parte 1</span><strong>{n1.nota}/50</strong></li>
            <li><span>Parte 2</span><strong>{n2.nota}/50</strong></li>
            <li><span>Aciertos</span><strong>{n1.aciertos + n2.aciertos}</strong></li>
            <li><span>Fallos</span><strong>{n1.fallos + n2.fallos}</strong></li>
          </ul>
          <p className="hint">
            Regla: 80 + 20 preguntas, 120 minutos, cada error resta 1/3; mínimo 25/50 en cada parte.
            Tiempo: {formatoTiempo(120 * 60 - timeLeft)}.
          </p>
          <div className="demo-actions">
            <button className="button" type="button" onClick={empezar}>Repetir simulacro</button>
            <button className="button button--link" type="button" onClick={() => { setPhase('setup'); }}>
              Volver a las reglas
            </button>
          </div>
        </section>
      </>
    );
  }

  return (
    <>
      <section className="page__header">
        <h1>Simulacro TAI <span className="demo-status demo-status--apuntes-pendiente">Simulación</span></h1>
        <p className="page__lead">
          80 preguntas de cuestionario + 20 de supuesto, 120 minutos, penalización −1/3 y mínimo 25/50 en
          cada parte.
        </p>
      </section>
      <section className="card">
        <h2>Reglas del simulacro</h2>
        <ul className="demo-memorizar">
          <li><strong>Parte 1:</strong> 80 preguntas de todos los bloques. Máximo 50 puntos; mínimo 25.</li>
          <li><strong>Parte 2:</strong> 20 preguntas de los bloques III y IV. Máximo 50 puntos; mínimo 25.</li>
          <li><strong>Tiempo:</strong> 120 minutos para las dos partes.</li>
          <li><strong>Penalización:</strong> cada error resta 1/3 de una correcta; en blanco no resta.</li>
          <li><strong>Sin corrección</strong> hasta el final.</li>
        </ul>
        <div className="demo-actions">
          <button className="button" type="button" onClick={empezar}>Empezar simulacro TAI</button>
        </div>
        <p className="hint">Es una simulación de la demo, no un examen oficial.</p>
      </section>
    </>
  );
}

function Cobertura() {
  const todos = data.curriculum.blocks.flatMap((block) => block.topics);
  const completos = todos.filter((topic) => topic.formato === 'desarrollado').length;
  const parciales = todos.filter((topic) => topic.formato !== 'desarrollado' && topic.apuntesStatus !== 'pendiente').length;
  const ausentes = todos.filter((topic) => topic.apuntesStatus === 'pendiente').length;
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
      <section className="card">
        <h2>Cobertura por epígrafe</h2>
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr><th scope="col">Estado</th><th scope="col">Temas</th><th scope="col">Criterio</th></tr>
            </thead>
            <tbody>
              <tr><td><strong>Completo</strong></td><td>{completos}</td><td>10 apartados + 15 test</td></tr>
              <tr><td><strong>Parcial</strong></td><td>{parciales}</td><td>Ficha corta + práctica</td></tr>
              <tr><td><strong>Ausente</strong></td><td>{ausentes}</td><td>Sin desarrollo</td></tr>
              <tr><td><strong>Total</strong></td><td>{todos.length}</td><td>40 temas del temario común</td></tr>
            </tbody>
          </table>
        </div>
      </section>
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
                  <th scope="col">Formato</th>
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
                    <td>
                      <FormatoBadge formato={topic.formato ?? 'esquema'} words={topic.longWords ?? 0} />
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
        <div className="demo-actions">
          <button className="button" type="button" onClick={() => { go('cobertura'); }}>
            Ver cobertura de los 40
          </button>
        </div>
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
                    <FormatoBadge formato={topic.formato ?? 'esquema'} words={topic.longWords ?? 0} />
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

function TopicIndexBar({
  sections,
  active,
  onActive,
}: {
  readonly sections: readonly DemoSection[];
  readonly active: number;
  readonly onActive: (index: number) => void;
}) {
  const [open, setOpen] = useState(false);
  useEffect(() => {
    const onScroll = () => {
      const nodes = Array.from(document.querySelectorAll('.demo-seccion'));
      let current = 0;
      for (let i = 0; i < nodes.length; i += 1) {
        const top = nodes[i]?.getBoundingClientRect().top ?? Number.POSITIVE_INFINITY;
        if (top <= 140) {
          current = i;
        }
      }
      onActive(current);
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    const frame = window.requestAnimationFrame(onScroll);
    return () => {
      window.cancelAnimationFrame(frame);
      window.removeEventListener('scroll', onScroll);
    };
  }, [onActive, sections.length]);
  const actual = sections[active]?.heading ?? '';
  return (
    <div className="demo-indexbar">
      <button
        className="demo-indexbar__toggle"
        type="button"
        aria-expanded={open}
        onClick={() => { setOpen((value) => !value); }}
      >
        <strong>Índice ▾</strong> <span>· {actual}</span>
      </button>
      {open && (
        <nav className="demo-indexbar__menu" aria-label="Índice del tema">
          {sections.map((section, index) => (
            <button
              key={section.heading}
              type="button"
              className={index === active ? 'demo-indexbar__item demo-indexbar__item--active' : 'demo-indexbar__item'}
              onClick={() => {
                setOpen(false);
                document.getElementById(`demo-seccion-${index}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
              }}
            >
              {section.heading}
            </button>
          ))}
        </nav>
      )}
    </div>
  );
}

function Tema({ path }: { path: string }) {
  const [comentario, setComentario] = useState('');
  const [aviso, setAviso] = useState('');
  const [active, setActive] = useState(0);
  const [resume] = useState(() => loadReadingPosition(path));
  const summary = TOPIC_BY_PATH.get(path);
  const topic: TopicContent = data.topics[path] ?? {
    path,
    title: summary?.title ?? path,
    apuntesStatus: 'pendiente',
    practicaStatus: 'pendiente',
    source: { label: '', url: '' },
    sections: [],
    reviewedAt: '',
    memorizar: [],
    errores: [],
  };
  const secciones = topic.longSections ?? topic.sections;
  const tieneResumen = secciones.some((section) => /resumen/i.test(section.heading));
  const tieneFuentes = secciones.some((section) => /fuentes/i.test(section.heading));
  const testIndex = secciones.findIndex((section) => /test|casos tipo/i.test(section.heading));
  useEffect(() => {
    if (secciones[active] !== undefined) {
      saveReadingPosition(path, active, secciones[active].heading);
    }
  }, [active, path, secciones]);
  if (summary === undefined) {
    return <p className="hint">Ese tema no existe en la demo.</p>;
  }
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
          <PracticaBadge status={topic.practicaStatus} />{' '}
          <FormatoBadge formato={topic.longSections !== undefined ? 'desarrollado' : 'esquema'} words={secciones.reduce((total, section) => total + (section.body ?? '').split(/\s+/).length, 0)} />{' '}
          <span className="demo-status demo-status--revisado">Revisado 11/2026</span>
        </p>
        <p className="hint demo-vigencia">Vigente a 11/2026</p>
        {testIndex >= 0 && (
          <button className="button button--link" type="button" onClick={() => { document.getElementById(`demo-seccion-${testIndex}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' }); setActive(testIndex); }}>
            Test del tema
          </button>
        )}
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
      <TopicIndexBar sections={secciones} active={active} onActive={setActive} />
      {resume !== null && resume.index > 0 && (
        <div className="demo-read-resume">
          <p>Continuar en <strong>{resume.heading}</strong></p>
          <button className="button" type="button" onClick={() => { document.getElementById(`demo-seccion-${resume.index}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' }); setActive(resume.index); }}>Continuar leyendo</button>
        </div>
      )}
      {secciones.map((section, sectionIndex) => (
        <section className="card demo-seccion" id={`demo-seccion-${sectionIndex}`} key={section.heading}>
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
      {!tieneFuentes && (
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
      )}
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
      {!tieneResumen && (
      <section className="card">
        <h2>Lo que hay que memorizar</h2>
        <ul className="demo-memorizar">
          {topic.memorizar.map((punto) => (
            <li key={punto}>{punto}</li>
          ))}
        </ul>
      </section>
      )}
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
    content = <Tema path={parts[1]} key={parts[1]} />;
  } else if (parts[0] === 'practicas') {
    content = <Practicas />;
  } else if (parts[0] === 'simulacro') {
    content = <Simulacro />;
  } else if (parts[0] === 'supuestos') {
    content = <Supuestos />;
  } else if (parts[0] === 'supuesto' && parts[1] !== undefined) {
    content = <SupuestoDetalle slug={parts[1]} />;
  } else if (parts[0] === 'resolver-supuesto' && parts[1] !== undefined) {
    content = <SupuestoRunner slug={parts[1]} />;
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
