/**
 * El progreso de un tema y el mapa de preguntas de un test (F3 del rediseño).
 *
 * El progreso va **en el color de acento**, no en verde ni en rojo: esos dos están reservados a
 * acertar y fallar, y un 40 % de temario no es un error. El mapa usa además la forma —relleno, borde
 * discontinuo, contorno grueso— porque el color no puede ser la única señal.
 */

export interface ProgressBarProps {
  /** De 0 a 100. */
  percent: number;
  label?: string;
}

export function ProgressBar({ percent, label }: ProgressBarProps) {
  const valor = Math.max(0, Math.min(100, Math.round(percent)));
  return (
    <div>
      {/* El porcentaje va **escrito**: una barra sin número obliga a adivinar si es un 40 % o un 60 %,
          y en un temario de 33 temas eso importa (revisión de las capturas, 6 de octubre de 2026). */}
      <div className="ui-progress__head">
        {label !== undefined && <span className="ui-progress__label">{label}</span>}
        <span className="ui-progress__value">{valor} %</span>
      </div>
      <div
        className="ui-progress"
        role="progressbar"
        aria-valuenow={valor}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={label ?? 'Progreso'}
      >
        <div className="ui-progress__fill" style={{ width: `${String(valor)}%` }} />
      </div>
    </div>
  );
}

export type CellState = 'blank' | 'answered' | 'doubtful';

export interface QuestionGridProps {
  /** Una casilla por pregunta, en orden: la posición es el número que se enseña. */
  cells: readonly CellState[];
  /** La pregunta en la que se está (1..N), si hay alguna. */
  current?: number;
  onGo?: (position: number) => void;
}

export function QuestionGrid({ cells, current, onGo }: QuestionGridProps) {
  return (
    <div className="ui-grid" role="group" aria-label="Mapa de preguntas">
      {cells.map((estado, indice) => {
        const posicion = indice + 1;
        const clases = ['ui-grid__cell'];
        if (estado === 'answered') {
          clases.push('ui-grid__cell--answered');
        }
        if (estado === 'doubtful') {
          clases.push('ui-grid__cell--doubtful');
        }
        if (posicion === current) {
          clases.push('ui-grid__cell--current');
        }
        const estadoTexto =
          estado === 'answered' ? 'respondida' : estado === 'doubtful' ? 'dudosa' : 'en blanco';
        return (
          <button
            key={posicion}
            type="button"
            className={clases.join(' ')}
            aria-current={posicion === current ? 'true' : undefined}
            aria-label={`Pregunta ${String(posicion)}: ${estadoTexto}`}
            onClick={() => onGo?.(posicion)}
          >
            {posicion}
          </button>
        );
      })}
    </div>
  );
}
