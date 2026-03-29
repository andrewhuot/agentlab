import { describe, expect, it } from 'vitest';
import { getRouteContext } from './Layout';

describe('getRouteContext', () => {
  it('returns section-aware breadcrumbs for integration routes', () => {
    expect(getRouteContext('/cx/import')).toEqual({
      title: 'CX Import',
      breadcrumbs: [
        { label: 'Integrations' },
        { label: 'CX Import' },
      ],
    });
  });

  it('returns nested breadcrumbs for eval detail routes', () => {
    expect(getRouteContext('/evals/run-1234567890')).toEqual({
      title: 'Eval Detail',
      breadcrumbs: [
        { label: 'Operate' },
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
