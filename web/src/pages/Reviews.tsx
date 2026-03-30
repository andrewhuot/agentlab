import { PageHeader } from '../components/PageHeader';

export function Reviews() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Collaborative Review"
        description="Team review workflows are staged behind the main CLI-aligned review surfaces for now."
        actions={<span className="rounded-full bg-sky-100 px-3 py-1 text-xs font-medium text-sky-800">Beta</span>}
      />
      <div className="rounded-lg border border-gray-200 bg-white p-8 text-center">
        <p className="text-gray-500">Use Change Review for the primary approval flow while collaborative review is still in beta.</p>
      </div>
    </div>
  );
}
