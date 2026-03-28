interface FilesTabProps {
  files: string[];
}

export function FilesTab({ files }: FilesTabProps) {
  return (
    <div className="space-y-1.5">
      {files.length === 0 ? (
        <p className="rounded-md border border-slate-700 bg-slate-900/70 px-3 py-2 text-xs text-slate-500">
          No files selected.
        </p>
      ) : (
        files.map((file) => (
          <p key={file} className="rounded-md border border-slate-700 bg-slate-900/70 px-3 py-2 font-mono text-[11px] text-slate-300">
            {file}
          </p>
        ))
      )}
    </div>
  );
}
