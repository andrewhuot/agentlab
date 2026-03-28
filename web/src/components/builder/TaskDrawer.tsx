import type { ApprovalRequest, BuilderTask } from '../../lib/builder-types';
import { ApprovalCard } from './cards';
import { ActionButton } from './widgets';

interface TaskDrawerProps {
  open: boolean;
  runningTasks: BuilderTask[];
  completedTasks: BuilderTask[];
  approvals: ApprovalRequest[];
  onClose: () => void;
  onPauseTask?: (taskId: string) => void;
  onResumeTask?: (taskId: string) => void;
  onCancelTask?: (taskId: string) => void;
  onForkTask?: (taskId: string) => void;
  onApproveRequest?: (approvalId: string) => void;
  onRejectRequest?: (approvalId: string) => void;
}

export function TaskDrawer({
  open,
  runningTasks,
  completedTasks,
  approvals,
  onClose,
  onPauseTask,
  onResumeTask,
  onCancelTask,
  onForkTask,
  onApproveRequest,
  onRejectRequest,
}: TaskDrawerProps) {
  if (!open) {
    return null;
  }

  return (
    <div className="absolute inset-x-0 bottom-0 z-30 border-t border-slate-800 bg-slate-950/95 p-3">
      <div className="mb-2 flex items-center justify-between">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Task Drawer</p>
        <button
          type="button"
          onClick={onClose}
          className="rounded border border-slate-700 px-2 py-1 text-[11px] text-slate-400 transition hover:bg-slate-800"
        >
          Close
        </button>
      </div>

      <div className="grid gap-3 lg:grid-cols-3">
        <section className="rounded-lg border border-slate-700 bg-slate-900/70 p-3">
          <p className="text-xs font-semibold text-slate-200">Running</p>
          <div className="mt-2 space-y-1.5">
            {runningTasks.length === 0 ? <p className="text-[11px] text-slate-500">None</p> : null}
            {runningTasks.map((task) => (
              <div
                key={task.task_id}
                className="rounded border border-slate-700 bg-slate-950/70 px-2 py-2 text-xs text-slate-300"
              >
                <p>{task.title}</p>
                <p className="text-[11px] text-slate-500">{task.current_step || task.status}</p>
                <div className="mt-1 h-1.5 overflow-hidden rounded bg-slate-800">
                  <div
                    className="h-full bg-sky-500"
                    style={{ width: `${Math.max(0, Math.min(task.progress, 100))}%` }}
                  />
                </div>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {task.status === 'running' ? (
                    <ActionButton
                      label="Pause"
                      variant="ghost"
                      onClick={() => onPauseTask?.(task.task_id)}
                    />
                  ) : (
                    <ActionButton
                      label="Resume"
                      variant="ghost"
                      onClick={() => onResumeTask?.(task.task_id)}
                    />
                  )}
                  <ActionButton
                    label="Cancel"
                    variant="danger"
                    onClick={() => onCancelTask?.(task.task_id)}
                  />
                  <ActionButton
                    label="Fork"
                    variant="secondary"
                    onClick={() => onForkTask?.(task.task_id)}
                  />
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-lg border border-slate-700 bg-slate-900/70 p-3">
          <p className="text-xs font-semibold text-slate-200">Approvals</p>
          <div className="mt-2 space-y-2">
            {approvals.length === 0 ? <p className="text-[11px] text-slate-500">None</p> : null}
            {approvals.map((approval) => (
              <ApprovalCard
                key={approval.approval_id}
                approval={approval}
                onApprove={onApproveRequest ? () => onApproveRequest(approval.approval_id) : undefined}
                onReject={onRejectRequest ? () => onRejectRequest(approval.approval_id) : undefined}
              />
            ))}
          </div>
        </section>

        <section className="rounded-lg border border-slate-700 bg-slate-900/70 p-3">
          <p className="text-xs font-semibold text-slate-200">Completed</p>
          <div className="mt-2 space-y-1.5">
            {completedTasks.length === 0 ? <p className="text-[11px] text-slate-500">None</p> : null}
            {completedTasks.map((task) => (
              <div
                key={task.task_id}
                className="rounded border border-slate-700 bg-slate-950/70 px-2 py-2 text-xs text-slate-300"
              >
                <p>{task.title}</p>
                <p className="text-[11px] text-slate-500">{task.status}</p>
                {task.error ? <p className="mt-1 text-[11px] text-rose-300">{task.error}</p> : null}
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
