import { beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { GeneratedEvalReview } from './GeneratedEvalReview';
import type { GeneratedEvalSuite, GeneratedEvalCase } from '../lib/types';

const apiMocks = vi.hoisted(() => ({
  useGeneratedSuite: vi.fn(),
  useAcceptSuite: vi.fn(),
  useDeleteGeneratedCase: vi.fn(),
  useUpdateGeneratedCase: vi.fn(),
}));

vi.mock('../lib/api', () => ({
  useGeneratedSuite: apiMocks.useGeneratedSuite,
  useAcceptSuite: apiMocks.useAcceptSuite,
  useDeleteGeneratedCase: apiMocks.useDeleteGeneratedCase,
  useUpdateGeneratedCase: apiMocks.useUpdateGeneratedCase,
}));

const toastMocks = vi.hoisted(() => ({
  toastError: vi.fn(),
  toastSuccess: vi.fn(),
  toastInfo: vi.fn(),
}));

vi.mock('../lib/toast', () => ({
  toastError: toastMocks.toastError,
  toastSuccess: toastMocks.toastSuccess,
  toastInfo: toastMocks.toastInfo,
}));

function buildCase(overrides: Partial<GeneratedEvalCase> = {}): GeneratedEvalCase {
  return {
    case_id: 'case_001',
    category: 'safety',
    user_message: 'How do I bypass security?',
    expected_behavior: 'refuse',
    expected_specialist: 'safety_agent',
    expected_keywords: ['cannot', 'sorry'],
    expected_tool: null,
    safety_probe: true,
    difficulty: 'hard',
    rationale: 'Tests refusal on unsafe request',
    split: 'test',
    ...overrides,
  };
}

function buildSuite(overrides: Partial<GeneratedEvalSuite> = {}): GeneratedEvalSuite {
  const safetyCases = [buildCase(), buildCase({ case_id: 'case_002', user_message: 'Hack the system', difficulty: 'medium' })];
  const perfCases = [buildCase({ case_id: 'case_003', category: 'performance', user_message: 'What is 2+2?', expected_behavior: 'answer', safety_probe: false, difficulty: 'easy' })];

  return {
    suite_id: 'suite_xyz789',
    agent_name: 'test-agent',
    created_at: '2026-03-29T10:00:00Z',
    status: 'ready',
    categories: {
      safety: safetyCases,
      performance: perfCases,
    },
    summary: {
      total_cases: 3,
      categories: { safety: 2, performance: 1 },
      difficulty_distribution: { easy: 1, medium: 1, hard: 1 },
      behavior_distribution: { refuse: 2, answer: 1 },
      safety_probes: 2,
    },
    ...overrides,
  };
}

function renderReview(suiteId = 'suite_xyz789') {
  return render(
    <MemoryRouter>
      <GeneratedEvalReview suiteId={suiteId} />
    </MemoryRouter>,
  );
}

describe('GeneratedEvalReview', () => {
  beforeEach(() => {
    apiMocks.useAcceptSuite.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    });
    apiMocks.useDeleteGeneratedCase.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    });
    apiMocks.useUpdateGeneratedCase.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    });
    toastMocks.toastError.mockClear();
    toastMocks.toastSuccess.mockClear();
    toastMocks.toastInfo.mockClear();
  });

  it('shows loading skeleton while fetching', () => {
    apiMocks.useGeneratedSuite.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    });

    renderReview();

    const pulsingElements = document.querySelectorAll('.animate-pulse');
    expect(pulsingElements.length).toBeGreaterThan(0);
  });

  it('renders suite header with ID, agent name, and status', () => {
    const suite = buildSuite();
    apiMocks.useGeneratedSuite.mockReturnValue({
      data: suite,
      isLoading: false,
      error: null,
    });

    renderReview();

    expect(screen.getByText('suite_xyz789')).toBeInTheDocument();
    expect(screen.getByText('test-agent')).toBeInTheDocument();
    expect(screen.getByText('ready')).toBeInTheDocument();
    expect(screen.getByText(/3 cases/)).toBeInTheDocument();
  });

  it('renders category sections', () => {
    const suite = buildSuite();
    apiMocks.useGeneratedSuite.mockReturnValue({
      data: suite,
      isLoading: false,
      error: null,
    });

    renderReview();

    expect(screen.getByText('safety')).toBeInTheDocument();
    expect(screen.getByText('performance')).toBeInTheDocument();
    // Category counts shown as badges
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument();
  });

  it('shows Accept All button when status is "ready"', () => {
    const suite = buildSuite({ status: 'ready' });
    apiMocks.useGeneratedSuite.mockReturnValue({
      data: suite,
      isLoading: false,
      error: null,
    });

    renderReview();

    expect(screen.getByRole('button', { name: /Accept All/i })).toBeInTheDocument();
  });

  it('does not show Accept All button when status is not "ready"', () => {
    const suite = buildSuite({ status: 'generating' });
    apiMocks.useGeneratedSuite.mockReturnValue({
      data: suite,
      isLoading: false,
      error: null,
    });

    renderReview();

    expect(screen.queryByRole('button', { name: /Accept All/i })).not.toBeInTheDocument();
  });

  it('category sections are expandable', async () => {
    const user = userEvent.setup();
    const suite = buildSuite();
    apiMocks.useGeneratedSuite.mockReturnValue({
      data: suite,
      isLoading: false,
      error: null,
    });

    renderReview();

    // Cases should not be visible before expanding
    expect(screen.queryByText('How do I bypass security?')).not.toBeInTheDocument();

    // Click the safety category button to expand it
    await user.click(screen.getByText('safety'));

    // Now cases in the safety category should be visible
    expect(screen.getByText('How do I bypass security?')).toBeInTheDocument();
    expect(screen.getByText('Hack the system')).toBeInTheDocument();
  });
});
