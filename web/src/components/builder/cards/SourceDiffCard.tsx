import type { ArtifactRef } from '../../../lib/builder-types';

interface SourceDiffCardProps {
  artifact: ArtifactRef;
}

function toStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is string => typeof item === 'string');
}

export function SourceDiffCard({ artifact }: SourceDiffCardProps) {
  const files = Array.isArray(artifact.payload.files) ? artifact.payload.files : [];

  return (
    <article className="rounded-xl border border-slate-700 bg-slate-900/80 p-4">
      <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Source Diff</p>
      <h3 className="mt-1 text-sm font-semibold text-slate-100">{artifact.title}</h3>
      <p className="mt-2 text-xs text-slate-400">{artifact.summary}</p>

      <div className="mt-3 space-y-2">
        {files.length === 0 ? (
          <p className="text-xs text-slate-500">No file hunks attached.</p>
        ) : (
          files.map((file, index) => {
            const record = typeof file === 'object' && file !== null ? (file as Record<string, unknown>) : {};
            const path = typeof record.path === 'string' ? record.path : `file-${index + 1}`;
            const lines = toStringArray(record.lines);
            return (
              <div key={path} className="rounded-md border border-slate-700 bg-slate-950/80 p-2">
                <p className="text-xs font-medium text-slate-200">{path}</p>
                {lines.length > 0 ? (
                  <pre className="mt-2 overflow-x-auto text-[11px] text-slate-400">{lines.join('\n')}</pre>
                ) : null}
              </div>
            );
          })
        )}
      </div>
    </article>
  );
}
