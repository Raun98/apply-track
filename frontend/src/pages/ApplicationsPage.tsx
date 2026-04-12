import { useEffect, useState, useRef, useCallback } from 'react';
import toast from 'react-hot-toast';
import { applicationsApi } from '@/services/api';
import { Application, ApplicationStatus, JobSource } from '@/types';
import { format } from 'date-fns';
import {
  Search,
  Filter,
  Plus,
  Pencil,
  Linkedin,
  Globe,
  Mail,
} from 'lucide-react';
import { ApplicationModal } from '@/components/Modals/ApplicationModal';

const sourceIcons: Record<JobSource, React.ReactNode> = {
  linkedin: <Linkedin className="w-4 h-4 text-blue-600" />,
  naukri: <Globe className="w-4 h-4 text-blue-500" />,
  indeed: <Globe className="w-4 h-4 text-blue-700" />,
  manual: <Mail className="w-4 h-4 text-gray-500" />,
  unknown: <Mail className="w-4 h-4 text-gray-400" />,
};

const statusColors: Record<ApplicationStatus, string> = {
  applied: 'bg-gray-100 text-gray-700',
  screening: 'bg-blue-100 text-blue-700',
  interview: 'bg-yellow-100 text-yellow-700',
  offer: 'bg-green-100 text-green-700',
  rejected: 'bg-red-100 text-red-700',
  accepted: 'bg-purple-100 text-purple-700',
};

export function ApplicationsPage() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleSearchChange = useCallback((value: string) => {
    setSearchQuery(value);
    if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
    debounceTimerRef.current = setTimeout(() => {
      setDebouncedSearch(value);
    }, 300);
  }, []);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [selectedApplication, setSelectedApplication] = useState<Application | null>(null);

  const fetchApplications = async () => {
    setIsLoading(true);
    try {
      const response = await applicationsApi.getAll({
        search: debouncedSearch || undefined,
        status: statusFilter || undefined,
        page,
        page_size: 20,
      });
      setApplications(response.data.items);
      setTotal(response.data.total);
    } catch (error) {
      toast.error('Failed to fetch applications');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchApplications();
  }, [debouncedSearch, statusFilter, page]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Applications</h1>
          <p className="text-gray-600 mt-1">Manage and track all your job applications</p>
        </div>
        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="flex items-center px-4 py-2 text-white bg-gradient-to-r from-blue-600 to-blue-700 rounded-lg hover:from-blue-700 hover:to-blue-800 transition-all shadow-sm font-medium"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add Application
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3 bg-gray-50 rounded-xl p-4 border border-gray-200">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search by company or position..."
            value={searchQuery}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none bg-white transition-all"
          />
        </div>

        <div className="flex items-center space-x-2 bg-white border border-gray-300 rounded-lg px-3 py-2.5">
          <Filter className="w-5 h-5 text-gray-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-1 py-0 border-0 focus:ring-0 outline-none font-medium text-gray-700 bg-white"
          >
            <option value="">All Statuses</option>
            <option value="applied">Applied</option>
            <option value="screening">Screening</option>
            <option value="interview">Interview</option>
            <option value="offer">Offer</option>
            <option value="rejected">Rejected</option>
            <option value="accepted">Accepted</option>
          </select>
        </div>
      </div>

      {/* Results Info */}
      {total > 0 && (
        <div className="flex items-center justify-between text-sm text-gray-600 bg-blue-50 border border-blue-200 rounded-lg p-3">
          <span><span className="font-semibold text-gray-900">{total}</span> total applications</span>
          <span>Page {page} of {Math.ceil(total / 20)}</span>
        </div>
      )}

      {/* Table */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gradient-to-r from-gray-50 to-gray-100 border-b border-gray-200">
              <tr>
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  Company
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  Position
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  Source
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  Applied Date
                </th>
                <th className="px-6 py-4 text-right text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {isLoading ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center">
                    <div className="flex items-center justify-center space-x-2">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                      <span className="text-gray-600">Loading applications...</span>
                    </div>
                  </td>
                </tr>
              ) : applications.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center">
                    <div className="text-gray-500">
                      <p className="font-medium">No applications found</p>
                      <p className="text-sm mt-1">Try adjusting your search or filters</p>
                    </div>
                  </td>
                </tr>
              ) : (
                applications.map((app) => (
                  <tr key={app.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4">
                      <div className="font-semibold text-gray-900">{app.company_name}</div>
                      {app.location && (
                        <div className="text-sm text-gray-500 mt-0.5">{app.location}</div>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <div className="font-medium text-gray-900">{app.position_title}</div>
                      {app.salary_range && (
                        <div className="text-sm text-gray-600 mt-0.5">{app.salary_range}</div>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`inline-flex px-3 py-1 text-xs font-semibold rounded-full ${
                          statusColors[app.status]
                        }`}
                      >
                        {app.status.charAt(0).toUpperCase() + app.status.slice(1)}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center space-x-2">
                        {sourceIcons[app.source]}
                        <span className="text-sm text-gray-600 capitalize font-medium">{app.source}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600 font-medium">
                      {format(new Date(app.applied_date), 'MMM d, yyyy')}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => setSelectedApplication(app)}
                        className="text-gray-400 hover:text-blue-600 hover:bg-blue-50 p-2 rounded-lg transition-colors"
                        title="Edit"
                      >
                        <Pencil className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {total > 20 && (
          <div className="flex items-center justify-between px-6 py-4 border-t border-gray-200 bg-gray-50">
            <div className="text-sm text-gray-600 font-medium">
              Showing <span className="text-gray-900 font-semibold">{((page - 1) * 20) + 1}-{Math.min(page * 20, total)}</span> of <span className="text-gray-900 font-semibold">{total}</span>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-4 py-2 text-sm font-medium border border-gray-300 rounded-lg disabled:opacity-50 hover:bg-white transition-colors"
              >
                Previous
              </button>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={page * 20 >= total}
                className="px-4 py-2 text-sm font-medium border border-gray-300 rounded-lg disabled:opacity-50 hover:bg-white transition-colors"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
      {/* Modals */}
      {isCreateModalOpen && (
        <ApplicationModal
          onClose={() => {
            setIsCreateModalOpen(false);
            fetchApplications();
          }}
        />
      )}
      {selectedApplication && (
        <ApplicationModal
          application={selectedApplication}
          onClose={() => {
            setSelectedApplication(null);
            fetchApplications();
          }}
        />
      )}
    </div>
  );
}
