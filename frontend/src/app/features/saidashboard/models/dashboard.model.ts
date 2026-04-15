/** Dashboard module models — mirrors backend DRF serializers exactly. */

import { ReportFilter } from './report-filter.model';

export interface DashboardUser {
  id: string;
  email: string;
  full_name: string;
}

export interface DashboardShare {
  user_id: string;
  user_email: string;
  user_name: string;
  puede_editar: boolean;
  shared_at: string;
}

export interface DashboardCard {
  id: number;
  card_type_code: string;
  chart_type: ChartType;
  pos_x: number;
  pos_y: number;
  width: number;
  height: number;
  filtros_config: Record<string, unknown>;
  titulo_personalizado: string;
  orden: number;
  // Campos para tarjetas de tipo 'bi_report' (null en otros tipos)
  bi_report_id: string | null;
  bi_report_titulo: string | null;
  bi_report_tipo_visualizacion: string | null;
  bi_report_campos_config: BiFieldConfigItem[] | null;
}

/** Estructura mínima de un campo BI para renderizar charts en tarjetas. */
export interface BiFieldConfigItem {
  source: string;
  field: string;
  role: 'dimension' | 'metric' | 'calculated';
  label: string;
  aggregation?: string;
  formula?: string;
  is_calculated?: boolean;
}

/** Reporte BI seleccionable para agregar como tarjeta de dashboard. */
export interface BiSelectableReport {
  id: string;
  titulo: string;
  descripcion: string;
  tipo_visualizacion: string;
  fuentes: string[];
  es_favorito: boolean;
  user_email: string;
}

export interface DashboardListItem {
  id: string;
  titulo: string;
  descripcion: string;
  es_privado: boolean;
  es_favorito: boolean;
  es_default: boolean;
  orientacion: DashboardOrientation;
  filtros_default: ReportFilter | null;
  user_email: string;
  card_count: number;
  created_at: string;
}

export interface DashboardDetail {
  id: string;
  titulo: string;
  descripcion: string;
  es_privado: boolean;
  es_favorito: boolean;
  es_default: boolean;
  orientacion: DashboardOrientation;
  filtros_default: ReportFilter | null;
  user: DashboardUser;
  cards: DashboardCard[];
  shares: DashboardShare[];
  created_at: string;
  updated_at: string;
}

export interface DashboardCreate {
  titulo: string;
  descripcion?: string;
  es_privado?: boolean;
  orientacion?: DashboardOrientation;
  filtros_default?: ReportFilter;
}

export interface DashboardCardCreate {
  card_type_code: string;
  chart_type: ChartType;
  pos_x: number;
  pos_y: number;
  width: number;
  height: number;
  filtros_config?: Record<string, unknown>;
  titulo_personalizado?: string;
  orden?: number;
  /** Solo para card_type_code='bi_report' */
  bi_report_id?: string;
}

export interface CardLayoutItem {
  id: number;
  pos_x: number;
  pos_y: number;
  width: number;
  height: number;
  orden: number;
}

export interface CardLayoutRequest {
  layout: CardLayoutItem[];
}

export interface ShareRequest {
  user_id: string;
  puede_editar?: boolean;
}

export type ChartType = 'bar' | 'line' | 'pie' | 'area' | 'waterfall' | 'gauge' | 'kpi' | 'table';
export type DashboardOrientation = 'horizontal' | 'vertical';
