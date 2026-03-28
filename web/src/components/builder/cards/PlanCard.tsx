import type { BuilderProposal } from '../../../lib/builder-types';
import { ActionButton } from '../widgets/ActionButton';

interface PlanCardProps {
  proposal: BuilderProposal;
  onApprove?: () => void;
  onReject?: () => void;
  onRevise?: () => void;
}

export function PlanCard({ proposal, onApprove, onReject, onRevise }: PlanCardProps) {
  return (
    <article className="rounded-xl border border-slate-700 bg-slate-900/80 p-4">
      <header className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Plan</p>
          <h3 className="mt-1 text-sm font-semibold text-slate-100">{proposal.goal}</h3>
        </div>
        <span className="rounded-md border border-slate-600 px-2 py-0.5 text-[11px] text-slate-300">
          {proposal.risk_level}
        </span>
      </header>

      {proposal.assumptions.length > 0 ? (
        <div className="mt-3">
          <p className="text-[11px] uppercase tracking-wide text-slate-500">Assumptions</p>
          <ul className="mt-1 space-y-1 text-xs text-slate-300">
            {proposal.assumptions.map((assumption) => (
              <li key={assumption}>• {assumption}</li>
            ))}
          </ul>
        </div>
      ) : null}

      <p className="mt-3 text-xs text-slate-400">Expected impact: {proposal.expected_impact}</p>

      <footer className="mt-3 flex flex-wrap items-center gap-2">
        {onApprove ? <ActionButton label="Approve" variant="primary" onClick={onApprove} /> : null}
        {onRevise ? <ActionButton label="Revise" onClick={onRevise} /> : null}
        {onReject ? <ActionButton label="Reject" variant="danger" onClick={onReject} /> : null}
      </footer>
    </article>
  );
}
