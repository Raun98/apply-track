import { useEffect, useState } from 'react';
import { emailAccountsApi } from '@/services/api';
import { EmailAccount, EmailAccountCreate } from '@/types';
import { Mail, Plus, Trash2, RefreshCw, Check, X } from 'lucide-react';

export function EmailSettingsPage() {
  const [accounts, setAccounts] = useState<EmailAccount[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  const [formData, setFormData] = useState<EmailAccountCreate>({
    provider: 'gmail',
    email: '',
    imap_username: '',
    imap_password: '',
  });

  const fetchAccounts = async () => {
    setIsLoading(true);
    try {
      const response = await emailAccountsApi.getAll();
      setAccounts(response.data);
    } catch (error) {
      console.error('Failed to fetch accounts:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAccounts();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);

    try {
      await emailAccountsApi.create(formData);
      setShowAddForm(false);
      setFormData({
        provider: 'gmail',
        email: '',
        imap_username: '',
        imap_password: '',
      });
      await fetchAccounts();
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      setError(error.response?.data?.detail || 'Failed to add email account');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to remove this email account?')) return;

    try {
      await emailAccountsApi.delete(id);
      await fetchAccounts();
    } catch (error) {
      console.error('Failed to delete account:', error);
    }
  };

  const handleSync = async (id: number) => {
    try {
      await emailAccountsApi.sync(id);
      alert('Sync started! New emails will be processed shortly.');
    } catch (error) {
      console.error('Failed to sync:', error);
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Email Settings</h1>
          <p className="text-gray-600">Connect your email accounts to automatically track applications</p>
        </div>
        <button
          onClick={() => setShowAddForm(true)}
          className="flex items-center px-4 py-2 text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add Account
        </button>
      </div>

      {/* Temp Mailbox Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-6 mb-6">
        <div className="flex items-start">
          <div className="p-2 bg-blue-100 rounded-lg">
            <Mail className="w-5 h-5 text-blue-600" />
          </div>
          <div className="ml-4 flex-1">
            <h3 className="text-lg font-semibold text-blue-900">Temporary Mailbox</h3>
            <p className="text-blue-700 mt-1">
              Forward job application emails to your unique address to automatically track them.
            </p>
            <div className="mt-4 p-3 bg-white rounded-lg border border-blue-200">
              <code className="text-sm text-gray-700">your-user-id@tracker.yourdomain.com</code>
            </div>
          </div>
        </div>
      </div>

      {/* Add Account Form */}
      {showAddForm && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Add Email Account</h3>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Provider</label>
                <select
                  value={formData.provider}
                  onChange={(e) => setFormData({ ...formData, provider: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                >
                  <option value="gmail">Gmail</option>
                  <option value="outlook">Outlook</option>
                  <option value="yahoo">Yahoo</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email Address</label>
                <input
                  type="email"
                  required
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                  placeholder="you@example.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">IMAP Username (optional)</label>
                <input
                  type="text"
                  value={formData.imap_username}
                  onChange={(e) => setFormData({ ...formData, imap_username: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                  placeholder="Same as email if left blank"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">IMAP Password / App Password</label>
                <input
                  type="password"
                  required
                  value={formData.imap_password}
                  onChange={(e) => setFormData({ ...formData, imap_password: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                  placeholder="Your app-specific password"
                />
              </div>
            </div>

            <div className="flex items-center justify-end space-x-3 pt-4">
              <button
                type="button"
                onClick={() => setShowAddForm(false)}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-4 py-2 text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                {isSubmitting ? 'Adding...' : 'Add Account'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Accounts List */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Connected Accounts</h3>
        </div>

        {isLoading ? (
          <div className="p-8 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          </div>
        ) : accounts.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <Mail className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p>No email accounts connected yet</p>
            <p className="text-sm mt-1">Add an account to start syncing your job emails</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {accounts.map((account) => (
              <div key={account.id} className="px-6 py-4 flex items-center justify-between">
                <div className="flex items-center">
                  <div className="p-2 bg-gray-100 rounded-lg">
                    <Mail className="w-5 h-5 text-gray-600" />
                  </div>
                  <div className="ml-4">
                    <p className="font-medium text-gray-900">{account.email}</p>
                    <div className="flex items-center text-sm text-gray-500">
                      <span className="capitalize">{account.provider}</span>
                      <span className="mx-2">•</span>
                      {account.is_active ? (
                        <span className="flex items-center text-green-600">
                          <Check className="w-3 h-3 mr-1" /> Active
                        </span>
                      ) : (
                        <span className="flex items-center text-red-600">
                          <X className="w-3 h-3 mr-1" /> Inactive
                        </span>
                      )}
                      {account.last_sync_at && (
                        <>
                          <span className="mx-2">•</span>
                          <span>
                            Last synced: {new Date(account.last_sync_at).toLocaleString()}
                          </span>
                        </>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleSync(account.id)}
                    className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                    title="Sync now"
                  >
                    <RefreshCw className="w-5 h-5" />
                  </button>
                  <button
                    onClick={() => handleDelete(account.id)}
                    className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    title="Remove account"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
