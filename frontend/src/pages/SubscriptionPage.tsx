import { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { subscriptionApi } from '@/services/api';
import { SubscriptionPlan, Subscription } from '@/types';
import { Check, Crown, Loader2, Star } from 'lucide-react';

function formatPrice(paise: number) {
  if (paise === 0) return 'Free';
  return `₹${(paise / 100).toLocaleString('en-IN')}`;
}

const planIcons: Record<string, typeof Crown> = {
  free: Star,
  pro: Crown,
  premium: Crown,
};

export function SubscriptionPage() {
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [currentSub, setCurrentSub] = useState<Subscription | null>(null);
  const [loading, setLoading] = useState(true);
  const [subscribing, setSubscribing] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      subscriptionApi.getPlans(),
      subscriptionApi.getCurrent(),
    ]).then(([plansRes, subRes]) => {
      setPlans(plansRes.data);
      setCurrentSub(subRes.data);
    }).catch((err) => {
      const msg = err instanceof Error ? err.message : 'Failed to load subscription data';
      setError(msg);
    }).finally(() => setLoading(false));
  }, []);

  const handleSubscribe = async (planId: number) => {
    setSubscribing(planId);
    try {
      const res = await subscriptionApi.create({ plan_id: planId });
      const paymentLink = res.data.razorpay_payment_link;
      if (paymentLink) {
        window.location.href = paymentLink;
      } else {
        toast.success('Subscription activated');
        // Refresh current subscription
        const subRes = await subscriptionApi.getCurrent();
        setCurrentSub(subRes.data);
      }
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      toast.error(err.response?.data?.detail || 'Failed to activate subscription');
      console.error(e);
    } finally {
      setSubscribing(null);
    }
  };

  const handleCancel = async () => {
    if (!currentSub) return;
    try {
      await subscriptionApi.cancel(currentSub.id);
      toast.success('Subscription cancelled');
      setCurrentSub({ ...currentSub, status: 'cancelled', cancelled_at: new Date().toISOString() });
    } catch (e) {
      toast.error('Failed to cancel subscription');
      console.error(e);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Subscription</h1>
        <p className="text-gray-600">Choose a plan that fits your needs</p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700">
          <p className="font-medium">Failed to load subscription data</p>
          <p className="text-sm mt-1">{error}</p>
        </div>
      )}

      {/* Current subscription banner */}
      {currentSub && currentSub.status === 'active' && (
        <div className="mb-8 bg-green-50 border border-green-200 rounded-xl p-4">
          <p className="text-green-800 font-medium">
            You are on the <span className="font-bold">{plans.find(p => p.id === currentSub.plan_id)?.name}</span> plan.
          </p>
          {currentSub.current_period_end && (
            <p className="text-green-600 text-sm mt-1">
              Renews on {new Date(currentSub.current_period_end).toLocaleDateString()}
            </p>
          )}
          <button
            onClick={handleCancel}
            className="mt-3 text-sm text-red-600 hover:underline"
          >
            Cancel subscription
          </button>
        </div>
      )}

      {/* Plans grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {plans.map((plan) => {
          const Icon = planIcons[plan.plan_type] || Star;
          const isCurrentPlan = currentSub?.plan_id === plan.id && currentSub.status === 'active';

          return (
            <div
              key={plan.id}
              className={`relative bg-white rounded-xl shadow-sm border-2 p-6 flex flex-col transition-colors ${
                isCurrentPlan ? 'border-green-400 bg-green-50' : 'border-gray-200 hover:border-blue-300'
              }`}
            >
              {isCurrentPlan && (
                <span className="absolute -top-3 left-4 bg-green-500 text-white text-xs font-semibold px-3 py-0.5 rounded-full">
                  Current
                </span>
              )}
              <div className="flex items-center mb-4">
                <div className={`p-2 rounded-lg ${
                  plan.plan_type === 'premium' ? 'bg-purple-100 text-purple-600' :
                  plan.plan_type === 'pro' ? 'bg-blue-100 text-blue-600' :
                  'bg-gray-100 text-gray-600'
                }`}>
                  <Icon className="w-6 h-6" />
                </div>
                <h2 className="ml-3 text-xl font-bold text-gray-900">{plan.name}</h2>
              </div>

              <div className="mb-4">
                <span className="text-3xl font-bold text-gray-900">
                  {formatPrice(plan.price_monthly)}
                </span>
                {plan.price_monthly > 0 && (
                  <span className="text-gray-500 text-sm"> /month</span>
                )}
              </div>

              {plan.description && (
                <p className="text-gray-600 text-sm mb-4">{plan.description}</p>
              )}

              <ul className="space-y-3 mb-6 flex-1">
                {plan.features && Object.entries(plan.features).map(([key, value]) => (
                  <li key={key} className="flex items-center text-sm text-gray-700">
                    <Check className="w-4 h-4 mr-2 text-green-500 flex-shrink-0" />
                    <span className="capitalize">{key.replace(/_/g, ' ')}: {
                      value === true ? 'Yes' :
                      value === false ? 'No' :
                      value === null ? 'Unlimited' :
                      String(value)
                    }</span>
                  </li>
                ))}
              </ul>

              {plan.price_yearly && plan.price_yearly > 0 && (
                <p className="text-sm text-gray-500 mb-4">
                  Yearly: {formatPrice(plan.price_yearly)} ({Math.round(100 - (plan.price_yearly / (plan.price_monthly * 12)) * 100)}% off)
                </p>
              )}

              {isCurrentPlan ? (
                <button disabled className="w-full py-2 rounded-lg bg-green-100 text-green-700 font-medium cursor-default">
                  Active
                </button>
              ) : (
                <button
                  onClick={() => handleSubscribe(plan.id)}
                  disabled={subscribing === plan.id}
                  className="w-full py-2 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-700 transition-colors disabled:opacity-50"
                >
                  {subscribing === plan.id ? (
                    <Loader2 className="w-5 h-5 animate-spin mx-auto" />
                  ) : plan.price_monthly === 0 ? 'Activate Free Plan' : 'Subscribe'}
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
