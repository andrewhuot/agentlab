import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

const API_BASE = '/api';

async function fetchApi<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

// Types
interface SkillGap {
  gap_id: string;
  gap_type: string;
  description: string;
  evidence: string[];
  failure_family: string;
  frequency: number;
  impact_score: number;
  suggested_name: string;
  suggested_platform: string;
}

interface GeneratedFile {
  path: string;
  content: string;
  is_new: boolean;
  diff: string | null;
}

interface GeneratedSkill {
  skill_id: string;
  gap_id: string;
  platform: string;
  skill_type: string;
  name: string;
  description: string;
  source_code: string | null;
  config_yaml: string | null;
  files: GeneratedFile[];
  eval_criteria: Array<Record<string, unknown>>;
  estimated_improvement: number;
  confidence: string;
  status: string;
  review_notes: string;
  created_at: number;
}

// Hooks
function useSkillGaps() {
  return useQuery<{ gaps: SkillGap[]; count: number }>({
    queryKey: ['agentSkillGaps'],
    queryFn: () => fetchApi('/agent-skills/gaps'),
  });
}

function useGeneratedSkills(status?: string) {
  return useQuery<{ skills: GeneratedSkill[]; count: number }>({
    queryKey: ['agentSkills', status],
    queryFn: () => fetchApi(`/agent-skills/${status ? `?status=${status}` : ''}`),
  });
}

function useAnalyzeGaps() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => fetchApi('/agent-skills/analyze', { method: 'POST' }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['agentSkillGaps'] });
    },
  });
}

function useGenerateSkills() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (gapId?: string) =>
      fetchApi('/agent-skills/generate', {
        method: 'POST',
        body: JSON.stringify(gapId ? { gap_id: gapId } : {}),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['agentSkills'] });
    },
  });
}

function useApproveSkill() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (skillId: string) =>
      fetchApi(`/agent-skills/${skillId}/approve`, { method: 'POST' }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['agentSkills'] });
    },
  });
}

function useRejectSkill() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ skillId, reason }: { skillId: string; reason: string }) =>
      fetchApi(`/agent-skills/${skillId}/reject`, {
        method: 'POST',
        body: JSON.stringify({ reason }),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['agentSkills'] });
    },
  });
}

// Components
function ConfidenceBadge({ confidence }: { confidence: string }) {
  const colors: Record<string, string> = {
    high: 'bg-green-100 text-green-700',
    medium: 'bg-yellow-100 text-yellow-700',
    low: 'bg-red-100 text-red-700',
  };
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${colors[confidence] ?? 'bg-gray-100 text-gray-700'}`}>
      {confidence}
    </span>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    draft: 'bg-gray-100 text-gray-700',
    approved: 'bg-green-100 text-green-700',
    rejected: 'bg-red-100 text-red-700',
    deployed: 'bg-blue-100 text-blue-700',
  };
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${colors[status] ?? 'bg-gray-100 text-gray-700'}`}>
      {status}
    </span>
  );
}

function GapCard({ gap, onGenerate }: { gap: SkillGap; onGenerate: (id: string) => void }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <div className="flex items-start justify-between">
        <div className="min-w-0 flex-1">
          <h3 className="text-sm font-medium text-gray-900">{gap.suggested_name}</h3>
          <p className="mt-1 text-xs text-gray-500">{gap.description}</p>
        </div>
        <span className="ml-2 inline-flex items-center rounded-full bg-orange-100 px-2 py-0.5 text-xs font-medium text-orange-700">
          {gap.gap_type.replace(/_/g, ' ')}
        </span>
      </div>
      <div className="mt-3 flex items-center gap-4 text-xs text-gray-500">
        <span>Frequency: <strong className="text-gray-700">{gap.frequency}</strong></span>
        <span>Impact: <strong className="text-gray-700">{(gap.impact_score * 100).toFixed(0)}%</strong></span>
        <span>Evidence: <strong className="text-gray-700">{gap.evidence.length}</strong></span>
        <span>Platform: <strong className="text-gray-700">{gap.suggested_platform}</strong></span>
      </div>
      <div className="mt-3 flex justify-end">
        <button
          onClick={() => onGenerate(gap.gap_id)}
          className="rounded-md bg-gray-900 px-3 py-1.5 text-xs font-medium text-white hover:bg-gray-800"
        >
          Generate Skill
        </button>
      </div>
    </div>
  );
}

