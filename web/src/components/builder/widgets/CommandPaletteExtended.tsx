import { useMemo } from 'react';

interface CommandPaletteExtendedProps {
  open: boolean;
  query: string;
  commands: string[];
  onClose: () => void;
  onSelect: (command: string) => void;
}

export function CommandPaletteExtended({
  open,
  query,
  commands,
  onClose,
  onSelect,
}: CommandPaletteExtendedProps) {
  const filtered = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return commands;
    return commands.filter((command) => command.toLowerCase().includes(normalized));
  }, [commands, query]);

  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-[70] flex items-start justify-center bg-slate-950/60 pt-24" onClick={onClose}>
      <div
        className="w-full max-w-xl rounded-xl border border-slate-700 bg-slate-900 p-3 shadow-2xl"
        onClick={(event) => event.stopPropagation()}
      >
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">Command Palette</p>
        <div className="max-h-72 overflow-y-auto">
          {filtered.map((command) => (
            <button
              key={command}
              type="button"
              onClick={() => onSelect(command)}
              className="block w-full rounded-md px-2 py-2 text-left text-sm text-slate-300 transition hover:bg-slate-800 hover:text-slate-100"
            >
              {command}
            </button>
          ))}
          {filtered.length === 0 ? (
            <p className="px-2 py-3 text-sm text-slate-500">No command matches your query.</p>
          ) : null}
        </div>
      </div>
    </div>
  );
}
