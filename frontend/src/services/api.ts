import axios, { AxiosError, AxiosInstance } from 'axios';
import { useAuthStore } from '@/stores/authStore';

const API_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export const api: AxiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().accessToken;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

let refreshPromise: Promise<any> | null = null;

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config;
    const authState = useAuthStore.getState();

    if (error.response?.status === 401 && originalRequest) {
      const refreshToken = authState.refreshToken;

      if (refreshToken) {
        if (!refreshPromise) {
          refreshPromise = axios.post(`${API_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          }).finally(() => {
            refreshPromise = null;
          });
        }

        try {
          const response = await refreshPromise;
          const { access_token } = response.data;
          useAuthStore.getState().setTokens(access_token, refreshToken);

          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        } catch (refreshError) {
          useAuthStore.getState().logout();
          return Promise.reject(refreshError);
        }
      }
      useAuthStore.getState().logout();
    }

    return Promise.reject(error);
  }
);

export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),

  register: (email: string, password: string) =>
    api.post('/auth/register', { email, password }),

  refresh: (refreshToken: string) =>
    api.post('/auth/refresh', { refresh_token: refreshToken }),

  getMe: () => api.get('/auth/me'),
};

export const applicationsApi = {
  getAll: (params?: { status?: string; source?: string; search?: string; page?: number; page_size?: number }) =>
    api.get('/applications', { params }),

  getById: (id: number) => api.get(`/applications/${id}`),

  create: (data: unknown) => api.post('/applications', data),

  update: (id: number, data: unknown) => api.patch(`/applications/${id}`, data),

  delete: (id: number) => api.delete(`/applications/${id}`),

  getHistory: (id: number) => api.get(`/applications/${id}/history`),

  getActivities: (id: number) => api.get(`/applications/${id}/activities`),

  addActivity: (id: number, data: { type: string; description: string; extra_data?: Record<string, unknown> }) =>
    api.post(`/applications/${id}/activities`, data),
};

export const boardApi = {
  getColumns: () => api.get('/board/columns'),

  getApplications: () => api.get('/board/applications'),

  moveCard: (applicationId: number, toColumn: string, order: number = 0) =>
    api.post(`/board/cards/${applicationId}/move`, { to_column: toColumn, order }),

  getStats: () => api.get('/board/stats'),
};

export const emailAccountsApi = {
  getAll: () => api.get('/email-accounts'),

  create: (data: unknown) => api.post('/email-accounts', data),

  delete: (id: number) => api.delete(`/email-accounts/${id}`),

  sync: (id: number) => api.post(`/email-accounts/${id}/sync`),

  getOAuthUrl: (provider: 'google' | 'microsoft') =>
    api.get<{ auth_url: string }>(`/email-accounts/oauth/${provider}/init`),
};

export const subscriptionApi = {
  getPlans: () => api.get('/subscriptions/plans'),

  getCurrent: () => api.get('/subscriptions/current'),

  create: (data: { plan_id: number }) => api.post('/subscriptions/create', data),

  cancel: (subscriptionId: number) => api.post(`/subscriptions/cancel/${subscriptionId}`),
};