function SkillCard({ skill }: { skill: GeneratedSkill }) {
  const [expanded, setExpanded] = useState(false);
  const approve = useApproveSkill();
  const reject = useRejectSkill();

  const code = skill.source_code ?? skill.config_yaml ?? '';

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <div className="flex items-start justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-medium text-gray-900">{skill.name}</h3>
            <StatusBadge status={skill.status} />
            <ConfidenceBadge confidence={skill.confidence} />
          </div>
          <p className="mt-1 text-xs text-gray-500">{skill.description}</p>
        </div>
        <span className="ml-2 text-xs text-gray-400">{skill.platform} / {skill.skill_type}</span>
      </div>

      <div className="mt-3 flex items-center gap-4 text-xs text-gray-500">
        <span>Est. improvement: <strong className="text-gray-700">{(skill.estimated_improvement * 100).toFixed(0)}%</strong></span>
        <span>Files: <strong className="text-gray-700">{skill.files.length}</strong></span>
      </div>

      {code && (
        <div className="mt-3">
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-xs font-medium text-blue-600 hover:text-blue-500"
          >
            {expanded ? 'Hide code' : 'Show code'}
          </button>
          {expanded && (
            <pre className="mt-2 max-h-80 overflow-auto rounded-md bg-gray-50 p-3 text-xs text-gray-800">
              <code>{code}</code>
            </pre>
          )}
        </div>
      )}

      {skill.review_notes && (
        <p className="mt-2 text-xs italic text-gray-400">{skill.review_notes}</p>
      )}

      {skill.status === 'draft' && (
        <div className="mt-3 flex gap-2">
          <button
            onClick={() => approve.mutate(skill.skill_id)}
            disabled={approve.isPending}
            className="rounded-md bg-green-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-green-500 disabled:opacity-50"
          >
            {approve.isPending ? 'Approving...' : 'Approve'}
          </button>
          <button
            onClick={() => reject.mutate({ skillId: skill.skill_id, reason: 'Rejected from UI' })}
            disabled={reject.isPending}
            className="rounded-md bg-red-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-red-500 disabled:opacity-50"
          >
            {reject.isPending ? 'Rejecting...' : 'Reject'}
          </button>
        </div>
      )}
    </div>
  );
}

// Main page
export function AgentSkills() {
  const gaps = useSkillGaps();
  const skills = useGeneratedSkills();
  const analyzeGaps = useAnalyzeGaps();
  const generateSkills = useGenerateSkills();

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Agent Skill Generation</h2>
          <p className="mt-1 text-sm text-gray-500">
            Identify capability gaps and generate new skills for your agent.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => analyzeGaps.mutate()}
            disabled={analyzeGaps.isPending}
            className="rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800 disabled:opacity-50"
          >
            {analyzeGaps.isPending ? 'Analyzing...' : 'Analyze Gaps'}
          </button>
        </div>
      </div>

      {/* Gaps Section */}
      <section>
        <h3 className="mb-3 text-sm font-semibold text-gray-700">Identified Gaps</h3>
        {gaps.isLoading ? (
          <p className="text-sm text-gray-400">Loading gaps...</p>
        ) : gaps.data?.gaps.length === 0 ? (
          <p className="text-sm text-gray-400">No gaps identified yet. Run gap analysis to get started.</p>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            {gaps.data?.gaps.map((gap) => (
              <GapCard key={gap.gap_id} gap={gap} onGenerate={(id) => generateSkills.mutate(id)} />
            ))}
          </div>
        )}
      </section>

      {/* Generated Skills Section */}
      <section>
        <h3 className="mb-3 text-sm font-semibold text-gray-700">
          Generated Skills
          {skills.data?.count ? (
            <span className="ml-2 text-xs font-normal text-gray-400">({skills.data.count})</span>
          ) : null}
        </h3>
        {skills.isLoading ? (
          <p className="text-sm text-gray-400">Loading skills...</p>
        ) : skills.data?.skills.length === 0 ? (
          <p className="text-sm text-gray-400">No skills generated yet.</p>
        ) : (
          <div className="space-y-3">
            {skills.data?.skills.map((skill) => (
              <SkillCard key={skill.skill_id} skill={skill} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
