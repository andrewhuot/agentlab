import { useEffect, useState } from 'react';
import { Gauge, Scale } from 'lucide-react';
import { LoadingSkeleton } from '../components/LoadingSkeleton';
import { PageHeader } from '../components/PageHeader';
import { StatusBadge } from '../components/StatusBadge';
import {
  useJudgeOpsCalibration,
  useJudgeOpsDrift,
  useJudgeOpsJudges,
  useSubmitJudgeFeedback,
} from '../lib/api';
import { toastError, toastSuccess } from '../lib/toast';
import { formatTimestamp, statusVariant } from '../lib/utils';

function pct(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export function JudgeOps() {
  const judgesQuery = useJudgeOpsJudges();
  const calibrationQuery = useJudgeOpsCalibration(50);
  const driftQuery = useJudgeOpsDrift();
  const feedbackMutation = useSubmitJudgeFeedback();

  const judges = judgesQuery.data || [];
  const selectedJudge = judges[0]?.judge_id || '';

  const [caseId, setCaseId] = useState('');
  const [judgeId, setJudgeId] = useState(selectedJudge);
  const [judgeScore, setJudgeScore] = useState(0.8);
  const [humanScore, setHumanScore] = useState(0.8);
  const [comment, setComment] = useState('');

  useEffect(() => {
    if (!judgeId && selectedJudge) {
      setJudgeId(selectedJudge);
    }
  }, [judgeId, selectedJudge]);

  function submitFeedback() {
    if (!caseId.trim() || !judgeId.trim()) {
      toastError('Missing required fields', 'Case ID and judge ID are required.');
      return;
    }

    feedbackMutation.mutate(
      {
        case_id: caseId.trim(),
        judge_id: judgeId.trim(),
        judge_score: judgeScore,
        human_score: humanScore,
        comment: comment.trim(),
      },
      {
        onSuccess: () => {
          toastSuccess('Feedback saved', 'Judge calibration metrics have been refreshed.');
          setCaseId('');
          setComment('');
          judgesQuery.refetch();
          calibrationQuery.refetch();
          driftQuery.refetch();
        },
        onError: (error) => {
          toastError('Failed to save feedback', error.message);
        },
      }
    );
  }

  if (judgesQuery.isLoading || calibrationQuery.isLoading || driftQuery.isLoading) {
    return (
      <div className="space-y-4">
        <LoadingSkeleton rows={5} />
        <LoadingSkeleton rows={7} />
      </div>
    );
  }

  const calibration = calibrationQuery.data || { agreement_rate: 0, disagreement_queue: [], total_feedback: 0 };
  const drift = driftQuery.data || [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Judge Ops"
        description="Version judges, collect human corrections, track calibration drift, and prioritize disagreement review."
      />

      <section className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <p className="text-xs text-gray-500">Judges</p>
          <p className="mt-1 text-2xl font-semibold text-gray-900">{judges.length}</p>
        </div>
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <p className="text-xs text-gray-500">Agreement Rate</p>
          <p className="mt-1 text-2xl font-semibold text-gray-900">{pct(calibration.agreement_rate)}</p>
        </div>
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <p className="text-xs text-gray-500">Feedback Records</p>
          <p className="mt-1 text-2xl font-semibold text-gray-900">{calibration.total_feedback}</p>
        </div>
      </section>

      <section className="rounded-lg border border-gray-200 bg-white p-5">
        <h3 className="mb-4 text-sm font-semibold text-gray-900">Judge Versions</h3>
        {judges.length === 0 ? (
          <div className="rounded-lg border border-dashed border-gray-200 bg-gray-50 p-4 text-sm text-gray-500">
            No judge versions available.
          </div>
        ) : (
          <div className="space-y-2">
            {judges.map((judge) => (
              <div key={judge.judge_id} className="rounded-lg border border-gray-200 bg-gray-50 p-3">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-medium text-gray-900">{judge.judge_id}</p>
                  <p className="text-xs text-gray-500">v{judge.version}</p>
                </div>
                <p className="mt-1 text-xs text-gray-600">{judge.model} · temp={judge.temperature.toFixed(2)}</p>
                <p className="mt-1 text-xs text-gray-600">Agreement {pct(judge.agreement_rate)} · {judge.feedback_count} samples</p>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="rounded-lg border border-gray-200 bg-white p-5">
        <div className="mb-4 flex items-center gap-2">
          <Gauge className="h-4 w-4 text-gray-500" />
          <h3 className="text-sm font-semibold text-gray-900">Drift Reports</h3>
        </div>
        {drift.length === 0 ? (
          <div className="rounded-lg border border-dashed border-gray-200 bg-gray-50 p-4 text-sm text-gray-500">
            No drift reports available yet.
          </div>
        ) : (
          <div className="space-y-2">
            {drift.map((report) => (
              <div key={report.judge_id} className="rounded-lg border border-gray-200 bg-gray-50 p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-sm font-medium text-gray-900">{report.judge_id}</p>
                  <StatusBadge
                    variant={statusVariant(report.alert ? 'degraded' : 'active')}
                    label={report.alert ? 'alert' : 'stable'}
                  />
                </div>
                <p className="mt-1 text-xs text-gray-600">
                  Baseline {pct(report.baseline_agreement)} · Recent {pct(report.recent_agreement)} · Drift {report.drift_delta.toFixed(4)}
                </p>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="rounded-lg border border-gray-200 bg-white p-5">
        <div className="mb-4 flex items-center gap-2">
          <Scale className="h-4 w-4 text-gray-500" />
          <h3 className="text-sm font-semibold text-gray-900">Disagreement Queue</h3>
        </div>
        {calibration.disagreement_queue.length === 0 ? (
          <div className="rounded-lg border border-dashed border-gray-200 bg-gray-50 p-4 text-sm text-gray-500">
            No disagreement samples yet.
          </div>
        ) : (
          <div className="space-y-2">
            {calibration.disagreement_queue.slice(0, 10).map((item) => (
              <div key={item.feedback_id} className="rounded-lg border border-gray-200 bg-gray-50 p-3">
                <p className="text-sm font-medium text-gray-900">{item.case_id}</p>
                <p className="mt-1 text-xs text-gray-600">
                  {item.judge_id} · judge={item.judge_score.toFixed(3)} · human={item.human_score.toFixed(3)}
                </p>
                <p className="mt-1 text-xs text-gray-500">{formatTimestamp(item.created_at)}</p>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="rounded-lg border border-gray-200 bg-white p-5">
        <h3 className="mb-4 text-sm font-semibold text-gray-900">Submit Human Correction</h3>
        <div className="grid gap-3 sm:grid-cols-2">
          <input
            value={caseId}
            onChange={(event) => setCaseId(event.target.value)}
            placeholder="Case ID"
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          />
          <input
            value={judgeId}
            onChange={(event) => setJudgeId(event.target.value)}
            placeholder="Judge ID"
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          />
          <input
            type="number"
            min={0}
            max={1}
            step={0.01}
            value={judgeScore}
            onChange={(event) => setJudgeScore(Number(event.target.value))}
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          />
          <input
            type="number"
            min={0}
            max={1}
            step={0.01}
            value={humanScore}
            onChange={(event) => setHumanScore(Number(event.target.value))}
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          />
        </div>
        <textarea
          value={comment}
          onChange={(event) => setComment(event.target.value)}
          placeholder="Optional comment"
          rows={3}
          className="mt-3 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
        />
        <div className="mt-3 flex justify-end">
          <button
            onClick={submitFeedback}
            disabled={feedbackMutation.isPending}
            className="rounded-lg bg-gray-900 px-3.5 py-2 text-sm font-medium text-white transition hover:bg-gray-800 disabled:opacity-60"
          >
            {feedbackMutation.isPending ? 'Saving...' : 'Submit Correction'}
          </button>
        </div>
      </section>
    </div>
  );
}
