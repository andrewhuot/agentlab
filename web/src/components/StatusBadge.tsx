import { classNames, statusLabel } from '../lib/utils';

type Variant = 'success' | 'error' | 'warning' | 'pending' | 'running';

interface StatusBadgeProps {
  variant: Variant;
  label: string;
}

const dotColors: Record<Variant, string> = {
  success: 'bg-green-500',
  error: 'bg-red-500',
  warning: 'bg-amber-500',
  pending: 'bg-gray-400',
  running: 'bg-blue-500',
};

export function StatusBadge({ variant, label }: StatusBadgeProps) {
  return (
    <span className="inline-flex items-center gap-1.5 text-xs text-gray-600">
      <span
        className={classNames(
          'h-1.5 w-1.5 rounded-full',
          dotColors[variant],
          variant === 'running' ? 'animate-pulse' : ''
        )}
      />
      {statusLabel(label)}
    </span>
  );
}
