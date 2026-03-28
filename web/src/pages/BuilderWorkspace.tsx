import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Composer,
  ConversationPane,
  Inspector,
  LeftRail,
  TaskDrawer,
  TopBar,
} from '../components/builder';
import type { ConversationEntry } from '../components/builder';
import type { InspectorTabId } from '../components/builder/Inspector';
import type { BuilderEnvironment } from '../components/builder/TopBar';
import type {
  ApprovalRequest,
  ArtifactRef,
  BuilderEvent,
  BuilderProposal,
  BuilderProject,
  BuilderSession,
  BuilderTask,
  EvalBundle,
  ExecutionMode,
  PermissionGrant,
  TraceBookmark,
} from '../lib/builder-types';
import { builderApi, BuilderApiError } from '../lib/builder-api';
import { builderWsClient } from '../lib/builder-websocket';

const DEFAULT_MODEL_OPTIONS = [
  'gpt-5.4',
  'gpt-5.4-mini',
  'claude-sonnet-4-6',
];

function toEventEntry(event: BuilderEvent): ConversationEntry {
  const payload = event.payload as Record<string, unknown>;
  const step = typeof payload.current_step === 'string' ? payload.current_step : '';
  const summary = typeof payload.status === 'string' ? payload.status : event.event_type;
  return {
    id: `evt-${event.event_id}`,
    role: 'system',
    content: step ? `${summary}: ${step}` : summary,
    task_id: event.task_id ?? undefined,
  };
}

function mapArtifactToInspectorTab(artifact: ArtifactRef): InspectorTabId {
  switch (artifact.artifact_type) {
    case 'source_diff':
      return 'diff';
    case 'adk_graph_diff':
      return 'adk_graph';
    case 'eval':
    case 'benchmark':
      return 'evals';
    case 'trace_evidence':
      return 'traces';
    case 'skill':
      return 'skills';
    case 'guardrail':
      return 'guardrails';
    case 'release':
      return 'config';
    default:
      return 'overview';
  }
}

