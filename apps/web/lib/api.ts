import {
  User,
  Thread,
  Message,
  Draft,
  SyncResult,
  ClassifyStatus,
  Category,
  ChatResponse,
  APIError,
} from '@/lib/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Friendly error message for users
 */
export function friendlyMessage(error: unknown): string {
  if (!(error instanceof APIError)) {
    return 'Something went wrong. Please try again.';
  }

  switch (error.status) {
    case 401:
      return 'Your session expired. Please sign in again.';
    case 404:
      return 'That item no longer exists.';
    case 409:
      return 'This draft was already sent or is being sent.';
    case 429:
      return 'Rate limit or daily send cap reached. Try again later.';
    case 502:
      return 'Gmail or the AI service failed. Try again.';
    default:
      return error.message || 'Something went wrong.';
  }
}

/**
 * API client with automatic error handling and 401 redirects
 */
const apiClient = {
  async request<T>(
    method: 'GET' | 'POST' | 'PATCH' | 'DELETE',
    path: string,
    data?: unknown
  ): Promise<T> {
    try {
      const url = `${API_URL}${path}`;
      const options: RequestInit = {
        method,
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      };

      if (data) {
        options.body = JSON.stringify(data);
      }

      const response = await fetch(url, options);

      // Handle 401 - redirect to login
      if (response.status === 401) {
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
        throw new APIError(401, 'Session expired');
      }

      // Parse response
      let responseData: unknown;
      try {
        responseData = await response.json();
      } catch {
        responseData = null;
      }

      if (!response.ok) {
        const message =
          (responseData as { detail?: string })?.detail ||
          `HTTP ${response.status}`;
        throw new APIError(response.status, message);
      }

      return responseData as T;
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }
      throw new APIError(
        500,
        error instanceof Error ? error.message : 'Unknown error'
      );
    }
  },

  get<T>(path: string) {
    return this.request<T>('GET', path);
  },

  post<T>(path: string, data?: unknown) {
    return this.request<T>('POST', path, data);
  },

  patch<T>(path: string, data?: unknown) {
    return this.request<T>('PATCH', path, data);
  },

  delete<T>(path: string) {
    return this.request<T>('DELETE', path);
  },
};

export const api = {
  auth: {
    getLoginUrl: () => `${API_URL}/api/auth/login`,

    me: async () => apiClient.get<User>('/api/auth/me'),

    logout: async () => apiClient.post<{ status: string }>('/api/auth/logout'),

    disconnect: async () =>
      apiClient.post<{ status: string }>('/api/auth/disconnect'),

    deleteAccount: async () =>
      apiClient.delete<{ status: string }>('/api/account'),
  },

  threads: {
    list: async () => apiClient.get<Thread[]>('/api/threads'),

    get: async (threadId: string) =>
      apiClient.get<Thread & { messages: Message[] }>(
        `/api/threads/${threadId}`
      ),

    setCategory: async (threadId: string, category: string) =>
      apiClient.patch<Thread>(`/api/threads/${threadId}`, { category }),
  },

  sync: async () => apiClient.post<SyncResult>('/api/sync'),

  classify: async () =>
    apiClient.post<{ status: string }>('/api/classify'),

  status: async () => apiClient.get<ClassifyStatus>('/api/status'),

  drafts: {
    create: async (threadId: string, instruction: string) =>
      apiClient.post<Draft>(`/api/threads/${threadId}/drafts`, {
        instruction,
      }),

    list: async (threadId: string) =>
      apiClient.get<Draft[]>(`/api/threads/${threadId}/drafts`),

    update: async (draftId: string, updates: Partial<Draft>) =>
      apiClient.patch<Draft>(`/api/drafts/${draftId}`, updates),

    send: async (draftId: string) =>
      apiClient.post<{ status: string }>(`/api/drafts/${draftId}/send`),

    discard: async (draftId: string) =>
      apiClient.post<{ status: string }>(`/api/drafts/${draftId}/discard`),
  },

  categories: {
    list: async () => apiClient.get<Category[]>('/api/categories'),
  },

  chat: {
    ask: async (message: string) =>
      apiClient.post<ChatResponse>('/api/chat', { message }),
  },
};

export { APIError, friendlyMessage };
