import type { ParetoFrontier } from '../lib/types';
import { StatusBadge } from './StatusBadge';

interface Props {
  frontier: ParetoFrontier;
}

export function ParetoFrontierView({ frontier }: Props) {
  if (!frontier.candidates.length) {
    return (
      <div className="text-sm text-zinc-500 py-4">
        No candidates in Pareto archive yet.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-zinc-400">Pareto Frontier</h3>
        <div className="flex gap-3 text-xs text-zinc-500">
          <span>{frontier.frontier_size} frontier</span>
          <span>{frontier.infeasible_count} infeasible</span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="text-zinc-500 border-b border-zinc-800">
              <th className="text-left py-2 pr-3">ID</th>
              <th className="text-left py-2 pr-3">Status</th>
              <th className="text-right py-2 pr-3">Quality</th>
              <th className="text-right py-2 pr-3">Safety</th>
              <th className="text-right py-2 pr-3">Latency</th>
              <th className="text-right py-2 pr-3">Cost</th>
              <th className="text-right py-2">Experiment</th>
            </tr>
          </thead>
          <tbody>
            {frontier.candidates.map((c) => (
              <tr
                key={c.candidate_id}
                className={`border-b border-zinc-800/50 ${
                  c.is_recommended ? 'bg-emerald-950/20' : ''
                }`}
              >
                <td className="py-2 pr-3 font-mono">
                  {c.candidate_id.slice(0, 8)}
                  {c.is_recommended && (
                    <span className="ml-1.5 text-[10px] text-emerald-400 font-medium">
                      recommended
                    </span>
                  )}
                </td>
                <td className="py-2 pr-3">
                  <StatusBadge
                    variant={c.constraints_passed ? 'success' : 'error'}
                    label={c.constraints_passed ? 'feasible' : 'infeasible'}
                  />
                </td>
                {c.objective_vector.slice(0, 4).map((v, i) => (
                  <td key={i} className="py-2 pr-3 text-right text-zinc-300">
                    {(v * 100).toFixed(1)}%
                  </td>
                ))}
                <td className="py-2 text-right text-zinc-500 font-mono">
                  {c.experiment_id?.slice(0, 8) || '\u2014'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
