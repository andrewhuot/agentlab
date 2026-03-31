import type { EvalResultExample } from '../lib/types';

interface ExampleDetailProps {
  example: EvalResultExample | null;
}

export function ExampleDetail({ example }: ExampleDetailProps) {
  if (!example) {
    return (
      <section className="rounded-2xl border border-dashed border-gray-200 bg-gray-50 p-4">
        <h3 className="text-sm font-semibold text-gray-900">Example Detail</h3>
        <p className="mt-2 text-sm text-gray-500">Choose an example to inspect full inputs, outputs, and grader scores.</p>
      </section>
    );
  }

  const scoreEntries = Object.entries(example.scores).sort(([left], [right]) => left.localeCompare(right));
  const traceId = typeof example.actual['trace_id'] === 'string' ? example.actual['trace_id'] : null;

  return (
    <section className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="font-mono text-sm font-semibold text-gray-900">{example.example_id}</h3>
          <p className="mt-1 text-xs text-gray-500">{example.category}</p>
        </div>
        <span
          className={`rounded-full px-2.5 py-1 text-[11px] font-medium ${
            example.passed ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
          }`}
        >
          {example.passed ? 'Passed' : 'Failed'}
        </span>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        {scoreEntries.map(([metric, score]) => (
          <div key={metric} className="rounded-xl border border-gray-200 bg-gray-50 px-3 py-2">
            <div className="flex items-center justify-between gap-2">
              <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">{metric}</p>
              <p className="text-sm font-semibold text-gray-900">{score.value.toFixed(3)}</p>
            </div>
            {score.reasoning && (
              <p className="mt-1 text-xs text-gray-500">{score.reasoning}</p>
            )}
          </div>
        ))}
      </div>

      {example.failure_reasons.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-2">
          {example.failure_reasons.map((reason) => (
            <span
              key={reason}
              className="rounded-full bg-amber-100 px-2.5 py-1 text-[11px] font-medium text-amber-700"
            >
              {reason}
            </span>
          ))}
        </div>
      )}

      <div className="mt-4 space-y-3">
        <JsonBlock title="Input" payload={example.input} />
        <JsonBlock title="Expected" payload={example.expected} />
        <JsonBlock title="Actual" payload={example.actual} />
      </div>

      {traceId && (
        <a
          href={`/traces?trace_id=${encodeURIComponent(traceId)}`}
          className="mt-4 inline-flex text-sm font-medium text-gray-700 underline decoration-gray-300 underline-offset-2 hover:text-gray-900"
        >
          Open linked trace
        </a>
      )}
    </section>
  );
}

function JsonBlock({
  title,
  payload,
}: {
  title: string;
  payload: Record<string, unknown> | null;
}) {
  return (
    <div className="rounded-xl border border-gray-200 bg-gray-50 p-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">{title}</p>
      <pre className="mt-2 overflow-x-auto whitespace-pre-wrap text-xs text-gray-700">
        {JSON.stringify(payload, null, 2)}
      </pre>
    </div>
  );
}
