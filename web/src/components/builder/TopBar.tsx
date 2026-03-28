import { Pause, Play, ShieldCheck } from 'lucide-react';
import type { BuilderProject, ExecutionMode } from '../../lib/builder-types';
import { ModeSelector } from './widgets';

export type BuilderEnvironment = 'dev' | 'staging' | 'prod';

interface TopBarProps {
  project: BuilderProject | null;
  projects: BuilderProject[];
  mode: ExecutionMode;
  model: string;
  modelOptions: string[];
  environment: BuilderEnvironment;
  paused: boolean;
  permissionCount: number;
  onProjectChange: (projectId: string) => void;
  onEnvironmentChange: (environment: BuilderEnvironment) => void;
  onModelChange: (model: string) => void;
  onModeChange: (mode: ExecutionMode) => void;
  onTogglePaused: () => void;
}

export function TopBar({
  project,
  projects,
  mode,
  model,
  modelOptions,
  environment,
  paused,
  permissionCount,
  onProjectChange,
  onEnvironmentChange,
  onModelChange,
  onModeChange,
  onTogglePaused,
}: TopBarProps) {
  const permissionTone = permissionCount > 0 ? 'text-amber-300 border-amber-500/40' : 'text-emerald-300 border-emerald-500/40';

  return (
    <header className="flex h-14 items-center gap-3 border-b border-slate-800 bg-slate-950/95 px-3">
      <div className="grid min-w-[260px] grid-cols-2 gap-2">
        <select
          aria-label="Project selector"
          value={project?.project_id ?? ''}
          onChange={(event) => onProjectChange(event.target.value)}
          className="rounded-md border border-slate-700 bg-slate-900 px-2 py-1.5 text-xs text-slate-200 outline-none transition focus:border-sky-500"
        >
          <option value="" disabled>
            Select project
          </option>
          {projects.map((item) => (
            <option key={item.project_id} value={item.project_id}>
              {item.name}
            </option>
          ))}
        </select>

        <select
          aria-label="Environment selector"
          value={environment}
          onChange={(event) => onEnvironmentChange(event.target.value as BuilderEnvironment)}
          className="rounded-md border border-slate-700 bg-slate-900 px-2 py-1.5 text-xs text-slate-200 outline-none transition focus:border-sky-500"
        >
          <option value="dev">dev</option>
          <option value="staging">staging</option>
          <option value="prod">prod</option>
        </select>
      </div>

      <ModeSelector value={mode} onChange={onModeChange} />

      <select
        aria-label="Model selector"
        value={model}
        onChange={(event) => onModelChange(event.target.value)}
        className="rounded-md border border-slate-700 bg-slate-900 px-2 py-1.5 text-xs text-slate-200 outline-none transition focus:border-sky-500"
      >
        {modelOptions.map((modelName) => (
          <option key={modelName} value={modelName}>
            {modelName}
          </option>
        ))}
      </select>

      <div
        className={`ml-auto inline-flex items-center gap-1 rounded-md border bg-slate-900 px-2 py-1 text-xs ${permissionTone}`}
        title={permissionCount > 0 ? 'Pending approvals exist' : 'No pending approvals'}
      >
        <ShieldCheck className="h-3.5 w-3.5" />
        {permissionCount} approvals
      </div>

      <button
        type="button"
        onClick={onTogglePaused}
        className="inline-flex items-center gap-1 rounded-md border border-slate-700 bg-slate-900 px-2.5 py-1.5 text-xs text-slate-200 transition hover:bg-slate-800"
      >
        {paused ? <Play className="h-3.5 w-3.5" /> : <Pause className="h-3.5 w-3.5" />}
        {paused ? 'Resume' : 'Pause'}
      </button>
    </header>
  );
}
