import { render, screen } from '@testing-library/react';
import { createElement } from 'react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import App from '../App';
import { getNavigationSections } from '../lib/navigation';
import { CommandPalette } from './CommandPalette';
import { getRouteContext } from './Layout';
import { Sidebar } from './Sidebar';

vi.mock('../lib/websocket', () => ({
  wsClient: {
    connect: vi.fn(),
  },
}));

vi.mock('../lib/api', () => ({
  useConfigs: () => ({ data: [] }),
  useConversations: () => ({ data: [] }),
  useEvalRuns: () => ({ data: [] }),
  useBuilderArtifacts: () => ({ data: [] }),
  useSavedBuildArtifacts: () => ({ data: [] }),
  useTranscriptReports: () => ({ data: [] }),
  useImportTranscriptArchive: () => ({ mutate: vi.fn(), isPending: false }),
  useGenerateAgent: () => ({ mutate: vi.fn(), isPending: false }),
  useChatRefine: () => ({ mutate: vi.fn(), isPending: false }),
}));

describe('getRouteContext', () => {
  it('uses taxonomy labels for build aliases and review routes', () => {
    expect(getRouteContext('/builder/demo')).toEqual({
      title: 'Build',
      breadcrumbs: [{ label: 'Build' }],
    });

    expect(getRouteContext('/changes')).toEqual({
      title: 'Change Review',
      breadcrumbs: [
        { label: 'Optimize' },
        { label: 'Review' },
      ],
    });
  });

  it('keeps eval detail breadcrumbs under the Eval group', () => {
    expect(getRouteContext('/evals/run-1234567890')).toEqual({
      title: 'Eval Detail',
      breadcrumbs: [
        { label: 'Eval' },
        { label: 'Eval Runs', href: '/evals' },
        { label: 'Run run-1234' },
      ],
    });
  });

  it('falls back to AutoAgent when a route is unknown', () => {
    expect(getRouteContext('/totally-unknown')).toEqual({
      title: 'AutoAgent',
      breadcrumbs: [],
    });
  });
});

describe('Sidebar', () => {
  it('renders taxonomy-driven section headings', () => {
    render(createElement(MemoryRouter, null, createElement(Sidebar, { mobileOpen: true, onClose: vi.fn() })));

    expect(
      screen.getAllByRole('heading', { level: 3 }).map((heading) => heading.textContent)
    ).toEqual(getNavigationSections().map((section) => section.label));
  });
});

describe('CommandPalette', () => {
  it('shows top-level taxonomy navigation items', async () => {
    render(createElement(MemoryRouter, null, createElement(CommandPalette)));

    window.dispatchEvent(new Event('open-command-palette'));

    for (const section of getNavigationSections()) {
      expect((await screen.findAllByRole('button', { name: section.label })).length).toBeGreaterThan(0);
    }
  });
});

describe('App', () => {
  it('mounts the unified Build workspace at /build', async () => {
    window.history.pushState({}, '', '/build');

    render(createElement(App));

    expect(await screen.findByRole('heading', { name: 'Build', level: 2 })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Prompt' })).toBeInTheDocument();
  });

  it('redirects legacy builder aliases to /build', async () => {
    window.history.pushState({}, '', '/assistant');

    render(createElement(App));

    expect(window.location.pathname).toBe('/build');
    expect(window.location.search).toBe('?tab=builder-chat');
  });

  it('redirects transcript intelligence to the unified transcript tab', async () => {
    window.history.pushState({}, '', '/intelligence');

    render(createElement(App));

    expect(window.location.pathname).toBe('/build');
    expect(window.location.search).toBe('?tab=transcript');
    expect(await screen.findByRole('tab', { name: 'Transcript' })).toHaveAttribute(
      'aria-selected',
      'true'
    );
  });
});
