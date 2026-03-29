import { beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LoopMonitor } from './LoopMonitor';

const apiMocks = vi.hoisted(() => ({
  useLoopStatus: vi.fn(),
  useStartLoop: vi.fn(),
  useStopLoop: vi.fn(),
  useControlState: vi.fn(),
  usePauseControl: vi.fn(),
  useResumeControl: vi.fn(),
}));

vi.mock('../lib/api', () => ({
  useLoopStatus: apiMocks.useLoopStatus,
  useStartLoop: apiMocks.useStartLoop,
  useStopLoop: apiMocks.useStopLoop,
  useControlState: apiMocks.useControlState,
  usePauseControl: apiMocks.usePauseControl,
  useResumeControl: apiMocks.useResumeControl,
}));

vi.mock('../lib/toast', () => ({
  toastError: vi.fn(),
  toastInfo: vi.fn(),
  toastSuccess: vi.fn(),
}));

vi.mock('../lib/websocket', () => ({
  wsClient: {
    onMessage: vi.fn(() => vi.fn()),
  },
}));

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/loop']}>
      <LoopMonitor />
    </MemoryRouter>
  );
}

describe('LoopMonitor', () => {
  beforeEach(() => {
    apiMocks.useLoopStatus.mockReturnValue({
      data: {
        running: true,
        completed_cycles: 2,
        total_cycles: 10,
        cycle_history: [],
      },
      isLoading: false,
      refetch: vi.fn(),
    });
    apiMocks.useStartLoop.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    });
    apiMocks.useStopLoop.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    });
    apiMocks.useControlState.mockReturnValue({
      data: {
        paused: true,
        immutable_surfaces: [],
        rejected_experiments: [],
        last_injected_mutation: null,
        updated_at: '2026-03-29T12:00:00Z',
      },
    });
    apiMocks.usePauseControl.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    });
    apiMocks.useResumeControl.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    });
  });

  it('lets operators resume optimization without ending the active loop run', async () => {
    const user = userEvent.setup();
    const resumeMutate = vi.fn();

    apiMocks.useResumeControl.mockReturnValue({
      mutate: resumeMutate,
      isPending: false,
    });

    renderPage();

    expect(screen.getByText('Pause optimization decisions while the loop keeps collecting data.')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Resume optimization' }));

    expect(resumeMutate).toHaveBeenCalledTimes(1);
  });
});
