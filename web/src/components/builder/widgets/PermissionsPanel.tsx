import type { PermissionGrant } from '../../../lib/builder-types';
import { ActionButton } from './ActionButton';

interface PermissionsPanelProps {
  grants: PermissionGrant[];
  onRevoke?: (grantId: string) => void;
}

export function PermissionsPanel({ grants, onRevoke }: PermissionsPanelProps) {
  return (
    <div className="rounded-lg border border-slate-700 bg-slate-900/60 p-3">
      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">Permissions</p>
      {grants.length === 0 ? (
        <p className="text-xs text-slate-500">No active grants.</p>
      ) : (
        <div className="space-y-2">
          {grants.map((grant) => (
            <div key={grant.grant_id} className="rounded-md border border-slate-700 bg-slate-950/80 p-2">
              <p className="text-xs font-medium text-slate-200">{grant.action}</p>
              <p className="mt-0.5 text-[11px] text-slate-500">Scope: {grant.scope}</p>
              {onRevoke ? (
                <div className="mt-2">
                  <ActionButton
                    label="Revoke"
                    variant="ghost"
                    onClick={() => onRevoke(grant.grant_id)}
                  />
                </div>
              ) : null}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
