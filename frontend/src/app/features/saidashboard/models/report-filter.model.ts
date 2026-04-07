/** Report filter and card data models — mirrors backend report endpoints. */

export interface ReportFilter {
  fecha_desde: string | null;
  fecha_hasta: string | null;
  tercero_id?: string | null;
  proyecto_codigo?: string | null;
  departamento_codigo?: string | null;
  periodo?: string | null;
  comparar_periodo?: boolean;
  /** Si true, el backend retorna serie mensual (12 barras) en lugar de total */
  agrupar_por_mes?: boolean;
  /** Año para la serie mensual (ej: "2025"). Requerido cuando agrupar_por_mes=true */
  anio?: string | null;
}

export interface CardDataRequest {
  card_type_code: string;
  filtros: ReportFilter;
  /** Configuracion especifica para tarjetas personalizadas (CUSTOM_RANGO_CUENTAS, DISTRIBUCION_POR_PROYECTO) */
  card_config?: Record<string, unknown>;
}

/** Tipos de nivel de cuenta PUC para tarjetas personalizadas */
export type NivelCuenta = 'titulo' | 'grupo' | 'cuenta' | 'subcuenta' | 'auxiliar';

/** Direccion del movimiento para calcular el saldo */
export type DireccionMovimiento = 'debito' | 'credito' | 'neto';

/** Configuracion de una tarjeta personalizada de rango de cuentas */
export interface CustomRangoCuentasConfig {
  nivel_cuenta: NivelCuenta;
  codigo_desde: number;
  codigo_hasta: number;
  direccion: DireccionMovimiento;
  titulo_personalizado: string;
  agrupar_por_mes: boolean;
  /** Si true, muestra una barra por cuenta individual en lugar del total del rango */
  agrupar_por_cuenta: boolean;
  top_n?: number | null;
  /** IDs de terceros para filtrar (opcional, multi-select) */
  tercero_ids?: string[];
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
