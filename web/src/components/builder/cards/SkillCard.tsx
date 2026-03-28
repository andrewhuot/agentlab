import type { ArtifactRef } from '../../../lib/builder-types';

interface SkillCardProps {
  artifact: ArtifactRef;
}

export function SkillCard({ artifact }: SkillCardProps) {
  const name = typeof artifact.payload.name === 'string' ? artifact.payload.name : artifact.title;
  const manifest = artifact.payload.manifest as Record<string, unknown> | undefined;

  return (
    <article className="rounded-xl border border-slate-700 bg-slate-900/80 p-4">
      <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Skill</p>
      <h3 className="mt-1 text-sm font-semibold text-slate-100">{name}</h3>
      <pre className="mt-3 overflow-x-auto rounded-md border border-slate-700 bg-slate-950/80 p-2 text-[11px] text-slate-500">
        {JSON.stringify(manifest ?? {}, null, 2)}
      </pre>
    </article>
  );
}
