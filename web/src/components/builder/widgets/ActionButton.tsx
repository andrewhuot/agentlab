import type { ReactNode } from 'react';
import { classNames } from '../../../lib/utils';

type ActionButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost';

interface ActionButtonProps {
  label: string;
  icon?: ReactNode;
  variant?: ActionButtonVariant;
  disabled?: boolean;
  onClick?: () => void;
}

const VARIANT_STYLES: Record<ActionButtonVariant, string> = {
  primary: 'bg-sky-500 text-white hover:bg-sky-400',
  secondary: 'bg-slate-800 text-slate-100 hover:bg-slate-700',
  danger: 'bg-rose-600 text-white hover:bg-rose-500',
  ghost: 'bg-transparent text-slate-300 hover:bg-slate-800/70',
};

export function ActionButton({
  label,
  icon,
  variant = 'secondary',
  disabled = false,
  onClick,
}: ActionButtonProps) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={classNames(
        'inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors duration-150',
        VARIANT_STYLES[variant],
        disabled && 'cursor-not-allowed opacity-50'
      )}
    >
      {icon}
      <span>{label}</span>
    </button>
  );
}
