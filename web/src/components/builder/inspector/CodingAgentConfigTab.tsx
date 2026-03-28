interface CodingAgentConfigTabProps {
  agentsMd: string;
  claudeMd: string;
}

export function CodingAgentConfigTab({ agentsMd, claudeMd }: CodingAgentConfigTabProps) {
  return (
    <div className="space-y-3">
      <section className="rounded-md border border-slate-700 bg-slate-900/70 p-3">
        <p className="text-xs font-semibold text-slate-200">AGENTS.md</p>
        <pre className="mt-2 overflow-x-auto text-[11px] text-slate-500">{agentsMd || 'No AGENTS.md loaded.'}</pre>
      </section>
      <section className="rounded-md border border-slate-700 bg-slate-900/70 p-3">
        <p className="text-xs font-semibold text-slate-200">CLAUDE.md</p>
        <pre className="mt-2 overflow-x-auto text-[11px] text-slate-500">{claudeMd || 'No CLAUDE.md loaded.'}</pre>
      </section>
    </div>
  );
}
