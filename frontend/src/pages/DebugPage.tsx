import { useAuthStore } from '@/stores/authStore';

export function DebugPage() {
  const { isAuthenticated, accessToken, refreshToken, user } = useAuthStore();

  return (
    <div className="min-h-screen bg-slate-900 p-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-4xl font-bold text-white mb-8">Auth Debug Info</h1>
        
        <div className="bg-slate-800 rounded-lg p-6 space-y-4 font-mono text-sm">
          <div className="bg-slate-700 p-4 rounded">
            <div className="text-blue-300">isAuthenticated:</div>
            <div className="text-green-300 text-lg font-bold">{String(isAuthenticated)}</div>
          </div>

          <div className="bg-slate-700 p-4 rounded">
            <div className="text-blue-300">accessToken (first 20 chars):</div>
            <div className="text-yellow-300">
              {accessToken ? `${accessToken.substring(0, 20)}...` : 'NULL'}
            </div>
          </div>

          <div className="bg-slate-700 p-4 rounded">
            <div className="text-blue-300">refreshToken (first 20 chars):</div>
            <div className="text-yellow-300">
              {refreshToken ? `${refreshToken.substring(0, 20)}...` : 'NULL'}
            </div>
          </div>

          <div className="bg-slate-700 p-4 rounded">
            <div className="text-blue-300">user:</div>
            <div className="text-cyan-300">{JSON.stringify(user, null, 2)}</div>
          </div>

          <div className="bg-slate-700 p-4 rounded mt-6 pt-6 border-t border-slate-600">
            <div className="text-blue-300 mb-2">localStorage auth-storage:</div>
            <div className="text-purple-300 text-xs overflow-auto max-h-40">
              {localStorage.getItem('auth-storage') || 'NOT FOUND'}
            </div>
          </div>

          <button
            onClick={() => {
              localStorage.removeItem('auth-storage');
              window.location.href = '/';
            }}
            className="mt-6 bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded"
          >
            Clear Auth & Go to /
          </button>
        </div>
      </div>
    </div>
  );
}
