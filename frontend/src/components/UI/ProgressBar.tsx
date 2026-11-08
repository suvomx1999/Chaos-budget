interface ProgressBarProps {
  progress: number; // 0-100
  color?: string;
  label?: string;
  showPercent?: boolean;
}

export default function ProgressBar({
  progress,
  color = "bg-primary",
  label,
  showPercent = true,
}: ProgressBarProps) {
  const clamped = Math.max(0, Math.min(100, progress));

  return (
    <div className="w-full">
      {(label || showPercent) && (
        <div className="flex justify-between items-center mb-1.5">
          {label && (
            <span className="text-xs font-medium text-text-dim">{label}</span>
          )}
          {showPercent && (
            <span className="text-xs font-mono text-text-muted">
              {clamped.toFixed(0)}%
            </span>
          )}
        </div>
      )}
      <div className="w-full h-1.5 bg-white/[0.04] rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-1000 ease-out ${color}`}
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  );
}
