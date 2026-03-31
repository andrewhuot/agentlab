import { useState } from 'react';
import type { EvalResultExample } from '../lib/types';

interface AnnotationPanelProps {
  example: EvalResultExample | null;
  isPending: boolean;
  onSubmit: (payload: { author: string; type: string; content: string; score_override: number | null }) => void;
}

export function AnnotationPanel({ example, isPending, onSubmit }: AnnotationPanelProps) {
  const [annotationType, setAnnotationType] = useState('comment');
  const [content, setContent] = useState('');
  const [scoreOverride, setScoreOverride] = useState('');

  if (!example) {
    return (
      <section className="rounded-2xl border border-dashed border-gray-200 bg-gray-50 p-4">
        <h3 className="text-sm font-semibold text-gray-900">Annotations</h3>
        <p className="mt-2 text-sm text-gray-500">Select an example to leave review notes or override a score.</p>
      </section>
    );
  }

  const existingAnnotations = example.annotations || [];

  function handleSubmit() {
    const normalizedScore = scoreOverride.trim() === '' ? null : Number(scoreOverride);
    if (!content.trim() && normalizedScore === null) {
      return;
    }
    onSubmit({
      author: 'web',
      type: annotationType,
      content: content.trim() || 'Manual score override',
      score_override: Number.isFinite(normalizedScore) ? normalizedScore : null,
    });
    setContent('');
    setScoreOverride('');
    setAnnotationType('comment');
  }

  return (
    <section className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-gray-900">Annotations</h3>
          <p className="mt-1 text-xs text-gray-500">{existingAnnotations.length} existing notes</p>
        </div>
      </div>

      <div className="mt-4 space-y-3">
        {existingAnnotations.map((annotation) => (
          <div key={`${annotation.timestamp}-${annotation.author}`} className="rounded-xl border border-gray-200 bg-gray-50 p-3">
            <div className="flex items-center justify-between gap-3">
              <p className="text-xs font-semibold text-gray-700">{annotation.author}</p>
              <span className="rounded-full bg-white px-2 py-0.5 text-[11px] font-medium text-gray-600">
                {annotation.type}
              </span>
            </div>
            <p className="mt-2 text-sm text-gray-700">{annotation.content}</p>
          </div>
        ))}
      </div>

      <div className="mt-4 space-y-3 rounded-xl border border-gray-200 bg-gray-50 p-3">
        <label className="space-y-1 text-sm text-gray-700">
          <span>Annotation type</span>
          <select
            value={annotationType}
            onChange={(event) => setAnnotationType(event.target.value)}
            className="w-full rounded-xl border border-gray-300 bg-white px-3 py-2 text-sm focus:border-gray-900 focus:outline-none"
          >
            <option value="comment">Comment</option>
            <option value="override">Override</option>
            <option value="flag">Flag</option>
            <option value="correct">Correct</option>
          </select>
        </label>

        <label className="space-y-1 text-sm text-gray-700">
          <span>Annotation</span>
          <textarea
            aria-label="Annotation"
            value={content}
            onChange={(event) => setContent(event.target.value)}
            rows={4}
            placeholder="Capture why this result needs a manual note or correction."
            className="w-full rounded-xl border border-gray-300 bg-white px-3 py-2 text-sm focus:border-gray-900 focus:outline-none"
          />
        </label>

        <label className="space-y-1 text-sm text-gray-700">
          <span>Override score</span>
          <input
            value={scoreOverride}
            onChange={(event) => setScoreOverride(event.target.value)}
            placeholder="Optional, e.g. 1.0"
            className="w-full rounded-xl border border-gray-300 bg-white px-3 py-2 text-sm focus:border-gray-900 focus:outline-none"
          />
        </label>

        <button
          type="button"
          onClick={handleSubmit}
          disabled={isPending}
          className="inline-flex items-center rounded-xl bg-gray-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-gray-800 disabled:opacity-60"
        >
          {isPending ? 'Saving…' : 'Save annotation'}
        </button>
      </div>
    </section>
  );
}
