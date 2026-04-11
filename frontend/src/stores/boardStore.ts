import { create } from 'zustand';
import { Application, ApplicationStatus, BoardColumn, BoardData, StatsOverview } from '@/types';
import { authApi, boardApi } from '@/services/api';
import { useAuthStore } from '@/stores/authStore';

// ---------- WebSocket singleton ----------
let ws: WebSocket | null = null;
let wsReconnectTimer: ReturnType<typeof setTimeout> | null = null;
const WS_RECONNECT_DELAY_MS = 5000;

function getWsUrl(token: string): string {
  const apiBase = import.meta.env.VITE_API_BASE_URL;
  let host: string;
  if (apiBase) {
    // e.g. https://backend.railway.app/api/v1  → wss://backend.railway.app
    const url = new URL(apiBase);
    host = `${url.protocol === 'https:' ? 'wss' : 'ws'}://${url.host}`;
  } else {
    // Dev proxy — same host as the frontend
    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
    host = `${proto}://${window.location.host}`;
  }
  return `${host}/api/v1/ws?token=${encodeURIComponent(token)}`;
}

// ---------- Store ----------
interface BoardState {
  columns: BoardColumn[];
  applications: Record<ApplicationStatus, Application[]>;
  stats: StatsOverview | null;
  isLoading: boolean;
  error: string | null;
  wsConnected: boolean;

  // Actions
  fetchBoardData: () => Promise<void>;
  fetchStats: () => Promise<void>;
  moveApplication: (applicationId: number, toColumn: ApplicationStatus) => Promise<void>;
  updateApplicationInBoard: (application: Application) => void;
  addApplicationToBoard: (application: Application) => void;
  connectWebSocket: () => void;
  disconnectWebSocket: () => void;
}

export const useBoardStore = create<BoardState>((set, get) => ({
  columns: [],
  applications: {
    applied: [],
    screening: [],
    interview: [],
    offer: [],
    rejected: [],
    accepted: [],
  },
  stats: null,
  isLoading: false,
  error: null,
  wsConnected: false,

  fetchBoardData: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await boardApi.getApplications();
      const data: BoardData = response.data;
      set({
        columns: data.columns,
        applications: data.data,
        isLoading: false,
      });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch board data',
        isLoading: false,
      });
    }
  },

  fetchStats: async () => {
    try {
      const response = await boardApi.getStats();
      set({ stats: response.data });
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  },

  moveApplication: async (applicationId: number, toColumn: ApplicationStatus) => {
    try {
      await boardApi.moveCard(applicationId, toColumn);
      await get().fetchBoardData();
    } catch (error) {
      console.error('Failed to move application:', error);
      throw error;
    }
  },

  updateApplicationInBoard: (application: Application) => {
    const { applications } = get();
    const newApplications = { ...applications };

    // Remove from old column
    Object.keys(newApplications).forEach((status) => {
      newApplications[status as ApplicationStatus] = newApplications[
        status as ApplicationStatus
      ].filter((app) => app.id !== application.id);
    });

    // Add to new column
    newApplications[application.status].unshift(application);
    set({ applications: newApplications });
  },

  addApplicationToBoard: (application: Application) => {
    const { applications } = get();
    const newApplications = { ...applications };
    newApplications[application.status].unshift(application);
    set({ applications: newApplications });
  },

  // ---- WebSocket ----
  connectWebSocket: () => {
    const token = useAuthStore.getState().accessToken;
    if (!token || ws) return;

    const connect = () => {
      const currentToken = useAuthStore.getState().accessToken;
      if (!currentToken) return;

      ws = new WebSocket(getWsUrl(currentToken));

      ws.onopen = () => {
        set({ wsConnected: true });
        // Start ping/pong keepalive
        const ping = setInterval(() => {
          if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
          } else {
            clearInterval(ping);
          }
        }, 30_000);
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          const { fetchBoardData, fetchStats } = get();

          switch (msg.type) {
            case 'application_update':
            case 'new_application':
            case 'status_change':
              // Refresh both board and stats on any application event
              fetchBoardData();
              fetchStats();
              break;
            case 'new_email':
              // An email was processed — re-fetch to pick up any new card
              fetchBoardData();
              break;
            default:
              break;
          }
        } catch {
          // ignore malformed messages
        }
      };

      ws.onerror = () => {
        ws?.close();
      };

      ws.onclose = () => {
        ws = null;
        set({ wsConnected: false });
        // Auto-reconnect if user is still logged in
        if (useAuthStore.getState().isAuthenticated) {
          wsReconnectTimer = setTimeout(async () => {
            // Before reconnecting, refresh auth token if needed
            const { refreshToken } = useAuthStore.getState();
            if (refreshToken) {
              try {
                const res = await authApi.refresh(refreshToken);
                const { access_token } = res.data;
                useAuthStore.getState().setTokens(access_token, refreshToken);
              } catch {
                // Token refresh failed — user will be logged out by interceptor
                return;
              }
            }
            connect();
          }, WS_RECONNECT_DELAY_MS);
        }
      };
    };

    connect();
  },

  disconnectWebSocket: () => {
    if (wsReconnectTimer) {
      clearTimeout(wsReconnectTimer);
      wsReconnectTimer = null;
    }
    if (ws) {
      ws.onclose = null; // prevent auto-reconnect
      ws.close();
      ws = null;
    }
    set({ wsConnected: false });
  },
}));
