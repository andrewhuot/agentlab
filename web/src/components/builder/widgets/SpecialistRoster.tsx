import { Bot } from 'lucide-react';
import type { SpecialistDefinition } from '../../../lib/builder-types';
import { classNames } from '../../../lib/utils';

interface SpecialistRosterProps {
  specialists: SpecialistDefinition[];
  activeRole: string;
}

export function SpecialistRoster({ specialists, activeRole }: SpecialistRosterProps) {
  return (
    <div className="rounded-lg border border-slate-700 bg-slate-900/70 p-3">
      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">Builder Roster</p>
      <div className="space-y-1.5">
        {specialists.map((specialist) => (
          <div
            key={specialist.role}
            className={classNames(
              'rounded-md border px-2 py-1.5',
              specialist.role === activeRole
                ? 'border-sky-500/60 bg-sky-500/10'
                : 'border-slate-700 bg-slate-900/40'
            )}
          >
            <div className="flex items-center gap-1.5">
              <Bot className="h-3.5 w-3.5 text-slate-400" />
              <p className="text-xs font-medium text-slate-200">{specialist.display_name}</p>
            </div>
            <p className="mt-1 text-[11px] text-slate-500">{specialist.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
