import type { ArtifactRef } from '../../../lib/builder-types';

interface EvalCardProps {
  artifact: ArtifactRef;
}

export function EvalCard({ artifact }: EvalCardProps) {
  const hardGate = Boolean(artifact.payload.hard_gate_passed);

  return (
    <article className="rounded-xl border border-slate-700 bg-slate-900/80 p-4">
      <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Eval</p>
      <h3 className="mt-1 text-sm font-semibold text-slate-100">{artifact.title}</h3>
      <p className="mt-2 text-xs text-slate-400">{artifact.summary}</p>
      <p className="mt-3 inline-flex rounded-md border border-slate-700 px-2 py-1 text-xs text-slate-300">
        Hard gate: {hardGate ? 'pass' : 'fail'}
      </p>
    </article>
  );
}
