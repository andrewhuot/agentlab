interface BuildtimeSkillsTabProps {
  skills: string[];
}

export function BuildtimeSkillsTab({ skills }: BuildtimeSkillsTabProps) {
  return (
    <div className="space-y-2">
      {skills.length === 0 ? (
        <p className="rounded-md border border-slate-700 bg-slate-900/70 px-3 py-2 text-xs text-slate-500">
          No buildtime skills installed.
        </p>
      ) : (
        skills.map((skill) => (
          <p key={skill} className="rounded-md border border-slate-700 bg-slate-900/70 px-3 py-2 text-xs text-slate-300">
            {skill}
          </p>
        ))
      )}
    </div>
  );
}
