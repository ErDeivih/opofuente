export interface EmptyStateProps {
  title: string;
  description: string;
  hint?: string;
}

/** Los estados vacíos enseñan el siguiente paso concreto (07_UI-UX §1). */
export function EmptyState({ title, description, hint }: EmptyStateProps) {
  return (
    <div className="empty">
      <p className="empty__title">{title}</p>
      <p className="empty__description">{description}</p>
      {hint !== undefined && <p className="empty__hint">{hint}</p>}
    </div>
  );
}
