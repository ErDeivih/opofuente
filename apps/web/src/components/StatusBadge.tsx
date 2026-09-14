import type { ReactNode } from 'react';

export type StatusTone = 'ok' | 'warning' | 'blocked' | 'info';

/** El estado nunca depende solo del color (07_UI-UX §1). */
const GLYPH: Record<StatusTone, string> = {
  ok: '✔',
  warning: '!',
  blocked: '×',
  info: '·',
};

export interface StatusBadgeProps {
  tone: StatusTone;
  children: ReactNode;
}

export function StatusBadge({ tone, children }: StatusBadgeProps) {
  return (
    <span className={`badge badge--${tone}`}>
      <span className="badge__glyph" aria-hidden="true">
        {GLYPH[tone]}
      </span>
      <span className="badge__text">{children}</span>
    </span>
  );
}
