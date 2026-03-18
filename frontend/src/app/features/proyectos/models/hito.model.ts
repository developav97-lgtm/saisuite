/**
 * SaiSuite — Modelos de Hito
 * Espeja HitoSerializer, HitoCreateSerializer y GenerarFacturaSerializer.
 */

export interface Hito {
  id: string;
  proyecto: string;
  fase: string | null;
  fase_nombre: string | null;
  nombre: string;
  descripcion: string;
  /** NUMERIC(15,2) como string */
  porcentaje_proyecto: string;
  valor_facturar: string;
  facturable: boolean;
  facturado: boolean;
  documento_factura: string | null;
  fecha_facturacion: string | null;
  created_at: string;
}

export interface HitoCreate {
  nombre: string;
  descripcion?: string;
  fase?: string | null;
  porcentaje_proyecto: string;
  valor_facturar: string;
  facturable: boolean;
}
