import { beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AdkImport } from './AdkImport';

const apiMocks = vi.hoisted(() => ({
  useAdkStatus: vi.fn(),
  useAdkImport: vi.fn(),
}));

vi.mock('../lib/api', () => ({
  useAdkStatus: apiMocks.useAdkStatus,
  useAdkImport: apiMocks.useAdkImport,
}));

vi.mock('../lib/toast', () => ({
  toastError: vi.fn(),
  toastSuccess: vi.fn(),
}));

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/adk/import']}>
      <AdkImport />
    </MemoryRouter>
  );
}

describe('AdkImport', () => {
  beforeEach(() => {
    apiMocks.useAdkStatus.mockReturnValue({
      data: {
        agent: {
          name: 'order_router',
          model: 'gpt-5-mini',
          tools: [{ name: 'lookup_order', description: 'Fetch order details' }],
          sub_agents: [{ name: 'billing', tools: [] }],
        },
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });
    apiMocks.useAdkImport.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
      data: null,
    });
  });

  it('shows next-step actions after a successful ADK import and lets the user reset the flow', async () => {
    const user = userEvent.setup();
    const mutate = vi.fn(
      (
        _payload: { path: string; output_dir?: string },
        options?: { onSuccess?: (value: unknown) => void }
      ) => {
        options?.onSuccess?.({
          agent_name: 'order_router',
          config_path: 'configs/order_router.yaml',
          snapshot_path: '.agentlab/order_router.snapshot.json',
          tools_imported: 3,
          surfaces_mapped: ['instructions', 'tools'],
        });
      }
    );

    apiMocks.useAdkImport.mockReturnValue({
      mutate,
      isPending: false,
      data: {
        agent_name: 'order_router',
        config_path: 'configs/order_router.yaml',
        snapshot_path: '.agentlab/order_router.snapshot.json',
        tools_imported: 3,
        surfaces_mapped: ['instructions', 'tools'],
      },
    });

    renderPage();

    await user.type(screen.getByLabelText('Agent directory'), '/tmp/order_router');
    await user.click(screen.getByRole('button', { name: 'Parse Agent' }));
    await user.click(screen.getByRole('button', { name: 'Import Agent' }));

    expect(screen.getByRole('link', { name: 'Run evaluations' })).toHaveAttribute('href', '/evals');
    expect(screen.getByRole('link', { name: 'Review configs' })).toHaveAttribute('href', '/configs');

    await user.click(screen.getByRole('button', { name: 'Import another agent' }));

    expect(screen.getByRole('button', { name: 'Parse Agent' })).toBeInTheDocument();
  });
});
