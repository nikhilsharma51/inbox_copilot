import axios , { AxiosError } from 'axios';

import {
    User,
    Thread,
    ThreadDetail,
    SyncResult,
    ClassifyStatus,
    Category,
    ChatResponse,
    DraftResponse,
    DraftListItem,
    APIError,
} from '../types/api-types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
    url : API_URL,
    withCredentials : true, 
    headers :  {
        'Content-Type': 'application/json',
    },
    timeout: 30000,
})

apiClient.interceptors.response.use(
    (response) => response,
    (error: AxiosError<{ detail?: string }>) => {
        const status = error.response?.status ?? 500;
        const message =
            error.response?.data?.detail ||
            error.message ||
            'Unknown error';

        return Promise.reject(new APIError(status, message));
    }

);

export const api = {
    auth: {
        getLoginUrl: () => `${API_URL}/api/auth/login`,

        me: async () =>
            (await apiClient.get<User>('/api/auth/me')).data,

        logout: async () =>
            (await apiClient.post<{ status: string }>('/api/auth/logout')).data,

        disconnect: async () =>
            (await apiClient.post<{ status: string }>('/api/auth/disconnect')).data,

        deleteAccount: async () =>
            (await apiClient.delete<{ status: string }>('/api/account')).data,
    },

    threads: {
        list: async () =>
            (await apiClient.get<Thread[]>('/api/threads')).data,

        get: async (threadId: string) =>
            (await apiClient.get<ThreadDetail>(
                `/api/threads/${threadId}`
            )).data,

        sync: async () =>
            (await apiClient.post<SyncResult>('/api/sync')).data,
    },

    classify: {
        start: async () =>
            (await apiClient.post<{ started: boolean }>('/api/classify')).data,

        status: async () =>
            (await apiClient.get<ClassifyStatus>('/api/status')).data,
    },

    drafts: {
        create: async (
            threadId: string,
            instruction: string,
            style: string = 'professional'
        ) =>
            (
                await apiClient.post<DraftResponse>(
                    `/api/threads/${threadId}/drafts`,
                    { instruction, style }
                )
            ).data,

        list: async (threadId: string) =>
            (
                await apiClient.get<DraftListItem[]>(
                    `/api/threads/${threadId}/drafts`
                )
            ).data,

        edit: async (
            draftId: string,
            updates: { subject?: string; body?: string }
        ) =>
            (
                await apiClient.patch<DraftResponse>(
                    `/api/drafts/${draftId}`,
                    updates
                )
            ).data,

        discard: async (draftId: string) =>
            (
                await apiClient.post<{ status: string }>(
                    `/api/drafts/${draftId}/discard`
                )
            ).data,

        send: async (draftId: string) =>
            (
                await apiClient.post<{
                    status: string;
                    sent_at: string;
                }>(`/api/drafts/${draftId}/send`)
            ).data,
    },

    categories: {
        list: async () =>
            (await apiClient.get<Category[]>('/api/categories')).data,
    },

    chat: {
        ask: async (message: string) =>
            (
                await apiClient.post<ChatResponse>(
                    '/api/chat',
                    { message }
                )
            ).data,
    },

    health: {
        check: async (): Promise<boolean> => {
            try {
                const response = await apiClient.get('/healthz');
                return response.status >= 200 && response.status < 300;
            } catch {
                return false;
            }
        },
    },
};

export { APIError };
export { apiClient };
