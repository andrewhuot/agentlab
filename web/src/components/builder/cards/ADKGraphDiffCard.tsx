import type { ArtifactRef } from '../../../lib/builder-types';

interface ADKGraphDiffCardProps {
  artifact: ArtifactRef;
}

export function ADKGraphDiffCard({ artifact }: ADKGraphDiffCardProps) {
  const beforeGraph = artifact.payload.before_graph as Record<string, unknown> | undefined;
  const afterGraph = artifact.payload.after_graph as Record<string, unknown> | undefined;

  return (
    <article className="rounded-xl border border-slate-700 bg-slate-900/80 p-4">
      <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">ADK Graph Diff</p>
      <h3 className="mt-1 text-sm font-semibold text-slate-100">{artifact.title}</h3>
      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        <div className="rounded-md border border-slate-700 bg-slate-950/80 p-2">
          <p className="text-xs font-medium text-slate-300">Before</p>
          <pre className="mt-1 overflow-x-auto text-[11px] text-slate-500">
            {JSON.stringify(beforeGraph ?? {}, null, 2)}
          </pre>
        </div>
        <div className="rounded-md border border-slate-700 bg-slate-950/80 p-2">
          <p className="text-xs font-medium text-slate-300">After</p>
          <pre className="mt-1 overflow-x-auto text-[11px] text-slate-500">
            {JSON.stringify(afterGraph ?? {}, null, 2)}
          </pre>
        </div>
      </div>
    </article>
  );
}
