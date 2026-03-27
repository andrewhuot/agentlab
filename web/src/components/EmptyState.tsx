import type { LucideIcon } from 'lucide-react';

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  cliHint?: string;
  actionLabel?: string;
  onAction?: () => void;
}

export function EmptyState({ icon: Icon, title, description, cliHint, actionLabel, onAction }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center px-4 py-24 text-center">
      <div className="mb-5 rounded-full bg-gradient-to-br from-gray-50 to-gray-100 p-4 shadow-sm ring-1 ring-gray-200/50">
        <Icon className="h-8 w-8 text-gray-400" />
      </div>
      <h3 className="text-base font-semibold text-gray-900">{title}</h3>
      <p className="mt-2 max-w-md text-sm leading-relaxed text-gray-600">{description}</p>
      {cliHint && (
        <code className="mt-4 rounded-lg border border-gray-200 bg-gray-50 px-4 py-2 text-xs font-mono text-gray-700 shadow-sm">
          {cliHint}
        </code>
      )}
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="mt-6 rounded-lg bg-gray-900 px-5 py-2.5 text-sm font-medium text-white shadow-sm transition-all hover:bg-gray-800 hover:shadow"
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}
