import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PageHeader } from '../components/PageHeader';

const API_BASE = '/api';

interface JudgeInfo {
  grader_id: string;
  latest_version: number;
  config: Record<string, unknown>;
  agreement_rate: number;
}

interface HumanFeedbackItem {
  feedback_id: string;
  case_id: string;
  judge_id: string;
  judge_score: number;
  human_score: number;
  human_notes: string;
  created_at: number;
}

interface DriftAlert {
  alert_id: string;
  grader_id: string;
  alert_type: string;
  severity: number;
  details: Record<string, unknown>;
}

function useJudges() {
  return useQuery<JudgeInfo[]>({
    queryKey: ['judges', 'list'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/judges`);
      const data = await res.json();
      return data.judges ?? [];
    },
    refetchInterval: 15000,
  });
}

function useCalibration(judgeId?: string) {
  return useQuery<{ agreement_rate: number; disagreements: HumanFeedbackItem[]; total_feedback: number }>({
    queryKey: ['judges', 'calibration', judgeId],
    queryFn: async () => {
      const qs = judgeId ? `?judge_id=${judgeId}` : '';
      const res = await fetch(`${API_BASE}/judges/calibration${qs}`);
      return res.json();
    },
    refetchInterval: 10000,
  });
}

function useDriftAlerts() {
  return useQuery<DriftAlert[]>({
    queryKey: ['judges', 'drift'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/judges/drift`);
      const data = await res.json();
      return data.alerts ?? [];
    },
    refetchInterval: 30000,
  });
}

function useSubmitFeedback() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: Record<string, unknown>) => {
      const res = await fetch(`${API_BASE}/judges/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      return res.json();
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['judges'] }),
  });
}

export function JudgeOps() {
  const [selectedJudge, setSelectedJudge] = useState<string | undefined>(undefined);
  const { data: judges = [], isLoading: loadingJudges } = useJudges();
  const { data: calibration } = useCalibration(selectedJudge);
  const { data: driftAlerts = [] } = useDriftAlerts();

  return (
    <div className="space-y-6">
      <PageHeader
        title="Judge Ops"
        description="Judge reliability monitoring, calibration, and human feedback"
      />

      {/* Drift alerts */}
      {driftAlerts.length > 0 && (
        <div className="space-y-2">
          {driftAlerts.map((alert) => (
            <div key={alert.alert_id} className="flex items-center gap-3 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3">
              <span className="h-2 w-2 rounded-full bg-amber-400" />
              <span className="text-sm font-medium text-amber-800">{alert.alert_type}</span>
              <span className="text-sm text-amber-600">
                {alert.grader_id} — severity {(alert.severity * 100).toFixed(0)}%
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Judge list */}
      <section className="rounded-xl border border-gray-200 bg-white p-5">
        <h2 className="text-sm font-semibold text-gray-900">Active Judges</h2>
        {loadingJudges ? (
          <div className="mt-3 text-sm text-gray-500">Loading...</div>
        ) : judges.length === 0 ? (
          <div className="mt-3 text-sm text-gray-500">No judges registered yet.</div>
        ) : (
          <div className="mt-3 space-y-2">
            {judges.map((j) => (
              <button
                key={j.grader_id}
                onClick={() => setSelectedJudge(j.grader_id === selectedJudge ? undefined : j.grader_id)}
                className={`flex w-full items-center justify-between rounded-lg border px-4 py-3 text-left transition-colors ${
                  j.grader_id === selectedJudge ? 'border-blue-200 bg-blue-50' : 'border-gray-100 hover:bg-gray-50'
                }`}
              >
                <div>
                  <span className="text-sm font-medium text-gray-900">{j.grader_id}</span>
                  <span className="ml-2 text-xs text-gray-500">v{j.latest_version}</span>
                </div>
                <span className="tabular-nums text-sm text-gray-600">
                  {(j.agreement_rate * 100).toFixed(1)}% agreement
                </span>
              </button>
            ))}
          </div>
        )}
      </section>

      {/* Calibration dashboard */}
      {calibration && (
        <section className="rounded-xl border border-gray-200 bg-white p-5">
          <h2 className="text-sm font-semibold text-gray-900">
            Calibration {selectedJudge ? `— ${selectedJudge}` : '(all judges)'}
          </h2>
          <div className="mt-3 flex items-center gap-6">
            <div>
              <span className="text-2xl font-semibold tabular-nums text-gray-900">
                {(calibration.agreement_rate * 100).toFixed(1)}%
              </span>
              <span className="ml-1 text-sm text-gray-500">agreement</span>
            </div>
            <div>
              <span className="text-2xl font-semibold tabular-nums text-gray-900">
                {calibration.total_feedback}
              </span>
              <span className="ml-1 text-sm text-gray-500">total feedback</span>
            </div>
          </div>

          {calibration.disagreements.length > 0 && (
            <div className="mt-4">
              <h3 className="text-xs font-semibold uppercase text-gray-500">Top Disagreements</h3>
              <div className="mt-2 space-y-1">
                {calibration.disagreements.slice(0, 10).map((d) => (
                  <div key={d.feedback_id} className="flex items-center gap-4 rounded-lg bg-gray-50 px-3 py-2 text-sm">
                    <span className="text-gray-600">{d.case_id}</span>
                    <span className="tabular-nums text-gray-900">Judge: {d.judge_score.toFixed(2)}</span>
                    <span className="tabular-nums text-gray-900">Human: {d.human_score.toFixed(2)}</span>
                    <span className="tabular-nums font-medium text-red-600">
                      gap: {Math.abs(d.judge_score - d.human_score).toFixed(2)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>
      )}
    </div>
  );
}
