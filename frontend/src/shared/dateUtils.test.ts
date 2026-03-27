import { describe, it, expect } from 'vitest';
import { toDateInputValue, todayISO } from './dateUtils';

describe('dateUtils', () => {
  it('toDateInputValue extracts YYYY-MM-DD', () => {
    expect(toDateInputValue('2026-03-24T10:00:00Z')).toBe('2026-03-24');
  });

  it('todayISO returns YYYY-MM-DD format', () => {
    const today = todayISO();
    expect(today).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });
});
