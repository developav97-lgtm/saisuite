/**
 * SaiSuite — Modelos de TerceroProyecto
 * Espeja exactamente TerceroProyectoSerializer y TerceroProyectoCreateSerializer.
 */

export type RolTercero =
  | 'cliente'
  | 'proveedor'
  | 'subcontratista'
  | 'interventor'
  | 'consultor'
  | 'otro';

export interface TerceroProyecto {
  id: string;
  proyecto: string;
  tercero_id: string;
  tercero_nombre: string;
  rol: RolTercero;
  rol_display: string;
  fase: string | null;
  fase_nombre: string | null;
  tercero_fk: string | null;
  tercero_fk_nombre: string | null;
  activo: boolean;
  created_at: string;
}

export interface TerceroProyectoCreate {
  tercero_id: string;
  tercero_nombre: string;
  rol: RolTercero;
  fase?: string | null;
  tercero_fk?: string | null;
}

export const ROL_LABELS: Record<RolTercero, string> = {
  cliente:        'Cliente',
  proveedor:      'Proveedor',
  subcontratista: 'Subcontratista',
  interventor:    'Interventor',
  consultor:      'Consultor',
  otro:           'Otro',
};

export const ROL_OPTIONS: { value: RolTercero; label: string }[] = (
  Object.entries(ROL_LABELS) as [RolTercero, string][]
).map(([value, label]) => ({ value, label }));
