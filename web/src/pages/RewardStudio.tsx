import { useState, useEffect } from 'react';
import { Award, Plus, Shield, AlertTriangle, CheckCircle, X, Play } from 'lucide-react';
import { PageHeader } from '../components/PageHeader';
import { StatusBadge } from '../components/StatusBadge';
import { classNames } from '../lib/utils';

const API_BASE = '/api';

interface Reward {
  name: string;
  kind: string;
  scope: string;
  granularity: string;
  source: string;
  trust_tier: number;
  weight: number;
  hard_gate: boolean;
  created_at?: string;
  version?: number;
}

interface AuditFinding {
  severity: 'critical' | 'warning' | 'info';
  message: string;
}

interface AuditResult {
  reward_name: string;
  findings: AuditFinding[];
  passed: boolean;
}

interface ChallengeReport {
  suite: string;
  passed: number;
  total: number;
  failures: string[];
}

interface RawReward {
  name?: string;
  kind?: string;
  scope?: string;
  granularity?: string;
  source?: string;
  trust_tier?: number;
  weight?: number;
  hard_gate?: boolean;
  created_at?: string;
  version?: number;
}

async function fetchJson<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json() as Promise<T>;
}

const trustTierColors: Record<string, string> = {
  high: 'bg-green-50 text-green-700 border-green-200',
  medium: 'bg-amber-50 text-amber-700 border-amber-200',
  low: 'bg-red-50 text-red-700 border-red-200',
};

const severityIcon = {
  critical: <AlertTriangle className="h-3.5 w-3.5 text-red-500" />,
  warning: <AlertTriangle className="h-3.5 w-3.5 text-amber-500" />,
  info: <CheckCircle className="h-3.5 w-3.5 text-blue-500" />,
};

const rewardOptions = {
  kind: ['verifiable', 'preference', 'business_outcome', 'constitutional'],
  scope: ['runtime', 'buildtime', 'multi_agent'],
  granularity: ['step', 'trajectory', 'episode', 'delayed_outcome'],
  source: ['deterministic_checker', 'environment_checker', 'human_label', 'llm_judge', 'ai_preference'],
} as const;

const defaultForm: Omit<Reward, 'name'> & { name: string } = {
  name: '',
  kind: 'verifiable',
  scope: 'runtime',
  granularity: 'step',
  source: 'deterministic_checker',
  trust_tier: 3,
  weight: 1.0,
  hard_gate: false,
};

function normalizeReward(raw: RawReward): Reward {
  return {
    name: raw.name ?? 'unnamed',
    kind: raw.kind ?? 'verifiable',
    scope: raw.scope ?? 'runtime',
    granularity: raw.granularity ?? 'step',
    source: raw.source ?? 'deterministic_checker',
    trust_tier: raw.trust_tier ?? 3,
    weight: raw.weight ?? 1,
    hard_gate: Boolean(raw.hard_gate),
    created_at: raw.created_at,
    version: raw.version,
  };
}

function normalizeTrustTier(value: number): 'high' | 'medium' | 'low' {
  if (value <= 2) {
    return 'high';
  }
  if (value === 3) {
    return 'medium';
  }
  return 'low';
}

function trustTierLabel(value: number): string {
  return `tier ${value}`;
}

function normalizeAuditResult(payload: unknown): AuditResult {
  const data = (typeof payload === 'object' && payload !== null)
    ? payload as {
        reward_name?: string;
        findings?: Array<{ severity?: AuditFinding['severity']; description?: string; message?: string }>;
        pass_rate?: number;
      }
    : {};
  const findings = Array.isArray(data.findings) ? data.findings : [];

  return {
    reward_name: data.reward_name ?? '',
    findings: findings.map((finding) => ({
      severity: finding.severity ?? 'info',
      message: finding.description ?? finding.message ?? 'No details provided.',
    })),
    passed: findings.length === 0 || (data.pass_rate ?? 0) >= 1,
  };
}

function normalizeChallengeReport(payload: unknown): ChallengeReport {
  const data = (typeof payload === 'object' && payload !== null)
    ? payload as {
        reports?: Array<{
          suite_name?: string;
          passed?: number;
          total_probes?: number;
          findings?: Array<{ description?: string; message?: string }>;
          results?: Array<{ passed?: boolean; details?: string }>;
        }>;
      }
    : {};
  const reports = Array.isArray(data.reports) ? data.reports : [];
  const total = reports.reduce((sum, report) => sum + (report.total_probes ?? 0), 0);
  const passed = reports.reduce((sum, report) => sum + (report.passed ?? 0), 0);
  const failures = reports.flatMap((report) => {
    const fromFindings = Array.isArray(report.findings)
      ? report.findings
          .map((finding) => finding.description ?? finding.message ?? '')
          .filter((entry): entry is string => entry.length > 0)
      : [];
    const fromResults = Array.isArray(report.results)
      ? report.results
          .filter((result) => result.passed === false && typeof result.details === 'string')
          .map((result) => result.details as string)
      : [];
    return [...fromFindings, ...fromResults];
  });

  return {
    suite: reports.length === 1 ? reports[0]?.suite_name ?? 'challenge' : 'all suites',
    passed,
    total,
    failures,
  };
}

