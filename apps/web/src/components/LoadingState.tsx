export interface LoadingStateProps {
  label: string;
}

export function LoadingState({ label }: LoadingStateProps) {
  return (
    <p className="loading" role="status">
      {label}
    </p>
  );
}
