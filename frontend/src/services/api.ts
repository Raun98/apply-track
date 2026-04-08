import axios, { AxiosError, AxiosInstance } from 'axios';
import { useAuthStore } from '@/stores/authStore';

// In production, set VITE_API_BASE_URL to your backend URL
// Example: VITE_API_BASE_URL=https://backend-your-service.up.railway.app/api/v1
// In development, defaults to relative path for Vite proxy
const API_URL = (import.meta as any).env.VITE_API_BASE_URL || '/api/v1';

export const api: AxiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
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

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config;
    const authState = useAuthStore.getState();

    if (error.response?.status === 401 && originalRequest) {
      // Only try to refresh if we have a refresh token
      const refreshToken = authState.refreshToken;

      if (refreshToken) {
        try {
          const response = await axios.post(`${API_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });

          const { access_token } = response.data;
          useAuthStore.getState().setTokens(access_token, refreshToken);

          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        } catch (refreshError) {
          useAuthStore.getState().logout();
          // Only redirect to login if we were trying to use an expired token
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      }
      // If no refresh token, just reject the error (don't redirect)
      // The app will handle showing the landing page
    }

    return Promise.reject(error);
  }
);

// Auth API
export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),

  register: (email: string, password: string) =>
    api.post('/auth/register', { email, password }),

  refresh: (refreshToken: string) =>
    api.post('/auth/refresh', { refresh_token: refreshToken }),

  getMe: () => api.get('/auth/me'),
};

// Applications API
export const applicationsApi = {
  getAll: (params?: { status?: string; source?: string; search?: string; page?: number; page_size?: number }) =>
    api.get('/applications', { params }),

  getById: (id: number) => api.get(`/applications/${id}`),

  create: (data: unknown) => api.post('/applications', data),

  update: (id: number, data: unknown) => api.patch(`/applications/${id}`, data),

  delete: (id: number) => api.delete(`/applications/${id}`),

  getHistory: (id: number) => api.get(`/applications/${id}/history`),
};

// Board API
export const boardApi = {
  getColumns: () => api.get('/board/columns'),

  getApplications: () => api.get('/board/applications'),

  moveCard: (applicationId: number, toColumn: string, order: number = 0) =>
    api.post(`/board/cards/${applicationId}/move`, { to_column: toColumn, order }),

  getStats: () => api.get('/board/stats'),
};

// Email Accounts API
export const emailAccountsApi = {
  getAll: () => api.get('/email-accounts'),

  create: (data: unknown) => api.post('/email-accounts', data),

  delete: (id: number) => api.delete(`/email-accounts/${id}`),

  sync: (id: number) => api.post(`/email-accounts/${id}/sync`),
};

// Subscription API
export const subscriptionApi = {
  getPlans: () => api.get('/subscriptions/plans'),

  getCurrent: () => api.get('/subscriptions/current'),

  create: (data: { plan_id: number }) => api.post('/subscriptions/create', data),

  cancel: (subscriptionId: number) => api.post(`/subscriptions/cancel/${subscriptionId}`),
};
