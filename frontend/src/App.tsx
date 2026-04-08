import { useEffect, useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import { Layout } from '@/components/Layout';
import { LandingPage } from '@/pages/LandingPage';
import { LoginPage } from '@/pages/LoginPage';
import { RegisterPage } from '@/pages/RegisterPage';
import { BoardPage } from '@/pages/BoardPage';
import { DashboardPage } from '@/pages/DashboardPage';
import { ApplicationsPage } from '@/pages/ApplicationsPage';
import { EmailSettingsPage } from '@/pages/EmailSettingsPage';
import { SubscriptionPage } from '@/pages/SubscriptionPage';
import { Loader2 } from 'lucide-react';

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuthStore();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return isAuthenticated ? <>{children}</> : <Navigate to="/login" />;
}

function App() {
  const { isAuthenticated, accessToken, isLoading } = useAuthStore();
  const [hydrated, setHydrated] = useState(false);

  // Wait for Zustand to hydrate from localStorage
  useEffect(() => {
    // Small delay to ensure hydration is complete
    const timer = setTimeout(() => {
      setHydrated(true);
    }, 0);
    return () => clearTimeout(timer);
  }, []);

  // Show loader while hydrating
  if (!hydrated || isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-900">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  // User is authenticated if they have a valid access token
  const isUserAuthenticated = !!accessToken && isAuthenticated;

  return (
    <Routes>
      {/* Public routes - these take priority */}
      <Route path="/" element={isUserAuthenticated ? <Navigate to="/dashboard" /> : <LandingPage />} />
      <Route path="/login" element={isUserAuthenticated ? <Navigate to="/dashboard" /> : <LoginPage />} />
      <Route path="/register" element={isUserAuthenticated ? <Navigate to="/dashboard" /> : <RegisterPage />} />
      
      {/* Protected layout routes - will redirect to /login if not authenticated */}
      {isUserAuthenticated && (
        <Route
          element={<Layout />}
        >
          <Route path="board" element={<BoardPage />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="applications" element={<ApplicationsPage />} />
          <Route path="email-settings" element={<EmailSettingsPage />} />
          <Route path="subscription" element={<SubscriptionPage />} />
        </Route>
      )}

      {/* Redirect any other path to home for unauthenticated users */}
      {!isUserAuthenticated && <Route path="*" element={<Navigate to="/" replace />} />}
      {isUserAuthenticated && <Route path="*" element={<Navigate to="/dashboard" replace />} />}
    </Routes>
  );
}

export default App;
