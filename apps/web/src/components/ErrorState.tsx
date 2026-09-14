export interface ErrorStateProps {
  title: string;
  message: string;
  onRetry?: () => void;
}

/** Un error siempre ofrece una acción (07_UI-UX §12) y nunca muestra una traza. */
export function ErrorState({ title, message, onRetry }: ErrorStateProps) {
  return (
    <div className="error-state" role="alert">
      <p className="error-state__title">{title}</p>
      <p className="error-state__message">{message}</p>
      {onRetry !== undefined && (
        <button type="button" className="button" onClick={onRetry}>
          Reintentar
        </button>
      )}
    </div>
  );
}
