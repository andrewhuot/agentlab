import type { TraceBookmark } from '../../../lib/builder-types';

interface TraceViewerTabProps {
  bookmarks: TraceBookmark[];
}

export function TraceViewerTab({ bookmarks }: TraceViewerTabProps) {
  return (
    <div className="space-y-2">
      {bookmarks.length === 0 ? (
        <p className="rounded-md border border-slate-700 bg-slate-900/70 px-3 py-2 text-xs text-slate-500">
          No trace bookmarks available.
        </p>
      ) : (
        bookmarks.map((bookmark) => (
          <div key={bookmark.bookmark_id} className="rounded-md border border-slate-700 bg-slate-900/70 p-3">
            <p className="text-xs font-medium text-slate-200">{bookmark.label}</p>
            <p className="mt-1 text-[11px] text-slate-500">Trace: {bookmark.trace_id}</p>
            <p className="text-[11px] text-slate-500">Span: {bookmark.span_id}</p>
          </div>
        ))
      )}
    </div>
  );
}
