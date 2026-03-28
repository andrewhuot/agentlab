import { useMemo, useState } from 'react';
import type {
  ArtifactRef,
  BuilderProject,
  EvalBundle,
  TraceBookmark,
} from '../../lib/builder-types';
import { BuildtimeSkillsTab } from './inspector/BuildtimeSkillsTab';
import { CodingAgentConfigTab } from './inspector/CodingAgentConfigTab';
import { EvalResultsTab } from './inspector/EvalResultsTab';
import { FilesTab } from './inspector/FilesTab';
import { GuardrailsTab } from './inspector/GuardrailsTab';
import { InstructionsMemoryTab } from './inspector/InstructionsMemoryTab';
import { RuntimeSkillsTab } from './inspector/RuntimeSkillsTab';
import { ToolsTab } from './inspector/ToolsTab';
import { TraceViewerTab } from './inspector/TraceViewerTab';

const TABS = [
  { id: 'overview', label: 'Overview' },
  { id: 'diff', label: 'Diff' },
  { id: 'adk_graph', label: 'ADK Graph' },
  { id: 'evals', label: 'Evals' },
  { id: 'traces', label: 'Traces' },
  { id: 'skills', label: 'Skills' },
  { id: 'guardrails', label: 'Guardrails' },
  { id: 'files', label: 'Files' },
  { id: 'config', label: 'Config' },
] as const;

export type InspectorTabId = (typeof TABS)[number]['id'];

interface InspectorProps {
  collapsed: boolean;
  onToggle: () => void;
  project: BuilderProject | null;
  selectedArtifact: ArtifactRef | null;
  evalBundle: EvalBundle | null;
  traceBookmarks: TraceBookmark[];
  activeTab?: InspectorTabId;
  onTabChange?: (tab: InspectorTabId) => void;
  width?: number;
}

export function Inspector({
  collapsed,
  onToggle,
  project,
  selectedArtifact,
  evalBundle,
  traceBookmarks,
  activeTab,
  onTabChange,
  width = 380,
}: InspectorProps) {
  const [internalTab, setInternalTab] = useState<InspectorTabId>('overview');
  const resolvedTab = activeTab ?? internalTab;

  const setTab = (tab: InspectorTabId) => {
    if (!activeTab) {
      setInternalTab(tab);
    }
    onTabChange?.(tab);
  };

  const toolItems = useMemo(
    () => [
      { id: 'tool-1', name: 'read_source', description: 'Read source files', attached: true },
      { id: 'tool-2', name: 'run_eval', description: 'Run eval slice', attached: true },
      { id: 'tool-3', name: 'deploy_release', description: 'Deploy candidate', attached: false },
    ],
    []
  );

  const guardrailItems = useMemo(
    () => [
      { id: 'guard-1', name: 'PII Guard', scope: 'project' },
      { id: 'guard-2', name: 'Safe Tools', scope: 'task' },
    ],
    []
  );

  const diffFiles = useMemo(() => {
    const payloadFiles = selectedArtifact?.payload.files;
    if (!Array.isArray(payloadFiles)) {
      return Object.keys(selectedArtifact?.source_versions ?? {});
    }
    return payloadFiles
      .map((file) => {
        if (typeof file !== 'object' || file === null) return '';
        const value = (file as Record<string, unknown>).path;
        return typeof value === 'string' ? value : '';
      })
      .filter((path) => path.length > 0);
  }, [selectedArtifact]);

  if (collapsed) {
    return (
      <aside className="flex h-full w-12 flex-col border-l border-slate-800 bg-slate-950">
        <button
          type="button"
          onClick={onToggle}
          className="m-2 rounded border border-slate-700 px-2 py-1 text-xs text-slate-400 transition hover:bg-slate-800"
          aria-label="Expand inspector"
        >
          ⇦
        </button>
      </aside>
    );
  }

  return (
    <aside
      className="flex h-full flex-col border-l border-slate-800 bg-slate-950/90"
      style={{ width, minWidth: width, maxWidth: width }}
    >
      <div className="flex items-center justify-between border-b border-slate-800 px-3 py-2">
        <p className="text-xs font-semibold text-slate-300">Inspector</p>
        <button
          type="button"
          onClick={onToggle}
          className="rounded border border-slate-700 px-2 py-1 text-xs text-slate-400 transition hover:bg-slate-800"
          aria-label="Collapse inspector"
        >
          ⇨
        </button>
      </div>

      <div className="border-b border-slate-800 px-2 py-2">
        <div className="flex flex-wrap gap-1">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setTab(tab.id)}
              className={
                resolvedTab === tab.id
                  ? 'rounded-md bg-slate-700 px-2 py-1 text-[11px] text-slate-100'
                  : 'rounded-md bg-slate-900 px-2 py-1 text-[11px] text-slate-500 transition hover:bg-slate-800 hover:text-slate-300'
              }
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto p-3">
        {resolvedTab === 'overview' ? (
          <div className="space-y-2 rounded-md border border-slate-700 bg-slate-900/70 p-3">
            <p className="text-xs font-medium text-slate-200">Project</p>
            <p className="text-[11px] text-slate-500">{project?.name || 'No project selected'}</p>
            <p className="text-xs font-medium text-slate-200">Selected Artifact</p>
            <p className="text-[11px] text-slate-500">{selectedArtifact?.title || 'None selected'}</p>
          </div>
        ) : null}

        {resolvedTab === 'diff' ? <FilesTab files={diffFiles} /> : null}
        {resolvedTab === 'adk_graph' ? <FilesTab files={diffFiles} /> : null}
        {resolvedTab === 'evals' ? <EvalResultsTab bundle={evalBundle} /> : null}
        {resolvedTab === 'traces' ? <TraceViewerTab bookmarks={traceBookmarks} /> : null}
        {resolvedTab === 'skills' ? (
          <div className="space-y-3">
            <RuntimeSkillsTab skills={project?.runtime_skills ?? []} />
            <BuildtimeSkillsTab skills={project?.buildtime_skills ?? []} />
            <ToolsTab tools={toolItems} />
          </div>
        ) : null}
        {resolvedTab === 'guardrails' ? <GuardrailsTab guardrails={guardrailItems} /> : null}
        {resolvedTab === 'files' ? <FilesTab files={project?.knowledge_files ?? []} /> : null}
        {resolvedTab === 'config' ? (
          <div className="space-y-3">
            <CodingAgentConfigTab agentsMd="Loaded from workspace" claudeMd="Loaded from workspace" />
            <InstructionsMemoryTab
              projectInstruction={project?.master_instruction ?? ''}
              memoryNotes="Inheritance scope: project > folder > task"
            />
          </div>
        ) : null}
      </div>
    </aside>
  );
}
