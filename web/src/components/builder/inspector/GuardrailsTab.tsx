interface GuardrailItem {
  id: string;
  name: string;
  scope: string;
}

interface GuardrailsTabProps {
  guardrails: GuardrailItem[];
}

export function GuardrailsTab({ guardrails }: GuardrailsTabProps) {
  return (
    <div className="space-y-2">
      {guardrails.length === 0 ? (
        <p className="rounded-md border border-slate-700 bg-slate-900/70 px-3 py-2 text-xs text-slate-500">
          No guardrails attached.
        </p>
      ) : (
        guardrails.map((guardrail) => (
          <div key={guardrail.id} className="rounded-md border border-slate-700 bg-slate-900/70 px-3 py-2">
            <p className="text-xs font-medium text-slate-200">{guardrail.name}</p>
            <p className="text-[11px] text-slate-500">Scope: {guardrail.scope}</p>
          </div>
        ))
      )}
    </div>
  );
}
