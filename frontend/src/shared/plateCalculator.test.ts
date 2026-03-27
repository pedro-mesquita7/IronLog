import { describe, it, expect } from 'vitest';
import { calculatePlates } from './plateCalculator';

const plates = [
  { weight_kg: 20, quantity: 10 },
  { weight_kg: 15, quantity: 10 },
  { weight_kg: 10, quantity: 10 },
  { weight_kg: 5, quantity: 10 },
  { weight_kg: 2.5, quantity: 10 },
];

describe('calculatePlates', () => {
  it('returns empty for bar-only weight', () => {
    const result = calculatePlates(20, 20, plates);
    expect(result.perSide).toEqual([]);
    expect(result.totalWeight).toBe(20);
  });

  it('calculates simple plate setup', () => {
    const result = calculatePlates(60, 20, plates);
    expect(result.perSide).toEqual([20]);
    expect(result.totalWeight).toBe(60);
    expect(result.remainder).toBe(0);
  });

  it('handles mixed plates', () => {
    const result = calculatePlates(85, 20, plates);
    // (85 - 20) / 2 = 32.5 per side
    // greedy: 20 + 10 + 2.5 = 32.5
    expect(result.perSide).toEqual([20, 10, 2.5]);
    expect(result.totalWeight).toBe(85);
  });

  it('handles weight below bar', () => {
    const result = calculatePlates(15, 20, plates);
    expect(result.perSide).toEqual([]);
    expect(result.totalWeight).toBe(20);
  });

  it('reports remainder for un-loadable weight', () => {
    const result = calculatePlates(21, 20, plates);
    // (21 - 20) / 2 = 0.5 per side, no plate small enough
    expect(result.perSide).toEqual([]);
    expect(result.remainder).toBe(0.5);
  });

  it('respects plate quantity limits', () => {
    const limited = [{ weight_kg: 20, quantity: 2 }]; // only 1 pair
    const result = calculatePlates(100, 20, limited);
    // (100 - 20) / 2 = 40, but only one 20 per side
    expect(result.perSide).toEqual([20]);
    expect(result.totalWeight).toBe(60);
    expect(result.remainder).toBe(20);
  });
});
