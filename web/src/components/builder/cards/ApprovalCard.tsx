import type { ApprovalRequest } from '../../../lib/builder-types';
import { ActionButton } from '../widgets/ActionButton';

interface ApprovalCardProps {
  approval: ApprovalRequest;
  onApprove?: () => void;
  onReject?: () => void;
}

export function ApprovalCard({ approval, onApprove, onReject }: ApprovalCardProps) {
  return (
    <article className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4">
      <p className="text-[11px] font-semibold uppercase tracking-wide text-amber-300">Approval Needed</p>
      <h3 className="mt-1 text-sm font-semibold text-amber-50">{approval.action}</h3>
      <p className="mt-2 text-xs text-amber-100/80">{approval.description}</p>
      <p className="mt-1 text-[11px] text-amber-200/80">Scope: {approval.scope}</p>
      <div className="mt-3 flex gap-2">
        {onApprove ? <ActionButton label="Approve" variant="primary" onClick={onApprove} /> : null}
        {onReject ? <ActionButton label="Reject" variant="danger" onClick={onReject} /> : null}
      </div>
    </article>
  );
}
