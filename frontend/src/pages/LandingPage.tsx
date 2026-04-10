import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Briefcase,
  CheckCircle2,
  Zap,
  BarChart3,
  Mail,
  Clock,
  ArrowRight,
  Menu,
  X,
  Star,
  TrendingUp,
  Shield,
} from 'lucide-react';

export function LandingPage() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Navigation */}
      <nav className="fixed top-0 w-full bg-slate-900/80 backdrop-blur-md border-b border-slate-700 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2">
              <Briefcase className="w-8 h-8 text-blue-500" />
              <span className="text-xl font-bold text-white">ApplyTrack</span>
            </div>

            {/* Desktop Menu */}
            <div className="hidden md:flex items-center gap-8">
              <a href="#features" className="text-slate-300 hover:text-white transition">
                Features
              </a>
              <a href="#benefits" className="text-slate-300 hover:text-white transition">
                Benefits
              </a>
              <a href="#pricing" className="text-slate-300 hover:text-white transition">
                Pricing
              </a>
            </div>

            <div className="hidden md:flex items-center gap-4">
              <Link
                to="/login"
                className="text-slate-300 hover:text-white transition font-medium"
              >
                Sign In
              </Link>
              <Link
                to="/register"
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium transition"
              >
                Get Started
              </Link>
            </div>

            {/* Mobile Menu Button */}
            <button
              className="md:hidden text-white"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>

          {/* Mobile Menu */}
          {mobileMenuOpen && (
            <div className="md:hidden pb-4 border-t border-slate-700">
              <a href="#features" className="block py-2 text-slate-300 hover:text-white">
                Features
              </a>
              <a href="#benefits" className="block py-2 text-slate-300 hover:text-white">
                Benefits
              </a>
              <a href="#pricing" className="block py-2 text-slate-300 hover:text-white">
                Pricing
              </a>
              <div className="flex gap-3 mt-4 pt-4 border-t border-slate-700">
                <Link to="/login" className="flex-1 text-center py-2 text-slate-300">
                  Sign In
                </Link>
                <Link
                  to="/register"
                  className="flex-1 bg-blue-600 text-white py-2 rounded-lg font-medium"
                >
                  Get Started
                </Link>
              </div>
            </div>
          )}
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 bg-blue-500/10 border border-blue-500/20 rounded-full px-4 py-2 mb-8">
            <Star className="w-4 h-4 text-blue-400" />
            <span className="text-sm font-medium text-blue-300">
              Trusted by job seekers worldwide
            </span>
          </div>

          <h1 className="text-5xl md:text-7xl font-bold text-white mb-6 leading-tight">
            Track Your Job
            <span className="block text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-400">
              Applications Effortlessly
            </span>
          </h1>

          <p className="text-xl text-slate-300 mb-8 max-w-2xl mx-auto leading-relaxed">
            Stop juggling spreadsheets and emails. ApplyTrack automatically organizes your
            applications, tracks their status, and keeps you updated—all in one beautiful dashboard.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
            <Link
              to="/register"
              className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 rounded-lg font-semibold flex items-center justify-center gap-2 transition transform hover:scale-105"
            >
              Start Free Trial
              <ArrowRight className="w-5 h-5" />
            </Link>
            <button className="border border-slate-600 hover:border-slate-400 text-white px-8 py-4 rounded-lg font-semibold transition">
              Watch Demo
            </button>
          </div>

          {/* Hero Stats */}
          <div className="grid grid-cols-3 gap-4 max-w-lg mx-auto text-sm">
            <div>
              <div className="text-2xl font-bold text-blue-400">Smart</div>
              <div className="text-slate-400">Email Parsing</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-cyan-400">Live</div>
              <div className="text-slate-400">Real-time Updates</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-purple-400">Visual</div>
              <div className="text-slate-400">Kanban Board</div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 px-4 sm:px-6 lg:px-8 bg-slate-800/50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
              Powerful Features
            </h2>
            <p className="text-xl text-slate-300 max-w-2xl mx-auto">
              Everything you need to manage your job search efficiently
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="bg-slate-700/50 backdrop-blur border border-slate-600 rounded-xl p-8 hover:bg-slate-700/70 transition">
              <Mail className="w-12 h-12 text-blue-400 mb-4" />
              <h3 className="text-xl font-bold text-white mb-3">Email Integration</h3>
              <p className="text-slate-300">
                Connect your email account and automatically capture job application confirmations
                and status updates.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="bg-slate-700/50 backdrop-blur border border-slate-600 rounded-xl p-8 hover:bg-slate-700/70 transition">
              <BarChart3 className="w-12 h-12 text-cyan-400 mb-4" />
              <h3 className="text-xl font-bold text-white mb-3">Smart Analytics</h3>
              <p className="text-slate-300">
                Get insights into your application success rate, response times, and trends to
                optimize your job search strategy.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="bg-slate-700/50 backdrop-blur border border-slate-600 rounded-xl p-8 hover:bg-slate-700/70 transition">
              <Zap className="w-12 h-12 text-purple-400 mb-4" />
              <h3 className="text-xl font-bold text-white mb-3">Real-time Updates</h3>
              <p className="text-slate-300">
                Get instant notifications when application statuses change, interviews are
                scheduled, or rejections arrive.
              </p>
            </div>

            {/* Feature 4 */}
            <div className="bg-slate-700/50 backdrop-blur border border-slate-600 rounded-xl p-8 hover:bg-slate-700/70 transition">
              <Clock className="w-12 h-12 text-orange-400 mb-4" />
              <h3 className="text-xl font-bold text-white mb-3">Follow-up Reminders</h3>
              <p className="text-slate-300">
                Never miss a follow-up deadline. Get reminders to check on your applications or
                reach out to recruiters.
              </p>
            </div>

            {/* Feature 5 */}
            <div className="bg-slate-700/50 backdrop-blur border border-slate-600 rounded-xl p-8 hover:bg-slate-700/70 transition">
              <TrendingUp className="w-12 h-12 text-green-400 mb-4" />
              <h3 className="text-xl font-bold text-white mb-3">Kanban Board</h3>
              <p className="text-slate-300">
                Visualize your job search with an intuitive Kanban board—see every application at
                a glance and drag to update status.
              </p>
            </div>

            {/* Feature 6 */}
            <div className="bg-slate-700/50 backdrop-blur border border-slate-600 rounded-xl p-8 hover:bg-slate-700/70 transition">
              <Shield className="w-12 h-12 text-indigo-400 mb-4" />
              <h3 className="text-xl font-bold text-white mb-3">Secure & Private</h3>
              <p className="text-slate-300">
                Your data is encrypted and secure. We never share your information with third
                parties.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section id="benefits" className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-16 text-center">
            Why Choose ApplyTrack?
          </h2>

          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div className="space-y-6">
              {[
                'Save hours per week managing applications manually',
                'Never miss an important status update or deadline',
                'Make data-driven decisions about your job search',
                'Reduce stress with organized application tracking',
                'Increase interview rates with follow-up reminders',
                'Stand out with professional application management',
              ].map((benefit, i) => (
                <div key={i} className="flex gap-4 items-start">
                  <CheckCircle2 className="w-6 h-6 text-green-400 flex-shrink-0 mt-1" />
                  <span className="text-lg text-slate-200">{benefit}</span>
                </div>
              ))}
            </div>

            <div className="bg-gradient-to-br from-blue-500/10 to-cyan-500/10 border border-blue-500/20 rounded-2xl p-12 h-96 flex items-center justify-center">
              <div className="text-center">
                <BarChart3 className="w-24 h-24 text-blue-400 mx-auto mb-4 opacity-20" />
                <p className="text-slate-400">Dashboard Preview</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-slate-800/50">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-16 text-center">
            How It Works
          </h2>

          <div className="grid md:grid-cols-4 gap-8">
            {[
              {
                step: '1',
                title: 'Sign Up',
                description: 'Create your free account in less than a minute',
              },
              {
                step: '2',
                title: 'Connect Email',
                description: 'Link your email for automatic application capture',
              },
              {
                step: '3',
                title: 'Track Applications',
                description: 'Watch your dashboard populate with job applications',
              },
              {
                step: '4',
                title: 'Get Insights',
                description: 'Analyze trends and optimize your job search',
              },
            ].map((item, i) => (
              <div key={i} className="relative">
                <div className="bg-gradient-to-br from-blue-500/20 to-cyan-500/20 border border-blue-500/30 rounded-xl p-8 text-center h-full">
                  <div className="inline-flex items-center justify-center w-12 h-12 bg-blue-600 text-white font-bold rounded-full mb-4">
                    {item.step}
                  </div>
                  <h3 className="text-xl font-bold text-white mb-2">{item.title}</h3>
                  <p className="text-slate-300">{item.description}</p>
                </div>
                {i < 3 && (
                  <div className="hidden md:block absolute top-1/2 -right-4 text-blue-500">
                    <ArrowRight className="w-8 h-8" />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
              Simple, Transparent Pricing
            </h2>
            <p className="text-xl text-slate-300">
              Start free. Upgrade only if you want premium features.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {/* Free Plan */}
            <div className="bg-slate-700/50 border border-slate-600 rounded-xl p-8">
              <h3 className="text-2xl font-bold text-white mb-2">Free</h3>
              <p className="text-slate-400 mb-6">Get started tracking your applications</p>
              <div className="mb-6">
                <span className="text-4xl font-bold text-white">Free</span>
              </div>
              <ul className="space-y-3 mb-8">
                {['Up to 10 applications', '1 email account', 'Kanban board', 'Basic analytics'].map(
                  (feature, i) => (
                    <li key={i} className="flex gap-2 items-center text-slate-300">
                      <CheckCircle2 className="w-5 h-5 text-green-400 flex-shrink-0" />
                      {feature}
                    </li>
                  )
                )}
              </ul>
              <Link
                to="/register"
                className="w-full bg-slate-600 hover:bg-slate-500 text-white py-2 rounded-lg font-semibold transition text-center"
              >
                Get Started
              </Link>
            </div>

            {/* Pro Plan */}
            <div className="bg-gradient-to-br from-blue-600/20 to-cyan-600/20 border-2 border-blue-500 rounded-xl p-8 transform md:scale-105">
              <div className="inline-flex items-center gap-2 bg-blue-500/20 border border-blue-500/40 rounded-full px-3 py-1 mb-4">
                <Star className="w-4 h-4 text-blue-300" />
                <span className="text-sm font-medium text-blue-300">Most Popular</span>
              </div>
              <h3 className="text-2xl font-bold text-white mb-2">Pro</h3>
              <p className="text-slate-300 mb-6">For serious job seekers</p>
              <div className="mb-6">
                <span className="text-4xl font-bold text-white">&#8377;499</span>
                <span className="text-slate-400">/month</span>
              </div>
              <ul className="space-y-3 mb-8">
                {[
                  'Unlimited applications',
                  '3 email accounts',
                  'AI-powered email parsing',
                  'Advanced analytics',
                ].map((feature, i) => (
                  <li key={i} className="flex gap-2 items-center text-slate-200">
                    <CheckCircle2 className="w-5 h-5 text-green-400 flex-shrink-0" />
                    {feature}
                  </li>
                ))}
              </ul>
              <Link
                to="/register"
                className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg font-semibold transition text-center"
              >
                Get Started
              </Link>
            </div>

            {/* Premium Plan */}
            <div className="bg-slate-700/50 border border-slate-600 rounded-xl p-8">
              <h3 className="text-2xl font-bold text-white mb-2">Premium</h3>
              <p className="text-slate-400 mb-6">Full feature access</p>
              <div className="mb-6">
                <span className="text-4xl font-bold text-white">&#8377;999</span>
                <span className="text-slate-400">/month</span>
              </div>
              <ul className="space-y-3 mb-8">
                {[
                  'Everything in Pro',
                  'Unlimited email accounts',
                  'Priority support',
                  'AI matching & analytics',
                ].map((feature, i) => (
                  <li key={i} className="flex gap-2 items-center text-slate-300">
                    <CheckCircle2 className="w-5 h-5 text-green-400 flex-shrink-0" />
                    {feature}
                  </li>
                ))}
              </ul>
              <Link
                to="/register"
                className="w-full border border-slate-500 hover:border-slate-400 text-white py-2 rounded-lg font-semibold transition text-center"
              >
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-r from-blue-600 to-cyan-600">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
            Ready to transform your job search?
          </h2>
          <p className="text-xl text-blue-100 mb-8">
            Join thousands of job seekers who are tracking smarter and landing more interviews.
          </p>
          <Link
            to="/register"
            className="inline-flex items-center gap-2 bg-white text-blue-600 px-8 py-4 rounded-lg font-bold hover:bg-blue-50 transition transform hover:scale-105"
          >
            Start Your Free Trial Today
            <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900 border-t border-slate-700 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <Briefcase className="w-6 h-6 text-blue-500" />
                <span className="font-bold text-white">ApplyTrack</span>
              </div>
              <p className="text-slate-400 text-sm">
                The smartest way to track your job applications.
              </p>
            </div>
            <div>
              <h4 className="font-bold text-white mb-4">Product</h4>
              <ul className="space-y-2 text-sm text-slate-400">
                <li>
                  <a href="#features" className="hover:text-white transition">
                    Features
                  </a>
                </li>
                <li>
                  <a href="#pricing" className="hover:text-white transition">
                    Pricing
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold text-white mb-4">Company</h4>
              <ul className="space-y-2 text-sm text-slate-400">
                <li>
                  <a href="#" className="hover:text-white transition">
                    About
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-white transition">
                    Blog
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold text-white mb-4">Legal</h4>
              <ul className="space-y-2 text-sm text-slate-400">
                <li>
                  <a href="#" className="hover:text-white transition">
                    Privacy
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-white transition">
                    Terms
                  </a>
                </li>
              </ul>
            </div>
          </div>
          <div className="border-t border-slate-700 pt-8">
            <p className="text-center text-slate-400 text-sm">
              © 2026 ApplyTrack. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
