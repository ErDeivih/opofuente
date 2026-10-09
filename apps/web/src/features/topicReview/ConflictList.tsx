import { useState } from 'react';

import type { ConflictCard } from '../../api/topicReview';
import { actorLabel } from '../../api/topicReview';
import { EmptyState } from '../../components/EmptyState';

/**
 * Las preguntas que cuentan en **dos temas** a la vez, para dejarlas con uno.
 *
 * Vienen de antes de esta tanda: la catalogación que heredaba el tema del documento, las
 * migraciones, y las dos corridas del clasificador que se pisaron. Una pregunta en dos temas suma
 * en los dos en todos los recuentos del alumno y en la cobertura, así que mientras exista, esas
 * cifras mienten.
 *
 * Dos decisiones que se ven en la pantalla:
 *
 * 1. **Cada tema va con quién lo escribió**, leído de la auditoría. Un tema heredado de una
 *    migración y uno propuesto por el modelo no se juzgan igual, y sin ese dato la elección sería a
 *    ciegas. Cuando no consta autor se dice, en lugar de inventarlo.
 * 2. **No se toca nada hasta que el propietario elige**: los temas son botones de opción (un grupo
 *    por pregunta) y solo el botón «Dejar este tema» escribe. Nada de arreglarlo en masa: esto es
 *    contenido.
 */
export function ConflictList({
  conflicts,
  busy,
  onKeep,
}: {
  conflicts: readonly ConflictCard[];
  busy: boolean;
  onKeep: (input: { questionVersionId: string; topicNodeId: string; topicPath: string }) => void;
}) {
  const [elegidos, setElegidos] = useState<Record<string, string>>({});

  if (conflicts.length === 0) {
    return (
      <EmptyState
        title="Ninguna pregunta cuenta en dos temas"
        description="Cada pregunta del banco está en un solo tema decidido: los recuentos por tema no se pisan."
      />
    );
  }

  return (
    <ul className="conflicts">
      {conflicts.map((conflicto) => (
        <li key={conflicto.question_version_id} className="conflict">
          <p className="conflict__question" data-contenido>
            {conflicto.stem}
          </p>
          <p className="hint">{conflicto.set_title}</p>
          {conflicto.options.length > 0 && (
            <ol className="topic-card__options" data-contenido>
              {conflicto.options.map((opcion) => (
                <li key={opcion.stable_key}>
                  <strong>{opcion.label ?? opcion.stable_key})</strong> {opcion.text}
                </li>
              ))}
            </ol>
          )}
          <fieldset className="conflict__topics">
            <legend>Cuál de los dos se queda</legend>
            {conflicto.topics.map((tema) => (
              <label key={tema.mapping_id} className="conflict__topic">
                <input
                  type="radio"
                  name={`tema-${conflicto.question_version_id}`}
                  value={tema.topic.node_id}
                  checked={elegidos[conflicto.question_version_id] === tema.topic.node_id}
                  onChange={() => {
                    setElegidos((previo) => ({
                      ...previo,
                      [conflicto.question_version_id]: tema.topic.node_id,
                    }));
                  }}
                />
                <span data-contenido>
                  <strong>{tema.topic.path}</strong> · {tema.topic.title}
                </span>
                <span className="hint">
                  {' '}
                  · {Math.round(tema.confidence * 100)} % · {actorLabel(tema.actor)}
                </span>
              </label>
            ))}
          </fieldset>
          <div className="form__row">
            <button
              className="button"
              type="button"
              disabled={busy || elegidos[conflicto.question_version_id] === undefined}
              onClick={() => {
                const elegido = conflicto.topics.find(
                  (tema) => tema.topic.node_id === elegidos[conflicto.question_version_id],
                );
                if (elegido === undefined) {
                  return;
                }
                onKeep({
                  questionVersionId: conflicto.question_version_id,
                  topicNodeId: elegido.topic.node_id,
                  topicPath: elegido.topic.path,
                });
              }}
            >
              Dejar este tema y retirar el otro
            </button>
            <span className="hint">
              El otro queda retirado (marcado, no borrado) con su evento de auditoría. Mientras no
              elijas, no se toca nada.
            </span>
          </div>
        </li>
      ))}
    </ul>
  );
}
