/**
 * SaiSuite — Módulo CRM: Modelos TypeScript
 * Espeja los serializers de apps/crm/
 */

// ── Enums ─────────────────────────────────────────────────────────────────────

export type FuenteLead = 'manual' | 'webhook' | 'csv' | 'referido' | 'otro';
export type TipoActividad = 'llamada' | 'reunion' | 'email' | 'tarea' | 'whatsapp' | 'otro';
export type TipoTimelineEvent =
  | 'nota'
  | 'cambio_etapa'
  | 'actividad_comp'
  | 'email_enviado'
  | 'cotizacion'
  | 'sistema';
export type EstadoCotizacion =
  | 'borrador'
  | 'enviada'
  | 'aceptada'
  | 'rechazada'
  | 'vencida'
  | 'anulada';

// ── Pipeline & Etapas ─────────────────────────────────────────────────────────

export interface CrmEtapa {
  id: string;
  nombre: string;
  orden: number;
  color: string;
  probabilidad: string;
  es_ganado: boolean;
  es_perdido: boolean;
  oportunidades_count?: number;
}

export interface CrmPipeline {
  id: string;
  nombre: string;
  es_default: boolean;
  etapas: CrmEtapa[];
  created_at: string;
}

// ── Kanban ────────────────────────────────────────────────────────────────────

export interface KanbanOportunidad {
  id: string;
  titulo: string;
  contacto_nombre: string | null;
  valor_esperado: string;
  probabilidad: string;
  asignado_a_nombre: string | null;
  proxima_actividad_tipo: TipoActividad | null;
  proxima_actividad_fecha: string | null;
  created_at: string;
}

export interface KanbanColumna {
  etapa_id: string;
  etapa_nombre: string;
  color: string;
  probabilidad: string;
  es_ganado: boolean;
  es_perdido: boolean;
  oportunidades: KanbanOportunidad[];
  total_count: number;
  total_valor: string;
}

// ── Leads ─────────────────────────────────────────────────────────────────────

export interface CrmLead {
  id: string;
  nombre: string;
  empresa: string;
  email: string;
  telefono: string;
  cargo: string;
  fuente: FuenteLead;
  score: number;
  convertido: boolean;
  oportunidad: string | null;
  asignado_a: string | null;
  asignado_a_nombre: string | null;
  pipeline: string | null;
  notas: string;
  created_at: string;
  updated_at: string;
}

export interface CrmLeadCreate {
  nombre: string;
  empresa?: string;
  email?: string;
  telefono?: string;
  cargo?: string;
  fuente: FuenteLead;
  pipeline?: string;
  asignado_a?: string | null;
  notas?: string;
}

// ── Oportunidad ───────────────────────────────────────────────────────────────

export interface CrmOportunidad {
  id: string;
  titulo: string;
  pipeline: string;
  pipeline_nombre: string;
  etapa: string;
  etapa_nombre: string;
  etapa_color: string;
  contacto: string | null;
  contacto_nombre: string | null;
  asignado_a: string | null;
  asignado_a_nombre: string | null;
  valor_esperado: string;
  probabilidad: string;
  valor_ponderado: string;
  fecha_cierre_estimada: string | null;
  ganada_en: string | null;
  perdida_en: string | null;
  motivo_perdida: string;
  proxima_actividad_fecha: string | null;
  proxima_actividad_tipo: TipoActividad | null;
  created_at: string;
  updated_at: string;
}

export interface CrmOportunidadCreate {
  titulo: string;
  pipeline: string;
  etapa: string;
  contacto?: string | null;
  asignado_a?: string | null;
  valor_esperado: string;
  probabilidad: string;
  fecha_cierre_estimada?: string | null;
}

// ── Actividad ─────────────────────────────────────────────────────────────────

export interface CrmActividad {
  id: string;
  oportunidad: string | null;
  lead: string | null;
  tipo: TipoActividad;
  tipo_display: string;
  titulo: string;
  descripcion: string;
  fecha_programada: string;
  completada: boolean;
  completada_en: string | null;
  resultado: string;
  asignado_a: string | null;
  asignado_a_nombre: string | null;
  created_at: string;
}

