import { beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { EvalGenerator } from './EvalGenerator';

const apiMocks = vi.hoisted(() => ({
  useGenerateEvals: vi.fn(),
}));

vi.mock('../lib/api', () => ({
  useGenerateEvals: apiMocks.useGenerateEvals,
}));

const toastMocks = vi.hoisted(() => ({
  toastError: vi.fn(),
  toastSuccess: vi.fn(),
}));

vi.mock('../lib/toast', () => ({
  toastError: toastMocks.toastError,
  toastSuccess: toastMocks.toastSuccess,
}));

function renderGenerator(props: Partial<Parameters<typeof EvalGenerator>[0]> = {}) {
  return render(
    <MemoryRouter>
      <EvalGenerator {...props} />
    </MemoryRouter>,
  );
}

describe('EvalGenerator', () => {
  let mutateFn: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    mutateFn = vi.fn();
    apiMocks.useGenerateEvals.mockReturnValue({
      mutate: mutateFn,
      isPending: false,
    });
    toastMocks.toastError.mockClear();
    toastMocks.toastSuccess.mockClear();
  });

  it('renders the form with agent name input and config textarea', () => {
    renderGenerator();

    expect(screen.getByLabelText('Agent Name')).toBeInTheDocument();
    expect(screen.getByLabelText('Agent Config (JSON)')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Generate Eval Suite/i })).toBeInTheDocument();
  });

  it('generate button is disabled when config is empty', () => {
    renderGenerator();

    const button = screen.getByRole('button', { name: /Generate Eval Suite/i });
    expect(button).toBeDisabled();
  });

  it('shows error toast on invalid JSON', async () => {
    const user = userEvent.setup();
    renderGenerator();

    await user.type(screen.getByLabelText('Agent Config (JSON)'), 'not valid json');
    await user.click(screen.getByRole('button', { name: /Generate Eval Suite/i }));

    expect(toastMocks.toastError).toHaveBeenCalledWith('Invalid JSON in agent config');
    expect(mutateFn).not.toHaveBeenCalled();
  });

  it('calls mutation with parsed config on valid submission', async () => {
    const user = userEvent.setup();
    renderGenerator();

    const config = '{"model":"claude-sonnet-4-20250514"}';

    await user.type(screen.getByLabelText('Agent Name'), 'my-agent');
    fireEvent.change(screen.getByLabelText('Agent Config (JSON)'), { target: { value: config } });
    await user.click(screen.getByRole('button', { name: /Generate Eval Suite/i }));

    expect(mutateFn).toHaveBeenCalledWith(
      { agent_config: { model: 'claude-sonnet-4-20250514' }, agent_name: 'my-agent' },
      expect.objectContaining({ onSuccess: expect.any(Function), onError: expect.any(Function) }),
    );
  });

  it('shows success state after generation', async () => {
    const user = userEvent.setup();
    const onSuiteGenerated = vi.fn();

    // Make mutate invoke the onSuccess callback immediately
    mutateFn.mockImplementation((_payload: unknown, opts: { onSuccess: (data: { suite_id: string; total_cases: number }) => void }) => {
      opts.onSuccess({ suite_id: 'suite_abc123', total_cases: 12 });
    });

    renderGenerator({ onSuiteGenerated });

    fireEvent.change(screen.getByLabelText('Agent Config (JSON)'), { target: { value: '{"model":"test"}' } });
    await user.click(screen.getByRole('button', { name: /Generate Eval Suite/i }));

    expect(toastMocks.toastSuccess).toHaveBeenCalledWith('Generated 12 eval cases');
    expect(screen.getByText('Eval Suite Generated')).toBeInTheDocument();
    expect(screen.getByText(/suite_abc123/)).toBeInTheDocument();
    expect(screen.getByText(/12 eval cases/)).toBeInTheDocument();
    expect(onSuiteGenerated).toHaveBeenCalledWith('suite_abc123');
  });
});
