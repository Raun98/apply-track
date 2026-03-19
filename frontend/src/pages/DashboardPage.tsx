import { useEffect } from 'react';
import { useBoardStore } from '@/stores/boardStore';
import {
  Briefcase,
  Mail,
  Users,
  TrendingUp,
  Calendar,
} from 'lucide-react';

export function DashboardPage() {
  const { stats, fetchStats } = useBoardStore();

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  const statCards = [
    {
      title: 'Total Applications',
      value: stats?.total_applications || 0,
      icon: Briefcase,
      color: 'bg-blue-500',
    },
    {
      title: 'Response Rate',
      value: `${stats?.response_rate || 0}%`,
      icon: Mail,
      color: 'bg-green-500',
    },
    {
      title: 'Interview Rate',
      value: `${stats?.interview_rate || 0}%`,
      icon: Users,
      color: 'bg-yellow-500',
    },
    {
      title: 'Offer Rate',
      value: `${stats?.offer_rate || 0}%`,
      icon: TrendingUp,
      color: 'bg-purple-500',
    },
  ];

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600">Overview of your job search progress</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {statCards.map((card) => {
          const Icon = card.icon;
          return (
            <div key={card.title} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <div className="flex items-center">
                <div className={`p-3 rounded-lg ${card.color}`}>
                  <Icon className="w-6 h-6 text-white" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">{card.title}</p>
                  <p className="text-2xl font-bold text-gray-900">{card.value}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Status Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Applications by Status</h2>
          {stats?.by_status && Object.entries(stats.by_status).length > 0 ? (
            <div className="space-y-3">
              {Object.entries(stats.by_status).map(([status, count]) => (
                <div key={status} className="flex items-center">
                  <div className="w-32 text-sm font-medium text-gray-600 capitalize">
                    {status}
                  </div>
                  <div className="flex-1 mx-4">
                    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-600 rounded-full"
                        style={{
                          width: `${stats.total_applications > 0 ? (count / stats.total_applications) * 100 : 0}%`,
                        }}
                      />
                    </div>
                  </div>
                  <div className="w-12 text-sm font-medium text-gray-900 text-right">
                    {count}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">No applications yet</p>
          )}
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h2>
          <div className="space-y-4">
            <div className="flex items-start space-x-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Calendar className="w-4 h-4 text-blue-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-900">Welcome to Job Tracker!</p>
                <p className="text-sm text-gray-500">
                  Start by adding your first application or connecting your email.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
