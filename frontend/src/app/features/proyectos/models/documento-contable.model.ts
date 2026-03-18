/**
 * SaiSuite — Modelos de DocumentoContable
 * Espeja DocumentoContableListSerializer y DocumentoContableDetailSerializer.
 * Solo lectura — los documentos los crea el agente Go/Saiopen.
 */

export type TipoDocumento =
  | 'factura_compra'
  | 'factura_venta'
  | 'nota_credito'
  | 'nota_debito'
  | 'anticipo'
  | 'legalizacion'
  | 'recibo_caja'
  | 'otro';

/** Documento en listado — campos mínimos */
export interface DocumentoContableList {
  id: string;
  tipo_documento: TipoDocumento;
  tipo_documento_display: string;
  numero_documento: string;
  fecha_documento: string;
  tercero_nombre: string;
  /** NUMERIC(15,2) serializado como string */
  valor_neto: string;
  sincronizado_desde_saiopen: string;
}

/** Documento en detalle — todos los campos */
export interface DocumentoContableDetail extends DocumentoContableList {
  proyecto: string;
  fase: string | null;
  saiopen_doc_id: string;
  tercero_id: string;
  valor_bruto: string;
  valor_descuento: string;
  observaciones: string;
}

export const TIPO_DOCUMENTO_LABELS: Record<TipoDocumento, string> = {
  factura_compra: 'Factura de compra',
  factura_venta:  'Factura de venta',
  nota_credito:   'Nota crédito',
  nota_debito:    'Nota débito',
  anticipo:       'Anticipo',
  legalizacion:   'Legalización',
  recibo_caja:    'Recibo de caja',
  otro:           'Otro',
};
