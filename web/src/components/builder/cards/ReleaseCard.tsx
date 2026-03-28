import type { ArtifactRef } from '../../../lib/builder-types';

interface ReleaseCardProps {
  artifact: ArtifactRef;
}

export function ReleaseCard({ artifact }: ReleaseCardProps) {
  const target = typeof artifact.payload.deployment_target === 'string' ? artifact.payload.deployment_target : 'unknown';

  return (
    <article className="rounded-xl border border-slate-700 bg-slate-900/80 p-4">
      <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Release</p>
      <h3 className="mt-1 text-sm font-semibold text-slate-100">{artifact.title}</h3>
      <p className="mt-2 text-xs text-slate-400">Target: {target}</p>
      <p className="mt-2 text-xs text-slate-500">{artifact.summary}</p>
    </article>
  );
}
