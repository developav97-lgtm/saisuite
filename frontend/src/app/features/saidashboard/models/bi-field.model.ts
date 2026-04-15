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

export type BIFieldFormat = 'string' | 'number' | 'currency' | 'date' | 'boolean';

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

// ── V2 Filter types ───────────────────────────────────────────────────────────

/** Operadores disponibles en el FilterTranslator v2 del backend. */
export type BIFilterOperator =
  | 'eq'         // igual a
  | 'neq'        // diferente de
  | 'contains'   // contiene (text)
  | 'starts_with'// empieza con (text)
  | 'ends_with'  // termina con (text)
  | 'gt'         // mayor que
  | 'gte'        // mayor o igual
  | 'lt'         // menor que
  | 'lte'        // menor o igual
  | 'between'    // entre (rango)
  | 'in'         // en lista
  | 'is_true'    // es verdadero (boolean)
  | 'is_false';  // es falso (boolean)

/** Un filtro en formato v2 — estructura enviada al backend. */
export interface BIFilterV2 {
  source: string;
  field: string;
  operator: BIFilterOperator;
  value: unknown;
}

/** Operadores disponibles según el tipo de campo. */
export const OPERATORS_BY_TYPE: Record<BIFieldType, { value: BIFilterOperator; label: string }[]> = {
  text: [
    { value: 'eq',          label: 'Igual a' },
    { value: 'neq',         label: 'Diferente de' },
    { value: 'contains',    label: 'Contiene' },
    { value: 'starts_with', label: 'Empieza con' },
    { value: 'ends_with',   label: 'Termina con' },
    { value: 'in',          label: 'En lista' },
  ],
  integer: [
    { value: 'eq',      label: 'Igual a' },
    { value: 'neq',     label: 'Diferente de' },
    { value: 'gt',      label: 'Mayor que' },
    { value: 'gte',     label: 'Mayor o igual' },
    { value: 'lt',      label: 'Menor que' },
    { value: 'lte',     label: 'Menor o igual' },
    { value: 'between', label: 'Entre' },
    { value: 'in',      label: 'En lista' },
  ],
  decimal: [
    { value: 'eq',      label: 'Igual a' },
    { value: 'neq',     label: 'Diferente de' },
    { value: 'gt',      label: 'Mayor que' },
    { value: 'gte',     label: 'Mayor o igual' },
    { value: 'lt',      label: 'Menor que' },
    { value: 'lte',     label: 'Menor o igual' },
    { value: 'between', label: 'Entre' },
    { value: 'in',      label: 'En lista' },
  ],
  date: [
    { value: 'eq',      label: 'Igual a' },
    { value: 'gt',      label: 'Después de' },
    { value: 'gte',     label: 'Desde' },
    { value: 'lt',      label: 'Antes de' },
    { value: 'lte',     label: 'Hasta' },
    { value: 'between', label: 'Entre' },
  ],
  boolean: [
    { value: 'is_true',  label: 'Es verdadero' },
    { value: 'is_false', label: 'Es falso' },
  ],
};

/** Metadato de una relación JOIN entre fuentes, tal como retorna /meta/joins/. */
export interface BIJoinInfo {
  source_a: string;
  source_b: string;
  description: string;
  type: 'fk' | 'subquery';
}

/** Flat field option for field selector (source + field merged). */
export interface BIFieldOption {
  source: string;
  sourceLabel: string;
  field: string;
  label: string;
  type: BIFieldType;
  role: BIFieldRole;
}