export function BuilderWorkspace() {
  const [leftCollapsed, setLeftCollapsed] = useState(false);
  const [inspectorCollapsed, setInspectorCollapsed] = useState(false);
  const [taskDrawerOpen, setTaskDrawerOpen] = useState(false);

  const [mode, setMode] = useState<ExecutionMode>('draft');
  const [environment, setEnvironment] = useState<BuilderEnvironment>('dev');
  const [model, setModel] = useState(DEFAULT_MODEL_OPTIONS[0]);
  const [paused, setPaused] = useState(false);

  const [projects, setProjects] = useState<BuilderProject[]>([]);
  const [sessions, setSessions] = useState<BuilderSession[]>([]);
  const [tasks, setTasks] = useState<BuilderTask[]>([]);
  const [proposals, setProposals] = useState<BuilderProposal[]>([]);
  const [artifacts, setArtifacts] = useState<ArtifactRef[]>([]);
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([]);
  const [grants, setGrants] = useState<PermissionGrant[]>([]);

  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);

  const [selectedArtifact, setSelectedArtifact] = useState<ArtifactRef | null>(null);
  const [inspectorTab, setInspectorTab] = useState<InspectorTabId>('overview');

  const [traceBookmarks] = useState<TraceBookmark[]>([]);
  const [evalBundle] = useState<EvalBundle | null>(null);

  const [draft, setDraft] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [localEntries, setLocalEntries] = useState<ConversationEntry[]>([]);

  const selectedProject = useMemo(
    () => projects.find((project) => project.project_id === selectedProjectId) ?? null,
    [projects, selectedProjectId]
  );

  const loadProjects = useCallback(async (): Promise<BuilderProject[]> => {
    const existingProjects = await builderApi.projects.list(false);
    if (existingProjects.length > 0) {
      setProjects(existingProjects);
      return existingProjects;
    }

    const created = await builderApi.projects.create({
      name: 'Builder Workspace',
      description: 'Primary workspace for agent authoring',
      root_path: '.',
      master_instruction: 'Optimize for safe, reviewable changes.',
    });
    setProjects([created]);
    return [created];
  }, []);

  const loadProjectContext = useCallback(
    async (projectId: string) => {
      const [sessionList, taskList, grantList] = await Promise.all([
        builderApi.sessions.list(projectId),
        builderApi.tasks.list({ projectId }),
        builderApi.permissions.listGrants({ projectId }),
      ]);

      setSessions(sessionList);
      setTasks(taskList);
      setGrants(grantList);

      if (sessionList.length > 0) {
        setSelectedSessionId((current) =>
          current && sessionList.some((session) => session.session_id === current)
            ? current
            : sessionList[0].session_id
        );
      } else {
        setSelectedSessionId(null);
      }
    },
    []
  );

  const loadSessionContext = useCallback(async (sessionId: string) => {
    const [taskList, artifactList, approvalList, proposalList, events] = await Promise.all([
      builderApi.tasks.list({ sessionId }),
      builderApi.artifacts.list({ sessionId }),
      builderApi.approvals.list({ sessionId }),
      builderApi.proposals.list(),
      builderApi.events.list({ sessionId }),
    ]);

    setTasks(taskList);
    setArtifacts(artifactList);
    setApprovals(approvalList);
    setProposals(proposalList.filter((proposal) => proposal.session_id === sessionId));
    setLocalEntries((current) => {
      const eventEntries = events.map(toEventEntry);
      const dedupe = new Map<string, ConversationEntry>();
      [...current, ...eventEntries].forEach((entry) => {
        dedupe.set(entry.id, entry);
      });
      return Array.from(dedupe.values());
    });
  }, []);

  useEffect(() => {
    let cancelled = false;

    const initialize = async () => {
      setLoading(true);
      setError(null);
      try {
        const list = await loadProjects();
        if (cancelled) return;

        const chosen = list[0]?.project_id ?? null;
        setSelectedProjectId((current) => current ?? chosen);
        if (chosen) {
          await loadProjectContext(chosen);
        }
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : 'Failed to load workspace data');
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    void initialize();

    return () => {
      cancelled = true;
    };
  }, [loadProjectContext, loadProjects]);

  useEffect(() => {
    if (!selectedProjectId) return;

    void loadProjectContext(selectedProjectId).catch((err) => {
      setError(err instanceof Error ? err.message : 'Failed to load project context');
    });
  }, [selectedProjectId, loadProjectContext]);

  useEffect(() => {
    if (!selectedSessionId) {
      setArtifacts([]);
      setApprovals([]);
      setProposals([]);
      return;
    }

    void loadSessionContext(selectedSessionId).catch((err) => {
      setError(err instanceof Error ? err.message : 'Failed to load session context');
    });
  }, [selectedSessionId, loadSessionContext]);

  useEffect(() => {
    if (!selectedSessionId) return;

    builderWsClient.connect({ sessionId: selectedSessionId });
    const unsubscribe = builderWsClient.on('*', (event) => {
      setLocalEntries((current) => [...current, toEventEntry(event)]);
      void loadSessionContext(selectedSessionId);
    });

    return () => {
      unsubscribe();
      builderWsClient.disconnect();
    };
  }, [selectedSessionId, loadSessionContext]);

  const ensureSession = useCallback(async (): Promise<string | null> => {
    if (selectedSessionId) return selectedSessionId;
    if (!selectedProjectId) return null;

    const created = await builderApi.sessions.create({
      project_id: selectedProjectId,
      title: `Session ${new Date().toLocaleString()}`,
      mode,
    });
    setSessions((current) => [created, ...current]);
    setSelectedSessionId(created.session_id);
    return created.session_id;
  }, [mode, selectedProjectId, selectedSessionId]);

  const refreshSession = useCallback(async () => {
    if (!selectedSessionId) return;
    await loadSessionContext(selectedSessionId);
  }, [selectedSessionId, loadSessionContext]);

  const handleSubmit = useCallback(async () => {
    const text = draft.trim();
    if (!text || paused || !selectedProjectId) return;

    setDraft('');
    setError(null);
    setLocalEntries((current) => [
      ...current,
      {
        id: `user-${Date.now()}`,
        role: 'user',
        content: text,
      },
    ]);

    setLoading(true);
    try {
      const sessionId = await ensureSession();
      if (!sessionId) {
        throw new Error('No active session available for task creation');
      }

      const task = await builderApi.tasks.create({
        project_id: selectedProjectId,
        session_id: sessionId,
        title: text.slice(0, 72),
        description: text,
        mode,
      });

      await builderApi.tasks.progress(task.task_id, {
        progress: 10,
        current_step: 'Request routed to specialist',
        specialist_message: text,
      });

      setSelectedTaskId(task.task_id);
      setTaskDrawerOpen(true);
      setLocalEntries((current) => [
        ...current,
        {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          content: `Task created in ${mode} mode. I am generating a plan and initial artifacts.`,
          specialist: task.active_specialist,
          task_id: task.task_id,
          streaming: true,
        },
      ]);

      await loadSessionContext(sessionId);
    } catch (err) {
      const message = err instanceof BuilderApiError ? err.message : 'Failed to create builder task';
      setError(message);
      setLocalEntries((current) => [
        ...current,
        {
          id: `error-${Date.now()}`,
          role: 'system',
          content: message,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }, [draft, paused, selectedProjectId, ensureSession, mode, loadSessionContext]);

  const handleSelectArtifact = useCallback((artifact: ArtifactRef) => {
    setSelectedArtifact(artifact);
    setInspectorCollapsed(false);
    setInspectorTab(mapArtifactToInspectorTab(artifact));
  }, []);

  const handleApproveProposal = useCallback(
    async (proposalId: string) => {
      await builderApi.proposals.approve(proposalId);
      await refreshSession();
    },
    [refreshSession]
  );

  const handleRejectProposal = useCallback(
    async (proposalId: string) => {
      await builderApi.proposals.reject(proposalId);
      await refreshSession();
    },
    [refreshSession]
  );

  const handleReviseProposal = useCallback(
    async (proposalId: string) => {
      await builderApi.proposals.revise(proposalId, 'Please revise with lower risk and narrower scope.');
      await refreshSession();
    },
    [refreshSession]
  );

  const handleRespondApproval = useCallback(
    async (approvalId: string, approved: boolean) => {
      await builderApi.approvals.respond(approvalId, {
        approved,
        responder: 'user',
        note: approved ? 'Approved from workspace drawer' : 'Rejected from workspace drawer',
      });
      await refreshSession();
      if (selectedProjectId) {
        const grantList = await builderApi.permissions.listGrants({ projectId: selectedProjectId });
        setGrants(grantList);
      }
    },
    [refreshSession, selectedProjectId]
  );

  const handlePauseTask = useCallback(
    async (taskId: string) => {
      await builderApi.tasks.pause(taskId);
      await refreshSession();
    },
    [refreshSession]
  );

  const handleResumeTask = useCallback(
    async (taskId: string) => {
      await builderApi.tasks.resume(taskId);
      await refreshSession();
    },
    [refreshSession]
  );

  const handleCancelTask = useCallback(
    async (taskId: string) => {
      await builderApi.tasks.cancel(taskId);
      await refreshSession();
    },
    [refreshSession]
  );

  const handleForkTask = useCallback(
    async (taskId: string) => {
      await builderApi.tasks.fork(taskId);
      await refreshSession();
    },
    [refreshSession]
  );

  const taskEntries = useMemo<ConversationEntry[]>(() => {
    const artifactsByTask = new Map<string, ArtifactRef[]>();
    artifacts.forEach((artifact) => {
      const existing = artifactsByTask.get(artifact.task_id) ?? [];
      existing.push(artifact);
      artifactsByTask.set(artifact.task_id, existing);
    });

    const approvalsByTask = new Map<string, ApprovalRequest[]>();
    approvals.forEach((approval) => {
      const existing = approvalsByTask.get(approval.task_id) ?? [];
      existing.push(approval);
      approvalsByTask.set(approval.task_id, existing);
    });

    const proposalByTask = new Map<string, BuilderProposal>();
    proposals.forEach((proposal) => {
      if (!proposalByTask.has(proposal.task_id)) {
        proposalByTask.set(proposal.task_id, proposal);
      }
    });

    return tasks
      .slice()
      .sort((a, b) => a.created_at - b.created_at)
      .map((task) => ({
        id: `task-${task.task_id}`,
        role: 'assistant',
        content: task.description || task.title,
        specialist: task.active_specialist,
        task_id: task.task_id,
        proposal: proposalByTask.get(task.task_id),
        artifacts: artifactsByTask.get(task.task_id) ?? [],
        approvals: approvalsByTask.get(task.task_id) ?? [],
      }));
  }, [approvals, artifacts, proposals, tasks]);

  const timelineEntries = useMemo(() => {
    const dedupe = new Map<string, ConversationEntry>();
    [...localEntries, ...taskEntries].forEach((entry) => {
      dedupe.set(entry.id, entry);
    });
    return Array.from(dedupe.values());
  }, [localEntries, taskEntries]);

  const runningTasks = useMemo(
    () => tasks.filter((task) => task.status === 'running' || task.status === 'paused'),
    [tasks]
  );

  const completedTasks = useMemo(
    () => tasks.filter((task) => ['completed', 'failed', 'cancelled'].includes(task.status)),
    [tasks]
  );

  const pendingApprovals = useMemo(
    () => approvals.filter((approval) => approval.status === 'pending'),
    [approvals]
  );

  const favorites = useMemo(
    () => [
      ...(selectedProjectId
        ? [{ id: selectedProjectId, label: selectedProject?.name ?? 'Current project', kind: 'project' as const }]
        : []),
      ...(selectedSessionId
        ? [{ id: selectedSessionId, label: 'Active session', kind: 'session' as const }]
        : []),
      ...(selectedTaskId ? [{ id: selectedTaskId, label: 'Focused task', kind: 'task' as const }] : []),
    ],
    [selectedProject?.name, selectedProjectId, selectedSessionId, selectedTaskId]
  );

  const notifications = useMemo(() => {
    const items: Array<{ id: string; message: string; severity: 'info' | 'warning' | 'error' }> = [];

    if (pendingApprovals.length > 0) {
      items.push({
        id: 'approvals',
        message: `${pendingApprovals.length} approval(s) waiting`,
        severity: 'warning',
      });
    }

    const failed = tasks.filter((task) => task.status === 'failed').length;
    if (failed > 0) {
      items.push({
        id: 'failed',
        message: `${failed} task(s) failed`,
        severity: 'error',
      });
    }

    if (error) {
      items.push({ id: 'error', message: error, severity: 'error' });
    }

    if (items.length === 0 && loading) {
      items.push({ id: 'loading', message: 'Syncing workspace data...', severity: 'info' });
    }

    return items;
  }, [error, loading, pendingApprovals.length, tasks]);

  return (
    <div className="flex h-full min-h-0 flex-col bg-slate-950 text-slate-100" style={{ fontFamily: 'Inter, system-ui, sans-serif' }}>
      <TopBar
        project={selectedProject}
        projects={projects}
        mode={mode}
        model={model}
        modelOptions={DEFAULT_MODEL_OPTIONS}
        environment={environment}
        paused={paused}
        permissionCount={pendingApprovals.length}
        onProjectChange={(projectId) => {
          setSelectedProjectId(projectId);
          setSelectedSessionId(null);
          setSelectedTaskId(null);
        }}
        onEnvironmentChange={setEnvironment}
        onModelChange={setModel}
        onModeChange={setMode}
        onTogglePaused={() => setPaused((current) => !current)}
      />

      <div
        className="grid min-h-0 flex-1"
        style={{
          gridTemplateColumns: `${leftCollapsed ? 56 : 260}px minmax(0,1fr) ${inspectorCollapsed ? 48 : 380}px`,
        }}
      >
        <LeftRail
          collapsed={leftCollapsed}
          projects={projects}
          sessions={sessions}
          tasks={tasks}
          selectedProjectId={selectedProjectId}
          selectedSessionId={selectedSessionId}
          selectedTaskId={selectedTaskId}
          favorites={favorites}
          notifications={notifications}
          onToggle={() => setLeftCollapsed((current) => !current)}
          onSelectProject={(projectId) => {
            setSelectedProjectId(projectId);
            setSelectedSessionId(null);
            setSelectedTaskId(null);
          }}
          onSelectSession={setSelectedSessionId}
          onSelectTask={(taskId) => {
            setSelectedTaskId(taskId);
            setTaskDrawerOpen(true);
          }}
        />

        <div className="relative flex min-h-0 flex-col overflow-hidden">
          <ConversationPane
            entries={timelineEntries}
            loading={loading}
            onSelectArtifact={handleSelectArtifact}
            onOpenTask={(taskId) => {
              setSelectedTaskId(taskId);
              setTaskDrawerOpen(true);
            }}
            onApproveProposal={(proposalId) => {
              void handleApproveProposal(proposalId);
            }}
            onRejectProposal={(proposalId) => {
              void handleRejectProposal(proposalId);
            }}
            onReviseProposal={(proposalId) => {
              void handleReviseProposal(proposalId);
            }}
            onApproveRequest={(approvalId) => {
              void handleRespondApproval(approvalId, true);
            }}
            onRejectRequest={(approvalId) => {
              void handleRespondApproval(approvalId, false);
            }}
          />

          {(runningTasks.length > 0 || pendingApprovals.length > 0) ? (
            <button
              type="button"
              onClick={() => setTaskDrawerOpen(true)}
              className="flex items-center gap-3 border-t border-slate-800 bg-slate-900/60 px-4 py-2 text-left transition-colors hover:bg-slate-900"
            >
              {runningTasks.length > 0 ? (
                <span className="flex items-center gap-1.5 text-xs text-sky-400">
                  <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-sky-400" />
                  {runningTasks.length} task(s) running
                </span>
              ) : null}
              {pendingApprovals.length > 0 ? (
                <span className="flex items-center gap-1.5 text-xs text-amber-400">
                  <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
                  {pendingApprovals.length} approval(s) needed
                </span>
              ) : null}
              <span className="ml-auto text-xs text-slate-500">Open drawer</span>
            </button>
          ) : null}

          <Composer
            mode={mode}
            value={draft}
            disabled={paused}
            onModeChange={setMode}
            onChange={setDraft}
            onSubmit={() => {
              void handleSubmit();
            }}
          />

          <TaskDrawer
            open={taskDrawerOpen}
            runningTasks={runningTasks}
            completedTasks={completedTasks}
            approvals={pendingApprovals}
            onClose={() => setTaskDrawerOpen(false)}
            onPauseTask={(taskId) => {
              void handlePauseTask(taskId);
            }}
            onResumeTask={(taskId) => {
              void handleResumeTask(taskId);
            }}
            onCancelTask={(taskId) => {
              void handleCancelTask(taskId);
            }}
            onForkTask={(taskId) => {
              void handleForkTask(taskId);
            }}
            onApproveRequest={(approvalId) => {
              void handleRespondApproval(approvalId, true);
            }}
            onRejectRequest={(approvalId) => {
              void handleRespondApproval(approvalId, false);
            }}
          />
        </div>

        <Inspector
          collapsed={inspectorCollapsed}
          onToggle={() => setInspectorCollapsed((current) => !current)}
          project={selectedProject}
          selectedArtifact={selectedArtifact}
          evalBundle={evalBundle}
          traceBookmarks={traceBookmarks}
          activeTab={inspectorTab}
          onTabChange={setInspectorTab}
        />
      </div>

      {grants.length > 0 ? (
        <div className="border-t border-slate-800 bg-slate-950 px-3 py-1.5 text-[11px] text-slate-500">
          Active permission grants: {grants.length}
        </div>
      ) : null}
    </div>
  );
}
