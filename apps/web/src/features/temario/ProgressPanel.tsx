import { Link } from 'react-router-dom';

import type { Progress } from '../../api/temario';

export interface ProgressPanelProps {
  progress: Progress;
}

interface PendingBlock {
  readonly blockId: string;
  readonly path: string;
  readonly title: string;
  readonly position: number;
  readonly remaining: number;
  readonly total: number;
}

/**
 * Avance del temario: total, por bloque y qué queda por estudiar.
 *
 * Los porcentajes los calcula el servidor (`/curricula/{code}/progress`) y aquí solo se pintan:
 * la pantalla no repite la cuenta ni explica cómo se obtiene (DOCTRINA-CALIDAD §8).
 */
export function ProgressPanel({ progress }: ProgressPanelProps) {
  const pendientes: PendingBlock[] = progress.blocks
    .map((block) => ({
      blockId: block.block_id,
      path: block.path,
      title: block.title,
      position: block.position,
      remaining: block.topics_total - block.topics_studied,
      total: block.topics_total,
    }))
    .filter((block) => block.remaining > 0)
    .sort((left, right) => right.remaining - left.remaining || left.position - right.position);

  return (
    <section className="card" aria-labelledby="avance-temario">
      <h2 id="avance-temario">Avance</h2>

      <p className="progress__caption">
        {progress.topics_studied} de {progress.topics_total} temas estudiados
      </p>
      <div
        className="progress__track"
        role="progressbar"
        aria-label="Avance total"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(progress.percent)}
        aria-valuetext={`${String(progress.topics_studied)} de ${String(progress.topics_total)} temas`}
      >
        <div className="progress__fill" style={{ width: `${String(progress.percent)}%` }} />
      </div>

      <h3>Por bloque</h3>
      <ul className="progress-list">
        {progress.blocks.map((block) => (
          <li key={block.block_id} className="progress-list__item">
            <div className="progress-list__header">
              <span className="tree__code">{block.path}</span>
              <span className="progress-list__title">{block.title}</span>
              <span className="hint">
                {block.topics_studied} de {block.topics_total}
              </span>
              <Link
                className="progress-list__practice"
                to={`/temario/${encodeURIComponent(block.block_id)}/practicar`}
              >
                Practicar este bloque
              </Link>
            </div>
            <div
              className="progress__track progress__track--small"
              role="progressbar"
              aria-label={`Avance del bloque ${block.path}`}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={Math.round(block.percent)}
              aria-valuetext={`${String(block.topics_studied)} de ${String(block.topics_total)} temas`}
            >
              <div className="progress__fill" style={{ width: `${String(block.percent)}%` }} />
            </div>
          </li>
        ))}
      </ul>

      <h3>Qué queda</h3>
      {pendientes.length === 0 ? (
        <p className="hint">No queda ningún tema por estudiar.</p>
      ) : (
        <ul className="pending-list">
          {pendientes.map((block) => (
            <li key={block.blockId} className="pending-list__item">
              <span className="tree__code">{block.path}</span>
              <span className="pending-list__title">{block.title}</span>
              <span className="tag">
                {block.remaining} de {block.total} sin estudiar
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
