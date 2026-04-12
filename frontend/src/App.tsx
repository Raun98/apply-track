import { Component, useEffect, useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore, isAuthHydrated } from '@/stores/authStore';
import { Layout } from '@/components/Layout';
import { LandingPage } from '@/pages/LandingPage';
import { LoginPage } from '@/pages/LoginPage';
import { RegisterPage } from '@/pages/RegisterPage';
import { BoardPage } from '@/pages/BoardPage';
import { DashboardPage } from '@/pages/DashboardPage';
import { ApplicationsPage } from '@/pages/ApplicationsPage';
import { EmailSettingsPage } from '@/pages/EmailSettingsPage';
import { SubscriptionPage } from '@/pages/SubscriptionPage';
import { DebugPage } from '@/pages/DebugPage';
import { AdminPage } from '@/pages/AdminPage';
import { Loader2 } from 'lucide-react';

class ErrorBoundary extends Component<{ children: React.ReactNode }, { hasError: boolean }> {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-slate-900">
          <div className="text-center">
            <p className="text-red-400 text-lg mb-2">Something went wrong</p>
            <button
              onClick={() => { this.setState({ hasError: false }); window.location.href = '/'; }}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Go Home
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

function App() {
  const { isAuthenticated, accessToken } = useAuthStore();
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    const startTime = Date.now();
    const MAX_WAIT = 3000;

    const checkHydration = () => {
      if (isAuthHydrated()) {
        setHydrated(true);
      } else if (Date.now() - startTime > MAX_WAIT) {
        setHydrated(true);
      } else {
        setTimeout(checkHydration, 10);
      }
    };

    checkHydration();
  }, []);

  if (!hydrated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-900">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  const isUserAuthenticated = !!(accessToken && accessToken.trim() && isAuthenticated);

  return (
    <ErrorBoundary>
      <Routes>
        {!import.meta.env.PROD && <Route path="/debug" element={<DebugPage />} />}

        <Route
          path="/"
          element={isUserAuthenticated ? <Navigate to="/dashboard" replace /> : <LandingPage />}
        />
        <Route
          path="/login"
          element={isUserAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginPage />}
        />
        <Route
          path="/register"
          element={isUserAuthenticated ? <Navigate to="/dashboard" replace /> : <RegisterPage />}
        />

        {isUserAuthenticated && (
          <>
            <Route element={<Layout />}>
              <Route path="board" element={<BoardPage />} />
              <Route path="dashboard" element={<DashboardPage />} />
              <Route path="applications" element={<ApplicationsPage />} />
              <Route path="email-settings" element={<EmailSettingsPage />} />
              <Route path="subscription" element={<SubscriptionPage />} />
              <Route path="admin" element={<AdminPage />} />
            </Route>
          </>
        )}

        {!isUserAuthenticated && <Route path="*" element={<Navigate to="/" replace />} />}
        {isUserAuthenticated && <Route path="*" element={<Navigate to="/dashboard" replace />} />}
      </Routes>
    </ErrorBoundary>
  );
}

export default App;
