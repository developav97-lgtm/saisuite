/** BI Field metadata — mirrors backend BIQueryEngine field definitions. */

export type BIFieldType = 'text' | 'integer' | 'decimal' | 'date' | 'boolean';
export type BIFieldRole = 'dimension' | 'metric';
export type BIAggregation = 'SUM' | 'AVG' | 'COUNT' | 'MIN' | 'MAX';

/** A single field definition returned by the /meta/fields/ endpoint. */
export interface BIFieldDef {
  field: string;
  label: string;
  type: BIFieldType;
  role: BIFieldRole;
}

/** Fields grouped by category as returned by the backend. */
export interface BIFieldCategory {
  category: string;
  fields: BIFieldDef[];
}

export type BIFieldFormat = 'string' | 'number' | 'currency' | 'date';

/** A field selected by the user for a report, with config. */
export interface BIFieldConfig {
  source: string;
  field: string;
  role: BIFieldRole | 'column';
  aggregation?: BIAggregation;
  label: string;
  format?: BIFieldFormat;
  /** Campo calculado: true si es el resultado de una fórmula. */
  is_calculated?: boolean;
  /** Fórmula aritmética usando nombres de campos métricos, ej: "debito - credito". */
  formula?: string;
}

/** Filter definition from /meta/filters/ endpoint.
 *  Backend returns: { key, label, type, field } where:
 *  - key:  semantic identifier used in filtros payload (e.g. 'fecha_desde')
 *  - field: ORM lookup — backend-only (e.g. 'fecha__gte')
 */
export interface BIFilterDef {
  key: string;
  field: string;
  label: string;
  type: 'date' | 'multi_select' | 'autocomplete_multi' | 'select' | 'text' | 'boolean' | 'decimal';
}

/** Sort config for a report. */
export interface BISortConfig {
  field: string;
  direction: 'asc' | 'desc';
}
