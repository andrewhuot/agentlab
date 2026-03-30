import { PageHeader } from '../components/PageHeader';

export function WhatIf() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="What-If Replay"
        description="Replay analysis remains visible for taxonomy completeness while the productized UI catches up."
        actions={<span className="rounded-full bg-sky-100 px-3 py-1 text-xs font-medium text-sky-800">Beta</span>}
      />
      <div className="rounded-lg border border-gray-200 bg-white p-8 text-center">
        <p className="text-gray-500">Use CLI what-if replay flows for now; the browser surface is still being expanded.</p>
      </div>
    </div>
  );
}
