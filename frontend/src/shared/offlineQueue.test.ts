import { describe, it, expect, beforeEach } from 'vitest';
import { enqueueOffline, getQueue, getQueueLength } from './offlineQueue';

// Mock localStorage
const store: Record<string, string> = {};
const mockLocalStorage = {
  getItem: (key: string) => store[key] || null,
  setItem: (key: string, val: string) => { store[key] = val; },
  removeItem: (key: string) => { delete store[key]; },
};
Object.defineProperty(globalThis, 'localStorage', { value: mockLocalStorage });

describe('offlineQueue', () => {
  beforeEach(() => {
    Object.keys(store).forEach((k) => delete store[k]);
  });

  it('starts empty', () => {
    expect(getQueueLength()).toBe(0);
    expect(getQueue()).toEqual([]);
  });

  it('enqueues a request', () => {
    enqueueOffline({ path: '/sessions/1/sets', method: 'POST', body: '{"reps":5}' });
    expect(getQueueLength()).toBe(1);
    const q = getQueue();
    expect(q[0].path).toBe('/sessions/1/sets');
    expect(q[0].method).toBe('POST');
    expect(q[0].timestamp).toBeTruthy();
  });

  it('preserves FIFO order', () => {
    enqueueOffline({ path: '/a', method: 'POST', body: null });
    enqueueOffline({ path: '/b', method: 'PUT', body: null });
    const q = getQueue();
    expect(q[0].path).toBe('/a');
    expect(q[1].path).toBe('/b');
  });
});
