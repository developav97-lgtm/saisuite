export type UserRole =
  | 'company_admin'
  | 'seller'
  | 'collector'
  | 'viewer'
  | 'valmen_admin'
  | 'valmen_support';

export const ROLE_LABELS: Record<UserRole, string> = {
  company_admin:   'Administrador',
  seller:          'Usuario',
  collector:       'Usuario',
  viewer:          'Solo lectura',
  valmen_admin:    'Super Admin',
  valmen_support:  'Soporte',
};

/** Opciones visibles para empresas cliente al crear/editar usuarios. No incluye roles internos ValMen ni collector. */
export const ROLE_OPTIONS: { value: UserRole; label: string }[] = [
  { value: 'company_admin', label: 'Administrador' },
  { value: 'seller',        label: 'Usuario' },
  { value: 'viewer',        label: 'Solo lectura' },
];

export type ModuleKey = 'crm' | 'soporte' | 'dashboard' | 'proyectos';

export const MODULE_LABELS: Record<string, string | undefined> = {
  crm:       'CRM',
  soporte:   'Soporte',
  dashboard: 'SaiDashboard',
  proyectos: 'SaiProyectos',
};

export interface RoleSummary {
  id: number;
  nombre: string;
  tipo: 'admin' | 'readonly' | 'custom';
}

export interface AdminUser {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  is_superadmin: boolean;
  modules_access: string[];
  rol_granular: RoleSummary | null;
}

export interface CreateUserDto {
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  password: string;
  modules_access: string[];
}

export interface CompanyModule {
  id: string;
  module: ModuleKey;
  is_active: boolean;
}

export interface CompanyLicense {
  id: string;
  plan: string;
  status: 'trial' | 'active' | 'expired' | 'suspended';
  starts_at: string;
  expires_at: string;
  max_users: number;
  days_until_expiry: number;
  is_expired: boolean;
  modules_included: string[];
}

export const LICENSE_STATUS_LABELS: Record<string, string> = {
  trial:     'Prueba',
  active:    'Activa',
  expired:   'Expirada',
  suspended: 'Suspendida',
};

export interface CompanySettings {
  id: string;
  name: string;
  nit: string;
  plan: string;
  saiopen_enabled: boolean;
  logo: string | null;
  is_active: boolean;
  modules: CompanyModule[];
  created_at: string;
}
