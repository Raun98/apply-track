/**
 * Debug utility for authentication issues
 * Use these functions to diagnose and fix auth-related problems
 */

export const authDebug = {
  /**
   * Check current authentication state
   */
  checkAuthState: () => {
    const authStorage = localStorage.getItem('auth-storage');
    console.log('Auth Storage:', authStorage ? JSON.parse(authStorage) : 'Empty');
  },

  /**
   * Force clear all authentication data
   * Call this if you're stuck in a redirect loop
   */
  clearAuthState: () => {
    localStorage.removeItem('auth-storage');
    console.log('Auth state cleared. Refreshing page...');
    setTimeout(() => {
      window.location.href = '/';
    }, 500);
  },

  /**
   * Reset to clean state and go to landing page
   */
  resetToLanding: () => {
    localStorage.removeItem('auth-storage');
    sessionStorage.clear();
    window.location.href = '/';
  },

  /**
   * Check if user has valid tokens
   */
  hasValidTokens: () => {
    const authStorage = localStorage.getItem('auth-storage');
    if (!authStorage) return false;
    try {
      const state = JSON.parse(authStorage);
      return !!(state.state?.accessToken && state.state?.isAuthenticated);
    } catch (e) {
      return false;
    }
  },
};

if (typeof window !== 'undefined' && !import.meta.env.PROD) {
  (window as any).authDebug = authDebug;
}
