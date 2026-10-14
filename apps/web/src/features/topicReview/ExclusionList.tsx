import { useId, useState } from 'react';

import type { Exclusion } from '../../api/topicReview';
import { EXCLUSION_LABELS } from '../../api/topicReview';
import { EmptyState } from '../../components/EmptyState';
import type { TopicOption } from './programme';
import { groupByBlock, topicLabel } from './programme';

/**
 * Las preguntas que se declararon **fuera de temario**, con su motivo y quién lo decidió.
 *
 * Se pueden deshacer, y deshacerlas es asignarles un tema: la marca se levanta sola (una pregunta no
 * puede ser de un tema y no ser del temario a la vez), así que aquí no hay un «botón de borrar» que
 * dejara dos verdades enfrentadas. El motivo se enseña con el texto del modelo porque es lo que
 * permite juzgar si la marca estaba bien puesta.
 *
 * El destino se elige con un `<select>` nativo: se llega con el tabulador y se resuelve con las
 * flechas y el Enter, sin ratón, sin que la pantalla tenga que inventar otro cursor.
 */
export function ExclusionList({
  exclusions,
  topics,
  busy,
  onAssign,
}: {
  exclusions: readonly Exclusion[];
  topics: readonly TopicOption[];
  busy: boolean;
  onAssign: (input: { questionVersionId: string; topicId: string; epigraphId: string }) => void;
}) {
  const id = useId();
  const [elegidos, setElegidos] = useState<Record<string, { topicId: string; epigraphId: string }>>(
    {},
  );

  if (exclusions.length === 0) {
    return (
      <EmptyState
        title="Ninguna pregunta fuera de temario"
        description="Aquí aparecerán las que se declaren fuera del programa, con el motivo por el que se decidió."
      />
    );
  }

  return (
    <table className="table">
      <caption className="table__caption">
        Preguntas fuera de temario, de la más nueva a la más antigua. Asignarles un tema levanta la
        marca.
      </caption>
      <thead>
        <tr>
          <th scope="col">Pregunta</th>
          <th scope="col">Motivo</th>
          <th scope="col">Decidido por</th>
          <th scope="col">Devolverla al temario</th>
        </tr>
      </thead>
      <tbody>
        {exclusions.map((marca, indice) => {
          const elegido = elegidos[marca.question_version_id] ?? { topicId: '', epigraphId: '' };
          const tema = topics.find((item) => item.id === elegido.topicId) ?? null;
          return (
            <tr key={marca.question_version_id}>
              <td data-contenido>
                {marca.stem ?? 'Enunciado no disponible'}
                {marca.note !== null && marca.note !== undefined && (
                  <span className="hint"> · {marca.note}</span>
                )}
              </td>
              <td>{EXCLUSION_LABELS[marca.reason]}</td>
              <td>
                {marca.actor}
                {marca.created_at !== null && marca.created_at !== undefined && (
                  <span className="hint"> · {marca.created_at.slice(0, 10)}</span>
                )}
              </td>
              <td>
                <label className="form__label" htmlFor={`${id}-${String(indice)}-tema`}>
                  Tema
                </label>
                <select
                  id={`${id}-${String(indice)}-tema`}
                  className="selector__select"
                  value={elegido.topicId}
                  onChange={(event) => {
                    setElegidos((previo) => ({
                      ...previo,
                      [marca.question_version_id]: { topicId: event.target.value, epigraphId: '' },
                    }));
                  }}
                >
                  <option value="">— elige un tema —</option>
                  {groupByBlock(topics).map((grupo) => (
                    <optgroup key={grupo.title} label={grupo.title}>
                      {grupo.topics.map((item) => (
                        <option key={item.id} value={item.id}>
                          {topicLabel(item)}
                        </option>
                      ))}
                    </optgroup>
                  ))}
                </select>
                {tema !== null && tema.epigraphs.length > 0 && (
                  <>
                    <label
                      className="form__label"
                      htmlFor={`${id}-${String(indice)}-epigrafe`}
                    >
                      Epígrafe
                    </label>
                    <select
                      id={`${id}-${String(indice)}-epigrafe`}
                      className="selector__select"
                      value={elegido.epigraphId}
                      onChange={(event) => {
                        setElegidos((previo) => ({
                          ...previo,
                          [marca.question_version_id]: {
                            topicId: elegido.topicId,
                            epigraphId: event.target.value,
                          },
                        }));
                      }}
                    >
                      <option value="">sin epígrafe</option>
                      {tema.epigraphs.map((epigrafe) => (
                        <option key={epigrafe.id} value={epigrafe.id}>
                          {epigrafe.path} · {epigrafe.title}
                        </option>
                      ))}
                    </select>
                  </>
                )}
                <button
                  className="button"
                  type="button"
                  disabled={busy || elegido.topicId === ''}
                  onClick={() => {
                    onAssign({
                      questionVersionId: marca.question_version_id,
                      topicId: elegido.topicId,
                      epigraphId: elegido.epigraphId,
                    });
                  }}
                >
                  Asignar y levantar la marca
                </button>
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
