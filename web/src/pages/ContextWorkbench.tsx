import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { PageHeader } from '../components/PageHeader';

const API_BASE = '/api';

interface ContextReport {
  utilization_ratio: number;
  compaction_loss: number;
  avg_handoff_fidelity: number;
  memory_staleness: number;
  status: string;
  recommendations: string[];
}

interface SimulationResult {
  strategy_name: string;
  total_compactions: number;
  total_tokens_lost: number;
  peak_tokens: number;
  avg_utilization: number;
  final_tokens: number;
}

function useContextReport() {
  return useQuery<ContextReport>({
    queryKey: ['context', 'report'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/context/report`);
      return res.json();
    },
    refetchInterval: 30000,
  });
}

function useSimulate() {
  return useMutation({
    mutationFn: async (body: Record<string, unknown>) => {
      const res = await fetch(`${API_BASE}/context/simulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      return res.json();
    },
  });
}

export function ContextWorkbench() {
  const { data: report } = useContextReport();
  const simulate = useSimulate();
  const [traceId, setTraceId] = useState('');
  const [analysisResult, setAnalysisResult] = useState<Record<string, unknown> | null>(null);
  const [analysisError, setAnalysisError] = useState('');

  const analyzeTrace = async () => {
    if (!traceId.trim()) return;
    setAnalysisError('');
    try {
      const res = await fetch(`${API_BASE}/context/analysis/${traceId}`);
      if (!res.ok) {
        setAnalysisError(`Trace not found: ${traceId}`);
        return;
      }
      setAnalysisResult(await res.json());
    } catch {
      setAnalysisError('Failed to analyze trace');
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Context Engineering Workbench"
        description="Diagnose and tune agent context — utilization, compaction, handoffs"
      />

      {/* Aggregate metrics */}
      {report && (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <MetricCard label="Utilization" value={`${(report.utilization_ratio * 100).toFixed(1)}%`} />
          <MetricCard label="Compaction Loss" value={`${(report.compaction_loss * 100).toFixed(1)}%`} />
          <MetricCard label="Handoff Fidelity" value={`${(report.avg_handoff_fidelity * 100).toFixed(1)}%`} />
          <MetricCard label="Memory Staleness" value={`${report.memory_staleness.toFixed(1)}s`} />
        </div>
      )}

      {/* Trace analysis */}
      <section className="rounded-xl border border-gray-200 bg-white p-5">
        <h2 className="text-sm font-semibold text-gray-900">Analyze Trace</h2>
        <div className="mt-3 flex gap-2">
          <input
            type="text"
            placeholder="Trace ID..."
            value={traceId}
            onChange={(e) => setTraceId(e.target.value)}
            className="flex-1 rounded-lg border border-gray-200 px-3 py-2 text-sm"
          />
          <button
            onClick={analyzeTrace}
            className="rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800"
          >
            Analyze
          </button>
        </div>
        {analysisError && (
          <p className="mt-2 text-sm text-red-600">{analysisError}</p>
        )}
        {analysisResult && (
          <pre className="mt-3 max-h-64 overflow-y-auto rounded-lg bg-gray-50 p-3 text-xs text-gray-700">
            {JSON.stringify(analysisResult, null, 2)}
          </pre>
        )}
      </section>

      {/* Compaction simulator */}
      <section className="rounded-xl border border-gray-200 bg-white p-5">
        <h2 className="text-sm font-semibold text-gray-900">Compaction Simulator</h2>
        <p className="mt-1 text-xs text-gray-500">
          Compare compaction strategies against recorded context patterns.
        </p>
        <button
          onClick={() => simulate.mutate({ snapshots: [] })}
          disabled={simulate.isPending}
          className="mt-3 rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800 disabled:opacity-50"
        >
          {simulate.isPending ? 'Simulating...' : 'Run Default Comparison'}
        </button>
        {simulate.data && (
          <div className="mt-3 space-y-2">
            {(simulate.data as { results: SimulationResult[] }).results.map((r: SimulationResult) => (
              <div key={r.strategy_name} className="flex items-center justify-between rounded-lg bg-gray-50 px-4 py-3">
                <span className="text-sm font-medium text-gray-900">{r.strategy_name}</span>
                <div className="flex gap-4 text-xs text-gray-600">
                  <span>Peak: {r.peak_tokens} tokens</span>
                  <span>Compactions: {r.total_compactions}</span>
                  <span>Lost: {r.total_tokens_lost} tokens</span>
                  <span>Avg util: {(r.avg_utilization * 100).toFixed(1)}%</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4">
      <p className="text-xs font-medium text-gray-500">{label}</p>
      <p className="mt-1 text-xl font-semibold tabular-nums text-gray-900">{value}</p>
    </div>
  );
}