export function RewardStudio() {
  const [rewards, setRewards] = useState<Reward[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ ...defaultForm });
  const [creating, setCreating] = useState(false);

  const [selected, setSelected] = useState<Reward | null>(null);
  const [auditResult, setAuditResult] = useState<AuditResult | null>(null);
  const [auditing, setAuditing] = useState(false);

  const [challengeReport, setChallengeReport] = useState<ChallengeReport | null>(null);
  const [running, setRunning] = useState(false);

  async function loadRewards(selectedName?: string) {
    setLoading(true);
    try {
      const payload = await fetchJson<{ rewards?: RawReward[] }>('/rewards');
      const nextRewards = (payload.rewards ?? []).map(normalizeReward);
      setRewards(nextRewards);
      if (selectedName) {
        setSelected(nextRewards.find((reward) => reward.name === selectedName) ?? null);
      }
      setError(null);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadRewards();
  }, []);

  async function createReward() {
    if (!form.name.trim()) return;
    setCreating(true);
    try {
      await fetchJson('/rewards', {
        method: 'POST',
        body: JSON.stringify(form),
      });
      await loadRewards(form.name);
      setForm({ ...defaultForm });
      setShowForm(false);
      setError(null);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to create reward');
    } finally {
      setCreating(false);
    }
  }

  async function runAudit(reward: Reward) {
    setAuditing(true);
    setAuditResult(null);
    try {
      const payload = await fetchJson<unknown>(`/rewards/${reward.name}/audit`, { method: 'POST' });
      setAuditResult(normalizeAuditResult(payload));
      setError(null);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to audit reward');
    } finally {
      setAuditing(false);
    }
  }

  async function runChallenge() {
    setRunning(true);
    setChallengeReport(null);
    try {
      const payload = await fetchJson<unknown>('/rewards/challenge/run', { method: 'POST' });
      setChallengeReport(normalizeChallengeReport(payload));
      setError(null);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to run challenge suite');
    } finally {
      setRunning(false);
    }
  }

  function field(key: keyof typeof form, value: string | number | boolean) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Reward Studio"
        description="Define, audit, and validate reward functions that drive RLHF training and policy optimization."
        actions={
          <button
            onClick={() => setShowForm(true)}
            className="inline-flex items-center gap-2 rounded-lg bg-gray-900 px-3.5 py-2 text-sm font-medium text-white transition hover:bg-gray-800"
          >
            <Plus className="h-4 w-4" />
            New Reward
          </button>
        }
      />

      {/* Create form */}
      {showForm && (
        <section className="rounded-lg border border-gray-200 bg-white p-5">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-900">Create Reward</h3>
            <button
              onClick={() => setShowForm(false)}
              className="rounded p-1 text-gray-500 hover:bg-gray-100"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <div className="sm:col-span-2">
              <label className="mb-1 block text-xs text-gray-500">Name *</label>
              <input
                value={form.name}
                onChange={(e) => field('name', e.target.value)}
                placeholder="e.g. helpfulness_v2"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
              />
            </div>
            {(['kind', 'scope', 'granularity', 'source'] as const).map((key) => (
              <div key={key}>
                <label className="mb-1 block text-xs capitalize text-gray-500">{key}</label>
                <select
                  value={form[key]}
                  onChange={(e) => field(key, e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                >
                  {rewardOptions[key].map((option) => (
                    <option key={option} value={option}>{option}</option>
                  ))}
                </select>
              </div>
            ))}
            <div>
              <label className="mb-1 block text-xs text-gray-500">Trust Tier</label>
              <select
                value={form.trust_tier}
                onChange={(e) => field('trust_tier', parseInt(e.target.value, 10))}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
              >
                <option value={1}>tier 1</option>
                <option value={2}>tier 2</option>
                <option value={3}>tier 3</option>
                <option value={4}>tier 4</option>
                <option value={5}>tier 5</option>
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs text-gray-500">Weight</label>
              <input
                type="number"
                step="0.1"
                min="0"
                value={form.weight}
                onChange={(e) => field('weight', parseFloat(e.target.value))}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
              />
            </div>
            <div className="flex items-end pb-1">
              <label className="flex cursor-pointer items-center gap-2 text-sm text-gray-700">
                <input
                  type="checkbox"
                  checked={form.hard_gate}
                  onChange={(e) => field('hard_gate', e.target.checked)}
                  className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                Hard Gate
              </label>
            </div>
          </div>
          <div className="mt-4 flex justify-end">
            <button
              onClick={createReward}
              disabled={creating || !form.name.trim()}
              className="rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-gray-800 disabled:opacity-60"
            >
              {creating ? 'Creating...' : 'Create Reward'}
            </button>
          </div>
        </section>
      )}

      {/* Error */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Reward grid */}
      <section>
        {loading ? (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-32 animate-pulse rounded-lg border border-gray-200 bg-gray-100" />
            ))}
          </div>
        ) : rewards.length === 0 ? (
          <div className="flex h-40 items-center justify-center rounded-lg border border-dashed border-gray-200 bg-gray-50 text-sm text-gray-500">
            No rewards defined yet. Create one to get started.
          </div>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {rewards.map((r) => (
              <button
                key={r.name}
                onClick={() => { setSelected(r); setAuditResult(null); }}
                className={classNames(
                  'rounded-lg border p-4 text-left transition-colors',
                  selected?.name === r.name
                    ? 'border-blue-300 bg-blue-50'
                    : 'border-gray-200 bg-white hover:bg-gray-50'
                )}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Award className="h-4 w-4 text-gray-400" />
                    <span className="text-sm font-medium text-gray-900">{r.name}</span>
                  </div>
                  {r.hard_gate && (
                    <span className="flex items-center gap-1 rounded border border-red-200 bg-red-50 px-1.5 py-0.5 text-[10px] font-medium text-red-700">
                      <Shield className="h-3 w-3" /> gate
                    </span>
                  )}
                </div>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  <span className="rounded bg-gray-100 px-1.5 py-0.5 text-[11px] text-gray-600">{r.kind}</span>
                  <span className="rounded bg-gray-100 px-1.5 py-0.5 text-[11px] text-gray-600">{r.scope}</span>
                  <span
                    className={classNames(
                      'rounded border px-1.5 py-0.5 text-[11px] font-medium',
                      trustTierColors[normalizeTrustTier(r.trust_tier)] ?? 'bg-gray-50 text-gray-700 border-gray-200'
                    )}
                  >
                    {trustTierLabel(r.trust_tier)}
                  </span>
                </div>
                <p className="mt-2 text-xs text-gray-500">weight: {r.weight} · source: {r.source}</p>
              </button>
            ))}
          </div>
        )}
      </section>

      {/* Detail panel */}
      {selected && (
        <section className="rounded-lg border border-gray-200 bg-white p-5">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-900">Reward: {selected.name}</h3>
            <div className="flex gap-2">
              <button
                onClick={() => runAudit(selected)}
                disabled={auditing}
                className="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 transition hover:bg-gray-50 disabled:opacity-60"
              >
                <Shield className="h-3.5 w-3.5" />
                {auditing ? 'Auditing...' : 'Run Audit'}
              </button>
              <button
                onClick={runChallenge}
                disabled={running}
                className="inline-flex items-center gap-1.5 rounded-lg bg-gray-900 px-3 py-1.5 text-xs font-medium text-white transition hover:bg-gray-800 disabled:opacity-60"
              >
                <Play className="h-3.5 w-3.5" />
                {running ? 'Running...' : 'Challenge Suite'}
              </button>
            </div>
          </div>
          <dl className="grid gap-2 sm:grid-cols-4 text-sm">
            {(['kind', 'scope', 'granularity', 'source', 'trust_tier', 'weight'] as const).map((k) => (
              <div key={k} className="rounded-lg border border-gray-100 bg-gray-50 p-3">
                <dt className="text-xs text-gray-500 capitalize">{k.replace('_', ' ')}</dt>
                <dd className="mt-0.5 font-medium text-gray-900">{String(selected[k])}</dd>
              </div>
            ))}
            <div className="rounded-lg border border-gray-100 bg-gray-50 p-3">
              <dt className="text-xs text-gray-500">Hard Gate</dt>
              <dd className="mt-0.5 font-medium text-gray-900">{selected.hard_gate ? 'Yes' : 'No'}</dd>
            </div>
          </dl>

          {/* Audit results */}
          {auditResult && (
            <div className="mt-4">
              <div className="mb-2 flex items-center gap-2">
                <StatusBadge variant={auditResult.passed ? 'success' : 'error'} label={auditResult.passed ? 'passed' : 'failed'} />
                <span className="text-sm font-medium text-gray-900">Audit Findings</span>
              </div>
              {auditResult.findings.length === 0 ? (
                <p className="text-xs text-gray-500">No findings — reward definition looks clean.</p>
              ) : (
                <div className="space-y-1.5">
                  {auditResult.findings.map((f, i) => (
                    <div key={i} className="flex items-start gap-2 rounded-lg border border-gray-100 bg-gray-50 px-3 py-2">
                      {severityIcon[f.severity]}
                      <p className="text-xs text-gray-700">{f.message}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Challenge report */}
          {challengeReport && (
            <div className="mt-4 rounded-lg border border-gray-200 bg-gray-50 p-4">
              <div className="mb-2 flex items-center justify-between">
                <span className="text-sm font-medium text-gray-900">Challenge Suite: {challengeReport.suite}</span>
                <StatusBadge
                  variant={challengeReport.passed === challengeReport.total ? 'success' : 'warning'}
                  label={`${challengeReport.passed}/${challengeReport.total} passed`}
                />
              </div>
              {challengeReport.failures.length > 0 && (
                <ul className="space-y-1 text-xs text-red-700">
                  {challengeReport.failures.map((f, i) => <li key={i}>• {f}</li>)}
                </ul>
              )}
            </div>
          )}
        </section>
      )}
    </div>
  );
}

export default RewardStudio;
