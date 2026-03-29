import { useEffect, useMemo, useState } from 'react';
import { PauseCircle, PlayCircle, RefreshCw } from 'lucide-react';
import { useControlState, useLoopStatus, usePauseControl, useResumeControl, useStartLoop, useStopLoop } from '../lib/api';
import { wsClient } from '../lib/websocket';
import { EmptyState } from '../components/EmptyState';
import { LoadingSkeleton } from '../components/LoadingSkeleton';
import { PageHeader } from '../components/PageHeader';
import { ScoreChart } from '../components/ScoreChart';
import { StatusBadge } from '../components/StatusBadge';
import { toastError, toastInfo, toastSuccess } from '../lib/toast';
import { formatPercent, statusVariant } from '../lib/utils';

export function LoopMonitor() {
  const { data: loopStatus, isLoading, refetch } = useLoopStatus();
  const controlState = useControlState();
  const startLoop = useStartLoop();
  const stopLoop = useStopLoop();
  const pauseControl = usePauseControl();
  const resumeControl = useResumeControl();

  const [cycles, setCycles] = useState(10);
  const [delay, setDelay] = useState(1);
  const [windowSize, setWindowSize] = useState(100);

  useEffect(() => {
    const unsubscribe = wsClient.onMessage('loop_cycle', () => {
      refetch();
    });

    return () => unsubscribe();
  }, [refetch]);

  const trajectoryData = useMemo(() => {
    return (loopStatus?.cycle_history || []).map((cycle) => ({
      label: `#${cycle.cycle}`,
      score: cycle.health_success_rate * 100,
    }));
  }, [loopStatus?.cycle_history]);

  function handleStart() {
    startLoop.mutate(
      { cycles, delay, window: windowSize },
      {
        onSuccess: () => {
          toastInfo('Loop started', 'Continuous observe → optimize cycle is now running.');
          refetch();
        },
        onError: (error) => {
          toastError('Failed to start loop', error.message);
        },
      }
    );
  }

  function handleStop() {
    stopLoop.mutate(undefined, {
      onSuccess: () => {
        toastSuccess('Loop stopped', 'Loop execution has been halted.');
        refetch();
      },
      onError: (error) => {
        toastError('Failed to stop loop', error.message);
      },
    });
  }

  function handlePauseResume() {
    const mutation = controlState.data?.paused ? resumeControl : pauseControl;
    mutation.mutate(undefined, {
      onSuccess: () => {
        if (controlState.data?.paused) {
          toastSuccess('Optimization resumed', 'Loop observations stay live and proposal decisions are active again.');
        } else {
          toastInfo('Optimization paused', 'Loop observations continue while optimization decisions stay on hold.');
        }
        controlState.refetch();
      },
      onError: (error) => {
        toastError('Failed to update optimization controls', error.message);
      },
    });
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        <LoadingSkeleton rows={4} />
        <LoadingSkeleton rows={8} />
      </div>
    );
  }

  const running = loopStatus?.running ?? false;
  const optimizationPaused = controlState.data?.paused ?? false;
  const controlPending = pauseControl.isPending || resumeControl.isPending;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Loop Monitor"
        description="Observe continuous optimization cycles in real time and intervene when needed."
        actions={
          running ? (
            <button
              onClick={handleStop}
              disabled={stopLoop.isPending}
              className="inline-flex items-center gap-2 rounded-lg border border-red-300 bg-white px-3.5 py-2 text-sm font-medium text-red-700 transition hover:bg-red-50 disabled:opacity-60"
            >
              <PauseCircle className="h-4 w-4" />
              {stopLoop.isPending ? 'Stopping...' : 'Stop Loop'}
            </button>
          ) : (
            <button
              onClick={handleStart}
              disabled={startLoop.isPending}
              className="rounded-lg bg-gray-900 px-3.5 py-2 text-sm font-medium text-white transition hover:bg-gray-800 disabled:opacity-60"
            >
              {startLoop.isPending ? 'Starting...' : 'Start Loop'}
            </button>
          )
        }
      />

      <section className="rounded-lg border border-gray-200 bg-white p-5">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h3 className="text-sm font-semibold text-gray-900">Optimization Controls</h3>
            <p className="mt-1 text-sm text-gray-600">
              Pause optimization decisions while the loop keeps collecting data.
            </p>
            <p className="mt-2 text-xs text-gray-500">
              Use Stop Loop to end the current run. Pause only freezes proposals, approvals, and deploy decisions.
            </p>
          </div>
          <button
            onClick={handlePauseResume}
            disabled={controlPending}
            className="inline-flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-3.5 py-2 text-sm font-medium text-gray-700 transition hover:bg-gray-50 disabled:opacity-60"
          >
            {optimizationPaused ? <PlayCircle className="h-4 w-4" /> : <PauseCircle className="h-4 w-4" />}
            {optimizationPaused
              ? (resumeControl.isPending ? 'Resuming...' : 'Resume optimization')
              : (pauseControl.isPending ? 'Pausing...' : 'Pause optimization')}
          </button>
        </div>

        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <div className="rounded-lg border border-gray-200 bg-gray-50 p-3">
            <p className="text-xs text-gray-500">Loop run</p>
            <div className="mt-1">
              <StatusBadge variant={running ? 'running' : 'pending'} label={running ? 'running' : 'idle'} />
            </div>
          </div>
          <div className="rounded-lg border border-gray-200 bg-gray-50 p-3">
            <p className="text-xs text-gray-500">Optimization state</p>
            <div className="mt-1">
              <StatusBadge
                variant={statusVariant(optimizationPaused ? 'warning' : 'running')}
                label={optimizationPaused ? 'paused' : 'active'}
              />
            </div>
          </div>
        </div>
      </section>

      {!running && (
        <section className="rounded-lg border border-gray-200 bg-white p-4">
          <div className="grid gap-3 sm:grid-cols-3">
            <div>
              <label className="mb-1 block text-xs text-gray-500">Cycles</label>
              <input
                type="number"
                min={1}
                max={200}
                value={cycles}
                onChange={(event) => setCycles(Number(event.target.value))}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs text-gray-500">Delay (seconds)</label>
              <input
                type="number"
                min={0}
                max={60}
                value={delay}
                onChange={(event) => setDelay(Number(event.target.value))}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs text-gray-500">Observation window</label>
              <input
                type="number"
                min={10}
                max={1000}
                value={windowSize}
                onChange={(event) => setWindowSize(Number(event.target.value))}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
              />
            </div>
          </div>
        </section>
      )}

      <section className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <p className="text-xs text-gray-500">Status</p>
          <div className="mt-2">
            <StatusBadge variant={running ? 'running' : 'pending'} label={running ? 'running' : 'idle'} />
          </div>
        </div>
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <p className="text-xs text-gray-500">Progress</p>
          <p className="mt-1 text-2xl font-semibold text-gray-900">
            {loopStatus?.completed_cycles ?? 0}/{loopStatus?.total_cycles ?? 0}
          </p>
        </div>
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <p className="text-xs text-gray-500">Latest Success Rate</p>
          <p className="mt-1 text-2xl font-semibold text-gray-900">
            {loopStatus?.cycle_history.length
              ? formatPercent(loopStatus.cycle_history[loopStatus.cycle_history.length - 1].health_success_rate)
              : '0.0%'}
          </p>
        </div>
      </section>

      {trajectoryData.length > 0 && (
        <section className="rounded-lg border border-gray-200 bg-white p-5">
          <h3 className="mb-4 text-sm font-semibold text-gray-900">Score Trajectory (Success Rate)</h3>
          <ScoreChart data={trajectoryData} height={260} />
        </section>
      )}

      {loopStatus?.cycle_history && loopStatus.cycle_history.length > 0 ? (
        <section className="rounded-lg border border-gray-200 bg-white p-5">
          <h3 className="mb-4 text-sm font-semibold text-gray-900">Cycle Cards</h3>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {loopStatus.cycle_history
              .slice()
              .reverse()
              .map((cycle) => {
                const cycleStatus = cycle.optimization_run
                  ? cycle.deploy_result
                    ? 'accepted'
                    : 'rejected_no_improvement'
                  : 'pending';

                return (
                  <div key={cycle.cycle} className="rounded-lg border border-gray-200 bg-gray-50 p-4">
                    <div className="mb-2 flex items-center justify-between">
                      <p className="text-sm font-semibold text-gray-900">Cycle #{cycle.cycle}</p>
                      <StatusBadge variant={statusVariant(cycleStatus)} label={cycleStatus.replaceAll('_', ' ')} />
                    </div>
                    <p className="text-xs text-gray-600">
                      Success: {formatPercent(cycle.health_success_rate)} · Error: {formatPercent(cycle.health_error_rate)}
                    </p>
                    <p className="mt-2 text-sm text-gray-700">
                      {cycle.optimization_result || 'No optimization run this cycle.'}
                    </p>
                    {cycle.deploy_result && (
                      <p className="mt-2 text-xs text-green-700">Deploy: {cycle.deploy_result}</p>
                    )}
                    {cycle.canary_result && (
                      <p className="mt-1 text-xs text-gray-600">Canary: {cycle.canary_result}</p>
                    )}
                  </div>
                );
              })}
          </div>
        </section>
      ) : (
        !running && (
          <EmptyState
            icon={RefreshCw}
            title="No loop data yet"
            description="Start the loop to continuously observe quality and apply candidate improvements."
            actionLabel="Start Loop"
            onAction={handleStart}
          />
        )
      )}
    </div>
  );
}
