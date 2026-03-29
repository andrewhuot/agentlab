import { beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CxImport } from './CxImport';

const apiMocks = vi.hoisted(() => ({
  useCxAgents: vi.fn(),
  useCxImport: vi.fn(),
}));

vi.mock('../lib/api', () => ({
  useCxAgents: apiMocks.useCxAgents,
  useCxImport: apiMocks.useCxImport,
}));

vi.mock('../lib/toast', () => ({
  toastError: vi.fn(),
  toastSuccess: vi.fn(),
}));

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/cx/import']}>
      <CxImport />
    </MemoryRouter>
  );
}

describe('CxImport', () => {
  beforeEach(() => {
    apiMocks.useCxAgents.mockReturnValue({
      data: [
        {
          name: 'projects/demo/agents/support-bot',
          display_name: 'Support Bot',
          description: 'Primary support entry point',
          default_language_code: 'en',
        },
      ],
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });
    apiMocks.useCxImport.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
      data: null,
    });
  });

  it('shows next-step actions after a successful import and lets the user start over', async () => {
    const user = userEvent.setup();
    const mutate = vi.fn(
      (
        _payload: { project: string; location: string; agent_id: string },
        options?: { onSuccess?: (value: unknown) => void }
      ) => {
        options?.onSuccess?.({
          agent_name: 'Support Bot',
          config_path: 'configs/support.yaml',
          eval_path: 'evals/support.jsonl',
          test_cases_imported: 24,
          snapshot_path: '.autoagent/support.snapshot.json',
          surfaces_mapped: ['instructions', 'tools'],
        });
      }
    );

    apiMocks.useCxImport.mockReturnValue({
      mutate,
      isPending: false,
      data: {
        agent_name: 'Support Bot',
        config_path: 'configs/support.yaml',
        eval_path: 'evals/support.jsonl',
        test_cases_imported: 24,
        snapshot_path: '.autoagent/support.snapshot.json',
        surfaces_mapped: ['instructions', 'tools'],
      },
    });

    renderPage();

    await user.type(screen.getByLabelText('GCP project ID'), 'demo-project');
    await user.click(screen.getByRole('button', { name: 'List Agents' }));
    await user.click(screen.getByRole('button', { name: /Support Bot/i }));
    await user.click(screen.getByRole('button', { name: 'Import Agent' }));

    expect(screen.getByRole('link', { name: 'Run evaluations' })).toHaveAttribute('href', '/evals');
    expect(screen.getByRole('link', { name: 'Review configs' })).toHaveAttribute('href', '/configs');

    await user.click(screen.getByRole('button', { name: 'Import another agent' }));

    expect(screen.getByRole('button', { name: 'List Agents' })).toBeInTheDocument();
  });
});
