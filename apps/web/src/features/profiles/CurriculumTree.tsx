import { useState } from 'react';

import type { CurriculumNode } from '../../api/profiles';
import type { NodeMastery } from '../../api/reviews';
import { MASTERY_LABEL } from '../../api/reviews';
import { StatusBadge } from '../../components/StatusBadge';
import { questionStatusLabel } from '../questions/labels';

export interface CurriculumTreeProps {
  nodes: CurriculumNode[];
  selectedId: string | null;
  onSelect: (node: CurriculumNode) => void;
  /** El dominio estimado por nodo (S10). Sin él, la columna no se enseña. */
  mastery?: Record<string, NodeMastery> | undefined;
}

const LEVEL_LABEL: Record<CurriculumNode['node_type'], string> = {
  block: 'bloque',
  topic: 'tema',
  epigraph: 'epígrafe',
};

/**
 * Árbol del programa: listas anidadas con botones que despliegan.
 *
 * No se usa `<details>`/`<summary>` con un botón dentro porque anidar controles interactivos es una
 * violación de accesibilidad real (axe `nested-interactive`). Aquí cada nodo es **un** botón que
 * selecciona el nodo y, si tiene hijos, los despliega, declarando `aria-expanded`. Sin roles ARIA
 * de árbol: no se declara una semántica que luego no se cumple.
 *
 * Cada fila lleva las columnas que pide 07_UI-UX §5 en forma de etiqueta: el dominio, las preguntas
 * que tiene el tema **por estado** (con las dudosas siempre visibles, que son las que piden algo) y
 * cuándo toca repasarlo. El desglose completo se lee al seleccionar el nodo.
 */
export function CurriculumTree({ nodes, selectedId, onSelect, mastery }: CurriculumTreeProps) {
  const [expandedIds, setExpandedIds] = useState<string[]>(() =>
    nodes.filter((node) => node.children.length > 0).map((node) => node.id),
  );

  const toggle = (nodeId: string) => {
    setExpandedIds((previous) =>
      previous.includes(nodeId) ? previous.filter((id) => id !== nodeId) : [...previous, nodeId],
    );
  };

  const renderItems = (items: CurriculumNode[], isRoot: boolean) => (
    <ul className="tree" aria-label={isRoot ? 'Programa oficial' : undefined}>
      {items.map((node) => {
        const hasChildren = node.children.length > 0;
        const isExpanded = expandedIds.includes(node.id);
        const isSelected = node.id === selectedId;
        const dominio = mastery?.[node.id];

        return (
          <li key={node.id} className="tree__item">
            <button
              type="button"
              className={isSelected ? 'tree__label tree__label--selected' : 'tree__label'}
              aria-current={isSelected ? 'true' : undefined}
              aria-expanded={hasChildren ? isExpanded : undefined}
              onClick={() => {
                onSelect(node);
                if (hasChildren) {
                  toggle(node.id);
                }
              }}
            >
              {hasChildren && (
                <span className="tree__caret" aria-hidden="true">
                  {isExpanded ? '▾' : '▸'}
                </span>
              )}
              <span className="tree__code">{node.official_code}</span>
              <span className="tree__title">{node.title}</span>
              <span className="tree__level">{LEVEL_LABEL[node.node_type]}</span>
              {dominio !== undefined && (
                <StatusBadge
                  tone={dominio.has_estimate ? 'ok' : 'info'}
                >{`dominio: ${MASTERY_LABEL[dominio.level]} (${String(dominio.recent_attempts)})`}</StatusBadge>
              )}
              {dominio !== undefined && (
                <>
                  <StatusBadge tone={dominio.study_state.questions_total === 0 ? 'info' : 'ok'}>
                    {dominio.study_state.questions_total === 0
                      ? 'sin preguntas asignadas'
                      : `preguntas: ${String(dominio.study_state.questions_total)}`}
                  </StatusBadge>
                  {dudosas(dominio).map((fila) => (
                    <StatusBadge key={fila.status} tone="blocked">
                      {`${questionStatusLabel(fila.status)}: ${String(fila.count)}`}
                    </StatusBadge>
                  ))}
                  <StatusBadge tone={dominio.study_state.reviews_due > 0 ? 'warning' : 'info'}>
                    {textoRepaso(dominio)}
                  </StatusBadge>
                </>
              )}
            </button>
            {hasChildren && isExpanded && renderItems(node.children, false)}
          </li>
        );
      })}
    </ul>
  );

  return renderItems(nodes, true);
}

/**
 * Las preguntas que piden algo: las `conflicting` y las `annulled` de 07_UI-UX §5 («dudosas»).
 *
 * Se enseñan siempre, aunque el tema tenga otras completas: un tema con doce preguntas y dos en
 * conflicto no está «bien», y esconder las dos detrás de un total sería el único dato que importa.
 */
function dudosas(dominio: NodeMastery): { status: string; count: number }[] {
  return dominio.study_state.questions_by_status.filter(
    (fila) => fila.status === 'conflicting' || fila.status === 'annulled',
  );
}

/**
 * La próxima revisión del tema: lo vencido primero, después la fecha programada y, si no hay nada,
 * se dice que no hay nada (no se deja la columna vacía, que se leería como «no se sabe»).
 */
function textoRepaso(dominio: NodeMastery): string {
  const { reviews_due: vencidos, next_review_at: proxima } = dominio.study_state;
  if (vencidos > 0) {
    return `repaso vencido: ${String(vencidos)}`;
  }
  if (proxima !== null && proxima !== undefined) {
    return `repaso: ${proxima.slice(0, 10)}`;
  }
  return 'sin repaso programado';
}
