import { useState } from 'react';
import { ChevronDown, ChevronRight, Check, Trash2, Edit3, Save, X, Shield, Zap, AlertTriangle } from 'lucide-react';
import { useGeneratedSuite, useAcceptSuite, useDeleteGeneratedCase, useUpdateGeneratedCase } from '../lib/api';
import type { GeneratedEvalCase } from '../lib/types';
import { toastError, toastSuccess, toastInfo } from '../lib/toast';
import { classNames } from '../lib/utils';

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface GeneratedEvalReviewProps {
  suiteId: string;
  onAccepted?: () => void;
}

// ---------------------------------------------------------------------------
// Badge helpers
// ---------------------------------------------------------------------------

const DIFFICULTY_COLORS: Record<string, string> = {
  easy: 'bg-green-100 text-green-700',
  medium: 'bg-yellow-100 text-yellow-700',
  hard: 'bg-red-100 text-red-700',
};

const BEHAVIOR_COLORS: Record<string, string> = {
  answer: 'bg-blue-100 text-blue-700',
  refuse: 'bg-red-100 text-red-700',
  route_correctly: 'bg-purple-100 text-purple-700',
  use_tool: 'bg-amber-100 text-amber-700',
};

const CATEGORY_ICONS: Record<string, typeof Shield> = {
  safety: Shield,
  performance: Zap,
  edge_cases: AlertTriangle,
};

