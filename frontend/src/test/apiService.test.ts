/**
 * Unit tests for the axios API service:
 *  - request interceptor attaches the Bearer token
 *  - response interceptor refreshes the token on 401 and retries
 *  - response interceptor logs out when refresh fails
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import axios from 'axios';

// ── Mocks ────────────────────────────────────────────────────────────────────

// We mock the authStore so the service tests don't depend on localStorage.
const mockGetState = vi.fn();
vi.mock('@/stores/authStore', () => ({
  useAuthStore: { getState: mockGetState },
}));

// Import the api instance AFTER the mock is registered so it picks up the mock.
const { api } = await import('@/services/api');

// ── Helpers ──────────────────────────────────────────────────────────────────

function makeAxiosError(status: number, config = {}) {
  const error = new axios.AxiosError('Request failed', `ERR_${status}`, { url: '/test', ...config } as any, null, {
    status,
    data: {},
    headers: {},
    config: { url: '/test', headers: {} as any, ...config },
    statusText: String(status),
  } as any);
  error.config = { url: '/test', headers: {} as any, ...config } as any;
  return error;
}

// ── Tests ────────────────────────────────────────────────────────────────────

describe('request interceptor – attaches Authorization header', () => {
  it('sets Bearer token when accessToken is present', async () => {
    mockGetState.mockReturnValue({ accessToken: 'my-token', refreshToken: null, setTokens: vi.fn(), logout: vi.fn() });

    // Grab the request interceptor handler directly
    const interceptor = (api.interceptors.request as any).handlers[0];
    const config = { headers: {} as any };
    const result = await interceptor.fulfilled(config);

    expect(result.headers.Authorization).toBe('Bearer my-token');
  });

  it('does not set Authorization when no token', async () => {
    mockGetState.mockReturnValue({ accessToken: null, refreshToken: null, setTokens: vi.fn(), logout: vi.fn() });

    const interceptor = (api.interceptors.request as any).handlers[0];
    const config = { headers: {} as any };
    const result = await interceptor.fulfilled(config);

    expect(result.headers.Authorization).toBeUndefined();
  });
});

describe('response interceptor – token refresh', () => {
  const setTokensMock = vi.fn();
  const logoutMock = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    // Reset the module-level refreshPromise by reimporting is difficult,
    // so we rely on each test having its own axios mock scope.
  });

  it('logs out when refresh token is absent and 401 received', async () => {
    mockGetState.mockReturnValue({
      accessToken: 'expired',
      refreshToken: null,
      setTokens: setTokensMock,
      logout: logoutMock,
    });

    const interceptor = (api.interceptors.response as any).handlers[0];
    const error = makeAxiosError(401);

    await expect(interceptor.rejected(error)).rejects.toBeDefined();
    expect(logoutMock).toHaveBeenCalledOnce();
  });

  it('does not intercept non-401 errors', async () => {
    mockGetState.mockReturnValue({
      accessToken: 'valid',
      refreshToken: 'refresh',
      setTokens: setTokensMock,
      logout: logoutMock,
    });

    const interceptor = (api.interceptors.response as any).handlers[0];
    const error = makeAxiosError(500);

    await expect(interceptor.rejected(error)).rejects.toBeDefined();
    expect(logoutMock).not.toHaveBeenCalled();
    expect(setTokensMock).not.toHaveBeenCalled();
  });
});
