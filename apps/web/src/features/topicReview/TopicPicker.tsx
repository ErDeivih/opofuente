import { useEffect, useId, useRef } from 'react';

import type { TopicOption } from './programme';
import { groupByBlock, topicLabel } from './programme';

/**
 * Elegir el destino de una pregunta: su tema y, si lo tiene, su epígrafe.
 *
 * Los dos selectores son nativos a propósito. El propietario despacha la cola con el teclado, y un
 * `<select>` se abre, se recorre y se elige con las flechas y el Enter sin que la pantalla tenga que
 * inventar un widget: lo que hay que añadir es el atajo que **llega** hasta aquí, no otro teclado.
 *
 * El epígrafe no sustituye al tema: al aplicarlo se escriben los dos (el epígrafe dice dónde encaja
 * la pregunta y el tema mantiene los recuentos que ya existen). Por eso el segundo selector está
 * deshabilitado mientras no haya tema, y se puede dejar en «sin epígrafe».
 */
export function TopicPicker({
  topics,
  topicId,
  epigraphId,
  busy,
  onTopicChange,
  onEpigraphChange,
  onCancel,
  onApply,
}: {
  topics: readonly TopicOption[];
  topicId: string;
  epigraphId: string;
  busy: boolean;
  onTopicChange: (id: string) => void;
  onEpigraphChange: (id: string) => void;
  onCancel: () => void;
  onApply: () => void;
}) {
  const id = useId();
  const elegido = topics.find((tema) => tema.id === topicId) ?? null;
  const primero = useRef<HTMLSelectElement | null>(null);

  // El foco entra en el primer campo **cuando se abre el selector**, que es lo que el propietario
  // acaba de pedir con `C`. No es un `autoFocus` de los que roban el foco al cargar la pantalla:
  // este elemento no existe hasta que alguien lo pide.
  useEffect(() => {
    primero.current?.focus();
  }, []);

  return (
    <form
      className="form topic-picker"
      aria-label="Elegir el tema de esta pregunta"
      onSubmit={(event) => {
        event.preventDefault();
        onApply();
      }}
    >
      <div className="form__row">
        <label className="form__label" htmlFor={`${id}-tema`}>
          Tema
        </label>
        <select
          id={`${id}-tema`}
          ref={primero}
          className="selector__select"
          value={topicId}
          onChange={(event) => {
            onTopicChange(event.target.value);
          }}
        >
          <option value="">— elige un tema —</option>
          {groupByBlock(topics).map((grupo) => (
            <optgroup key={grupo.title} label={grupo.title}>
              {grupo.topics.map((tema) => (
                <option key={tema.id} value={tema.id}>
                  {topicLabel(tema)}
                </option>
              ))}
            </optgroup>
          ))}
        </select>
      </div>
      <div className="form__row">
        <label className="form__label" htmlFor={`${id}-epigrafe`}>
          Epígrafe
        </label>
        <select
          id={`${id}-epigrafe`}
          className="selector__select"
          value={epigraphId}
          disabled={elegido === null || elegido.epigraphs.length === 0}
          onChange={(event) => {
            onEpigraphChange(event.target.value);
          }}
        >
          <option value="">sin epígrafe</option>
          {(elegido?.epigraphs ?? []).map((epigrafe) => (
            <option key={epigrafe.id} value={epigrafe.id}>
              {epigrafe.path} · {epigrafe.title}
            </option>
          ))}
        </select>
        {elegido !== null && elegido.epigraphs.length === 0 && (
          <span className="hint">Este tema no tiene epígrafes: se asigna solo el tema.</span>
        )}
      </div>
      <div className="form__row">
        <button className="button" type="submit" disabled={busy || topicId === ''}>
          Aplicar el cambio
        </button>
        <button className="button button--link" type="button" onClick={onCancel}>
          Cancelar
        </button>
        <span className="hint">
          Al aplicar se retiran las demás propuestas de esta pregunta: una pregunta no puede quedar
          con dos temas.
        </span>
      </div>
    </form>
  );
}