function Badge({ label, colorClass }: { label: string; colorClass: string }) {
  return (
    <span className={classNames('rounded-md px-2 py-0.5 text-[11px] font-medium', colorClass)}>
      {label}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Inline case editor
// ---------------------------------------------------------------------------

interface CaseEditorProps {
  evalCase: GeneratedEvalCase;
  onSave: (updates: Partial<GeneratedEvalCase>) => void;
  onCancel: () => void;
}

function CaseEditor({ evalCase, onSave, onCancel }: CaseEditorProps) {
  const [userMessage, setUserMessage] = useState(evalCase.user_message);
  const [behavior, setBehavior] = useState(evalCase.expected_behavior);
  const [difficulty, setDifficulty] = useState(evalCase.difficulty);

  return (
    <div className="space-y-3 rounded-lg border border-blue-200 bg-blue-50/50 p-4">
      <div>
        <label className="mb-1 block text-[11px] font-medium uppercase tracking-wide text-gray-500">
          User Message
        </label>
        <textarea
          value={userMessage}
          onChange={(e) => setUserMessage(e.target.value)}
          rows={3}
          className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400"
        />
      </div>
      <div className="flex gap-4">
        <div className="flex-1">
          <label className="mb-1 block text-[11px] font-medium uppercase tracking-wide text-gray-500">
            Expected Behavior
          </label>
          <select
            value={behavior}
            onChange={(e) => setBehavior(e.target.value)}
            className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-blue-400 focus:outline-none"
          >
            <option value="answer">answer</option>
            <option value="refuse">refuse</option>
            <option value="route_correctly">route_correctly</option>
            <option value="use_tool">use_tool</option>
          </select>
        </div>
        <div className="flex-1">
          <label className="mb-1 block text-[11px] font-medium uppercase tracking-wide text-gray-500">
            Difficulty
          </label>
          <select
            value={difficulty}
            onChange={(e) => setDifficulty(e.target.value as GeneratedEvalCase['difficulty'])}
            className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-blue-400 focus:outline-none"
          >
            <option value="easy">easy</option>
            <option value="medium">medium</option>
            <option value="hard">hard</option>
          </select>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <button
          onClick={() => onSave({ user_message: userMessage, expected_behavior: behavior, difficulty })}
          className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-medium text-white transition hover:bg-blue-700"
        >
          <Save className="h-3.5 w-3.5" />
          Save
        </button>
        <button
          onClick={onCancel}
          className="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 transition hover:bg-gray-50"
        >
          <X className="h-3.5 w-3.5" />
          Cancel
        </button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Case row
// ---------------------------------------------------------------------------

interface CaseRowProps {
  evalCase: GeneratedEvalCase;
  suiteId: string;
}

function CaseRow({ evalCase, suiteId }: CaseRowProps) {
  const [editing, setEditing] = useState(false);
  const updateCase = useUpdateGeneratedCase();
  const deleteCase = useDeleteGeneratedCase();

  function handleSave(updates: Partial<GeneratedEvalCase>) {
    updateCase.mutate(
      { suiteId, caseId: evalCase.case_id, updates },
      {
        onSuccess: () => {
          toastSuccess('Case updated');
          setEditing(false);
        },
        onError: (err) => toastError('Update failed', err.message),
      },
    );
  }

  function handleDelete() {
    deleteCase.mutate(
      { suiteId, caseId: evalCase.case_id },
      {
        onSuccess: () => toastInfo('Case deleted'),
        onError: (err) => toastError('Delete failed', err.message),
      },
    );
  }

  if (editing) {
    return <CaseEditor evalCase={evalCase} onSave={handleSave} onCancel={() => setEditing(false)} />;
  }

  return (
    <div className="flex items-start gap-3 rounded-lg border border-gray-200 bg-white p-4">
      <div className="min-w-0 flex-1 space-y-1.5">
        <p className="text-sm text-gray-900">{evalCase.user_message}</p>
        <div className="flex flex-wrap items-center gap-2">
          <Badge
            label={evalCase.expected_behavior}
            colorClass={BEHAVIOR_COLORS[evalCase.expected_behavior] ?? 'bg-gray-100 text-gray-700'}
          />
          <Badge
            label={evalCase.difficulty}
            colorClass={DIFFICULTY_COLORS[evalCase.difficulty] ?? 'bg-gray-100 text-gray-700'}
          />
          {evalCase.safety_probe && (
            <Badge label="safety probe" colorClass="bg-red-50 text-red-600" />
          )}
        </div>
        {evalCase.rationale && (
          <p className="text-xs text-gray-500">{evalCase.rationale}</p>
        )}
      </div>
      <div className="flex shrink-0 items-center gap-1.5">
        <button
          onClick={() => setEditing(true)}
          className="rounded-md p-1.5 text-gray-400 transition hover:bg-gray-100 hover:text-gray-600"
          title="Edit case"
        >
          <Edit3 className="h-4 w-4" />
        </button>
        <button
          onClick={handleDelete}
          disabled={deleteCase.isPending}
          className="rounded-md p-1.5 text-gray-400 transition hover:bg-red-50 hover:text-red-600 disabled:opacity-50"
          title="Delete case"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Category section (expand/collapse)
// ---------------------------------------------------------------------------

interface CategorySectionProps {
  category: string;
  cases: GeneratedEvalCase[];
  suiteId: string;
}

function CategorySection({ category, cases, suiteId }: CategorySectionProps) {
  const [open, setOpen] = useState(false);
  const Icon = CATEGORY_ICONS[category] ?? Zap;
  const Chevron = open ? ChevronDown : ChevronRight;

  return (
    <div className="rounded-lg border border-gray-200 bg-white">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center gap-2 px-4 py-3 text-left transition hover:bg-gray-50"
      >
        <Chevron className="h-4 w-4 text-gray-400" />
        <Icon className="h-4 w-4 text-gray-500" />
        <span className="text-sm font-medium text-gray-900">{category.replaceAll('_', ' ')}</span>
        <span className="rounded-full bg-gray-100 px-2 py-0.5 text-[11px] font-medium text-gray-600">
          {cases.length}
        </span>
      </button>
      {open && (
        <div className="space-y-2 border-t border-gray-100 px-4 py-3">
          {cases.map((c) => (
            <CaseRow key={c.case_id} evalCase={c} suiteId={suiteId} />
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function GeneratedEvalReview({ suiteId, onAccepted }: GeneratedEvalReviewProps) {
  const { data: suite, isLoading, error } = useGeneratedSuite(suiteId);
  const acceptSuite = useAcceptSuite();

  function handleAcceptAll() {
    acceptSuite.mutate(suiteId, {
      onSuccess: (res) => {
        toastSuccess('Suite accepted', `${res.total_cases} cases promoted to eval set`);
        onAccepted?.();
      },
      onError: (err) => toastError('Accept failed', err.message),
    });
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="rounded-lg border border-gray-200 bg-white p-5">
          {Array.from({ length: 5 }).map((_, i) => (
            <div
              key={i}
              className="mb-3 h-3.5 animate-pulse rounded bg-gray-100 last:mb-0"
              style={{ width: `${92 - i * 8}%` }}
            />
          ))}
        </div>
      </div>
    );
  }

  if (error || !suite) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-5 text-sm text-red-700">
        {error ? `Failed to load suite: ${(error as Error).message}` : 'Suite not found'}
      </div>
    );
  }

  const categories = Object.entries(suite.categories);
  const { summary } = suite;

  const statusColors: Record<string, string> = {
    generating: 'bg-yellow-100 text-yellow-700',
    ready: 'bg-blue-100 text-blue-700',
    accepted: 'bg-green-100 text-green-700',
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-start justify-between rounded-lg border border-gray-200 bg-white p-5">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs text-gray-500">{suite.suite_id}</span>
            <Badge label={suite.status} colorClass={statusColors[suite.status] ?? 'bg-gray-100 text-gray-700'} />
          </div>
          <p className="text-sm font-medium text-gray-900">{suite.agent_name}</p>
          <p className="text-xs text-gray-400">
            Created {new Date(suite.created_at).toLocaleString()} &middot; {summary.total_cases} cases
          </p>
        </div>
        {suite.status === 'ready' && (
          <button
            onClick={handleAcceptAll}
            disabled={acceptSuite.isPending}
            className="inline-flex items-center gap-1.5 rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-green-700 disabled:opacity-50"
          >
            <Check className="h-4 w-4" />
            {acceptSuite.isPending ? 'Accepting...' : 'Accept All'}
          </button>
        )}
      </div>

      {/* Summary bar */}
      <div className="flex flex-wrap items-center gap-3 rounded-lg border border-gray-200 bg-gray-50 px-4 py-3">
        <span className="text-[11px] font-medium uppercase tracking-wide text-gray-500">Categories</span>
        {Object.entries(summary.categories).map(([cat, count]) => (
          <Badge key={cat} label={`${cat.replaceAll('_', ' ')} (${count})`} colorClass="bg-white text-gray-700 border border-gray-200" />
        ))}
        <span className="mx-1 h-4 w-px bg-gray-300" />
        <span className="text-[11px] font-medium uppercase tracking-wide text-gray-500">Difficulty</span>
        {Object.entries(summary.difficulty_distribution).map(([diff, count]) => (
          <Badge key={diff} label={`${diff} (${count})`} colorClass={DIFFICULTY_COLORS[diff] ?? 'bg-gray-100 text-gray-700'} />
        ))}
        <span className="mx-1 h-4 w-px bg-gray-300" />
        <div className="flex items-center gap-1.5">
          <Shield className="h-3.5 w-3.5 text-red-500" />
          <span className="text-xs text-gray-600">{summary.safety_probes} safety probes</span>
        </div>
      </div>

      {/* Category sections */}
      <div className="space-y-3">
        {categories.map(([category, cases]) => (
          <CategorySection
            key={category}
            category={category}
            cases={cases}
            suiteId={suiteId}
          />
        ))}
      </div>
    </div>
  );
}
