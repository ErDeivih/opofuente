import { useState } from 'react';

import type { CurriculumNode } from '../../api/profiles';
import type { NodeMastery } from '../../api/reviews';
import { MASTERY_LABEL } from '../../api/reviews';
import { StatusBadge } from '../../components/StatusBadge';

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
            </button>
            {hasChildren && isExpanded && renderItems(node.children, false)}
          </li>
        );
      })}
    </ul>
  );

  return renderItems(nodes, true);
}
