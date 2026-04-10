export interface User {
  id: number;
  email: string;
  name?: string;
  is_active: boolean;
  created_at: string;
  inbox_address?: string;
}

export type ApplicationStatus = 'applied' | 'screening' | 'interview' | 'offer' | 'rejected' | 'accepted';
export type JobSource = 'linkedin' | 'naukri' | 'indeed' | 'manual' | 'unknown';

export interface Application {
  id: number;
  user_id: number;
  company_name: string;
  position_title: string;
  location?: string;
  salary_range?: string;
  source: JobSource;
  status: ApplicationStatus;
  applied_date: string;
  last_updated: string;
  notes?: string;
  email_thread_id?: string;
  metadata?: Record<string, unknown>;
}

export interface ApplicationCreate {
  company_name: string;
  position_title: string;
  location?: string;
  salary_range?: string;
  source?: string;
  status?: string;
  notes?: string;
}

export interface ApplicationUpdate {
  company_name?: string;
  position_title?: string;
  location?: string;
  salary_range?: string;
  status?: string;
  notes?: string;
}

export interface StatusHistory {
  id: number;
  from_status: string | null;
  to_status: string;
  changed_at: string;
  reason?: string;
}

export interface EmailAccount {
  id: number;
  user_id: number;
  provider: string;
  email: string;
  last_sync_at?: string;
  is_active: boolean;
  created_at: string;
}

export interface EmailAccountCreate {
  provider: string;
  email: string;
  imap_host?: string;
  imap_port?: number;
  imap_username?: string;
  imap_password?: string;
}

export interface BoardColumn {
  id: ApplicationStatus;
  title: string;
  order: number;
}

export interface BoardData {
  columns: BoardColumn[];
  data: Record<ApplicationStatus, Application[]>;
}

export interface StatsOverview {
  total_applications: number;
  by_status: Record<string, number>;
  response_rate: number;
  interview_rate: number;
  offer_rate: number;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface SubscriptionPlan {
  id: number;
  name: string;
  plan_type: string;
  price_monthly: number;
  price_yearly?: number;
  razorpay_plan_id?: string;
  description?: string;
  features?: Record<string, unknown>;
  is_active: boolean;
}

export interface Subscription {
  id: number;
  user_id: number;
  plan_id: number;
  razorpay_subscription_id?: string;
  razorpay_customer_id?: string;
  status: string;
  current_period_start?: string;
  current_period_end?: string;
  trial_start?: string;
  trial_end?: string;
  cancelled_at?: string;
  created_at: string;
}

export interface SubscriptionCreate {
  plan_id: number;
}

export interface Activity {
  id: number;
  type: string;
  description: string;
  extra_data?: Record<string, unknown>;
  created_at: string;
}

export interface ActivityCreate {
  type: string;
  description: string;
  extra_data?: Record<string, unknown>;
}
