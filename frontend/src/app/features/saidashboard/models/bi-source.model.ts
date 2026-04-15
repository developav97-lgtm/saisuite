/** BI Source metadata — mirrors backend SOURCE_FIELDS / SOURCE_FILTERS shapes. */

export type BISourceCode =
  // v1 — Fuentes transaccionales
  | 'gl'
  | 'facturacion'
  | 'facturacion_detalle'
  | 'cartera'
  | 'inventario'
  // v2 — Maestros y dimensiones
  | 'terceros_saiopen'
  | 'productos'
  | 'cuentas_contables'
  | 'proyectos_saiopen'
  | 'actividades_saiopen'
  | 'departamentos'
  | 'centros_costo'
  | 'tipos_documento'
  | 'direcciones_envio'
  | 'impuestos';

export type BISourceGroup = 'transaccional' | 'maestro';

export interface BISource {
  code: BISourceCode;
  label: string;
  description: string;
  icon: string;
  group: BISourceGroup;
}

export const BI_SOURCES: BISource[] = [
  // ── Transaccionales ───────────────────────────────────────────
  {
    code: 'gl',
    label: 'Contabilidad',
    description: 'Asientos contables, balances, estados financieros',
    icon: 'account_balance',
    group: 'transaccional',
  },
  {
    code: 'facturacion',
    label: 'Facturación',
    description: 'Ventas, compras, notas crédito, devoluciones',
    icon: 'receipt_long',
    group: 'transaccional',
  },
  {
    code: 'facturacion_detalle',
    label: 'Facturación Detalle',
    description: 'Líneas de factura: productos, cantidades, márgenes',
    icon: 'receipt_long',
    group: 'transaccional',
  },
  {
    code: 'cartera',
    label: 'Cartera (CxC/CxP)',
    description: 'Cuentas por cobrar, cuentas por pagar, aging',
    icon: 'payments',
    group: 'transaccional',
  },
  {
    code: 'inventario',
    label: 'Inventario',
    description: 'Entradas, salidas, saldos, rotación',
    icon: 'inventory_2',
    group: 'transaccional',
  },
  // ── Maestros y dimensiones ─────────────────────────────────────
  {
    code: 'terceros_saiopen',
    label: 'Terceros',
    description: 'Clientes, proveedores y empleados de Saiopen',
    icon: 'people',
    group: 'maestro',
  },
  {
    code: 'productos',
    label: 'Productos',
    description: 'Catálogo de productos sincronizado de Saiopen',
    icon: 'inventory',
    group: 'maestro',
  },
  {
    code: 'cuentas_contables',
    label: 'Cuentas Contables',
    description: 'Plan de cuentas del PUC',
    icon: 'account_tree',
    group: 'maestro',
  },
  {
    code: 'proyectos_saiopen',
    label: 'Proyectos',
    description: 'Proyectos sincronizados de Saiopen',
    icon: 'folder',
    group: 'maestro',
  },
  {
    code: 'actividades_saiopen',
    label: 'Actividades',
    description: 'Actividades económicas de Saiopen',
    icon: 'category',
    group: 'maestro',
  },
  {
    code: 'departamentos',
    label: 'Departamentos',
    description: 'Departamentos contables (tipo DP)',
    icon: 'corporate_fare',
    group: 'maestro',
  },
  {
    code: 'centros_costo',
    label: 'Centros de Costo',
    description: 'Centros de costo contables (tipo CC)',
    icon: 'hub',
    group: 'maestro',
  },
  {
    code: 'tipos_documento',
    label: 'Tipos de Documento',
    description: 'Tipos de transacción Saiopen (TIPDOC)',
    icon: 'description',
    group: 'maestro',
  },
  {
    code: 'direcciones_envio',
    label: 'Direcciones de Envío',
    description: 'Sucursales de clientes para despacho (SHIPTO)',
    icon: 'local_shipping',
    group: 'maestro',
  },
  {
    code: 'impuestos',
    label: 'Impuestos',
    description: 'Configuración de impuestos (IVA, etc.)',
    icon: 'percent',
    group: 'maestro',
  },
];

export const BI_SOURCE_GROUPS: { group: BISourceGroup; label: string }[] = [
  { group: 'transaccional', label: 'Fuentes Transaccionales' },
  { group: 'maestro', label: 'Maestros y Dimensiones' },
];

/** Busca el label de una fuente por su código. */
export function getSourceLabel(code: string): string {
  return BI_SOURCES.find(s => s.code === code)?.label ?? code;
}
