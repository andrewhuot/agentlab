import { PageHeader } from '../components/PageHeader';

export function Sandbox() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Sandbox Testing"
        description="The isolated execution workspace is visible in the taxonomy, but the full UI is still being hardened."
        actions={<span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800">Coming Soon</span>}
      />
      <div className="rounded-lg border border-gray-200 bg-white p-8 text-center">
        <p className="text-gray-500">Sandbox orchestration is not fully surfaced in the web console yet.</p>
      </div>
    </div>
  );
}
