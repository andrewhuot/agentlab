import { PageHeader } from '../components/PageHeader';

export function Knowledge() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Knowledge Mining"
        description="Knowledge extraction and synthesis remain under active development."
        actions={<span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800">Coming Soon</span>}
      />
      <div className="rounded-lg border border-gray-200 bg-white p-8 text-center">
        <p className="text-gray-500">Knowledge mining tools will arrive after the shared build and optimize surfaces settle.</p>
      </div>
    </div>
  );
}
