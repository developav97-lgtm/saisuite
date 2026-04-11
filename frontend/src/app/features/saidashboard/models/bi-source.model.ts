/** BI Source metadata — mirrors backend SOURCE_FIELDS / SOURCE_FILTERS shapes. */

export type BISourceCode = 'gl' | 'facturacion' | 'facturacion_detalle' | 'cartera' | 'inventario';

export interface BISource {
  code: BISourceCode;
  label: string;
  description: string;
  icon: string;
}

export const BI_SOURCES: BISource[] = [
  { code: 'gl',                   label: 'Contabilidad (GL)', description: 'Asientos contables, balances, estados financieros', icon: 'account_balance' },
  { code: 'facturacion',          label: 'Facturación',       description: 'Ventas, compras, notas crédito, devoluciones',      icon: 'receipt_long' },
  { code: 'facturacion_detalle',  label: 'Facturación Detalle', description: 'Líneas de factura: productos, cantidades, márgenes', icon: 'receipt_long' },
  { code: 'cartera',              label: 'Cartera (CxC/CxP)', description: 'Cuentas por cobrar, cuentas por pagar, aging',      icon: 'payments' },
  { code: 'inventario',           label: 'Inventario',        description: 'Entradas, salidas, saldos, rotación',               icon: 'inventory_2' },
];
