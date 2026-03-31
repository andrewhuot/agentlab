import { describe, expect, it } from 'vitest';
import * as api from './api';

describe('api hook contract', () => {
  it('exports compare and results hooks used by the current pages', () => {
    expect(api.usePairwiseComparisons).toBeTypeOf('function');
    expect(api.usePairwiseComparison).toBeTypeOf('function');
    expect(api.useStartPairwiseComparison).toBeTypeOf('function');
    expect(api.useResultRuns).toBeTypeOf('function');
    expect(api.useResultsRun).toBeTypeOf('function');
    expect(api.useResultsDiff).toBeTypeOf('function');
    expect(api.useAddResultAnnotation).toBeTypeOf('function');
    expect(api.useExportEvalResults).toBeTypeOf('function');
  });
});
