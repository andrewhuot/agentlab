import { useEffect, useRef } from 'react';
import type {
  ApprovalRequest,
  ArtifactRef,
  BuilderProposal,
  SpecialistRole,
} from '../../lib/builder-types';
import {
  ADKGraphDiffCard,
  ApprovalCard,
  BenchmarkCard,
  EvalCard,
  GuardrailCard,
  PlanCard,
  ReleaseCard,
  SkillCard,
  SourceDiffCard,
  TraceEvidenceCard,
} from './cards';

export interface ConversationEntry {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  specialist?: SpecialistRole;
  task_id?: string;
  proposal?: BuilderProposal;
  artifacts?: ArtifactRef[];
  approvals?: ApprovalRequest[];
  streaming?: boolean;
}

interface ConversationPaneProps {
  entries: ConversationEntry[];
  loading?: boolean;
  onSelectArtifact?: (artifact: ArtifactRef) => void;
  onOpenTask?: (taskId: string) => void;
  onApproveProposal?: (proposalId: string) => void;
  onRejectProposal?: (proposalId: string) => void;
  onReviseProposal?: (proposalId: string) => void;
  onApproveRequest?: (approvalId: string) => void;
  onRejectRequest?: (approvalId: string) => void;
}

export function ConversationPane({
  entries,
  loading = false,
  onSelectArtifact,
  onOpenTask,
  onApproveProposal,
  onRejectProposal,
  onReviseProposal,
  onApproveRequest,
  onRejectRequest,
}: ConversationPaneProps) {
  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [entries]);

  return (
    <section className="flex min-h-0 flex-col bg-slate-950/40">
      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-4">
        {entries.length === 0 ? (
          <EmptyConversationState />
        ) : (
          <div className="space-y-4">
            {entries.map((entry) => (
              <article key={entry.id} className="space-y-3">
                <div className="rounded-lg border border-slate-800 bg-slate-900/70 p-3">
                  <div className="flex items-center gap-2 text-[11px] uppercase tracking-wide text-slate-500">
                    <span>{entry.role}</span>
                    {entry.specialist ? <span>· {entry.specialist.replace('_', ' ')}</span> : null}
                    {entry.task_id && onOpenTask ? (
                      <button
                        type="button"
                        onClick={() => onOpenTask(entry.task_id!)}
                        className="rounded border border-slate-700 px-1.5 py-0.5 text-[10px] text-slate-300 transition hover:bg-slate-800"
                      >
                        {entry.task_id.slice(0, 8)}
                      </button>
                    ) : null}
                    {entry.streaming ? (
                      <span className="inline-flex items-center gap-1 text-sky-300">
                        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-sky-300" />
                        streaming
                      </span>
                    ) : null}
                  </div>
                  <p className="mt-1 whitespace-pre-wrap text-sm text-slate-200">{entry.content}</p>
                </div>

                {entry.proposal ? (
                  <PlanCard
                    proposal={entry.proposal}
                    onApprove={
                      onApproveProposal ? () => onApproveProposal(entry.proposal!.proposal_id) : undefined
                    }
                    onReject={
                      onRejectProposal ? () => onRejectProposal(entry.proposal!.proposal_id) : undefined
                    }
                    onRevise={
                      onReviseProposal ? () => onReviseProposal(entry.proposal!.proposal_id) : undefined
                    }
                  />
                ) : null}

                {(entry.approvals ?? []).map((approval) => (
                  <ApprovalCard
                    key={approval.approval_id}
                    approval={approval}
                    onApprove={
                      onApproveRequest ? () => onApproveRequest(approval.approval_id) : undefined
                    }
                    onReject={
                      onRejectRequest ? () => onRejectRequest(approval.approval_id) : undefined
                    }
                  />
                ))}

                {(entry.artifacts ?? []).map((artifact) => (
                  <button
                    key={artifact.artifact_id}
                    type="button"
                    onClick={() => onSelectArtifact?.(artifact)}
                    className="block w-full text-left"
                  >
                    <ArtifactRenderer artifact={artifact} />
                  </button>
                ))}
              </article>
            ))}
            {loading ? <LoadingSkeleton /> : null}
            <div ref={endRef} />
          </div>
        )}
      </div>
    </section>
  );
}

function ArtifactRenderer({ artifact }: { artifact: ArtifactRef }) {
  switch (artifact.artifact_type) {
    case 'plan':
      return (
        <PlanCard
          proposal={{
            proposal_id: artifact.artifact_id,
            task_id: artifact.task_id,
            session_id: artifact.session_id,
            project_id: artifact.project_id,
            goal: typeof artifact.payload.goal === 'string' ? artifact.payload.goal : artifact.title,
            assumptions: Array.isArray(artifact.payload.assumptions)
              ? (artifact.payload.assumptions as string[])
              : [],
            targeted_artifacts: Array.isArray(artifact.payload.targeted_artifacts)
              ? (artifact.payload.targeted_artifacts as string[])
              : [],
            targeted_surfaces: [],
            expected_impact:
              typeof artifact.payload.expected_impact === 'string'
                ? artifact.payload.expected_impact
                : artifact.summary,
            risk_level:
              typeof artifact.payload.risk_level === 'string'
                ? (artifact.payload.risk_level as 'low' | 'medium' | 'high' | 'critical')
                : 'medium',
            required_approvals: Array.isArray(artifact.payload.required_approvals)
              ? (artifact.payload.required_approvals as string[])
              : [],
            steps: [],
            created_at: artifact.created_at,
            updated_at: artifact.updated_at,
            status: 'pending',
            accepted: false,
            rejected: false,
            revision_count: 0,
            revision_comments: [],
          }}
        />
      );
    case 'source_diff':
      return <SourceDiffCard artifact={artifact} />;
    case 'adk_graph_diff':
      return <ADKGraphDiffCard artifact={artifact} />;
    case 'skill':
      return <SkillCard artifact={artifact} />;
    case 'guardrail':
      return <GuardrailCard artifact={artifact} />;
    case 'eval':
      return <EvalCard artifact={artifact} />;
    case 'trace_evidence':
      return <TraceEvidenceCard artifact={artifact} />;
    case 'benchmark':
      return <BenchmarkCard artifact={artifact} />;
    case 'release':
      return <ReleaseCard artifact={artifact} />;
    default:
      return null;
  }
}

function EmptyConversationState() {
  return (
    <div className="flex h-full items-center justify-center rounded-xl border border-dashed border-slate-700 bg-slate-900/40">
      <div className="max-w-md p-6 text-center">
        <p className="text-base font-semibold text-slate-200">Start Building</p>
        <p className="mt-2 text-sm text-slate-500">
          Ask for a plan, run a trace diagnosis, or request an apply/delegate task.
        </p>
      </div>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/70 p-3">
      <div className="h-3 w-24 animate-pulse rounded bg-slate-700" />
      <div className="mt-2 h-3 w-full animate-pulse rounded bg-slate-800" />
      <div className="mt-1 h-3 w-2/3 animate-pulse rounded bg-slate-800" />
    </div>
  );
}
