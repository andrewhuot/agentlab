interface CompareMetric {
  label: string;
  baseline: number;
  candidate: number;
}

interface CompareViewProps {
  metrics: CompareMetric[];
}

export function CompareView({ metrics }: CompareViewProps) {
  return (
    <div className="rounded-xl border border-slate-700 bg-slate-900/80 p-4">
      <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Compare</p>
      <div className="mt-2 space-y-1.5">
        {metrics.map((metric) => {
          const delta = metric.candidate - metric.baseline;
          const tone = delta >= 0 ? 'text-emerald-300' : 'text-rose-300';
          return (
            <div key={metric.label} className="flex items-center justify-between rounded-md border border-slate-700 bg-slate-950/70 px-2 py-1.5 text-xs">
              <span className="text-slate-300">{metric.label}</span>
              <span className="text-slate-500">{metric.baseline.toFixed(2)} → {metric.candidate.toFixed(2)}</span>
              <span className={tone}>{delta >= 0 ? '+' : ''}{delta.toFixed(2)}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
