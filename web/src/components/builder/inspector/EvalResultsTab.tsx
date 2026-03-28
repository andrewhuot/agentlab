import type { EvalBundle } from '../../../lib/builder-types';

interface EvalResultsTabProps {
  bundle: EvalBundle | null;
}

export function EvalResultsTab({ bundle }: EvalResultsTabProps) {
  if (!bundle) {
    return (
      <p className="rounded-md border border-slate-700 bg-slate-900/70 px-3 py-2 text-xs text-slate-500">
        No eval bundle attached.
      </p>
    );
  }

  return (
    <div className="space-y-2 rounded-md border border-slate-700 bg-slate-900/70 p-3 text-xs text-slate-300">
      <p>Hard gate: {bundle.hard_gate_passed ? 'pass' : 'fail'}</p>
      <p>Trajectory quality: {bundle.trajectory_quality.toFixed(3)}</p>
      <p>Outcome quality: {bundle.outcome_quality.toFixed(3)}</p>
      <p>Coverage delta: {bundle.eval_coverage_pct.toFixed(2)}%</p>
      <p>Cost delta: {bundle.cost_delta_pct.toFixed(2)}%</p>
      <p>Latency delta: {bundle.latency_delta_pct.toFixed(2)}%</p>
    </div>
  );
}
