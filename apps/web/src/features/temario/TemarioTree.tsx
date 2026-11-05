import { useState } from 'react';
import { Link } from 'react-router-dom';

import type { CurriculumNode } from '../../api/temario';
import { StatusBadge } from '../../components/StatusBadge';

export interface TemarioTreeProps {
  nodes: CurriculumNode[];
  /** Con una búsqueda activa los bloques se abren para enseñar lo que coincide. */
  searching: boolean;
}

const LEVEL_LABEL: Record<CurriculumNode['node_type'], string> = {
  block: 'bloque',
  topic: 'tema',
  epigraph: 'epígrafe',
};

/**
 * Árbol bloque → tema del temario común, en orden oficial.
 *
 * Los bloques son botones que pliegan y despliegan (`aria-expanded`); los temas son enlaces a su
 * ficha. No se anidan controles: cada elemento es **una** cosa interactiva, sin roles ARIA de árbol
 * que luego no se cumplan.
 */
export function TemarioTree({ nodes, searching }: TemarioTreeProps) {
  // Arranca todo desplegado: el temario se lee de arriba abajo y plegar es una decisión, no el
  // estado por defecto.
  const [collapsedIds, setCollapsedIds] = useState<string[]>([]);

  const toggle = (nodeId: string) => {
    setCollapsedIds((previous) =>
      previous.includes(nodeId)
        ? previous.filter((id) => id !== nodeId)
        : [...previous, nodeId],
    );
  };

  const renderNodes = (items: CurriculumNode[], isRoot: boolean) => (
    <ul className="tree" aria-label={isRoot ? 'Temario común' : undefined}>
      {items.map((node) => {
        const hasChildren = node.children.length > 0;
        const isExpanded = searching || !collapsedIds.includes(node.id);

        return (
          <li key={node.id} className="tree__item">
            {node.node_type === 'block' ? (
              <button
                type="button"
                className="tree__label"
                aria-expanded={isExpanded}
                onClick={() => {
                  toggle(node.id);
                }}
              >
                <span className="tree__caret" aria-hidden="true">
                  {isExpanded ? '▾' : '▸'}
                </span>
                <span className="tree__code">{node.official_code}</span>
                <span className="tree__title">{node.title}</span>
                <span className="tree__level">{LEVEL_LABEL[node.node_type]}</span>
              </button>
            ) : (
              <Link className="tree__label" to={`/temario/${node.id}`}>
                <span className="tree__code">{node.official_code}</span>
                <span className="tree__title">{node.title}</span>
                {node.studied_at !== null && node.studied_at !== undefined && (
                  <StatusBadge tone="ok">Estudiado</StatusBadge>
                )}
                <span className="tree__level">{LEVEL_LABEL[node.node_type]}</span>
              </Link>
            )}
            {hasChildren && isExpanded && renderNodes(node.children, false)}
          </li>
        );
      })}
    </ul>
  );

  return renderNodes(nodes, true);
}
