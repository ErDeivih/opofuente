import type { Evidence, Section, Version } from '../../api/library';
import { CopyCitationButton } from './CopyCitationButton';
import { pageLabel } from './labels';

export interface StructureTabProps {
  documentTitle: string;
  version: Version | null;
  sections: Section[];
  evidence: Evidence[];
  isPending: boolean;
}

interface SectionNode {
  section: Section;
  children: SectionNode[];
}

/**
 * Monta el árbol por `parent_id`.
 *
 * El servidor no promete que los hijos lleguen juntos ni en orden de profundidad: se reconstruye
 * por parentesco y se ordena por `position`, que es lo que sí declara el contrato. Una sección
 * cuyo padre no está en la lista no se pierde: se muestra como raíz, porque esconderla sería
 * mentir por omisión sobre lo que el documento tiene.
 */
function buildTree(sections: Section[]): SectionNode[] {
  const nodes = new Map<string, SectionNode>(
    sections.map((section) => [section.id, { section, children: [] }]),
  );
  const roots: SectionNode[] = [];
  for (const section of sections) {
    const node = nodes.get(section.id);
    if (node === undefined) {
      continue;
    }
    const parentId = section.parent_id;
    const parent = parentId === null || parentId === undefined ? undefined : nodes.get(parentId);
    if (parent !== undefined && parent !== node) {
      parent.children.push(node);
    } else {
      roots.push(node);
    }
  }
  const sort = (items: SectionNode[]) => {
    items.sort((left, right) => left.section.position - right.section.position);
    for (const item of items) {
      sort(item.children);
    }
  };
  sort(roots);
  return roots;
}

function SectionBranch({
  nodes,
  documentTitle,
  version,
  depth,
}: {
  nodes: SectionNode[];
  documentTitle: string;
  version: Version;
  depth: number;
}) {
  return (
    <ul className={depth === 0 ? 'tree' : 'tree tree--nested'}>
      {nodes.map((node) => (
        <li key={node.section.id} className="tree__item">
          <div>
            <span className="tree__code">{node.section.ordinal}</span>{' '}
            <span className="tree__title">
              {node.section.title ?? node.section.label ?? 'sección sin título'}
            </span>{' '}
            <span className="hint">
              {pageLabel(node.section.page_start, node.section.page_end)} · tipo{' '}
              {node.section.section_type} · caracteres {node.section.char_start}-
              {node.section.char_end}
            </span>
            <div>
              <CopyCitationButton
                title={documentTitle}
                version={version}
                place={pageLabel(node.section.page_start, node.section.page_end)}
                label={`${documentTitle}, sección ${
                  node.section.title ?? node.section.label ?? node.section.ordinal
                }`}
              />
            </div>
          </div>
          {node.children.length > 0 && (
            <SectionBranch
              nodes={node.children}
              documentTitle={documentTitle}
              version={version}
              depth={depth + 1}
            />
          )}
        </li>
      ))}
    </ul>
  );
}

/**
 * Estructura de la versión (07_UI-UX §6): el árbol de secciones con su página.
 *
 * La estructura la extrajo el servidor; aquí solo se muestra y se ordena. Sin páginas —un texto sin
 * paginación— se dice «sin página» en lugar de inventar una numeración.
 */
export function StructureTab({
  documentTitle,
  version,
  sections,
  evidence,
  isPending,
}: StructureTabProps) {
  if (version === null) {
    return (
      <p className="hint">
        Este documento no tiene ninguna versión, así que no hay estructura que mostrar.
      </p>
    );
  }

  if (isPending) {
    return (
      <p className="loading" role="status">
        Cargando la estructura…
      </p>
    );
  }

  if (sections.length === 0) {
    return (
      <p className="hint">
        La extracción no dejó secciones en esta versión: el documento se puede leer y citar por su
        evidencia, pero no tiene árbol de estructura.
      </p>
    );
  }

  const sinEvidencia = sections.filter(
    (section) => !evidence.some((item) => item.section_id === section.id),
  ).length;

  return (
    <>
      <p className="hint">
        {sections.length} secciones extraídas de la versión «{version.version_label ?? version.id}».
        El orden y la jerarquía son los que declaró la extracción.
      </p>
      <SectionBranch
        nodes={buildTree(sections)}
        documentTitle={documentTitle}
        version={version}
        depth={0}
      />
      {sinEvidencia > 0 && (
        <p className="hint">
          {sinEvidencia} secciones no tienen evidencia citable guardada: se ve su estructura y su
          página, pero no hay fragmento que citar.
        </p>
      )}
    </>
  );
}
