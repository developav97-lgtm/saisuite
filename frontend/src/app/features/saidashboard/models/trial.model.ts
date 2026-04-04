/** Trial/license status model — mirrors backend trial endpoints. */

export interface TrialStatus {
  tiene_acceso: boolean;
  tipo_acceso: 'trial' | 'licensed' | 'none';
  dias_restantes: number;
  expira_en: string | null;
}

export interface TrialActivateResponse {
  module_code: string;
  iniciado_en: string;
  expira_en: string;
  esta_activo: boolean;
  dias_restantes: number;
}
