import type { ArtifactRef } from '../../../lib/builder-types';

interface BenchmarkCardProps {
  artifact: ArtifactRef;
}

export function BenchmarkCard({ artifact }: BenchmarkCardProps) {
  const metrics = artifact.payload.metrics as Record<string, unknown> | undefined;

  return (
    <article className="rounded-xl border border-slate-700 bg-slate-900/80 p-4">
      <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Benchmark</p>
      <h3 className="mt-1 text-sm font-semibold text-slate-100">{artifact.title}</h3>
      <pre className="mt-3 overflow-x-auto rounded-md border border-slate-700 bg-slate-950/80 p-2 text-[11px] text-slate-500">
        {JSON.stringify(metrics ?? {}, null, 2)}
      </pre>
    </article>
  );
}
