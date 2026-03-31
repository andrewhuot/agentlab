import { beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { render, screen } from '@testing-library/react';
import { Dashboard } from './Dashboard';

const apiMocks = vi.hoisted(() => ({
  useHealth: vi.fn(),
  useOptimizeHistory: vi.fn(),
  useControlState: vi.fn(),
  useCostHealth: vi.fn(),
  useEvalSetHealth: vi.fn(),
  useSystemEvents: vi.fn(),
  usePauseControl: vi.fn(),
  usePinSurface: vi.fn(),
  useRejectExperimentControl: vi.fn(),
  useResumeControl: vi.fn(),
  useUnpinSurface: vi.fn(),
}));

vi.mock('../lib/api', () => ({
  useHealth: apiMocks.useHealth,
  useOptimizeHistory: apiMocks.useOptimizeHistory,
  useControlState: apiMocks.useControlState,
  useCostHealth: apiMocks.useCostHealth,
  useEvalSetHealth: apiMocks.useEvalSetHealth,
  useSystemEvents: apiMocks.useSystemEvents,
  usePauseControl: apiMocks.usePauseControl,
  usePinSurface: apiMocks.usePinSurface,
  useRejectExperimentControl: apiMocks.useRejectExperimentControl,
  useResumeControl: apiMocks.useResumeControl,
  useUnpinSurface: apiMocks.useUnpinSurface,
}));

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/dashboard']}>
      <Dashboard />
    </MemoryRouter>
  );
}

describe('Dashboard', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => ({
        json: async () => ({ has_demo_data: false }),
      }))
    );

    Object.defineProperty(window, 'localStorage', {
      configurable: true,
      value: {
        getItem: vi.fn(() => 'true'),
        setItem: vi.fn(),
      },
    });

    apiMocks.useHealth.mockReturnValue({
      isLoading: false,
      data: {
        metrics: {
          success_rate: 0.91,
          error_rate: 0.04,
          safety_violation_rate: 0,
          avg_latency_ms: 240,
          avg_cost: 0.012,
        },
      },
      refetch: vi.fn(),
    });
    apiMocks.useOptimizeHistory.mockReturnValue({
      data: [
        {
          id: 'attempt-1',
          score_after: 0.91,
          status: 'accepted',
          created_at: '2026-03-31T10:00:00Z',
        },
      ],
      refetch: vi.fn(),
    });
    apiMocks.useControlState.mockReturnValue({
      isLoading: false,
      data: {
        paused: false,
        immutable_surfaces: [],
        rejected_experiments: [],
      },
      refetch: vi.fn(),
    });
    apiMocks.useCostHealth.mockReturnValue({
      data: { recent_cycles: [] },
      refetch: vi.fn(),
    });
    apiMocks.useEvalSetHealth.mockReturnValue({
      data: null,
      refetch: vi.fn(),
    });
    apiMocks.useSystemEvents.mockReturnValue({
      data: [],
      refetch: vi.fn(),
    });
    apiMocks.usePauseControl.mockReturnValue({ mutate: vi.fn() });
    apiMocks.usePinSurface.mockReturnValue({ mutate: vi.fn() });
    apiMocks.useRejectExperimentControl.mockReturnValue({ mutate: vi.fn() });
    apiMocks.useResumeControl.mockReturnValue({ mutate: vi.fn() });
    apiMocks.useUnpinSurface.mockReturnValue({ mutate: vi.fn() });
  });

  it('uses a professional scorecard title on the dashboard', async () => {
    renderPage();

    expect(await screen.findByRole('heading', { name: 'System Scorecard' })).toBeInTheDocument();
  });
});
