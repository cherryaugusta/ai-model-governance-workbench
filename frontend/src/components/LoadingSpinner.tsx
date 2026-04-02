type LoadingSpinnerProps = {
  label?: string;
};

export function LoadingSpinner({
  label = "Loading data...",
}: LoadingSpinnerProps) {
  return (
    <div className="panel">
      <div className="loading-row">
        <div className="spinner" aria-hidden="true" />
        <p>{label}</p>
      </div>
    </div>
  );
}
