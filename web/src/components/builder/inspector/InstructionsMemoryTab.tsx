interface InstructionsMemoryTabProps {
  projectInstruction: string;
  memoryNotes: string;
}

export function InstructionsMemoryTab({ projectInstruction, memoryNotes }: InstructionsMemoryTabProps) {
  return (
    <div className="space-y-3">
      <section className="rounded-md border border-slate-700 bg-slate-900/70 p-3">
        <p className="text-xs font-semibold text-slate-200">Project Instruction</p>
        <p className="mt-2 whitespace-pre-wrap text-[11px] text-slate-400">
          {projectInstruction || 'No project instruction set.'}
        </p>
      </section>
      <section className="rounded-md border border-slate-700 bg-slate-900/70 p-3">
        <p className="text-xs font-semibold text-slate-200">Memory</p>
        <p className="mt-2 whitespace-pre-wrap text-[11px] text-slate-400">
          {memoryNotes || 'No memory notes stored.'}
        </p>
      </section>
    </div>
  );
}
