import type { ReactNode } from 'react';

/**
 * Las tres superficies de la aplicación (F3 del rediseño): la tarjeta, la cifra y el estado vacío.
 *
 * Van juntas porque son la misma idea —un trozo de pantalla con un borde y un aire— y porque el estado
 * vacío **siempre** lleva una acción: un hueco sin salida no ayuda a nadie.
 */

export interface CardProps {
  title?: string;
  children: ReactNode;
}

export function Card({ title, children }: CardProps) {
  return (
    <section className="ui-card">
      {title !== undefined && <h2 className="ui-card__title">{title}</h2>}
      {children}
    </section>
  );
}

export interface StatTileProps {
  label: string;
  value: ReactNode;
  hint?: string;
}

export function StatTile({ label, value, hint }: StatTileProps) {
  return (
    <div className="ui-stat">
      <span className="ui-stat__value">{value}</span>
      <span className="ui-stat__label">{label}</span>
      {hint !== undefined && <span className="hint">{hint}</span>}
    </div>
  );
}

export interface EmptyStateProps {
  message: string;
  action?: ReactNode;
}

export function EmptyState({ message, action }: EmptyStateProps) {
  return (
    <div className="ui-empty">
      <p>{message}</p>
      {action}
    </div>
  );
}
