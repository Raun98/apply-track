import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User, AuthResponse } from '@/types';

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setAuth: (data: AuthResponse) => void;
  setTokens: (accessToken: string, refreshToken: string) => void;
  logout: () => void;
  setLoading: (loading: boolean) => void;
}

// Track if the store has been hydrated from localStorage
let isHydrated = false;

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,

      setAuth: (data: AuthResponse) => {
        set({
          user: data.user,
          accessToken: data.access_token,
          refreshToken: data.refresh_token,
          isAuthenticated: true,
          isLoading: false,
        });
      },

      setTokens: (accessToken: string, refreshToken: string) => {
        set({
          accessToken,
          refreshToken,
        });
      },

      logout: () => {
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
          isLoading: false,
        });
        // Clear localStorage to ensure clean state
        localStorage.removeItem('auth-storage');
      },

      setLoading: (loading: boolean) => {
        set({ isLoading: loading });
      },
    }),
    {
      name: 'auth-storage',
      onRehydrateStorage: () => {
        return (state, error) => {
          // Mark as hydrated when this callback is called
          isHydrated = true;
          
          if (!error && state) {
            // CRITICAL FIX: If no token exists, ensure isAuthenticated is false
            // This prevents redirect loops when localStorage is corrupted
            if (!state.accessToken || !state.refreshToken) {
              state.isAuthenticated = false;
              state.user = null;
              state.accessToken = null;
              state.refreshToken = null;
            }
            state.isLoading = false;
          } else {
            // If there's an error rehydrating, reset to unauthenticated
            if (state) {
              state.isAuthenticated = false;
              state.accessToken = null;
              state.refreshToken = null;
              state.user = null;
              state.isLoading = false;
            }
          }
        };
      },
    }
  )
);

// Export a function to check if hydration is complete
export const isAuthHydrated = () => isHydrated;
