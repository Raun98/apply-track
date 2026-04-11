import { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { Users, CreditCard, Gift, BarChart3, RefreshCw, Plus, Trash2, Edit2, Loader2 } from 'lucide-react';
import { api } from '@/services/api';

type Tab = 'overview' | 'plans' | 'coupons' | 'users' | 'subscriptions';

interface Stats {
  by_status: Record<string, number>;
  by_plan: { plan: string; count: number }[];
  total_users: number;
}

interface Plan {
  id: number;
  name: string;
  plan_type: string;
  price_monthly: number;
  price_yearly?: number;
  razorpay_plan_id?: string;
  features: Record<string, any>;
  is_active: boolean;
}

interface Coupon {
  id: number;
  code: string;
  discount_type: string;
  discount_value: number;
  min_order_amount?: number;
  max_uses?: number;
  current_uses: number;
  expires_at?: string;
  is_active: boolean;
}

interface User {
  id: number;
  email: string;
  name?: string;
  is_active: boolean;
  created_at: string;
  subscription?: string;
}

export function AdminPage() {
  const [activeTab, setActiveTab] = useState<Tab>('overview');
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);

  // Data states
  const [stats, setStats] = useState<Stats | null>(null);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [coupons, setCoupons] = useState<Coupon[]>([]);
  const [users, setUsers] = useState<User[]>([]);

  // Modal states
  const [showPlanModal, setShowPlanModal] = useState(false);
  const [showCouponModal, setShowCouponModal] = useState(false);
  const [editingPlan, setEditingPlan] = useState<Plan | null>(null);
  const [editingCoupon, setEditingCoupon] = useState<Coupon | null>(null);

  useEffect(() => {
    fetchData();
  }, [activeTab]);

  const fetchData = async () => {
    setLoading(true);
    try {
      switch (activeTab) {
        case 'overview':
          const statsRes = await api.get('/admin/subscriptions/stats');
          setStats(statsRes.data);
          break;
        case 'plans':
          const plansRes = await api.get('/admin/plans');
          setPlans(plansRes.data);
          break;
        case 'coupons':
          const couponsRes = await api.get('/admin/coupons');
          setCoupons(couponsRes.data);
          break;
        case 'users':
          const usersRes = await api.get('/admin/users');
          setUsers(usersRes.data);
          break;
        case 'subscriptions':
          const subsRes = await api.get('/admin/subscriptions');
          setStats({ ...stats!, by_plan: subsRes.data.subscriptions });
          break;
      }
    } catch (e) {
      console.error(e);
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const syncRazorpayPlans = async () => {
    setSyncing(true);
    try {
      const res = await api.post('/admin/razorpay/sync-plans');
      toast.success(`Synced: ${res.data.synced.join(', ')}`);
      fetchData();
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Failed to sync plans');
    } finally {
      setSyncing(false);
    }
  };

  const deletePlan = async (id: number) => {
    if (!confirm('Deactivate this plan?')) return;
    try {
      await api.delete(`/admin/plans/${id}`);
      toast.success('Plan deactivated');
      fetchData();
    } catch (e) {
      toast.error('Failed to delete plan');
    }
  };

  const deleteCoupon = async (id: number) => {
    if (!confirm('Deactivate this coupon?')) return;
    try {
      await api.delete(`/admin/coupons/${id}`);
      toast.success('Coupon deactivated');
      fetchData();
    } catch (e) {
      toast.error('Failed to delete coupon');
    }
  };

  const tabs = [
    { id: 'overview', label: 'Overview', icon: BarChart3 },
    { id: 'plans', label: 'Plans', icon: CreditCard },
    { id: 'coupons', label: 'Coupons', icon: Gift },
    { id: 'users', label: 'Users', icon: Users },
  ];

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
        <p className="text-gray-600">Manage subscriptions, plans, and users</p>
      </div>

      {/* Tabs */}
      <div className="flex space-x-1 mb-6 bg-gray-100 p-1 rounded-lg w-fit">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as Tab)}
              className={`flex items-center px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Icon className="w-4 h-4 mr-2" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        </div>
      ) : (
        <>
          {activeTab === 'overview' && stats && (
            <div className="space-y-6">
              {/* Stats Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-white rounded-xl shadow-sm border p-6">
                  <p className="text-sm text-gray-500">Total Users</p>
                  <p className="text-3xl font-bold text-gray-900">{stats.total_users}</p>
                </div>
                <div className="bg-white rounded-xl shadow-sm border p-6">
                  <p className="text-sm text-gray-500">Active Subscriptions</p>
                  <p className="text-3xl font-bold text-green-600">{stats.by_status?.active || 0}</p>
                </div>
                <div className="bg-white rounded-xl shadow-sm border p-6">
                  <p className="text-sm text-gray-500">Cancelled</p>
                  <p className="text-3xl font-bold text-red-600">{stats.by_status?.cancelled || 0}</p>
                </div>
                <div className="bg-white rounded-xl shadow-sm border p-6">
                  <p className="text-sm text-gray-500">Inactive</p>
                  <p className="text-3xl font-bold text-gray-600">{stats.by_status?.inactive || 0}</p>
                </div>
              </div>

              {/* Subscriptions by Plan */}
              <div className="bg-white rounded-xl shadow-sm border p-6">
                <h2 className="text-lg font-semibold mb-4">Subscriptions by Plan</h2>
                <div className="space-y-3">
                  {stats.by_plan?.map((item, i) => (
                    <div key={i} className="flex justify-between items-center">
                      <span className="font-medium">{item.plan}</span>
                      <span className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-sm">
                        {item.count}
                      </span>
                    </div>
                  ))}
                  {(!stats.by_plan || stats.by_plan.length === 0) && (
                    <p className="text-gray-500 text-sm">No subscriptions yet</p>
                  )}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'plans' && (
            <div>
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-semibold">Subscription Plans</h2>
                <div className="flex gap-2">
                  <button
                    onClick={syncRazorpayPlans}
                    disabled={syncing}
                    className="flex items-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
                  >
                    <RefreshCw className={`w-4 h-4 mr-2 ${syncing ? 'animate-spin' : ''}`} />
                    Sync from Razorpay
                  </button>
                </div>
              </div>

              <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Plan</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Monthly Price</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Razorpay ID</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {plans.map((plan) => (
                      <tr key={plan.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 font-medium">{plan.name}</td>
                        <td className="px-6 py-4 capitalize">{plan.plan_type}</td>
                        <td className="px-6 py-4">₹{(plan.price_monthly / 100).toFixed(2)}</td>
                        <td className="px-6 py-4 text-sm text-gray-500">
                          {plan.razorpay_plan_id || <span className="text-red-500">Not set</span>}
                        </td>
                        <td className="px-6 py-4">
                          <span className={`px-2 py-1 rounded-full text-xs ${
                            plan.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                          }`}>
                            {plan.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-right">
                          <button
                            onClick={() => deletePlan(plan.id)}
                            className="text-red-600 hover:text-red-700"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === 'coupons' && (
            <div>
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-semibold">Coupons</h2>
                <button
                  onClick={() => { setEditingCoupon(null); setShowCouponModal(true); }}
                  className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Add Coupon
                </button>
              </div>

              <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Code</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Discount</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Uses</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Expires</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {coupons.map((coupon) => (
                      <tr key={coupon.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 font-mono font-bold">{coupon.code}</td>
                        <td className="px-6 py-4">
                          {coupon.discount_type === 'percentage' 
                            ? `${coupon.discount_value}%` 
                            : `₹${coupon.discount_value / 100}`}
                        </td>
                        <td className="px-6 py-4">{coupon.current_uses}/{coupon.max_uses || '∞'}</td>
                        <td className="px-6 py-4 text-sm">
                          {coupon.expires_at ? new Date(coupon.expires_at).toLocaleDateString() : 'Never'}
                        </td>
                        <td className="px-6 py-4">
                          <span className={`px-2 py-1 rounded-full text-xs ${
                            coupon.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                          }`}>
                            {coupon.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-right">
                          <button
                            onClick={() => deleteCoupon(coupon.id)}
                            className="text-red-600 hover:text-red-700"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                    {coupons.length === 0 && (
                      <tr>
                        <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                          No coupons yet. Create one to offer discounts!
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === 'users' && (
            <div>
              <h2 className="text-lg font-semibold mb-4">Users</h2>
              <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">User</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Subscription</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Joined</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {users.map((user) => (
                      <tr key={user.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 font-medium">{user.name || 'N/A'}</td>
                        <td className="px-6 py-4">{user.email}</td>
                        <td className="px-6 py-4">
                          {user.subscription ? (
                            <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded-full text-xs">
                              {user.subscription}
                            </span>
                          ) : (
                            <span className="text-gray-400 text-sm">Free</span>
                          )}
                        </td>
                        <td className="px-6 py-4 text-sm">{new Date(user.created_at).toLocaleDateString()}</td>
                        <td className="px-6 py-4">
                          <span className={`px-2 py-1 rounded-full text-xs ${
                            user.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                          }`}>
                            {user.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}

      {/* Coupon Modal */}
      {showCouponModal && (
        <CouponModal
          coupon={editingCoupon}
          onClose={() => setShowCouponModal(false)}
          onSave={() => { setShowCouponModal(false); fetchData(); }}
        />
      )}
    </div>
  );
}

// Simple Coupon Modal Component
function CouponModal({ 
  coupon, 
  onClose, 
  onSave 
}: { 
  coupon: Coupon | null; 
  onClose: () => void; 
  onSave: () => void; 
}) {
  const [form, setForm] = useState({
    code: coupon?.code || '',
    discount_type: coupon?.discount_type || 'percentage',
    discount_value: coupon?.discount_value || 10,
    max_uses: coupon?.max_uses || 100,
  });
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      if (coupon) {
        await api.patch(`/admin/coupons/${coupon.id}`, form);
      } else {
        await api.post('/admin/coupons', form);
      }
      toast.success(coupon ? 'Coupon updated' : 'Coupon created');
      onSave();
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Failed to save coupon');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-md">
        <h2 className="text-lg font-semibold mb-4">{coupon ? 'Edit Coupon' : 'Create Coupon'}</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Code</label>
            <input
              type="text"
              value={form.code}
              onChange={(e) => setForm({ ...form, code: e.target.value.toUpperCase() })}
              className="w-full border rounded-lg px-3 py-2"
              required
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
              <select
                value={form.discount_type}
                onChange={(e) => setForm({ ...form, discount_type: e.target.value })}
                className="w-full border rounded-lg px-3 py-2"
              >
                <option value="percentage">Percentage</option>
                <option value="fixed">Fixed (₹)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Value</label>
              <input
                type="number"
                value={form.discount_value}
                onChange={(e) => setForm({ ...form, discount_value: parseInt(e.target.value) })}
                className="w-full border rounded-lg px-3 py-2"
                required
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Max Uses (0 = unlimited)</label>
            <input
              type="number"
              value={form.max_uses}
              onChange={(e) => setForm({ ...form, max_uses: parseInt(e.target.value) })}
              className="w-full border rounded-lg px-3 py-2"
            />
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <button type="button" onClick={onClose} className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg">
              Cancel
            </button>
            <button type="submit" disabled={saving} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
              {saving ? 'Saving...' : 'Save'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
