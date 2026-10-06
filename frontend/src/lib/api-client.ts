// =============================================================================
// CyberLearn — Client API Axios
// Gère : token JWT, refresh automatique, erreurs globales
// =============================================================================

import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from "axios";
import { useAuthStore } from "@/lib/auth-store";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Instance Axios principale ─────────────────────────────────────────────────
const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: { "Content-Type": "application/json" },
  withCredentials: true, // Envoyer les cookies (refresh token)
  timeout: 30000,
});

// ── Intercepteur requête : ajouter le Bearer token ────────────────────────────
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = useAuthStore.getState().accessToken;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ── Intercepteur réponse : refresh automatique si 401 ────────────────────────
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value: unknown) => void;
  reject: (reason?: unknown) => void;
}> = [];

const processQueue = (error: AxiosError | null, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return apiClient(originalRequest);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const response = await axios.post(
          `${API_URL}/api/v1/auth/refresh`,
          {},
          { withCredentials: true }
        );
        const newToken = response.data.access_token;
        useAuthStore.getState().setAccessToken(newToken);
        processQueue(null, newToken);
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError as AxiosError, null);
        useAuthStore.getState().logout();
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

// ── API Functions ─────────────────────────────────────────────────────────────

export const authApi = {
  register: (data: unknown) => apiClient.post("/auth/register", data),
  login: (data: unknown) => apiClient.post("/auth/login", data),
  logout: () => apiClient.post("/auth/logout"),
  refresh: () => apiClient.post("/auth/refresh"),
  me: () => apiClient.get("/auth/me"),
};

export const catalogueApi = {
  getChapters: () => apiClient.get("/catalogue/chapters"),
  getMission: (id: number) => apiClient.get(`/catalogue/missions/${id}`),
};

export const sessionsApi = {
  startMission: (missionId: number) =>
    apiClient.post(`/sessions/missions/${missionId}/start`),
  sendCommand: (sessionId: number, command: string) =>
    apiClient.post(`/sessions/${sessionId}/command`, { command }),
  submitSolution: (sessionId: number, answer: string) =>
    apiClient.post(`/sessions/${sessionId}/submit`, { answer }),
  getHint: (sessionId: number) =>
    apiClient.post(`/sessions/${sessionId}/hint`),
  abandon: (sessionId: number) =>
    apiClient.patch(`/sessions/${sessionId}/abandon`),
  getResults: (sessionId: number) =>
    apiClient.get(`/sessions/${sessionId}/results`),
};

export const progressApi = {
  getMyProgress: () => apiClient.get("/progress/me"),
  getMyBadges: () => apiClient.get("/progress/me/badges"),
  getHistory: (limit = 20, offset = 0) =>
    apiClient.get(`/progress/me/history?limit=${limit}&offset=${offset}`),
  getLeaderboard: () => apiClient.get("/progress/leaderboard"),
};

export const recommendApi = {
  getRecommendations: (limit = 5) =>
    apiClient.get(`/recommendations/me?limit=${limit}`),
};

export const adminApi = {
  getStats: () => apiClient.get("/admin/stats"),
  getUsers: () => apiClient.get("/admin/users"),
  createChapter: (data: unknown) => apiClient.post("/admin/chapters", data),
  updateChapter: (id: number, data: unknown) => apiClient.put(`/admin/chapters/${id}`, data),
  createMission: (data: unknown) => apiClient.post("/admin/missions", data),
  updateMission: (id: number, data: unknown) => apiClient.put(`/admin/missions/${id}`, data),
};

export default apiClient;
