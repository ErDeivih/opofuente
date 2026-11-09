import type { ReactNode } from 'react';

export interface EmptyStateProps {
  title: string;
  description: string;
  hint?: string;
  /** Acción concreta para salir del vacío. Si falta, el estado vacío solo explica. */
  action?: ReactNode;
}

/** Los estados vacíos enseñan el siguiente paso concreto (07_UI-UX §1). */
export function EmptyState({ title, description, hint, action }: EmptyStateProps) {
  return (
    <div className="empty">
      <p className="empty__title">{title}</p>
      <p className="empty__description">{description}</p>
      {hint !== undefined && <p className="empty__hint">{hint}</p>}
      {action !== undefined && <p className="empty__action">{action}</p>}
    </div>
  );
}
