import { useState, useEffect } from 'react';
import { Application, ApplicationCreate, ApplicationUpdate, StatusHistory } from '@/types';
import { applicationsApi } from '@/services/api';
import {
  X,
  Loader2,
  Clock,
  MessageSquare,
  Plus,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { format } from 'date-fns';

// ---- Local type for activities (not yet in global types) ----
interface Activity {
  id: number;
  type: string;
  description: string;
  extra_data?: Record<string, unknown>;
  created_at: string;
}

const ACTIVITY_TYPE_LABELS: Record<string, string> = {
  note: 'Note',
  call: 'Call',
  email: 'Email',
  interview: 'Interview',
  offer: 'Offer',
  other: 'Other',
};

const STATUS_BADGE: Record<string, string> = {
  applied:   'bg-gray-100 text-gray-700',
  screening: 'bg-blue-100 text-blue-700',
  interview: 'bg-yellow-100 text-yellow-700',
  offer:     'bg-green-100 text-green-700',
  rejected:  'bg-red-100 text-red-700',
  accepted:  'bg-purple-100 text-purple-700',
};

interface ApplicationModalProps {
  application?: Application;
  onClose: () => void;
}

type Tab = 'details' | 'history' | 'activity';

export function ApplicationModal({ application, onClose }: ApplicationModalProps) {
  const isEditing = !!application;

  // ---- form state ----
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<Tab>('details');

  const [formData, setFormData] = useState<ApplicationCreate & ApplicationUpdate>({
    company_name: application?.company_name || '',
    position_title: application?.position_title || '',
    location: application?.location || '',
    salary_range: application?.salary_range || '',
    status: application?.status || 'applied',
    source: application?.source || 'manual',
    notes: application?.notes || '',
  });

  // ---- history ----
  const [history, setHistory] = useState<StatusHistory[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  // ---- activities ----
  const [activities, setActivities] = useState<Activity[]>([]);
  const [activitiesLoading, setActivitiesLoading] = useState(false);
  const [newActivityType, setNewActivityType] = useState('note');
  const [newActivityText, setNewActivityText] = useState('');
  const [addingActivity, setAddingActivity] = useState(false);
  const [showActivityForm, setShowActivityForm] = useState(false);

  // Fetch history + activities when switching tabs
  useEffect(() => {
    if (!application) return;

    if (activeTab === 'history' && history.length === 0) {
      setHistoryLoading(true);
      applicationsApi
        .getHistory(application.id)
        .then((r) => setHistory(r.data))
        .catch(console.error)
        .finally(() => setHistoryLoading(false));
    }

    if (activeTab === 'activity' && activities.length === 0) {
      setActivitiesLoading(true);
      applicationsApi
        .getActivities(application.id)
        .then((r) => setActivities(r.data))
        .catch(console.error)
        .finally(() => setActivitiesLoading(false));
    }
  }, [activeTab, application]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    try {
      if (isEditing) {
        await applicationsApi.update(application.id, formData);
      } else {
        await applicationsApi.create(formData);
      }
      onClose();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setError(e.response?.data?.detail || 'Failed to save application');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!application || !confirm('Delete this application?')) return;
    setIsLoading(true);
    try {
      await applicationsApi.delete(application.id);
      onClose();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setError(e.response?.data?.detail || 'Failed to delete application');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddActivity = async () => {
    if (!application || !newActivityText.trim()) return;
    setAddingActivity(true);
    try {
      const res = await applicationsApi.addActivity(application.id, {
        type: newActivityType,
        description: newActivityText.trim(),
      });
      setActivities([res.data, ...activities]);
      setNewActivityText('');
      setShowActivityForm(false);
    } catch (err) {
      console.error(err);
    } finally {
      setAddingActivity(false);
    }
  };

  const tabs: { id: Tab; label: string }[] = isEditing
    ? [
        { id: 'details', label: 'Details' },
        { id: 'history', label: 'Status History' },
        { id: 'activity', label: 'Activity Log' },
      ]
    : [{ id: 'details', label: 'Details' }];

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        {/* Backdrop */}
        <div className="fixed inset-0 transition-opacity" onClick={onClose}>
          <div className="absolute inset-0 bg-gray-900 opacity-60" />
        </div>

        <span className="hidden sm:inline-block sm:align-middle sm:h-screen">&#8203;</span>

        <div className="inline-block align-bottom bg-white rounded-xl text-left overflow-hidden shadow-2xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg w-full relative z-10">
          {/* Header */}
          <div className="px-6 pt-5 pb-0">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                {isEditing ? (
                  <span>
                    {application.company_name}
                    <span className="ml-2 text-sm font-normal text-gray-500">
                      — {application.position_title}
                    </span>
                  </span>
                ) : (
                  'Add Application'
                )}
              </h3>
              <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Tabs */}
            {tabs.length > 1 && (
              <div className="flex space-x-1 border-b border-gray-200">
                {tabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                      activeTab === tab.id
                        ? 'border-blue-600 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="px-6 py-4">
            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
                {error}
              </div>
            )}

            {/* ---- DETAILS TAB ---- */}
            {activeTab === 'details' && (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Company Name *</label>
                  <input
                    type="text"
                    required
                    value={formData.company_name}
                    onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Position Title *</label>
                  <input
                    type="text"
                    required
                    value={formData.position_title}
                    onChange={(e) => setFormData({ ...formData, position_title: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
                    <input
                      type="text"
                      value={formData.location}
                      onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                      placeholder="City, Country"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Salary Range</label>
                    <input
                      type="text"
                      value={formData.salary_range}
                      onChange={(e) => setFormData({ ...formData, salary_range: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                      placeholder="e.g. ₹20-25 LPA"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                    <select
                      value={formData.status}
                      onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                    >
                      <option value="applied">Applied</option>
                      <option value="screening">Screening</option>
                      <option value="interview">Interview</option>
                      <option value="offer">Offer</option>
                      <option value="rejected">Rejected</option>
                      <option value="accepted">Accepted</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Source</label>
                    <select
                      value={formData.source}
                      onChange={(e) => setFormData({ ...formData, source: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                    >
                      <option value="manual">Manual</option>
                      <option value="linkedin">LinkedIn</option>
                      <option value="naukri">Naukri</option>
                      <option value="indeed">Indeed</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
                  <textarea
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none resize-none"
                  />
                </div>

                <div className="flex items-center justify-between pt-2">
                  {isEditing ? (
                    <button
                      type="button"
                      onClick={handleDelete}
                      disabled={isLoading}
                      className="text-red-600 hover:text-red-700 text-sm font-medium"
                    >
                      Delete
                    </button>
                  ) : (
                    <div />
                  )}
                  <div className="flex items-center space-x-3">
                    <button
                      type="button"
                      onClick={onClose}
                      className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors text-sm font-medium"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={isLoading}
                      className="flex items-center px-4 py-2 text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors text-sm font-medium"
                    >
                      {isLoading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                      {isEditing ? 'Save Changes' : 'Add Application'}
                    </button>
                  </div>
                </div>
              </form>
            )}

            {/* ---- STATUS HISTORY TAB ---- */}
            {activeTab === 'history' && (
              <div className="space-y-3 max-h-80 overflow-y-auto pr-1">
                {historyLoading ? (
                  <div className="flex justify-center py-8">
                    <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
                  </div>
                ) : history.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <Clock className="w-10 h-10 mx-auto mb-2 text-gray-300" />
                    <p className="text-sm">No status changes recorded yet</p>
                  </div>
                ) : (
                  history.map((h) => (
                    <div key={h.id} className="flex items-start space-x-3 text-sm">
                      <div className="mt-0.5 w-2 h-2 rounded-full bg-blue-500 flex-shrink-0 mt-1.5" />
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          {h.from_status && (
                            <>
                              <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_BADGE[h.from_status] || 'bg-gray-100 text-gray-700'} capitalize`}>
                                {h.from_status}
                              </span>
                              <span className="text-gray-400">→</span>
                            </>
                          )}
                          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_BADGE[h.to_status] || 'bg-gray-100 text-gray-700'} capitalize`}>
                            {h.to_status}
                          </span>
                        </div>
                        {h.reason && <p className="text-gray-500 mt-0.5 text-xs">{h.reason}</p>}
                        <p className="text-gray-400 text-xs mt-0.5">
                          {format(new Date(h.changed_at), 'MMM d, yyyy · h:mm a')}
                        </p>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}

            {/* ---- ACTIVITY LOG TAB ---- */}
            {activeTab === 'activity' && (
              <div className="space-y-3">
                {/* Add activity */}
                <div className="border border-gray-200 rounded-lg overflow-hidden">
                  <button
                    onClick={() => setShowActivityForm((v) => !v)}
                    className="w-full flex items-center justify-between px-4 py-2.5 text-sm font-medium text-gray-700 bg-gray-50 hover:bg-gray-100 transition-colors"
                  >
                    <span className="flex items-center">
                      <Plus className="w-4 h-4 mr-2 text-blue-600" />
                      Log an activity
                    </span>
                    {showActivityForm ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
                  </button>

                  {showActivityForm && (
                    <div className="p-3 space-y-2 border-t border-gray-200">
                      <div className="flex space-x-2">
                        <select
                          value={newActivityType}
                          onChange={(e) => setNewActivityType(e.target.value)}
                          className="text-xs border border-gray-300 rounded-md px-2 py-1.5 outline-none focus:ring-1 focus:ring-blue-500"
                        >
                          {Object.entries(ACTIVITY_TYPE_LABELS).map(([val, label]) => (
                            <option key={val} value={val}>{label}</option>
                          ))}
                        </select>
                        <input
                          type="text"
                          value={newActivityText}
                          onChange={(e) => setNewActivityText(e.target.value)}
                          placeholder="What happened?"
                          className="flex-1 text-sm border border-gray-300 rounded-md px-3 py-1.5 outline-none focus:ring-1 focus:ring-blue-500"
                          onKeyDown={(e) => e.key === 'Enter' && handleAddActivity()}
                        />
                        <button
                          onClick={handleAddActivity}
                          disabled={addingActivity || !newActivityText.trim()}
                          className="px-3 py-1.5 text-xs font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
                        >
                          {addingActivity ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : 'Add'}
                        </button>
                      </div>
                    </div>
                  )}
                </div>

                {/* Activity list */}
                <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                  {activitiesLoading ? (
                    <div className="flex justify-center py-8">
                      <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
                    </div>
                  ) : activities.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      <MessageSquare className="w-10 h-10 mx-auto mb-2 text-gray-300" />
                      <p className="text-sm">No activities logged yet</p>
                    </div>
                  ) : (
                    activities.map((a) => (
                      <div key={a.id} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg text-sm">
                        <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full text-xs font-medium capitalize flex-shrink-0 mt-0.5">
                          {ACTIVITY_TYPE_LABELS[a.type] || a.type}
                        </span>
                        <div className="flex-1 min-w-0">
                          <p className="text-gray-800 break-words">{a.description}</p>
                          <p className="text-gray-400 text-xs mt-0.5">
                            {format(new Date(a.created_at), 'MMM d, yyyy · h:mm a')}
                          </p>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
