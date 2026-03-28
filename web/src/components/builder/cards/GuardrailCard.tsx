import type { ArtifactRef } from '../../../lib/builder-types';

interface GuardrailCardProps {
  artifact: ArtifactRef;
}

function toStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is string => typeof item === 'string');
}

export function GuardrailCard({ artifact }: GuardrailCardProps) {
  const scope = toStringArray(artifact.payload.attached_scope);
  const failures = toStringArray(artifact.payload.failure_examples);

  return (
    <article className="rounded-xl border border-slate-700 bg-slate-900/80 p-4">
      <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Guardrail</p>
      <h3 className="mt-1 text-sm font-semibold text-slate-100">{artifact.title}</h3>
      <p className="mt-2 text-xs text-slate-400">Attached scope: {scope.join(', ') || 'none'}</p>
      <div className="mt-2 space-y-1 text-xs text-slate-300">
        {failures.map((failure) => (
          <p key={failure}>• {failure}</p>
        ))}
      </div>
    </article>
  );
}
