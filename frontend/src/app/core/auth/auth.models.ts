export interface LicenseSummary {
  status: 'trial' | 'active' | 'expired' | 'suspended';
  expires_at: string;
  days_until_expiry: number;
  is_active_and_valid: boolean;
  concurrent_users: number;
  modules_included: string[];
}

export interface CompanySummary {
  id: string;
  name: string;
  nit: string;
  plan?: string;
  license?: LicenseSummary | null;
}

export interface PermissionSummary {
  id: number;
  codigo: string;
  modulo: string;
  accion: string;
}

export interface RolGranularSummary {
  id: number;
  nombre: string;
  tipo: 'admin' | 'readonly' | 'custom';
  permisos?: PermissionSummary[];
}

export interface UserProfile {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: string;
  is_superadmin?: boolean;
  is_staff?: boolean;
  is_superuser?: boolean;
  company: CompanySummary | null;
  effective_company?: CompanySummary | null;
  tipo_usuario?: 'superadmin' | 'soporte' | 'admin_tenant' | 'usuario_tenant';
  tenant_activo?: { id: string; name: string; nit: string } | null;
  rol_granular?: RolGranularSummary | null;
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
