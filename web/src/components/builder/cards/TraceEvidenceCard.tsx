import type { ArtifactRef } from '../../../lib/builder-types';

interface TraceEvidenceCardProps {
  artifact: ArtifactRef;
}

function toStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is string => typeof item === 'string');
}

export function TraceEvidenceCard({ artifact }: TraceEvidenceCardProps) {
  const links = toStringArray(artifact.payload.evidence_links);

  return (
    <article className="rounded-xl border border-slate-700 bg-slate-900/80 p-4">
      <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Trace Evidence</p>
      <h3 className="mt-1 text-sm font-semibold text-slate-100">{artifact.title}</h3>
      <div className="mt-2 space-y-1 text-xs text-slate-300">
        {links.length === 0 ? <p className="text-slate-500">No evidence links.</p> : null}
        {links.map((link) => (
          <p key={link}>{link}</p>
        ))}
      </div>
    </article>
  );
}
