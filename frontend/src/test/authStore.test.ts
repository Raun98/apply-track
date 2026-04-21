/**
 * Unit tests for authStore — state transitions only (no network, no DOM).
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { useAuthStore } from '@/stores/authStore';
import type { AuthResponse } from '@/types';

const mockUser = {
  id: 1,
  email: 'test@example.com',
  is_active: true,
  created_at: '2024-01-01T00:00:00Z',
};

const mockAuthResponse: AuthResponse = {
  access_token: 'access-abc',
  refresh_token: 'refresh-xyz',
  token_type: 'bearer',
  user: mockUser,
};

// Reset store state between tests
beforeEach(() => {
  useAuthStore.setState({
    user: null,
    accessToken: null,
    refreshToken: null,
    isAuthenticated: false,
    isLoading: false,
  });
});

describe('authStore – setAuth', () => {
  it('populates user, tokens, and isAuthenticated on setAuth', () => {
    useAuthStore.getState().setAuth(mockAuthResponse);
    const state = useAuthStore.getState();

    expect(state.user).toEqual(mockUser);
    expect(state.accessToken).toBe('access-abc');
    expect(state.refreshToken).toBe('refresh-xyz');
    expect(state.isAuthenticated).toBe(true);
    expect(state.isLoading).toBe(false);
  });
});

describe('authStore – setTokens', () => {
  it('updates tokens and marks isAuthenticated without touching user', () => {
    useAuthStore.setState({ user: mockUser });
    useAuthStore.getState().setTokens('new-access', 'new-refresh');
    const state = useAuthStore.getState();

    expect(state.accessToken).toBe('new-access');
    expect(state.refreshToken).toBe('new-refresh');
    expect(state.isAuthenticated).toBe(true);
    expect(state.user).toEqual(mockUser);
  });
});

describe('authStore – logout', () => {
  it('clears all auth state on logout', () => {
    useAuthStore.getState().setAuth(mockAuthResponse);
    useAuthStore.getState().logout();
    const state = useAuthStore.getState();

    expect(state.user).toBeNull();
    expect(state.accessToken).toBeNull();
    expect(state.refreshToken).toBeNull();
    expect(state.isAuthenticated).toBe(false);
    expect(state.isLoading).toBe(false);
  });
});

describe('authStore – setLoading', () => {
  it('toggles isLoading', () => {
    useAuthStore.getState().setLoading(true);
    expect(useAuthStore.getState().isLoading).toBe(true);

    useAuthStore.getState().setLoading(false);
    expect(useAuthStore.getState().isLoading).toBe(false);
  });
});

describe('authStore – initial state', () => {
  it('starts unauthenticated', () => {
    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.accessToken).toBeNull();
    expect(state.user).toBeNull();
  });
});
