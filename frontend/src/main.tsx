import React, { useEffect, useState } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import { useAuthStore } from './stores/authStore';
import { Loader2 } from 'lucide-react';
import './index.css';

function RootApp() {
  const { isLoading, setLoading, accessToken } = useAuthStore();
  const [initialized, setInitialized] = useState(false);

  useEffect(() => {
    // Initialize auth state on app load
    const initializeAuth = async () => {
      // If there's a token, we'll consider the user as authenticated
      // The app will validate it when making requests
      if (!accessToken) {
        // No token, so definitely not authenticated
        useAuthStore.setState({ isAuthenticated: false });
      }
      setLoading(false);
      setInitialized(true);
    };

    initializeAuth();
  }, []);

  if (!initialized) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-900">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <React.StrictMode>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </React.StrictMode>
  );
}

ReactDOM.createRoot(document.getElementById('root')!).render(<RootApp />);
