/** Report BI models — mirrors backend ReportBI serializers exactly. */

import { BIFieldConfig, BIFilterV2, BISortConfig } from './bi-field.model';

export type ReportBICategory =
  | 'contabilidad'
  | 'cuentas_pagar'
  | 'cuentas_cobrar'
  | 'ventas'
  | 'inventario'
  | 'costos'
  | 'proyectos'
  | 'tributario'
  | 'gerencial';

export const REPORT_BI_CATEGORY_LABELS: Record<ReportBICategory, string> = {
  contabilidad:   'Contabilidad',
  cuentas_pagar:  'Cuentas por Pagar',
  cuentas_cobrar: 'Cuentas por Cobrar',
  ventas:         'Ventas',
  inventario:     'Inventario',
  costos:         'Costos y Gastos',
  proyectos:      'Proyectos',
  tributario:     'Tributario',
  gerencial:      'Gerencial / KPIs',
};

export const REPORT_BI_CATEGORY_ICONS: Record<ReportBICategory, string> = {
  contabilidad:   'account_balance',
  cuentas_pagar:  'payments',
  cuentas_cobrar: 'receipt_long',
  ventas:         'store',
  inventario:     'inventory_2',
  costos:         'analytics',
  proyectos:      'folder_special',
  tributario:     'gavel',
  gerencial:      'leaderboard',
};

export type ReportBIVisualization = 'table' | 'pivot' | 'bar' | 'line' | 'pie' | 'area' | 'kpi' | 'waterfall';

export const VISUALIZATION_LABELS: Record<ReportBIVisualization, string> = {
  table:     'Tabla',
  pivot:     'Tabla Dinámica',
  bar:       'Barras',
  line:      'Líneas',
  pie:       'Torta',
  area:      'Área',
  kpi:       'KPI',
  waterfall: 'Cascada',
};

export const VISUALIZATION_ICONS: Record<ReportBIVisualization, string> = {
  table:     'table_chart',
  pivot:     'pivot_table_chart',
  bar:       'bar_chart',
  line:      'show_chart',
  pie:       'donut_large',
  area:      'area_chart',
  kpi:       'speed',
  waterfall: 'waterfall_chart',
};

export interface ReportBIUser {
  id: string;
  email: string;
  full_name: string;
}

export interface ReportBIShare {
  user_id: string;
  email: string;
  full_name: string;
  puede_editar: boolean;
  creado_en: string;
}

/** Listado — campos mínimos. */
export interface ReportBIListItem {
  id: string;
  titulo: string;
  es_privado: boolean;
  es_favorito: boolean;
  es_template: boolean;
  fuentes: string[];
  tipo_visualizacion: ReportBIVisualization;
  categoria_galeria: ReportBICategory | null;
  user_email: string;
  user_id: string;
  created_at: string;
  updated_at: string;
}

/** Detalle — config completa. */
export interface ReportBIDetail {
  id: string;
  titulo: string;
  es_privado: boolean;
  es_favorito: boolean;
  es_template: boolean;
  fuentes: string[];
  categoria_galeria: ReportBICategory | null;
  campos_config: BIFieldConfig[];
  tipo_visualizacion: ReportBIVisualization;
  viz_config: Record<string, unknown>;
  /** V2: array de filtros con operadores. V1 (legacy): dict key→value. */
  filtros: BIFilterV2[] | Record<string, unknown>;
  orden_config: BISortConfig[];
  limite_registros: number | null;
  template_origen: string | null;
  user: ReportBIUser;
  shares: ReportBIShare[];
  created_at: string;
  updated_at: string;
}

/** Payload para crear reporte. */
export interface ReportBICreateRequest {
  titulo: string;
  es_privado?: boolean;
  fuentes: string[];
  campos_config?: BIFieldConfig[];
  tipo_visualizacion?: ReportBIVisualization;
  viz_config?: Record<string, unknown>;
  filtros?: BIFilterV2[];
  orden_config?: BISortConfig[];
  limite_registros?: number | null;
  template_origen?: string | null;
}

/** Payload para actualizar reporte. */
export interface ReportBIUpdateRequest {
  titulo?: string;
  es_privado?: boolean;
  es_favorito?: boolean;
  fuentes?: string[];
  campos_config?: BIFieldConfig[];
  tipo_visualizacion?: ReportBIVisualization;
  viz_config?: Record<string, unknown>;
  filtros?: BIFilterV2[];
  orden_config?: BISortConfig[];
  limite_registros?: number | null;
}

/** Payload para ejecutar/preview.
 *  filtros: V2 array (nuevo) o dict V1 (legacy drill-down). Backend acepta ambos. */
export interface ReportBIExecuteRequest {
  fuentes: string[];
  campos_config: BIFieldConfig[];
  tipo_visualizacion?: ReportBIVisualization;
  viz_config?: Record<string, unknown>;
  filtros?: BIFilterV2[] | Record<string, unknown>;
  orden_config?: BISortConfig[];
  limite_registros?: number | null;
}

/** Payload para duplicar reporte. */
export interface ReportBIDuplicateRequest {
  titulo: string;
}

/** Columna de resultado — tal como la devuelve el backend. */
export interface ReportBIColumn {
  field: string;
  label: string;
  type: 'dimension' | 'metric';
}

/** Resultado de ejecución — tabla plana. */
export interface ReportBITableResult {
  columns: ReportBIColumn[];
  rows: Record<string, unknown>[];
  total_count: number;
}

/** Resultado de ejecución — pivot. */
export interface ReportBIPivotResult {
  row_headers: Record<string, unknown>[];
  col_headers: Record<string, unknown>[];
  data: Record<string, Record<string, number>>;
  row_totals: Record<string, Record<string, number>>;
  col_totals: Record<string, Record<string, number>>;
  grand_total: Record<string, number>;
  value_aliases: string[];
  no_column_mode: boolean;
  value_labels: Record<string, string>;
}

/** Resultado unificado de ejecución de reporte. */
export type ReportBIExecuteResult = ReportBITableResult | ReportBIPivotResult;

/** Type guards */
export function isPivotResult(r: ReportBIExecuteResult): r is ReportBIPivotResult {
  return 'row_headers' in r && 'col_headers' in r && 'data' in r;
}

export function isTableResult(r: ReportBIExecuteResult): r is ReportBITableResult {
  return 'columns' in r && 'rows' in r;
}

/** Grupo de galería — categoría + lista de reportes. */
export interface ReportBIGalleryGroup {
  categoria: ReportBICategory;
  categoria_label: string;
  reportes: ReportBIListItem[];
}

/** Resultado de sugerencia IA de reporte. */
export interface BISuggestResult {
  template_titulo: string | null;
  explanation: string;
  config: ReportBICreateRequest | null;
}

/**
 * Template estático del catálogo del sistema (viene de bi_templates.py vía /catalogo/).
 * Global: disponible a todos los tenants sin seeding.
 */
export interface StaticTemplate {
  titulo: string;
  descripcion?: string;
  fuentes: string[];
  campos_config: BIFieldConfig[];
  tipo_visualizacion: ReportBIVisualization;
  viz_config?: Record<string, unknown>;
  filtros?: BIFilterV2[] | Record<string, unknown>;
  orden_config?: BISortConfig[];
  limite_registros?: number | null;
  categoria_galeria?: string;
}

/** Payload para compartir. */
export interface ReportBIShareRequest {
  user_id: string;
  puede_editar?: boolean;
}
