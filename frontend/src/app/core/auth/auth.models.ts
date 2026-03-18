export interface CompanySummary {
  id: string;
  name: string;
  nit: string;
  plan?: string;
}

export interface UserProfile {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: string;
  is_superadmin?: boolean;
  company: CompanySummary | null;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access: string;
  refresh: string;
  user: UserProfile;
}

export interface TokenRefreshResponse {
  access: string;
  refresh: string;
}

export interface RegisterRequest {
  company_name: string;
  company_nit: string;
  company_plan: 'starter' | 'professional' | 'enterprise';
  email: string;
  password: string;
  first_name: string;
  last_name: string;
}

export interface RegisterResponse {
  access: string;
  refresh: string;
  user: UserProfile;
  company: CompanyDetail;
}

export interface CompanyDetail {
  id: string;
  name: string;
  nit: string;
  plan: string;
  saiopen_enabled: boolean;
  saiopen_db_path: string;
  is_active: boolean;
  modules: string[];
  created_at: string;
}

export interface UserCompanyInfo {
  id: string;
  name: string;
  nit: string;
  plan: string;
  role: string;
}
