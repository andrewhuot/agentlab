import type { ReactNode } from 'react';
import { Eye, FilePenLine, Wrench, Network } from 'lucide-react';
import type { ExecutionMode } from '../../../lib/builder-types';
import { classNames } from '../../../lib/utils';

interface ModeSelectorProps {
  value: ExecutionMode;
  onChange: (mode: ExecutionMode) => void;
}

const MODE_OPTIONS: Array<{
  mode: ExecutionMode;
  label: string;
  icon: ReactNode;
}> = [
  { mode: 'ask', label: 'Ask', icon: <Eye className="h-3.5 w-3.5" /> },
  { mode: 'draft', label: 'Draft', icon: <FilePenLine className="h-3.5 w-3.5" /> },
  { mode: 'apply', label: 'Apply', icon: <Wrench className="h-3.5 w-3.5" /> },
  { mode: 'delegate', label: 'Delegate', icon: <Network className="h-3.5 w-3.5" /> },
];

export function ModeSelector({ value, onChange }: ModeSelectorProps) {
  return (
    <div className="inline-flex items-center rounded-lg border border-slate-700 bg-slate-900 p-1">
      {MODE_OPTIONS.map((option) => (
        <button
          key={option.mode}
          type="button"
          onClick={() => onChange(option.mode)}
          className={classNames(
            'inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium transition-colors',
            option.mode === value
              ? 'bg-slate-700 text-slate-100'
              : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
          )}
        >
          {option.icon}
          {option.label}
        </button>
      ))}
    </div>
  );
}
