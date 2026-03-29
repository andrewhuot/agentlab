import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ChevronDown, ChevronRight, TrendingDown, TrendingUp, Minus } from 'lucide-react';
import { useSearchParams } from 'react-router-dom';
import { PageHeader } from '../components/PageHeader';
import { classNames } from '../lib/utils';

const API_BASE = '/api';

const timeWindows = [
  { label: '1h', seconds: 3600 },
  { label: '6h', seconds: 21600 },
  { label: '24h', seconds: 86400 },
  { label: '7d', seconds: 604800 },
] as const;

interface BlameCluster {
  id: string;
  grader_name: string;
  agent_path: string;
  failure_reason: string;
  count: number;
  impact: number;
  trend: 'up' | 'down' | 'flat';
  traces: { trace_id: string; timestamp: string; summary: string }[];
}

interface RawBlameCluster {
  cluster_id?: string;
  grader_name?: string;
  agent_path?: string;
  failure_reason?: string;
  count?: number;
  impact_score?: number;
  trend?: string;
  example_trace_ids?: string[];
  first_seen?: number;
  last_seen?: number;
}

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json() as Promise<T>;
}

function normalizeTrend(trend: string | undefined): 'up' | 'down' | 'flat' {
  if (trend === 'growing' || trend === 'up') {
    return 'up';
  }
  if (trend === 'shrinking' || trend === 'down') {
    return 'down';
  }
  return 'flat';
}

function normalizeBlameClusters(payload: { clusters?: RawBlameCluster[] } | RawBlameCluster[]): BlameCluster[] {
  const rawClusters = Array.isArray(payload) ? payload : payload.clusters ?? [];

  return rawClusters.map((cluster, index) => {
    const failureReason = cluster.failure_reason ?? 'Unspecified failure';
    const traceIds = Array.isArray(cluster.example_trace_ids) ? cluster.example_trace_ids : [];
    const lastSeen = cluster.last_seen ?? cluster.first_seen ?? Date.now() / 1000;
    const firstSeen = cluster.first_seen ?? lastSeen;

    return {
      id: cluster.cluster_id ?? `cluster-${index + 1}`,
      grader_name: cluster.grader_name ?? 'unknown',
      agent_path: cluster.agent_path ?? 'unknown',
      failure_reason: failureReason,
      count: cluster.count ?? 0,
      impact: cluster.impact_score ?? 0,
      trend: normalizeTrend(cluster.trend),
      traces: traceIds.map((traceId, traceIndex) => ({
        trace_id: traceId,
        timestamp: new Date((traceIndex === 0 ? lastSeen : firstSeen) * 1000).toISOString(),
        summary: failureReason,
      })),
    };
  });
}

function TrendIcon({ trend }: { trend: 'up' | 'down' | 'flat' }) {
  if (trend === 'up') return <TrendingUp className="h-3.5 w-3.5 text-red-500" />;
  if (trend === 'down') return <TrendingDown className="h-3.5 w-3.5 text-green-500" />;
  return <Minus className="h-3.5 w-3.5 text-gray-400" />;
}

