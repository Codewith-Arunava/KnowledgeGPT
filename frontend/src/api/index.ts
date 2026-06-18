import axios from 'axios';
import { useAuthStore } from '@/stores/authStore';

const api = axios.create({
  baseURL: (import.meta.env.VITE_API_URL || '') + '/api/v1',
  headers: { 'Content-Type': 'application/json' },
  timeout: 60000,
});

// ─── Request Interceptor ──────────────────────────────────────
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ─── Response Interceptor ─────────────────────────────────────
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;

    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      try {
        const refreshToken = useAuthStore.getState().refreshToken;
        if (!refreshToken) throw new Error('No refresh token');

        const { data } = await axios.post('/api/v1/auth/refresh', {
          refresh_token: refreshToken,
        });

        useAuthStore.getState().setAccessToken(data.access_token);
        original.headers.Authorization = `Bearer ${data.access_token}`;
        return api(original);
      } catch {
        useAuthStore.getState().logout();
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// ─── Auth ─────────────────────────────────────────────────────
export const authApi = {
  register: (data: { name: string; email: string; password: string }) =>
    api.post('/auth/register', data),
  login: (data: { email: string; password: string }) =>
    api.post('/auth/login', data),
  refresh: (refreshToken: string) =>
    api.post('/auth/refresh', { refresh_token: refreshToken }),
  logout: () => api.post('/auth/logout'),
  me: () => api.get('/auth/me'),
};

// ─── Knowledge Bases ──────────────────────────────────────────
export const kbApi = {
  list: () => api.get('/knowledge-bases/'),
  get: (id: string) => api.get(`/knowledge-bases/${id}`),
  create: (data: unknown) => api.post('/knowledge-bases/', data),
  update: (id: string, data: unknown) => api.put(`/knowledge-bases/${id}`, data),
  delete: (id: string) => api.delete(`/knowledge-bases/${id}`),
};

// ─── Documents ────────────────────────────────────────────────
export const documentsApi = {
  list: (kbId: string) => api.get(`/documents/${kbId}`),
  upload: (kbId: string, files: File[]) => {
    const formData = new FormData();
    files.forEach((f) => formData.append('files', f));
    return api.post(`/documents/upload/${kbId}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  delete: (docId: string) => api.delete(`/documents/${docId}`),
};

// ─── Chat ─────────────────────────────────────────────────────
export const chatApi = {
  send: (data: unknown) => api.post('/chat/', data),
  conversations: () => api.get('/chat/conversations'),
  conversation: (id: string) => api.get(`/chat/conversations/${id}`),
  deleteConversation: (id: string) => api.delete(`/chat/conversations/${id}`),
};

// ─── Analytics ────────────────────────────────────────────────
export const analyticsApi = {
  get: (days = 30) => api.get(`/analytics/?days=${days}`),
};

// ─── Evaluation ───────────────────────────────────────────────
export const evaluationApi = {
  get: (days = 30) => api.get(`/evaluation/?days=${days}`),
};

// ─── Feedback ─────────────────────────────────────────────────
export const feedbackApi = {
  submit: (data: unknown) => api.post('/feedback/', data),
};

export default api;
