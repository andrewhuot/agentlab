import type { EvalResultsMetricSummary } from '../lib/types';

interface ScoreDistributionProps {
  title: string;
  summary: EvalResultsMetricSummary;
}

export function ScoreDistribution({ title, summary }: ScoreDistributionProps) {
  const peak = Math.max(...summary.histogram, 1);

  return (
    <section className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-gray-900">{title}</h3>
          <p className="mt-1 text-xs text-gray-500">
            mean {summary.mean.toFixed(3)} · median {summary.median.toFixed(3)} · std {summary.std.toFixed(3)}
          </p>
        </div>
        <div className="rounded-full bg-gray-100 px-2.5 py-1 text-[11px] font-medium text-gray-700">
          min {summary.min.toFixed(2)} · max {summary.max.toFixed(2)}
        </div>
      </div>

      <div className="mt-4 flex h-28 items-end gap-1.5">
        {summary.histogram.map((count, index) => (
          <div key={`${title}-${index}`} className="flex flex-1 flex-col items-center gap-2">
            <div
              className="w-full rounded-t-md bg-gray-900/80 transition-all"
              style={{ height: `${Math.max((count / peak) * 100, count > 0 ? 12 : 0)}%` }}
            />
            <span className="text-[10px] text-gray-400">{index + 1}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
