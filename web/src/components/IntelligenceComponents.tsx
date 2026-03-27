import type { ReactNode } from 'react';
import type { PromptBuildArtifact, TranscriptReport } from '../lib/types';
import { formatPercent } from '../lib/utils';

export function SummaryCard({
  label,
  value,
  tone = 'default',
}: {
  label: string;
  value: string | number;
  tone?: 'default' | 'accent';
}) {
  return (
    <div
      className={
        tone === 'accent'
          ? 'rounded-2xl border border-sky-200 bg-gradient-to-br from-sky-50 to-cyan-50 p-4'
          : 'rounded-2xl border border-gray-200 bg-white p-4'
      }
    >
      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-gray-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold tracking-tight text-gray-900">{value}</p>
    </div>
  );
}

export function ListPanel({
  title,
  eyebrow,
  children,
}: {
  title: string;
  eyebrow: string;
  children: ReactNode;
}) {
  return (
    <section className="rounded-3xl border border-gray-200 bg-white p-5 shadow-sm shadow-gray-100/60">
      <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-gray-400">{eyebrow}</p>
      <h3 className="mt-2 text-lg font-semibold tracking-tight text-gray-900">{title}</h3>
      <div className="mt-4">{children}</div>
    </section>
  );
}

export function ReportHighlights({
  report,
  onApplyInsight,
  applyPending,
}: {
  report: TranscriptReport;
  onApplyInsight: (insightId: string) => void;
  applyPending: boolean;
}) {
  return (
    <div className="space-y-5">
      <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <SummaryCard label="Archive Conversations" value={report.conversation_count} tone="accent" />
        <SummaryCard label="Languages" value={report.languages.join(', ')} />
        <SummaryCard label="Insights" value={report.insights.length} />
        <SummaryCard label="Knowledge Entries" value={report.knowledge_asset.entry_count} />
      </section>

      <div className="grid gap-5 xl:grid-cols-[1.3fr_0.7fr]">
        <ListPanel title="Root-Cause Insights" eyebrow="Research">
          <div className="space-y-3">
            {report.insights.map((insight) => (
              <div key={insight.insight_id} className="rounded-2xl border border-sky-100 bg-sky-50/70 p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-slate-900">{insight.title}</p>
                    <p className="mt-1 text-sm text-slate-600">{insight.summary}</p>
                  </div>
                  <span className="rounded-full bg-white px-2.5 py-1 text-xs font-semibold text-sky-700">
                    {formatPercent(insight.share)}
                  </span>
                </div>
                <p className="mt-3 text-xs uppercase tracking-[0.16em] text-slate-400">Recommended change</p>
                <p className="mt-1 text-sm text-slate-700">{insight.recommendation}</p>
                {insight.evidence.length > 0 && (
                  <div className="mt-3 rounded-2xl bg-white/80 p-3">
                    <p className="text-xs uppercase tracking-[0.16em] text-slate-400">Evidence</p>
                    <ul className="mt-2 space-y-1.5 text-sm text-slate-600">
                      {insight.evidence.map((item) => (
                        <li key={`${insight.insight_id}-${item}`}>"{item}"</li>
                      ))}
                    </ul>
                  </div>
                )}
                <div className="mt-4 flex flex-wrap gap-2">
                  <button
                    onClick={() => onApplyInsight(insight.insight_id)}
                    disabled={applyPending}
                    className="rounded-full bg-slate-900 px-3.5 py-2 text-xs font-semibold text-white transition hover:bg-slate-800 disabled:opacity-60"
                  >
                    {applyPending ? 'Drafting...' : 'Apply Insight To Agent'}
                  </button>
                  <span className="rounded-full border border-slate-200 bg-white px-3 py-2 text-xs text-slate-600">
                    {insight.drafted_change_prompt}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </ListPanel>

        <div className="space-y-5">
          <ListPanel title="Missing Intents" eyebrow="Coverage">
            <div className="space-y-3">
              {report.missing_intents.map((intent) => (
                <div key={intent.intent} className="rounded-2xl border border-gray-200 bg-gray-50 p-3">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-semibold text-gray-900">{intent.intent.replaceAll('_', ' ')}</p>
                    <span className="rounded-full bg-white px-2 py-1 text-xs font-medium text-gray-600">{intent.count}</span>
                  </div>
                  <p className="mt-2 text-sm text-gray-600">{intent.reason}</p>
                </div>
              ))}
            </div>
          </ListPanel>

          <ListPanel title="Workflow Suggestions" eyebrow="Operationalize">
            <div className="space-y-3">
              {report.workflow_suggestions.map((item) => (
                <div key={item.title} className="rounded-2xl border border-gray-200 bg-gray-50 p-3">
                  <p className="text-sm font-semibold text-gray-900">{item.title}</p>
                  <p className="mt-1 text-sm text-gray-600">{item.description}</p>
                </div>
              ))}
            </div>
          </ListPanel>
        </div>
      </div>

      <div className="grid gap-5 xl:grid-cols-2">
        <ListPanel title="FAQ / Knowledge Base Seeds" eyebrow="Knowledge">
          <div className="space-y-3">
            {report.faq_entries.map((entry) => (
              <div key={`${entry.intent}-${entry.question}`} className="rounded-2xl border border-gray-200 bg-gray-50 p-3">
                <p className="text-xs uppercase tracking-[0.16em] text-gray-400">{entry.intent.replaceAll('_', ' ')}</p>
                <p className="mt-2 text-sm font-medium text-gray-900">{entry.question}</p>
                <p className="mt-2 text-sm text-gray-600">{entry.answer}</p>
              </div>
            ))}
          </div>
        </ListPanel>

        <ListPanel title="Suggested Regression Tests" eyebrow="Quality">
          <div className="space-y-3">
            {report.suggested_tests.map((test) => (
              <div key={test.name} className="rounded-2xl border border-gray-200 bg-gray-50 p-3">
                <p className="text-sm font-semibold text-gray-900">{test.name}</p>
                <p className="mt-2 text-sm text-gray-600">Prompt: {test.user_message}</p>
                <p className="mt-1 text-sm text-gray-600">Expected: {test.expected_behavior}</p>
              </div>
            ))}
          </div>
        </ListPanel>
      </div>

      <div className="grid gap-5 xl:grid-cols-2">
        <ListPanel title="Procedure Extraction" eyebrow="Procedures">
          <div className="space-y-3">
            {report.procedure_summaries.map((procedure) => (
              <div key={`${procedure.intent}-${procedure.source_conversation_id}`} className="rounded-2xl border border-gray-200 bg-gray-50 p-3">
                <p className="text-sm font-semibold text-gray-900">{procedure.intent.replaceAll('_', ' ')}</p>
                <ol className="mt-3 space-y-1 text-sm text-gray-600">
                  {procedure.steps.map((step, index) => (
                    <li key={`${procedure.source_conversation_id}-${index}`}>{index + 1}. {step}</li>
                  ))}
                </ol>
              </div>
            ))}
          </div>
        </ListPanel>

        <ListPanel title="Conversation Corpus Samples" eyebrow="Corpus">
          <div className="space-y-3">
            {report.conversations.slice(0, 4).map((conversation) => (
              <div key={conversation.conversation_id} className="rounded-2xl border border-gray-200 bg-gray-50 p-3">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-xs uppercase tracking-[0.16em] text-gray-400">
                    {conversation.language} · {conversation.intent.replaceAll('_', ' ')}
                  </p>
                  <span className="rounded-full bg-white px-2 py-1 text-xs font-medium text-gray-600">{conversation.outcome}</span>
                </div>
                <p className="mt-2 text-sm font-medium text-gray-900">{conversation.user_message}</p>
                <p className="mt-2 text-sm text-gray-600">{conversation.agent_response}</p>
              </div>
            ))}
          </div>
        </ListPanel>
      </div>
    </div>
  );
}

export function BuilderResult({ artifact }: { artifact: PromptBuildArtifact }) {
  const workspaceCapabilities = [
    ['Journeys', artifact.workspace_access.journeys],
    ['Integrations', artifact.workspace_access.integrations],
    ['Simulations', artifact.workspace_access.simulations],
    ['Knowledge Base', artifact.workspace_access.knowledge_base],
    ['Triage', artifact.workspace_access.triage],
  ] as const;

  return (
    <div className="space-y-5">
      <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <SummaryCard label="Connectors" value={artifact.connectors.join(', ') || 'None'} tone="accent" />
        <SummaryCard label="Intents" value={artifact.intents.length} />
        <SummaryCard label="Tools" value={artifact.tools.length} />
        <SummaryCard label="Guardrails" value={artifact.guardrails.length} />
      </section>

      <div className="grid gap-5 xl:grid-cols-2">
        <ListPanel title="Intent Spec" eyebrow="Builder">
          <div className="space-y-3">
            {artifact.intents.map((intent) => (
              <div key={intent.name} className="rounded-2xl border border-gray-200 bg-gray-50 p-3">
                <p className="text-sm font-semibold text-gray-900">{intent.name.replaceAll('_', ' ')}</p>
                <p className="mt-1 text-sm text-gray-600">{intent.description}</p>
              </div>
            ))}
          </div>
        </ListPanel>

        <ListPanel title="Connector Tools" eyebrow="Execution">
          <div className="space-y-3">
            {artifact.tools.map((tool) => (
              <div key={tool.name} className="rounded-2xl border border-gray-200 bg-gray-50 p-3">
                <p className="text-sm font-semibold text-gray-900">{tool.name}</p>
                <p className="mt-1 text-sm text-gray-600">{tool.connector} · {tool.purpose}</p>
              </div>
            ))}
          </div>
        </ListPanel>
      </div>

      <div className="grid gap-5 xl:grid-cols-2">
        <ListPanel title="Business Rules & Guardrails" eyebrow="Policy">
          <div className="space-y-3 text-sm text-gray-600">
            {artifact.business_rules.map((rule) => (
              <div key={rule} className="rounded-2xl border border-gray-200 bg-gray-50 p-3">{rule}</div>
            ))}
            {artifact.guardrails.map((rule) => (
              <div key={rule} className="rounded-2xl border border-sky-100 bg-sky-50/70 p-3 text-slate-700">{rule}</div>
            ))}
          </div>
        </ListPanel>

        <ListPanel title="Auth & Escalation" eyebrow="Controls">
          <div className="space-y-3">
            {artifact.auth_steps.map((step) => (
              <div key={step} className="rounded-2xl border border-gray-200 bg-gray-50 p-3 text-sm text-gray-600">{step}</div>
            ))}
            {artifact.escalation_conditions.map((condition) => (
              <div key={condition} className="rounded-2xl border border-amber-100 bg-amber-50/80 p-3 text-sm text-amber-900">{condition}</div>
            ))}
          </div>
        </ListPanel>
      </div>

      <ListPanel title="Journeys & Tests" eyebrow="Artifacts">
        <div className="grid gap-4 xl:grid-cols-2">
          <div className="space-y-3">
            {artifact.journeys.map((journey) => (
              <div key={journey.name} className="rounded-2xl border border-gray-200 bg-gray-50 p-3">
                <p className="text-sm font-semibold text-gray-900">{journey.name}</p>
                <ol className="mt-3 space-y-1 text-sm text-gray-600">
                  {journey.steps.map((step, index) => (
                    <li key={`${journey.name}-${index}`}>{index + 1}. {step}</li>
                  ))}
                </ol>
              </div>
            ))}
          </div>
          <div className="space-y-3">
            {artifact.suggested_tests.map((test) => (
              <div key={test.name} className="rounded-2xl border border-gray-200 bg-gray-50 p-3">
                <p className="text-sm font-semibold text-gray-900">{test.name}</p>
                <p className="mt-1 text-sm text-gray-600">Prompt: {test.user_message}</p>
                <p className="mt-1 text-sm text-gray-600">Expected: {test.expected_behavior}</p>
              </div>
            ))}
          </div>
        </div>
      </ListPanel>

      <div className="grid gap-5 xl:grid-cols-2">
        <ListPanel title="Integration Templates" eyebrow="System Integration">
          <div className="space-y-3">
            {artifact.integration_templates.map((template) => (
              <div
                key={`${template.connector}-${template.name}`}
                className="rounded-2xl border border-gray-200 bg-gray-50 p-3"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-sm font-semibold text-gray-900">{template.name}</p>
                  <span className="rounded-full bg-white px-2 py-1 text-xs font-medium text-gray-600">
                    {template.method} {template.endpoint}
                  </span>
                </div>
                <p className="mt-1 text-sm text-gray-600">{template.connector} · {template.auth_strategy}</p>
                <p className="mt-2 text-sm text-gray-600">{template.error_handling}</p>
              </div>
            ))}
          </div>
        </ListPanel>

        <ListPanel title="Workspace Access" eyebrow="Platform Architecture">
          <div className="space-y-3">
            {workspaceCapabilities.map(([label, enabled]) => (
              <div key={label} className="rounded-2xl border border-gray-200 bg-gray-50 p-3">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-semibold text-gray-900">{label}</p>
                  <span
                    className={`rounded-full px-2 py-1 text-xs font-medium ${
                      enabled ? 'bg-emerald-100 text-emerald-700' : 'bg-gray-200 text-gray-600'
                    }`}
                  >
                    {enabled ? 'Enabled' : 'Disabled'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </ListPanel>
      </div>
    </div>
  );
}
