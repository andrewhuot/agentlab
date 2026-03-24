import { useState } from 'react';
import { Activity } from 'lucide-react';
import { useSystemEvents } from '../lib/api';
import { LoadingSkeleton } from '../components/LoadingSkeleton';
import { PageHeader } from '../components/PageHeader';
import { formatTimestamp } from '../lib/utils';

export function EventLogPage() {
  const [eventType, setEventType] = useState('');
  const events = useSystemEvents({
    limit: 200,
    event_type: eventType.trim() || undefined,
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="System Event Log"
        description="Append-only timeline for mutations, evals, promotions, rollbacks, budget gates, and human overrides."
      />

      <section className="rounded-lg border border-gray-200 bg-white p-4">
        <label className="mb-1 block text-xs text-gray-500">Filter by event type</label>
        <input
          value={eventType}
          onChange={(event) => setEventType(event.target.value)}
          placeholder="candidate_promoted"
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
        />
      </section>

      {events.isLoading ? (
        <LoadingSkeleton rows={8} />
      ) : events.data && events.data.length > 0 ? (
        <section className="rounded-lg border border-gray-200 bg-white p-5">
          <div className="space-y-2">
            {events.data.map((entry) => (
              <div key={entry.id} className="rounded-lg border border-gray-200 bg-gray-50 p-3">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Activity className="h-3.5 w-3.5 text-gray-500" />
                    <p className="text-sm font-medium text-gray-900">{entry.event_type}</p>
                  </div>
                  <p className="text-xs text-gray-500">{formatTimestamp(entry.timestamp)}</p>
                </div>
                <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-gray-600">
                  {entry.cycle_id && <span>cycle: {entry.cycle_id}</span>}
                  {entry.experiment_id && <span>experiment: {entry.experiment_id}</span>}
                </div>
                {Object.keys(entry.payload || {}).length > 0 && (
                  <pre className="mt-2 overflow-x-auto rounded-md border border-gray-200 bg-white p-2 text-[11px] text-gray-700">
                    {JSON.stringify(entry.payload, null, 2)}
                  </pre>
                )}
              </div>
            ))}
          </div>
        </section>
      ) : (
        <section className="rounded-lg border border-dashed border-gray-200 bg-gray-50 p-8 text-center text-sm text-gray-500">
          No events found for the current filter.
        </section>
      )}
    </div>
  );
}
