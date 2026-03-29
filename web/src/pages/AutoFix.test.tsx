import { beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AutoFix } from './AutoFix';

const apiMocks = vi.hoisted(() => ({
  useAutoFixProposals: vi.fn(),
  useAutoFixHistory: vi.fn(),
  useSuggestAutoFix: vi.fn(),
  useApplyAutoFix: vi.fn(),
  useRejectAutoFix: vi.fn(),
}));

vi.mock('../lib/api', () => ({
  useAutoFixProposals: apiMocks.useAutoFixProposals,
  useAutoFixHistory: apiMocks.useAutoFixHistory,
  useSuggestAutoFix: apiMocks.useSuggestAutoFix,
  useApplyAutoFix: apiMocks.useApplyAutoFix,
  useRejectAutoFix: apiMocks.useRejectAutoFix,
}));

vi.mock('../lib/toast', () => ({
  toastError: vi.fn(),
  toastInfo: vi.fn(),
  toastSuccess: vi.fn(),
}));

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/autofix']}>
      <AutoFix />
    </MemoryRouter>
  );
}

describe('AutoFix', () => {
  beforeEach(() => {
    apiMocks.useAutoFixProposals.mockReturnValue({
      data: [
        {
          proposal_id: 'fix-001',
          created_at: '2026-03-29T12:00:00Z',
          proposer_name: 'AutoFix Engine',
          opportunity_id: 'routing',
          operator_name: 'routing_edit',
          operator_params: { temperature: 0.2 },
          expected_lift: 0.11,
          affected_eval_slices: ['routing', 'latency'],
          risk_class: 'low',
          cost_impact_estimate: 0.01,
          diff_preview: '- route: default\n+ route: specialist',
          status: 'pending',
          rationale: 'Tighten routing around specialist handoff failures.',
        },
      ],
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });
    apiMocks.useAutoFixHistory.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });
    apiMocks.useSuggestAutoFix.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    });
    apiMocks.useApplyAutoFix.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    });
    apiMocks.useRejectAutoFix.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    });
  });

  it('allows a pending proposal to be rejected from the review card', async () => {
    const user = userEvent.setup();
    const rejectMutate = vi.fn();

    apiMocks.useRejectAutoFix.mockReturnValue({
      mutate: rejectMutate,
      isPending: false,
    });

    renderPage();

    expect(screen.getByText('Tighten routing around specialist handoff failures.')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Reject proposal' }));

    expect(rejectMutate).toHaveBeenCalledWith(
      { proposal_id: 'fix-001' },
      expect.any(Object)
    );
  });

  it('shows explicit recovery guidance when the autofix queries fail', () => {
    apiMocks.useAutoFixProposals.mockReturnValue({
      data: [],
      isLoading: false,
      isError: true,
      refetch: vi.fn(),
    });
    apiMocks.useAutoFixHistory.mockReturnValue({
      data: [],
      isLoading: false,
      isError: true,
      refetch: vi.fn(),
    });

    renderPage();

    expect(
      screen.getByText('Unable to load AutoFix proposals. Generate a fresh batch or retry the API.')
    ).toBeInTheDocument();
    expect(
      screen.getByText('Unable to load AutoFix history. Recent apply outcomes may be stale.')
    ).toBeInTheDocument();
  });
});
