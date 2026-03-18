export type UserRole =
  | 'company_admin'
  | 'seller'
  | 'collector'
  | 'viewer'
  | 'valmen_admin'
  | 'valmen_support';

export const ROLE_LABELS: Record<UserRole, string> = {
  company_admin:   'Administrador',
  seller:          'Vendedor',
  collector:       'Cobrador',
  viewer:          'Solo lectura',
  valmen_admin:    'Admin ValMen Tech',
  valmen_support:  'Soporte ValMen Tech',
};

export const ROLE_OPTIONS = (Object.entries(ROLE_LABELS) as [UserRole, string][]).map(
  ([value, label]) => ({ value, label }),
);

export type ModuleKey = 'ventas' | 'cobros' | 'dashboard' | 'proyectos';

export const MODULE_LABELS: Record<ModuleKey, string> = {
  ventas:    'SaiVentas',
  cobros:    'SaiCobros',
  dashboard: 'SaiDashboard',
  proyectos: 'SaiProyectos',
};

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

export interface CompanySettings {
  id: string;
  name: string;
  nit: string;
  plan: string;
  saiopen_enabled: boolean;
  is_active: boolean;
  modules: CompanyModule[];
  created_at: string;
}
