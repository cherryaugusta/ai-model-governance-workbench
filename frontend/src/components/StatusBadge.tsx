import clsx from "clsx";

type StatusBadgeProps = {
  value: string | null | undefined;
};

function normalize(value: string) {
  return value.toLowerCase().replaceAll("_", "-");
}

export function StatusBadge({ value }: StatusBadgeProps) {
  const displayValue = value ?? "unknown";
  const normalized = normalize(displayValue);

  return (
    <span className={clsx("badge", `badge-${normalized}`)}>
      {displayValue.replaceAll("_", " ")}
    </span>
  );
}
