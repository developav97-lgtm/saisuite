/**
 * SaiSuite — Modelos de DocumentoContable
 * Espeja DocumentoContableListSerializer y DocumentoContableDetailSerializer.
 * Solo lectura — los documentos los sincroniza sync_from_gl() desde MovimientoContable.
 */

/** Enum de tipos de documento — espeja DocumentType en proyectos/models.py */
export type TipoDocumento =
  | 'sales_invoice'
  | 'purchase_invoice'
  | 'purchase_order'
  | 'cash_receipt'
  | 'expense_voucher'
  | 'payroll'
  | 'advance'
  | 'work_certificate';

/** Documento en listado — campos mínimos */
export interface DocumentoContableList {
  id: string;
  tipo_documento: TipoDocumento;
  tipo_documento_display: string;
  numero_documento: string;
  fecha_documento: string;
  tercero_nombre: string;
  /** NUMERIC(15,2) serializado como string — max(Σdebito, Σcredito) */
  valor_bruto: string;
  /** NUMERIC(15,2) serializado como string — abs(Σdebito - Σcredito), 0 en asientos balanceados */
  valor_neto: string;
  sincronizado_desde_saiopen: string;
  /** Claves GL — para mostrar badge TIPDOC y filtrar */
  tipo_gl: string;
  batch_gl: number | null;
  invc_gl: string;
  tipdoc_descripcion: string;
  tipdoc_sigla: string;
}

/** Documento en detalle — todos los campos */
export interface DocumentoContableDetail extends DocumentoContableList {
  proyecto: string;
  fase: string | null;
  saiopen_doc_id: string;
  tercero_id: string;
  valor_descuento: string;
  observaciones: string;
}

/** Resultado de sincronización desde GL */
export interface SyncDocumentosResult {
  created: number;
  updated: number;
  skipped: number;
  errors: string[];
}

/** Línea de asiento contable — viene de MovimientoContable */
export interface LineaContable {
  conteo: number;
  auxiliar: string;
  auxiliar_nombre: string;
  titulo_nombre: string;
  grupo_nombre: string;
  cuenta_nombre: string;
  subcuenta_nombre: string;
  tercero_id: string;
  tercero_nombre: string;
  debito: string;
  credito: string;
  descripcion: string;
  fecha: string;
  periodo: string;
}

export const TIPO_DOCUMENTO_LABELS: Record<TipoDocumento, string> = {
  sales_invoice:    'Factura de venta',
  purchase_invoice: 'Factura de compra',
  purchase_order:   'Orden de compra',
  cash_receipt:     'Recibo de caja',
  expense_voucher:  'Comprobante de egreso',
  payroll:          'Nómina',
  advance:          'Anticipo',
  work_certificate: 'Acta de obra',
};
