import { enqueueOffline } from './offlineQueue';

const BASE_URL = import.meta.env.VITE_API_BASE_URL;

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const token = localStorage.getItem('ironlog_jwt');
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  try {
    const res = await fetch(`${BASE_URL}${path}`, {
      ...options,
      headers: { ...headers, ...options?.headers },
    });

    if (res.status === 401) {
      localStorage.removeItem('ironlog_jwt');
      localStorage.removeItem('ironlog_jwt_expires');
      window.location.hash = '#/login';
      throw new ApiError(401, 'Unauthorized');
    }

    const body = await res.json();

    if (!res.ok) {
      throw new ApiError(res.status, body.error || 'Request failed');
    }

    return body as T;
  } catch (err) {
    if (
      err instanceof TypeError &&
      !navigator.onLine &&
      options?.method &&
      options.method !== 'GET'
    ) {
      enqueueOffline({ path, method: options.method, body: options.body as string });
      return { queued: true } as T;
    }
    throw err;
  }
}
