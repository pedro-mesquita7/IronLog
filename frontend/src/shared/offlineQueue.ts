const QUEUE_KEY = 'ironlog_offline_queue';

interface QueuedRequest {
  path: string;
  method: string;
  body: string | null;
  timestamp: string;
}

export function enqueueOffline(req: { path: string; method: string; body: string | null }) {
  const queue = getQueue();
  queue.push({ ...req, timestamp: new Date().toISOString() });
  localStorage.setItem(QUEUE_KEY, JSON.stringify(queue));
}

export function getQueue(): QueuedRequest[] {
  try {
    return JSON.parse(localStorage.getItem(QUEUE_KEY) || '[]');
  } catch {
    return [];
  }
}

export function getQueueLength(): number {
  return getQueue().length;
}

export async function replayQueue(): Promise<number> {
  const queue = getQueue();
  if (queue.length === 0) return 0;

  const BASE_URL = import.meta.env.VITE_API_BASE_URL;
  const token = localStorage.getItem('ironlog_jwt');
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  let replayed = 0;
  const remaining: QueuedRequest[] = [];

  for (const req of queue) {
    try {
      const res = await fetch(`${BASE_URL}${req.path}`, {
        method: req.method,
        headers,
        body: req.body,
      });
      if (res.ok || res.status === 409) {
        replayed++;
      } else {
        remaining.push(req);
      }
    } catch {
      remaining.push(req);
      break;
    }
  }

  localStorage.setItem(QUEUE_KEY, JSON.stringify(remaining));
  return replayed;
}