export interface CrmActividadCreate {
  tipo: TipoActividad;
  titulo: string;
  descripcion?: string;
  fecha_programada: string;
  asignado_a?: string | null;
}

export interface CrmActividadAgenda extends CrmActividad {
  contexto_nombre: string | null;
  contexto_tipo: 'oportunidad' | 'lead' | null;
}

// ── Timeline ──────────────────────────────────────────────────────────────────

export interface CrmTimelineEvent {
  id: string;
  tipo: TipoTimelineEvent;
  descripcion: string;
  usuario_nombre: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
}

// ── Cotización ────────────────────────────────────────────────────────────────

export interface CrmImpuesto {
  id: string;
  nombre: string;
  porcentaje: string;
}

export interface CrmProducto {
  id: string;
  codigo: string;
  nombre: string;
  descripcion: string;
  precio_base: string;
  unidad_venta: string;
  impuesto: string | null;
  impuesto_nombre: string | null;
  impuesto_porcentaje: string | null;
}

export interface CrmLineaCotizacion {
  id: string;
  conteo: number;
  producto: string | null;
  descripcion: string;
  cantidad: string;
  vlr_unitario: string;
  descuento_p: string;
  impuesto: string | null;
  iva_valor: string;
  total_parcial: string;
}

export interface CrmLineaCotizacionCreate {
  producto?: string | null;
  descripcion: string;
  cantidad: string;
  vlr_unitario: string;
  descuento_p?: string;
  impuesto?: string | null;
}

export interface CrmCotizacion {
  id: string;
  oportunidad: string;
  numero_interno: string;
  titulo: string;
  estado: EstadoCotizacion;
  contacto: string | null;
  contacto_nombre: string | null;
  validez_dias: number;
  fecha_vencimiento: string | null;
  subtotal: string;
  descuento_adicional_p: string;
  descuento_adicional_val: string;
  total_iva: string;
  total: string;
  notas: string;
  terminos: string;
  sai_key: string | null;
  saiopen_synced: boolean;
  lineas: CrmLineaCotizacion[];
  created_at: string;
  updated_at: string;
}

export interface CrmCotizacionCreate {
  titulo?: string;
  contacto?: string | null;
  validez_dias?: number;
  notas?: string;
  terminos?: string;
}

// ── Dashboard ─────────────────────────────────────────────────────────────────

export interface CrmFunnelItem {
  etapa_id: string;
  etapa_nombre: string;
  color: string;
  count: number;
  valor_total: string;
  probabilidad: string;
}

export interface CrmVendedorRendimiento {
  usuario_id: string;
  nombre: string;
  oportunidades_activas: number;
  ganadas_mes: number;
  perdidas_mes: number;
  valor_ganado_mes: string;
}

export interface CrmForecastDetalle {
  etapa_id: string;
  etapa_nombre: string;
  count: number;
  valor_esperado: string;
  valor_ponderado: string;
  probabilidad: string;
}

export interface CrmDashboard {
  total_leads: number;
  leads_nuevos_mes: number;
  oportunidades_activas: number;
  valor_total_activo: string;
  tasa_conversion: string;
  forecast: string;
  funnel: CrmFunnelItem[];
  rendimiento_vendedores: CrmVendedorRendimiento[];
}

export interface CrmForecast {
  total_forecast: string;
  total_valor_esperado: string;
  detalle: CrmForecastDetalle[];
}

// ── Scoring Rule ──────────────────────────────────────────────────────────────

export type OperadorRegla = 'eq' | 'neq' | 'contains' | 'not_empty' | 'gt' | 'lt';

export interface CrmLeadScoringRule {
  id: string;
  nombre: string;
  campo: string;
  operador: OperadorRegla;
  valor: string;
  puntos: number;
  orden: number;
  activa: boolean;
}
