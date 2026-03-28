import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Activity,
  ArrowRight,
  CheckCircle2,
  ChevronRight,
  ExternalLink,
  Hammer,
  Package,
  Play,
  RefreshCw,
  Shield,
  Sparkles,
  TestTubes,
  Zap,
} from 'lucide-react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface DemoAct {
  act_id: string;
  number: number;
  title: string;
  subtitle: string;
  description: string;
  narrator: string;
  spotlight: string;
  featured_objects: {
    projects?: string[];
    sessions?: string[];
    tasks?: string[];
    artifacts?: string[];
    proposals?: string[];
    approvals?: string[];
    eval_bundles?: string[];
    trace_bookmarks?: string[];
    releases?: string[];
  };
}

interface DemoStatus {
  demo_loaded: boolean;
  demo_projects: Array<{
    project_id: string;
    name: string;
    session_count: number;
    task_count: number;
  }>;
  act_count: number;
}

type ActPlayState = 'idle' | 'loading' | 'active' | 'error';

// ---------------------------------------------------------------------------
// Act icon map
// ---------------------------------------------------------------------------

const ACT_ICONS = [Hammer, Zap, TestTubes, Sparkles, Package];

const ACT_GRADIENTS = [
  'from-sky-500 to-blue-600',
  'from-violet-500 to-purple-600',
  'from-amber-500 to-orange-600',
  'from-emerald-500 to-teal-600',
  'from-rose-500 to-pink-600',
];

const ACT_RING_COLORS = [
  'ring-sky-500/40',
  'ring-violet-500/40',
  'ring-amber-500/40',
  'ring-emerald-500/40',
  'ring-rose-500/40',
];

const ACT_TEXT_COLORS = [
  'text-sky-400',
  'text-violet-400',
  'text-amber-400',
  'text-emerald-400',
  'text-rose-400',
];

const ACT_BG_COLORS = [
  'bg-sky-500/10 border-sky-500/20',
  'bg-violet-500/10 border-violet-500/20',
  'bg-amber-500/10 border-amber-500/20',
  'bg-emerald-500/10 border-emerald-500/20',
  'bg-rose-500/10 border-rose-500/20',
];

// ---------------------------------------------------------------------------
// Spotlight pill labels
// ---------------------------------------------------------------------------

const SPOTLIGHT_LABELS: Record<string, string> = {
  conversation: 'Conversation Pane',
  inspector: 'Inspector Panel',
  traces: 'Trace Viewer',
  diff: 'Diff Viewer',
  config: 'Release Panel',
};

// ---------------------------------------------------------------------------
// Featured object counts helper
// ---------------------------------------------------------------------------

