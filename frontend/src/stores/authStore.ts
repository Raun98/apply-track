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
          isAuthenticated: true,
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
          isHydrated = true;

          if (!error && state) {
            if (!state.accessToken || !state.refreshToken) {
              useAuthStore.setState({
                isAuthenticated: false,
                user: null,
                accessToken: null,
                refreshToken: null,
              });
            }
            useAuthStore.setState({ isLoading: false });
          } else if (state) {
            useAuthStore.setState({
              isAuthenticated: false,
              accessToken: null,
              refreshToken: null,
              user: null,
              isLoading: false,
            });
          }
        };
      },
    }
  )
);

export const isAuthHydrated = () => isHydrated;
