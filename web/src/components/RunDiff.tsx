import type { EvalResultsDiff } from '../lib/types';

interface RunDiffProps {
  diff: EvalResultsDiff | undefined;
  isLoading: boolean;
}

export function RunDiff({ diff, isLoading }: RunDiffProps) {
  if (isLoading) {
    return (
      <section className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
        <p className="text-sm text-gray-500">Loading run diff…</p>
      </section>
    );
  }

  if (!diff) {
    return (
      <section className="rounded-2xl border border-dashed border-gray-200 bg-gray-50 p-4">
        <h3 className="text-sm font-semibold text-gray-900">Run-to-Run Diff</h3>
        <p className="mt-2 text-sm text-gray-500">
          Choose a comparison run to highlight new passes, regressions, and changed examples.
        </p>
      </section>
    );
  }

  return (
    <section className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-gray-900">Run-to-Run Diff</h3>
          <p className="mt-1 text-xs text-gray-500">
            {diff.baseline_run_id} vs {diff.candidate_run_id}
          </p>
        </div>
        <div className="rounded-full bg-gray-100 px-2.5 py-1 text-[11px] font-medium text-gray-700">
          {diff.changed_examples.length} changed
        </div>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <DiffStat label="New passes" value={diff.new_passes} tone="green" />
        <DiffStat label="New failures" value={diff.new_failures} tone="red" />
        <DiffStat label="Changed examples" value={diff.changed_examples.length} tone="slate" />
      </div>

      <div className="mt-4 space-y-2">
        {diff.changed_examples.length === 0 ? (
          <p className="text-sm text-gray-500">No changed examples between these runs.</p>
        ) : (
          diff.changed_examples.map((change) => (
            <div
              key={change.example_id}
              className="flex items-center justify-between gap-3 rounded-xl border border-gray-200 bg-gray-50 px-3 py-2"
            >
              <div>
                <p className="font-mono text-xs text-gray-800">{change.example_id}</p>
                <p className="text-xs text-gray-500">
                  {change.before_passed ? 'pass' : 'fail'} {'->'} {change.after_passed ? 'pass' : 'fail'}
                </p>
              </div>
              <span
                className={`rounded-full px-2 py-1 text-[11px] font-medium ${
                  change.score_delta >= 0 ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
                }`}
              >
                {change.score_delta >= 0 ? '+' : ''}
                {change.score_delta.toFixed(3)}
              </span>
            </div>
          ))
        )}
      </div>
    </section>
  );
}

function DiffStat({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: 'green' | 'red' | 'slate';
}) {
  const tones = {
    green: 'border-emerald-200 bg-emerald-50 text-emerald-800',
    red: 'border-red-200 bg-red-50 text-red-800',
    slate: 'border-gray-200 bg-gray-50 text-gray-800',
  };

  return (
    <div className={`rounded-xl border px-3 py-3 ${tones[tone]}`}>
      <p className="text-xs uppercase tracking-wide opacity-70">{label}</p>
      <p className="mt-1 text-2xl font-semibold">{value}</p>
    </div>
  );
}
