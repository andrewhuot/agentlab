import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PageHeader } from '../components/PageHeader';

const API_BASE = '/api';

interface AutoFixProposal {
  proposal_id: string;
  mutation_name: string;
  surface: string;
  expected_lift: number;
  risk_class: string;
  affected_eval_slices: string[];
  cost_impact_estimate: number;
  diff_preview: string;
  status: string;
  created_at: number;
}

function useAutoFixProposals(status?: string) {
  return useQuery<AutoFixProposal[]>({
    queryKey: ['autofix', 'proposals', status],
    queryFn: async () => {
      const qs = status ? `?status=${status}` : '';
      const res = await fetch(`${API_BASE}/autofix/proposals${qs}`);
      const data = await res.json();
      return data.proposals ?? [];
    },
    refetchInterval: 10000,
  });
}

function useSuggest() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const res = await fetch(`${API_BASE}/autofix/suggest`, { method: 'POST' });
      return res.json();
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['autofix'] }),
  });
}

function useApply() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (proposalId: string) => {
      const res = await fetch(`${API_BASE}/autofix/apply/${proposalId}`, { method: 'POST' });
      return res.json();
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['autofix'] }),
  });
}

const riskColors: Record<string, string> = {
  low: 'bg-green-100 text-green-700',
  medium: 'bg-amber-100 text-amber-700',
  high: 'bg-red-100 text-red-700',
  critical: 'bg-red-200 text-red-800',
};

export function AutoFix() {
  const [filter, setFilter] = useState<string | undefined>(undefined);
  const { data: proposals = [], isLoading } = useAutoFixProposals(filter);
  const suggest = useSuggest();
  const apply = useApply();

  return (
    <div className="space-y-6">
      <PageHeader
        title="AutoFix Copilot"
        description="Constrained, reviewable improvement proposals for your agent config"
      />

      <div className="flex items-center gap-3">
        <button
          onClick={() => suggest.mutate()}
          disabled={suggest.isPending}
          className="rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800 disabled:opacity-50"
        >
          {suggest.isPending ? 'Generating...' : 'Generate Proposals'}
        </button>
        <select
          value={filter ?? ''}
          onChange={(e) => setFilter(e.target.value || undefined)}
          className="rounded-lg border border-gray-200 px-3 py-2 text-sm"
        >
          <option value="">All statuses</option>
          <option value="pending">Pending</option>
          <option value="evaluated">Evaluated</option>
          <option value="applied">Applied</option>
          <option value="rejected">Rejected</option>
        </select>
      </div>

      {isLoading && (
        <div className="flex h-32 items-center justify-center rounded-xl border border-dashed border-gray-200 bg-gray-50 text-sm text-gray-500">
          Loading proposals...
        </div>
      )}

      {!isLoading && proposals.length === 0 && (
        <div className="flex h-32 items-center justify-center rounded-xl border border-dashed border-gray-200 bg-gray-50 text-sm text-gray-500">
          No proposals yet. Click "Generate Proposals" to get started.
        </div>
      )}

      <div className="space-y-3">
        {proposals.map((p) => (
          <div key={p.proposal_id} className="rounded-xl border border-gray-200 bg-white p-5">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-medium text-gray-900">{p.mutation_name}</span>
                  <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${riskColors[p.risk_class] ?? 'bg-gray-100 text-gray-600'}`}>
                    {p.risk_class}
                  </span>
                  <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
                    {p.surface}
                  </span>
                </div>
                <p className="mt-1 text-sm text-gray-500">
                  Expected lift: {(p.expected_lift * 100).toFixed(1)}% | Cost impact: ${p.cost_impact_estimate.toFixed(4)}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600">
                  {p.status}
                </span>
                {p.status === 'pending' && (
                  <button
                    onClick={() => apply.mutate(p.proposal_id)}
                    disabled={apply.isPending}
                    className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-500"
                  >
                    Apply
                  </button>
                )}
              </div>
            </div>
            {p.diff_preview && (
              <pre className="mt-3 rounded-lg bg-gray-50 p-3 text-xs text-gray-700 overflow-x-auto">
                {p.diff_preview}
              </pre>
            )}
            {p.affected_eval_slices.length > 0 && (
              <div className="mt-2 flex gap-1">
                {p.affected_eval_slices.map((s) => (
                  <span key={s} className="rounded bg-blue-50 px-1.5 py-0.5 text-xs text-blue-600">{s}</span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
