/** Report filter and card data models — mirrors backend report endpoints. */

export interface ReportFilter {
  fecha_desde: string | null;
  fecha_hasta: string | null;
  tercero_id?: string | null;
  proyecto_codigo?: string | null;
  departamento_codigo?: string | null;
  periodo?: string | null;
  comparar_periodo?: boolean;
}

export interface CardDataRequest {
  card_type_code: string;
  filtros: ReportFilter;
}

export interface DatasetItem {
  label: string;
  data: number[];
}

export interface CardDataResponse {
  labels: string[];
  datasets: DatasetItem[];
  summary: Record<string, number | string>;
}

/** Autocomplete filter options from backend. */
export interface FilterTercero {
  id: string;
  nombre: string;
}

export interface FilterProyecto {
  codigo: string;
  nombre: string;
}

export interface FilterDepartamento {
  codigo: string;
  nombre: string;
}

export interface FilterPeriodo {
  periodo: string;
  label: string;
}
