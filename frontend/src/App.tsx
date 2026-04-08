import { useEffect, useState } from 'react';
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
import { Loader2 } from 'lucide-react';

function App() {
  const { isAuthenticated, accessToken } = useAuthStore();
  const [hydrated, setHydrated] = useState(false);

  // Check if Zustand has hydrated from localStorage
  useEffect(() => {
    const checkHydration = () => {
      if (isAuthHydrated()) {
        setHydrated(true);
      } else {
        // Check again in 10ms
        setTimeout(checkHydration, 10);
      }
    };
    
    checkHydration();
  }, []);

  // Show loader while hydrating
  if (!hydrated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-900">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  // User is authenticated ONLY if they have both accessToken AND isAuthenticated flag
  const isUserAuthenticated = !!accessToken && isAuthenticated;

  return (
    <Routes>
      {/* Public routes - unauthenticated users see these */}
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
      
      {/* Protected routes - only render if authenticated */}
      {isUserAuthenticated && (
        <>
          <Route element={<Layout />}>
            <Route path="board" element={<BoardPage />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="applications" element={<ApplicationsPage />} />
            <Route path="email-settings" element={<EmailSettingsPage />} />
            <Route path="subscription" element={<SubscriptionPage />} />
          </Route>
        </>
      )}

      {/* Catch-all fallback */}
      {!isUserAuthenticated && <Route path="*" element={<Navigate to="/" replace />} />}
      {isUserAuthenticated && <Route path="*" element={<Navigate to="/dashboard" replace />} />}
    </Routes>
  );
}

export default App;
