import type { DimensionScores } from '../lib/types';

const DIMENSION_LABELS: Record<keyof DimensionScores, string> = {
  task_success_rate: 'Task Success',
  response_quality: 'Response Quality',
  safety_compliance: 'Safety Compliance',
  latency_p50: 'Latency (p50)',
  latency_p95: 'Latency (p95)',
  latency_p99: 'Latency (p99)',
  token_cost: 'Token Cost',
  tool_correctness: 'Tool Correctness',
  routing_accuracy: 'Routing Accuracy',
  handoff_fidelity: 'Handoff Fidelity',
  user_satisfaction_proxy: 'User Satisfaction',
};

interface Props {
  dimensions: DimensionScores;
}

export function DimensionBreakdown({ dimensions }: Props) {
  return (
    <div className="space-y-2">
      <h3 className="text-sm font-medium text-zinc-400">Dimension Breakdown</h3>
      <div className="space-y-1.5">
        {(Object.entries(DIMENSION_LABELS) as [keyof DimensionScores, string][]).map(
          ([key, label]) => {
            const value = dimensions[key];
            return (
              <div key={key} className="flex items-center gap-3">
                <span className="text-xs text-zinc-500 w-32 truncate">{label}</span>
                <div className="flex-1 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: `${Math.round(value * 100)}%`,
                      backgroundColor:
                        value >= 0.8 ? '#22c55e' : value >= 0.5 ? '#eab308' : '#ef4444',
                    }}
                  />
                </div>
                <span className="text-xs text-zinc-400 w-10 text-right">
                  {(value * 100).toFixed(0)}%
                </span>
              </div>
            );
          }
        )}
      </div>
    </div>
  );
}
