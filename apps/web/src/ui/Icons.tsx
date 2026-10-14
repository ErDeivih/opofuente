import type { ReactNode } from 'react';

/**
 * Los iconos del carril de navegación (F13).
 *
 * Son SVG en línea y no una fuente de iconos ni un paquete: la CSP del proyecto no permite cargar
 * una fuente externa (`font-src 'self' data:`) y añadir una dependencia entera por siete dibujos no
 * tiene sentido. Todos comparten trazo (1.6), rejilla de 24 y `currentColor`, así que heredan el
 * color del enlace y se ven igual en todos los estados.
 *
 * Van marcados `aria-hidden`: el nombre de la sección lo pone el texto del enlace, y un icono que
 * también se anuncia hace que un lector de pantalla lea cada entrada dos veces.
 */

const TRAZO = {
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.6,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
} as const;

function Icon({ children }: { children: ReactNode }) {
  return (
    <svg
      className="nav-icono"
      viewBox="0 0 24 24"
      width="20"
      height="20"
      aria-hidden="true"
      focusable="false"
      {...TRAZO}
    >
      {children}
    </svg>
  );
}

export function IconInicio() {
  return (
    <Icon>
      <path d="M4 10.5 12 4l8 6.5V20a1 1 0 0 1-1 1h-4v-6H9v6H5a1 1 0 0 1-1-1z" />
    </Icon>
  );
}

export function IconTemario() {
  return (
    <Icon>
      <path d="M4 5.5A1.5 1.5 0 0 1 5.5 4H10a2 2 0 0 1 2 2v13a2 2 0 0 0-2-2H4z" />
      <path d="M20 5.5A1.5 1.5 0 0 0 18.5 4H14a2 2 0 0 0-2 2v13a2 2 0 0 1 2-2h6z" />
    </Icon>
  );
}

export function IconTests() {
  return (
    <Icon>
      <path d="M5 4h14v16H5z" />
      <path d="M8.5 9.5h7M8.5 13h7M8.5 16.5h4" />
    </Icon>
  );
}

export function IconSimulacros() {
  return (
    <Icon>
      <circle cx="12" cy="13" r="7.5" />
      <path d="M12 9.5V13l2.5 2M9.5 3h5" />
    </Icon>
  );
}

export function IconExamenes() {
  return (
    <Icon>
      <path d="M6 3.5h9L19 8v12.5H6z" />
      <path d="M14.5 3.5V8H19M9 12.5h6M9 16h4" />
    </Icon>
  );
}

export function IconFallos() {
  return (
    <Icon>
      <circle cx="12" cy="12" r="8" />
      <path d="M12 8v5M12 16h.01" />
    </Icon>
  );
}

export function IconProgreso() {
  return (
    <Icon>
      <path d="M4 19.5h16" />
      <path d="M7 19.5V12M12 19.5V6M17 19.5v-5" />
    </Icon>
  );
}
