import type { ButtonHTMLAttributes, ReactNode } from 'react';

export type ButtonVariant = 'primary' | 'secondary' | 'ghost';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  children: ReactNode;
}

/**
 * El botón de la aplicación (F3 del rediseño).
 *
 * Reglas que van en el componente y no en cada pantalla: 44 px de alto mínimo (se estudia también
 * desde el móvil), y **un solo botón principal por pantalla** —por eso el color de acento está
 * reservado a `primary`—.
 */
export function Button({ variant = 'secondary', children, ...rest }: ButtonProps) {
  return (
    <button className={`ui-button ui-button--${variant}`} {...rest}>
      {children}
    </button>
  );
}
