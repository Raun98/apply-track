import { useEffect, useState } from 'react';
import { useBoardStore } from '@/stores/boardStore';
import { OnboardingEmptyState } from '@/components/OnboardingEmptyState';
import { ApplicationModal } from '@/components/Modals/ApplicationModal';
import {
  Briefcase,
  Mail,
  Users,
  Target,
  CheckCircle,
  Clock,
} from 'lucide-react';

export function DashboardPage() {
  const { stats, fetchStats, fetchBoardData } = useBoardStore();
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  const getTrendColor = (rate: number) => {
    if (rate === 0) return 'text-gray-400';
    if (rate < 5) return 'text-red-500';
    if (rate < 15) return 'text-orange-500';
    if (rate < 30) return 'text-yellow-500';
    return 'text-green-500';
  };

  // Show onboarding empty state when no applications
  if (stats && stats.total_applications === 0) {
    return (
      <>
        <OnboardingEmptyState onAddApplication={() => setIsCreateModalOpen(true)} />
        {isCreateModalOpen && (
          <ApplicationModal
            onClose={() => {
              setIsCreateModalOpen(false);
              fetchStats();
              fetchBoardData();
            }}
          />
        )}
      </>
    );
  }

  const statCards = [
    {
      title: 'Total Applications',
      value: stats?.total_applications || 0,
      icon: Briefcase,
      color: 'from-blue-500 to-blue-600',
      bgColor: 'bg-blue-50',
      description: 'Applications submitted',
    },
    {
      title: 'Response Rate',
      value: `${stats?.response_rate || 0}%`,
      icon: Mail,
      color: 'from-green-500 to-emerald-600',
      bgColor: 'bg-green-50',
      description: 'Companies responded',
    },
    {
      title: 'Interview Rate',
      value: `${stats?.interview_rate || 0}%`,
      icon: Users,
      color: 'from-purple-500 to-indigo-600',
      bgColor: 'bg-purple-50',
      description: 'Advanced to interviews',
    },
    {
      title: 'Offer Rate',
      value: `${stats?.offer_rate || 0}%`,
      icon: Target,
      color: 'from-amber-500 to-orange-600',
      bgColor: 'bg-amber-50',
      description: 'Offers received',
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Dashboard</h1>
        <p className="text-gray-600">Track your job search performance and insights</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((card) => {
          const Icon = card.icon;
          return (
            <div
              key={card.title}
              className="relative overflow-hidden rounded-2xl bg-white shadow-sm hover:shadow-md transition-shadow border border-gray-100 p-6 group"
            >
              {/* Gradient background */}
              <div
                className={`absolute inset-0 bg-gradient-to-br ${card.color} opacity-5 group-hover:opacity-10 transition-opacity`}
              />
              <div className="relative z-10">
                <div className="flex items-start justify-between mb-4">
                  <div className={`p-3 rounded-xl ${card.bgColor}`}>
                    <Icon className={`w-6 h-6 text-${card.color.split('-')[1]}-600`} />
                  </div>
                </div>
                <p className="text-sm font-medium text-gray-600 mb-1">{card.title}</p>
                <p className="text-3xl font-bold text-gray-900 mb-2">{card.value}</p>
                <p className="text-xs text-gray-500">{card.description}</p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Status Breakdown */}
        <div className="lg:col-span-2 bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-bold text-gray-900">Applications by Status</h2>
              <p className="text-sm text-gray-500 mt-1">Distribution across pipeline stages</p>
            </div>
          </div>

          {stats?.by_status && Object.entries(stats.by_status).length > 0 ? (
            <div className="space-y-4">
              {Object.entries(stats.by_status).map(([status, count]) => {
                const percentage = stats.total_applications > 0
                  ? (count / stats.total_applications) * 100
                  : 0;

                const statusColors: Record<string, {bar: string, badge: string}> = {
                  applied: { bar: 'bg-blue-500', badge: 'bg-blue-100 text-blue-700' },
                  screening: { bar: 'bg-indigo-500', badge: 'bg-indigo-100 text-indigo-700' },
                  interview: { bar: 'bg-purple-500', badge: 'bg-purple-100 text-purple-700' },
                  offer: { bar: 'bg-green-500', badge: 'bg-green-100 text-green-700' },
                  rejected: { bar: 'bg-red-500', badge: 'bg-red-100 text-red-700' },
                  accepted: { bar: 'bg-emerald-500', badge: 'bg-emerald-100 text-emerald-700' },
                };

                const colors = statusColors[status] || { bar: 'bg-gray-500', badge: 'bg-gray-100 text-gray-700' };

                return (
                  <div key={status} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${colors.badge} capitalize`}>
                          {status}
                        </span>
                      </div>
                      <div className="flex items-center space-x-3">
                        <span className="text-sm font-semibold text-gray-900">{count}</span>
                        <span className="text-sm font-medium text-gray-600">{percentage.toFixed(1)}%</span>
                      </div>
                    </div>
                    <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${colors.bar} rounded-full transition-all duration-300`}
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-12">
              <Briefcase className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500 font-medium">No applications yet</p>
              <p className="text-sm text-gray-400 mt-1">Start tracking your job applications</p>
            </div>
          )}
        </div>

        {/* Quick Stats */}
        <div className="space-y-6">
          {/* Average Response */}
          <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl border border-green-100 p-6">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-gray-900">Success Metrics</h3>
              <CheckCircle className="w-5 h-5 text-green-600" />
            </div>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-700">Interview Conversion</span>
                <span className={`font-bold ${getTrendColor(stats?.interview_rate || 0)}`}>
                  {stats?.interview_rate || 0}%
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-700">Offer Rate</span>
                <span className={`font-bold ${getTrendColor(stats?.offer_rate || 0)}`}>
                  {stats?.offer_rate || 0}%
                </span>
              </div>
            </div>
          </div>

          {/* Active Pipeline */}
          <div className="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-2xl border border-blue-100 p-6">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-gray-900">Active Pipeline</h3>
              <Clock className="w-5 h-5 text-blue-600" />
            </div>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-700">In Progress</span>
                <span className="font-bold text-blue-600">
                  {(stats?.by_status?.screening || 0) + (stats?.by_status?.interview || 0)}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-700">Offers</span>
                <span className="font-bold text-green-600">
                  {stats?.by_status?.offer || 0}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
