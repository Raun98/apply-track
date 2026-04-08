import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import './index.css';
import { authDebug } from './lib/authDebug';

// Make auth debug tools available in console for troubleshooting
if (import.meta.env.DEV) {
  console.log('🔧 Auth Debug Tools Available:');
  console.log('  - authDebug.checkAuthState()    : Check current auth state');
  console.log('  - authDebug.clearAuthState()    : Clear auth and reload');
  console.log('  - authDebug.resetToLanding()    : Reset everything and go to /');
  console.log('  - authDebug.hasValidTokens()    : Check if user has valid tokens');
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
