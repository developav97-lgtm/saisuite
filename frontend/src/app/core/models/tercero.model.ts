/**
 * SaiSuite — Modelo Tercero (TRANSVERSAL)
 * Espeja exactamente TerceroListSerializer, TerceroDetailSerializer,
 * TerceroCreateUpdateSerializer y TerceroDireccionSerializer de apps/terceros.
 */

export type TipoIdentificacion = 'nit' | 'cc' | 'ce' | 'pas' | 'otro';
export type TipoPersona = 'natural' | 'juridica';
export type TipoTercero =
  | 'cliente'
  | 'proveedor'
  | 'subcontratista'
  | 'interventor'
  | 'consultor'
  | 'empleado'
  | 'otro';
export type TipoDireccion =
  | 'principal'
  | 'sucursal'
  | 'bodega'
  | 'facturacion'
  | 'otro';

// ── TerceroDireccion ──────────────────────────────────────────────────────────

export interface TerceroDireccion {
  id: string;
  tipo: TipoDireccion;
  nombre_sucursal: string;
  pais: string;
  departamento: string;
  ciudad: string;
  direccion_linea1: string;
  direccion_linea2: string;
  codigo_postal: string;
  nombre_contacto: string;
  telefono_contacto: string;
  email_contacto: string;
  saiopen_linea_id: string | null;
  activa: boolean;
  es_principal: boolean;
  created_at: string;
  updated_at: string;
}

// ── Tercero List (campos mínimos para tablas / autocomplete) ─────────────────

export interface TerceroList {
  id: string;
  codigo: string;
  tipo_identificacion: TipoIdentificacion;
  numero_identificacion: string;
  nombre_completo: string;
  tipo_persona: TipoPersona;
  tipo_tercero: TipoTercero | '';
  email: string;
  telefono: string;
  celular: string;
  saiopen_synced: boolean;
  activo: boolean;
}

// ── Tercero Detail (detalle completo con direcciones) ─────────────────────────

export interface TerceroDetail extends TerceroList {
  primer_nombre: string;
  segundo_nombre: string;
  primer_apellido: string;
  segundo_apellido: string;
  razon_social: string;
  saiopen_id: string | null;
  sai_key: string | null;
  direcciones: TerceroDireccion[];
  created_at: string;
  updated_at: string;
}

// ── Tercero Create/Update ─────────────────────────────────────────────────────

export interface TerceroCreate {
  tipo_identificacion: TipoIdentificacion;
  numero_identificacion: string;
  primer_nombre?: string;
  segundo_nombre?: string;
  primer_apellido?: string;
  segundo_apellido?: string;
  razon_social?: string;
  tipo_persona: TipoPersona;
  tipo_tercero?: TipoTercero | '';
  email?: string;
  telefono?: string;
  celular?: string;
}

// ── Labels ────────────────────────────────────────────────────────────────────

export const TIPO_IDENTIFICACION_LABELS: Record<TipoIdentificacion, string> = {
  nit:  'NIT',
  cc:   'Cédula de ciudadanía',
  ce:   'Cédula de extranjería',
  pas:  'Pasaporte',
  otro: 'Otro',
};

export const TIPO_PERSONA_LABELS: Record<TipoPersona, string> = {
  natural:  'Persona natural',
  juridica: 'Persona jurídica',
};

export const TIPO_TERCERO_LABELS: Partial<Record<TipoTercero, string>> = {
  cliente:        'Cliente',
  proveedor:      'Proveedor',
  subcontratista: 'Subcontratista',
  interventor:    'Interventor',
  consultor:      'Consultor',
  empleado:       'Empleado',
  otro:           'Otro',
};
