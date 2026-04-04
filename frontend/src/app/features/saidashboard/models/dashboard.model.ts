/** Dashboard module models — mirrors backend DRF serializers exactly. */

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
  id: string;
  card_type_code: string;
  chart_type: ChartType;
  pos_x: number;
  pos_y: number;
  width: number;
  height: number;
  filtros_config: Record<string, unknown>;
  titulo_personalizado: string;
  orden: number;
}

export interface DashboardListItem {
  id: string;
  titulo: string;
  descripcion: string;
  es_privado: boolean;
  es_favorito: boolean;
  es_default: boolean;
  orientacion: DashboardOrientation;
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
  user: DashboardUser;
  cards: DashboardCard[];
  shares: DashboardShare[];
  created_at: string;
}

export interface DashboardCreate {
  titulo: string;
  descripcion?: string;
  es_privado?: boolean;
  orientacion?: DashboardOrientation;
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
}

export interface CardLayoutItem {
  id: string;
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

export type ChartType = 'bar' | 'line' | 'pie' | 'area' | 'waterfall' | 'gauge' | 'kpi';
export type DashboardOrientation = 'horizontal' | 'vertical';
