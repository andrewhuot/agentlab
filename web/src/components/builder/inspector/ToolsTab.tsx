interface ToolItem {
  id: string;
  name: string;
  description: string;
  attached: boolean;
}

interface ToolsTabProps {
  tools: ToolItem[];
}

export function ToolsTab({ tools }: ToolsTabProps) {
  return (
    <div className="space-y-2">
      {tools.length === 0 ? (
        <p className="rounded-md border border-slate-700 bg-slate-900/70 px-3 py-2 text-xs text-slate-500">
          No tools attached yet.
        </p>
      ) : (
        tools.map((tool) => (
          <div key={tool.id} className="rounded-md border border-slate-700 bg-slate-900/70 p-3">
            <div className="flex items-center justify-between gap-2">
              <p className="text-xs font-semibold text-slate-100">{tool.name}</p>
              <span className="rounded px-1.5 py-0.5 text-[11px] text-slate-300">
                {tool.attached ? 'attached' : 'available'}
              </span>
            </div>
            <p className="mt-1 text-[11px] text-slate-500">{tool.description}</p>
          </div>
        ))
      )}
    </div>
  );
}
