import { useMemo } from 'react';

interface SlashCommandMenuProps {
  visible: boolean;
  query: string;
  onSelect: (command: string) => void;
}

const COMMANDS = [
  '/plan',
  '/improve',
  '/trace',
  '/eval',
  '/skill',
  '/guardrail',
  '/compare',
  '/branch',
  '/deploy',
  '/rollback',
  '/memory',
  '/permissions',
];

export function SlashCommandMenu({ visible, query, onSelect }: SlashCommandMenuProps) {
  const items = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return COMMANDS.filter((command) => command.includes(normalized));
  }, [query]);

  if (!visible) {
    return null;
  }

  return (
    <div className="absolute bottom-16 left-3 z-40 w-64 rounded-lg border border-slate-700 bg-slate-900 p-2 shadow-xl">
      <p className="px-2 pb-1 text-[11px] font-medium uppercase tracking-wide text-slate-500">
        Slash Commands
      </p>
      <div className="max-h-52 overflow-y-auto">
        {items.length === 0 ? (
          <p className="px-2 py-3 text-xs text-slate-500">No matching command.</p>
        ) : (
          items.map((command) => (
            <button
              key={command}
              type="button"
              onClick={() => onSelect(command)}
              className="block w-full rounded-md px-2 py-1.5 text-left text-xs text-slate-300 transition hover:bg-slate-800 hover:text-slate-100"
            >
              {command}
            </button>
          ))
        )}
      </div>
    </div>
  );
}
