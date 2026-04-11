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

/** A field selected by the user for a report, with config. */
export interface BIFieldConfig {
  source: string;
  field: string;
  role: BIFieldRole | 'column';
  aggregation?: BIAggregation;
  label: string;
}

/** Filter definition from /meta/filters/ endpoint. */
export interface BIFilterDef {
  field: string;
  label: string;
  type: 'date_range' | 'multi_select' | 'text' | 'boolean' | 'select';
}

/** Sort config for a report. */
export interface BISortConfig {
  field: string;
  direction: 'asc' | 'desc';
}