function countFeatured(featured: DemoAct['featured_objects']): string {
  const parts: string[] = [];
  if (featured.tasks?.length) parts.push(`${featured.tasks.length} tasks`);
  if (featured.artifacts?.length) parts.push(`${featured.artifacts.length} artifacts`);
  if (featured.proposals?.length) parts.push(`${featured.proposals.length} proposals`);
  if (featured.approvals?.length) parts.push(`${featured.approvals.length} approvals`);
  if (featured.eval_bundles?.length) parts.push(`${featured.eval_bundles.length} eval bundles`);
  if (featured.trace_bookmarks?.length) parts.push(`${featured.trace_bookmarks.length} trace bookmarks`);
  if (featured.releases?.length) parts.push(`${featured.releases.length} releases`);
  return parts.join(' · ');
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function BuilderDemo() {
  const navigate = useNavigate();
  const [acts, setActs] = useState<DemoAct[]>([]);
  const [status, setStatus] = useState<DemoStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [seeding, setSeeding] = useState(false);
  const [activeActId, setActiveActId] = useState<string | null>(null);
  const [actStates, setActStates] = useState<Record<string, ActPlayState>>({});
  const [playedActIds, setPlayedActIds] = useState<Set<string>>(new Set());
  const activeActRef = useRef<HTMLDivElement | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      const [actsRes, statusRes] = await Promise.all([
        fetch('/api/builder/demo/acts'),
        fetch('/api/builder/demo/status'),
      ]);
      if (actsRes.ok) {
        const data = await actsRes.json() as { acts: DemoAct[] };
        setActs(data.acts);
      }
      if (statusRes.ok) {
        const data = await statusRes.json() as DemoStatus;
        setStatus(data);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchStatus();
  }, [fetchStatus]);

  useEffect(() => {
    if (activeActRef.current) {
      activeActRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }, [activeActId]);

  const handleSeed = useCallback(async () => {
    setSeeding(true);
    try {
      await fetch('/api/builder/demo/seed', { method: 'POST' });
      await fetchStatus();
    } finally {
      setSeeding(false);
    }
  }, [fetchStatus]);

  const handleReset = useCallback(async () => {
    setSeeding(true);
    try {
      await fetch('/api/builder/demo/reset', { method: 'POST' });
      setPlayedActIds(new Set());
      setActiveActId(null);
      await fetchStatus();
    } finally {
      setSeeding(false);
    }
  }, [fetchStatus]);

  const handlePlayAct = useCallback(async (actId: string) => {
    setActStates((prev) => ({ ...prev, [actId]: 'loading' }));
    try {
      const res = await fetch(`/api/builder/demo/acts/${actId}/play`, { method: 'POST' });
      if (!res.ok) throw new Error('Failed to activate act');
      const data = await res.json() as { act: DemoAct; load: { project_id: string | null; session_id: string | null } };
      setActStates((prev) => ({ ...prev, [actId]: 'active' }));
      setActiveActId(actId);
      setPlayedActIds((prev) => new Set([...prev, actId]));
      await fetchStatus();

      // Navigate to the Builder Workspace with demo data loaded
      const { project_id, session_id } = data.load;
      if (project_id && session_id) {
        navigate(`/builder/${project_id}/${session_id}`);
      } else if (project_id) {
        navigate(`/builder/${project_id}`);
      }
    } catch {
      setActStates((prev) => ({ ...prev, [actId]: 'error' }));
    }
  }, [fetchStatus, navigate]);

  const handleOpenWorkspace = useCallback(() => {
    if (status?.demo_projects[0]?.project_id) {
      navigate(`/builder/${status.demo_projects[0].project_id}`);
    } else {
      navigate('/builder');
    }
  }, [navigate, status]);

  if (loading) {
    return (
      <div
        className="flex min-h-screen items-center justify-center"
        style={{ background: 'linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%)', fontFamily: 'Inter, system-ui, sans-serif' }}
      >
        <div className="flex items-center gap-3 text-slate-400">
          <Activity className="h-5 w-5 animate-pulse" />
          <span className="text-sm">Loading demo...</span>
        </div>
      </div>
    );
  }

  return (
    <div
      className="min-h-screen text-slate-100"
      style={{
        background: 'linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%)',
        fontFamily: 'Inter, system-ui, sans-serif',
      }}
    >
      {/* ----------------------------------------------------------------- */}
      {/* Header */}
      {/* ----------------------------------------------------------------- */}
      <header className="relative overflow-hidden border-b border-white/5 px-6 py-12 text-center">
        {/* Background glow */}
        <div
          className="pointer-events-none absolute inset-0 opacity-30"
          style={{
            background:
              'radial-gradient(ellipse 80% 60% at 50% 0%, rgba(139,92,246,0.4) 0%, transparent 70%)',
          }}
        />
        <div className="relative">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-violet-500/30 bg-violet-500/10 px-4 py-1.5 text-xs font-medium text-violet-300">
            <Sparkles className="h-3.5 w-3.5" />
            Builder Workspace — Guided Demo
          </div>
          <h1 className="text-4xl font-bold tracking-tight text-white">
            See the Builder in Action
          </h1>
          <p className="mx-auto mt-3 max-w-2xl text-base text-slate-400">
            A 5-act walkthrough of building, evaluating, and shipping an AI agent —
            from first conversation to production deployment.
          </p>

          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            {status?.demo_loaded ? (
              <>
                <button
                  onClick={handleOpenWorkspace}
                  className="inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-violet-600 to-purple-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-violet-500/25 transition-all hover:from-violet-500 hover:to-purple-500 hover:shadow-violet-500/40"
                >
                  <ExternalLink className="h-4 w-4" />
                  Open Builder Workspace
                </button>
                <button
                  onClick={() => void handleReset()}
                  disabled={seeding}
                  className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-5 py-2.5 text-sm font-medium text-slate-300 transition-all hover:border-white/20 hover:bg-white/10 disabled:opacity-50"
                >
                  <RefreshCw className={`h-4 w-4 ${seeding ? 'animate-spin' : ''}`} />
                  Reset Demo
                </button>
              </>
            ) : (
              <button
                onClick={() => void handleSeed()}
                disabled={seeding}
                className="inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-violet-600 to-purple-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-violet-500/25 transition-all hover:from-violet-500 hover:to-purple-500 disabled:opacity-50"
              >
                {seeding ? (
                  <Activity className="h-4 w-4 animate-pulse" />
                ) : (
                  <Sparkles className="h-4 w-4" />
                )}
                {seeding ? 'Loading demo data...' : 'Load Demo Data'}
              </button>
            )}
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-5xl px-6 py-12">
        {/* ----------------------------------------------------------------- */}
        {/* Status strip */}
        {/* ----------------------------------------------------------------- */}
        {status?.demo_loaded && (
          <div className="mb-10 rounded-xl border border-white/5 bg-white/[0.03] p-4">
            <div className="flex flex-wrap items-center gap-6">
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-emerald-400" />
                <span className="text-xs font-medium text-emerald-400">Demo data loaded</span>
              </div>
              {status.demo_projects.map((proj) => (
                <div key={proj.project_id} className="flex items-center gap-2 text-xs text-slate-400">
                  <span className="font-medium text-slate-300">{proj.name}</span>
                  <span>·</span>
                  <span>{proj.session_count} sessions</span>
                  <span>·</span>
                  <span>{proj.task_count} tasks</span>
                </div>
              ))}
              <div className="ml-auto">
                <div className="flex gap-1">
                  {acts.map((act, i) => (
                    <div
                      key={act.act_id}
                      title={`Act ${act.number}: ${act.title}`}
                      className={`h-1.5 w-6 rounded-full transition-all ${
                        playedActIds.has(act.act_id)
                          ? `bg-gradient-to-r ${ACT_GRADIENTS[i]}`
                          : 'bg-slate-700'
                      }`}
                    />
                  ))}
                </div>
                <p className="mt-1 text-right text-[10px] text-slate-500">
                  {playedActIds.size}/{acts.length} acts played
                </p>
              </div>
            </div>
          </div>
        )}

        {/* ----------------------------------------------------------------- */}
        {/* Acts */}
        {/* ----------------------------------------------------------------- */}
        <div className="space-y-4">
          {acts.map((act, i) => {
            const Icon = ACT_ICONS[i] ?? Sparkles;
            const isActive = activeActId === act.act_id;
            const isPlayed = playedActIds.has(act.act_id);
            const playState = actStates[act.act_id] ?? 'idle';

            return (
              <div
                key={act.act_id}
                ref={isActive ? activeActRef : null}
                className={`group relative overflow-hidden rounded-2xl border transition-all duration-300 ${
                  isActive
                    ? `border-white/10 ${ACT_BG_COLORS[i]} ring-1 ${ACT_RING_COLORS[i]}`
                    : 'border-white/5 bg-white/[0.02] hover:border-white/10 hover:bg-white/[0.04]'
                }`}
              >
                {/* Subtle gradient glow for active act */}
                {isActive && (
                  <div
                    className="pointer-events-none absolute -inset-px opacity-20"
                    style={{
                      background: `radial-gradient(ellipse 60% 100% at 0% 50%, rgba(139,92,246,0.6) 0%, transparent 60%)`,
                    }}
                  />
                )}

                <div className="relative flex items-start gap-5 p-6">
                  {/* Act number + icon */}
                  <div className="shrink-0">
                    <div
                      className={`flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br ${ACT_GRADIENTS[i]} shadow-lg`}
                    >
                      <Icon className="h-5 w-5 text-white" />
                    </div>
                    <div className="mt-2 text-center text-[10px] font-semibold text-slate-500">
                      ACT {act.number}
                    </div>
                  </div>

                  {/* Content */}
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <h2 className="text-lg font-semibold text-white">{act.title}</h2>
                        <p className={`text-sm font-medium ${ACT_TEXT_COLORS[i]}`}>{act.subtitle}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        {isPlayed && !isActive && (
                          <span className="flex items-center gap-1.5 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-400">
                            <CheckCircle2 className="h-3 w-3" />
                            Played
                          </span>
                        )}
                        <button
                          onClick={() => void handlePlayAct(act.act_id)}
                          disabled={playState === 'loading' || seeding}
                          className={`inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-all disabled:opacity-50 ${
                            isActive
                              ? 'bg-white text-slate-900 shadow-md hover:bg-slate-100'
                              : `bg-gradient-to-r ${ACT_GRADIENTS[i]} text-white shadow-md shadow-black/20 hover:opacity-90`
                          }`}
                        >
                          {playState === 'loading' ? (
                            <>
                              <Activity className="h-3.5 w-3.5 animate-pulse" />
                              Opening...
                            </>
                          ) : isActive ? (
                            <>
                              <ExternalLink className="h-3.5 w-3.5" />
                              View in Workspace
                            </>
                          ) : (
                            <>
                              <Play className="h-3.5 w-3.5" />
                              Play Act {act.number}
                            </>
                          )}
                        </button>
                      </div>
                    </div>

                    <p className="mt-3 text-sm leading-relaxed text-slate-400">{act.description}</p>

                    {/* Narrator callout */}
                    <div className="mt-4 rounded-lg border border-white/5 bg-white/[0.03] p-3">
                      <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                        Narrator
                      </p>
                      <p className="mt-1 text-sm italic text-slate-300">{act.narrator}</p>
                    </div>

                    {/* Metadata strip */}
                    <div className="mt-4 flex flex-wrap items-center gap-4 text-xs text-slate-500">
                      <span className="flex items-center gap-1.5">
                        <Shield className="h-3.5 w-3.5" />
                        Spotlight:{' '}
                        <span className="font-medium text-slate-400">
                          {SPOTLIGHT_LABELS[act.spotlight] ?? act.spotlight}
                        </span>
                      </span>
                      {countFeatured(act.featured_objects) && (
                        <span className="flex items-center gap-1.5">
                          <ChevronRight className="h-3.5 w-3.5" />
                          {countFeatured(act.featured_objects)}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* ----------------------------------------------------------------- */}
        {/* Footer CTA */}
        {/* ----------------------------------------------------------------- */}
        <div className="mt-16 rounded-2xl border border-white/5 bg-white/[0.02] p-8 text-center">
          <h3 className="text-xl font-semibold text-white">Ready to build your own agent?</h3>
          <p className="mx-auto mt-2 max-w-md text-sm text-slate-400">
            The Builder Workspace is the full product — open it to start a real project, import from
            ADK or CX, or continue exploring the demo data at your own pace.
          </p>
          <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
            <button
              onClick={handleOpenWorkspace}
              className="inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-violet-600 to-purple-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-violet-500/25 transition-all hover:from-violet-500 hover:to-purple-500"
            >
              Open Builder Workspace
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Padding */}
        <div className="h-16" />
      </div>
    </div>
  );
}
