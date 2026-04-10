import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mail, Plus, Copy, Check, Briefcase } from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';

interface OnboardingEmptyStateProps {
  onAddApplication?: () => void;
}

export function OnboardingEmptyState({ onAddApplication }: OnboardingEmptyStateProps) {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [copied, setCopied] = useState(false);

  const inboxAddress = user?.inbox_address || '';

  const handleCopy = async () => {
    if (!inboxAddress) return;
    try {
      await navigator.clipboard.writeText(inboxAddress);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // fallback
    }
  };

  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      {/* Logo / Icon */}
      <div className="p-4 bg-blue-100 rounded-2xl mb-6">
        <Briefcase className="w-12 h-12 text-blue-600" />
      </div>

      <h2 className="text-2xl font-bold text-gray-900 mb-2">Welcome to ApplyTrack</h2>
      <p className="text-gray-500 mb-8 text-center max-w-md">
        Get started by connecting your email or adding your first application.
      </p>

      {/* Action Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full max-w-2xl mb-8">
        {/* Connect Email */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm hover:shadow-md transition-shadow">
          <div className="p-3 bg-blue-50 rounded-xl inline-block mb-4">
            <Mail className="w-6 h-6 text-blue-600" />
          </div>
          <h3 className="font-semibold text-gray-900 mb-2">Connect your email</h3>
          <p className="text-sm text-gray-500 mb-4">
            Link your email account so ApplyTrack can automatically detect and track job applications.
          </p>
          <button
            onClick={() => navigate('/email-settings')}
            className="w-full px-4 py-2 text-blue-600 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors font-medium text-sm"
          >
            Go to Email Settings
          </button>
        </div>

        {/* Add Application */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm hover:shadow-md transition-shadow">
          <div className="p-3 bg-green-50 rounded-xl inline-block mb-4">
            <Plus className="w-6 h-6 text-green-600" />
          </div>
          <h3 className="font-semibold text-gray-900 mb-2">Add your first application</h3>
          <p className="text-sm text-gray-500 mb-4">
            Manually add a job application to start tracking your progress on the board.
          </p>
          <button
            onClick={onAddApplication}
            className="w-full px-4 py-2 text-green-600 bg-green-50 rounded-lg hover:bg-green-100 transition-colors font-medium text-sm"
          >
            Add Application
          </button>
        </div>
      </div>

      {/* Forwarding Address */}
      {inboxAddress && (
        <div className="w-full max-w-2xl bg-blue-50 border border-blue-200 rounded-xl p-6">
          <h3 className="font-semibold text-blue-900 mb-2">Your forwarding address</h3>
          <p className="text-sm text-blue-700 mb-3">
            Forward job emails to this address and we'll track them automatically.
          </p>
          <div className="flex items-center bg-white rounded-lg border border-blue-200 px-4 py-2">
            <code className="text-sm text-gray-800 flex-1 truncate">{inboxAddress}</code>
            <button
              onClick={handleCopy}
              className="ml-2 p-1.5 text-blue-600 hover:bg-blue-50 rounded transition-colors flex-shrink-0"
              title="Copy to clipboard"
            >
              {copied ? <Check className="w-4 h-4 text-green-600" /> : <Copy className="w-4 h-4" />}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
