// Modelos para el panel de gestión de tenants (superadmin)

// ── License Period ────────────────────────────────────────────────────────
export type LicensePeriod = 'trial' | 'monthly' | 'bimonthly' | 'quarterly' | 'annual';

export const LICENSE_PERIOD_LABELS: Record<LicensePeriod, string> = {
  trial:     'Prueba (14 días)',
  monthly:   'Mensual (30 días)',
  bimonthly: 'Bimestral (60 días)',
  quarterly: 'Trimestral (90 días)',
  annual:    'Anual (360 días)',
};

export const LICENSE_PERIOD_DAYS: Record<LicensePeriod, number> = {
  trial:     14,
  monthly:   30,
  bimonthly: 60,
  quarterly: 90,
  annual:    360,
};

// ── License Renewal ───────────────────────────────────────────────────────
export type RenewalStatus = 'pending' | 'confirmed' | 'activated' | 'cancelled';

export interface LicenseRenewal {
  id: string;
  period: LicensePeriod;
  period_display: string;
  status: RenewalStatus;
  status_display: string;
  new_starts_at: string;
  new_expires_at: string;
  payment_method: 'manual' | 'gateway';
  gateway_reference: string;
  auto_generated: boolean;
  confirmed_by: string | null;
  confirmed_by_email: string | null;
  confirmed_at: string | null;
  activated_at: string | null;
  notes: string;
  created_at: string;
}

export interface LicenseHistory {
  id: string;
  change_type: 'created' | 'renewed' | 'extended' | 'suspended' | 'activated' | 'modified';
  changed_by: string | null;
  changed_by_email: string | null;
  previous_state: Record<string, unknown>;
  notes: string;
  created_at: string;
}

export interface LicensePayment {
  id: string;
  amount: string;
  payment_date: string;
  method: 'transfer' | 'cash' | 'card';
  reference: string;
  notes: string;
  created_at: string;
}

export interface TenantLicense {
  id: string;
  company: string;
  company_name: string;
  company_nit: string;
  plan: 'starter' | 'professional' | 'enterprise';
  status: 'trial' | 'active' | 'expired' | 'suspended';
  period: LicensePeriod;
  starts_at: string;
  expires_at: string;
  pending_renewal: LicenseRenewal | null;
  max_users: number;
  concurrent_users: number;
  modules_included: string[];
  messages_quota: number;
  messages_used: number;
  ai_tokens_quota: number;
  ai_tokens_used: number;
  last_reset_date: string | null;
  notes: string;
  days_until_expiry: number;
  is_expired: boolean;
  is_active_and_valid: boolean;
  created_by: string | null;
  created_by_email: string | null;
  payments: LicensePayment[];
  history: LicenseHistory[];
  created_at: string;
  updated_at: string;
}

export interface TenantLicenseSummary {
  id: string;
  company: string;
  company_name: string;
  company_nit: string;
  plan: string;
  status: string;
  starts_at: string;
  expires_at: string;
  max_users: number;
  concurrent_users: number;
  days_until_expiry: number;
  is_expired: boolean;
  is_active_and_valid: boolean;
  updated_at: string;
}

export interface Tenant {
  id: string;
  name: string;
  nit: string;
  plan: 'starter' | 'professional' | 'enterprise';
  is_active: boolean;
  created_at: string;
  license: TenantLicenseSummary | null;
  active_users: number;
  modules: string[];
}

export interface TenantCreateRequest {
  // Empresa
  name: string;
  nit: string;
  plan: 'starter' | 'professional' | 'enterprise';
  saiopen_enabled?: boolean;
  // Licencia
  license_status: 'trial' | 'active';
  license_starts_at: string;
  license_expires_at: string;
  concurrent_users: number;
  max_users: number;
  modules_included: string[];
  messages_quota?: number;
  ai_tokens_quota?: number;
  license_notes?: string;
}

export interface LicenseWriteRequest {
  plan?: string;
  status?: string;
  starts_at: string;
  expires_at: string;
  max_users?: number;
  concurrent_users?: number;
  modules_included?: string[];
  messages_quota?: number;
  ai_tokens_quota?: number;
  notes?: string;
}

export interface LicensePaymentRequest {
  amount: number;
  payment_date: string;
  method: 'transfer' | 'cash' | 'card';
  reference?: string;
  notes?: string;
}

export const LICENSE_STATUS_LABELS: Record<string, string> = {
  trial:     'Prueba',
  active:    'Activa',
  expired:   'Expirada',
  suspended: 'Suspendida',
};

export const LICENSE_STATUS_COLOR: Record<string, 'primary' | 'accent' | 'warn'> = {
  trial:     'accent',
  active:    'primary',
  expired:   'warn',
  suspended: 'warn',
};

export const PLAN_LABELS: Record<string, string> = {
  starter:      'Starter',
  professional: 'Professional',
  enterprise:   'Enterprise',
};

export const MODULE_LABELS: Record<string, string> = {
  proyectos: 'SaiProyectos',
  crm:       'CRM',
  soporte:   'Soporte',
  dashboard: 'SaiDashboard',
};

// ── LicensePackage (catálogo global) ─────────────────────────────────────
export type PackageType = 'module' | 'user_seats' | 'ai_tokens' | 'ai_messages';

export const PACKAGE_TYPE_LABELS: Record<PackageType, string> = {
  module:      'Módulo',
  user_seats:  'Puestos de usuario',
  ai_tokens:   'Tokens IA',
  ai_messages: 'Mensajes IA',
};

export interface LicensePackage {
  id: string;
  code: string;
  name: string;
  description: string;
  package_type: PackageType;
  package_type_display: string;
  module_code: string;
  quantity: number;
  price_monthly: string;
  price_annual: string;
  is_active: boolean;
  created_at: string;
}

export interface LicensePackageWriteRequest {
  code: string;
  name: string;
  description?: string;
  package_type: PackageType;
  module_code?: string;
  quantity?: number;
  price_monthly: number;
  price_annual: number;
  is_active?: boolean;
}

// ── LicensePackageItem (paquete asignado a una licencia) ──────────────────
export interface LicensePackageItem {
  id: string;
  package: LicensePackage;
  quantity: number;
  added_at: string;
  added_by_email: string | null;
}

// ── MonthlyLicenseSnapshot ────────────────────────────────────────────────
export interface MonthlyLicenseSnapshot {
  id: string;
  month: string;
  snapshot: Record<string, unknown>;
  created_at: string;
}

// ── AIUsageLog ────────────────────────────────────────────────────────────
export interface AIUsageSummary {
  total_requests: number;
  total_tokens: number;
  messages_quota: number;
  messages_used: number;
  tokens_quota: number;
  tokens_used: number;
  messages_pct: number;
  tokens_pct: number;
}

export interface AIUsagePerUser {
  user_id: string;
  email: string;
  full_name: string;
  total_requests: number;
  total_tokens: number;
}

export interface AgentTokenInfo {
  id: string;
  token: string;
  label: string;
  is_active: boolean;
  last_used: string | null;
  created_at: string;
}