export function BlameMap() {
  const [searchParams] = useSearchParams();
  const [windowSeconds, setWindowSeconds] = useState(86400);
  const [expandedCluster, setExpandedCluster] = useState<string | null>(null);
  const requestedFilter = searchParams.get('filter');

  const blameQuery = useQuery({
    queryKey: ['blame', windowSeconds],
    queryFn: async () => {
      const payload = await fetchJson<{ clusters?: RawBlameCluster[] }>(`/traces/blame?window=${windowSeconds}`);
      return normalizeBlameClusters(payload);
    },
  });

  function toggleCluster(id: string) {
    setExpandedCluster((current) => (current === id ? null : id));
  }

  const clusters = (blameQuery.data ?? []).filter((cluster) => {
    if (!requestedFilter) {
      return true;
    }
    return cluster.failure_reason === requestedFilter;
  });
  const maxImpact = clusters.length > 0 ? Math.max(...clusters.map((c) => c.impact)) : 1;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Blame Map"
        description="Top failure clusters ranked by impact with contributing traces"
      />

      {/* Time window selector */}
      <div className="flex items-center gap-2 rounded-xl border border-gray-200 bg-white px-4 py-3">
        <span className="text-xs text-gray-500">Time window</span>
        <div className="flex gap-1">
          {timeWindows.map(({ label, seconds }) => (
            <button
              key={seconds}
              onClick={() => {
                setWindowSeconds(seconds);
                setExpandedCluster(null);
              }}
              className={classNames(
                'rounded-lg px-3 py-1.5 text-sm font-medium transition-colors',
                windowSeconds === seconds
                  ? 'bg-gray-900 text-white'
                  : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
              )}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Loading / error states */}
      {blameQuery.isLoading && (
        <div className="flex h-32 items-center justify-center rounded-xl border border-dashed border-gray-200 bg-gray-50 text-sm text-gray-500">
          Loading blame clusters...
        </div>
      )}
      {blameQuery.isError && (
        <div className="flex h-32 items-center justify-center rounded-xl border border-dashed border-red-200 bg-red-50 text-sm text-red-600">
          Failed to load blame data.
        </div>
      )}

      {/* Cluster cards */}
      {!blameQuery.isLoading && !blameQuery.isError && (
        <div className="space-y-2">
          {clusters.length === 0 ? (
            <div className="flex h-32 items-center justify-center rounded-xl border border-dashed border-gray-200 bg-gray-50 text-sm text-gray-500">
              No blame clusters in this time window.
            </div>
          ) : (
            clusters.map((cluster, index) => {
              const isExpanded = expandedCluster === cluster.id;
              const impactPercent = Math.round((cluster.impact / maxImpact) * 100);

              return (
                <div
                  key={cluster.id}
                  className="rounded-xl border border-gray-200 bg-white transition-colors"
                >
                  {/* Cluster header */}
                  <button
                    onClick={() => toggleCluster(cluster.id)}
                    className="flex w-full items-center gap-3 px-4 py-3 text-left"
                  >
                    {isExpanded ? (
                      <ChevronDown className="h-4 w-4 shrink-0 text-gray-400" />
                    ) : (
                      <ChevronRight className="h-4 w-4 shrink-0 text-gray-400" />
                    )}

                    <span className="flex h-5 w-5 items-center justify-center rounded-full bg-gray-100 text-[11px] font-medium text-gray-600">
                      {index + 1}
                    </span>

                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-gray-900">{cluster.grader_name}</span>
                        <span className="rounded-md bg-gray-100 px-2 py-0.5 text-[11px] text-gray-500">
                          {cluster.agent_path}
                        </span>
                      </div>
                      <p className="mt-0.5 truncate text-xs text-gray-500">{cluster.failure_reason}</p>
                    </div>

                    {/* Impact bar */}
                    <div className="flex w-32 items-center gap-2">
                      <div className="h-2 flex-1 overflow-hidden rounded-full bg-gray-200">
                        <div
                          className="h-full rounded-full bg-red-500"
                          style={{ width: `${impactPercent}%` }}
                        />
                      </div>
                    </div>

                    <span className="tabular-nums text-sm font-medium text-gray-700">{cluster.count}</span>
                    <TrendIcon trend={cluster.trend} />
                  </button>

                  {/* Expanded: contributing traces */}
                  {isExpanded && (
                    <div className="border-t border-gray-100 px-4 py-4">
                      <h4 className="text-xs font-medium text-gray-500">Contributing Traces</h4>
                      <div className="mt-2 space-y-1">
                        {cluster.traces.length === 0 ? (
                          <p className="text-xs text-gray-400">No traces available.</p>
                        ) : (
                          cluster.traces.map((trace) => (
                            <div
                              key={trace.trace_id}
                              className="flex items-center justify-between rounded-lg border border-gray-200 bg-gray-50 px-3 py-2"
                            >
                              <span className="font-mono text-xs text-gray-700">{trace.trace_id}</span>
                              <div className="flex items-center gap-3">
                                <span className="text-xs text-gray-500">{trace.summary}</span>
                                <span className="text-xs text-gray-400">{trace.timestamp}</span>
                              </div>
                            </div>
                          ))
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      )}
    </div>
  );
}
