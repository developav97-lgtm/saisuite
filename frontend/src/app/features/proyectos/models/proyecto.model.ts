/**
 * SaiSuite — Modelos de Proyecto
 * Espeja exactamente los serializers de Django. snake_case en todo (DEC-010).
 */

export type TipoProyecto =
  | 'obra_civil'
  | 'consultoria'
  | 'manufactura'
  | 'servicios'
  | 'licitacion_publica'
  | 'otro';

export type EstadoProyecto =
  | 'borrador'
  | 'planificado'
  | 'en_ejecucion'
  | 'suspendido'
  | 'cerrado'
  | 'cancelado';

export interface UserSummary {
  id: string;
  email: string;
  full_name: string;
}

/** Proyecto en listado — campos mínimos */
export interface ProyectoList {
  id: string;
  codigo: string;
  nombre: string;
  tipo: TipoProyecto;
  estado: EstadoProyecto;
  cliente_nombre: string;
  gerente: UserSummary;
  fecha_inicio_planificada: string;
  fecha_fin_planificada: string;
  /** Decimal serializado como string desde DRF */
  presupuesto_total: string;
  /** Porcentaje de avance físico (0-100). Auto-calculado desde fases. */
  porcentaje_avance: string;
  activo: boolean;
  created_at: string;
}

/** Proyecto en detalle — todos los campos */
export interface ProyectoDetail extends ProyectoList {
  cliente_id: string;
  coordinador: UserSummary | null;
  fecha_inicio_real: string | null;
  fecha_fin_real: string | null;
  porcentaje_administracion: string;
  porcentaje_imprevistos: string;
  porcentaje_utilidad: string;
  saiopen_proyecto_id: string | null;
  sincronizado_con_saiopen: boolean;
  ultima_sincronizacion: string | null;
  fases_count: number;
  presupuesto_fases_total: string;
  updated_at: string;
}

/** Payload para crear/actualizar proyecto */
export interface ProyectoCreate {
  codigo?: string;
  nombre: string;
  tipo: TipoProyecto;
  cliente_id: string;
  cliente_nombre: string;
  gerente: string; // UUID
  coordinador?: string | null; // UUID
  fecha_inicio_planificada: string;
  fecha_fin_planificada: string;
  fecha_inicio_real?: string | null;
  fecha_fin_real?: string | null;
  presupuesto_total: string;
  porcentaje_administracion?: string;
  porcentaje_imprevistos?: string;
  porcentaje_utilidad?: string;
  consecutivo_id?: string | null;
}

/** Respuesta del endpoint estado-financiero */
export interface EstadoFinanciero {
  presupuesto_total: string;
  presupuesto_costos: string;
  precio_venta_aiu: string;
  costo_ejecutado: string;
  porcentaje_avance_fisico: string;
  porcentaje_avance_financiero: string;
  desviacion_presupuesto: string;
  desglose_presupuesto: {
    mano_obra: string;
    materiales: string;
    subcontratos: string;
    equipos: string;
    otros: string;
  };
  aiu: {
    porcentaje_administracion: string;
    porcentaje_imprevistos: string;
    porcentaje_utilidad: string;
    valor_aiu: string;
  };
}

/** Labels para los estados del proyecto */
export const ESTADO_LABELS: Record<EstadoProyecto, string> = {
  borrador: 'Borrador',
  planificado: 'Planificado',
  en_ejecucion: 'En ejecución',
  suspendido: 'Suspendido',
  cerrado: 'Cerrado',
  cancelado: 'Cancelado',
};

/** Severidades PrimeNG p-tag por estado */
export const ESTADO_SEVERITY: Record<EstadoProyecto, 'info' | 'success' | 'warn' | 'danger' | 'secondary' | 'contrast'> = {
  borrador: 'secondary',
  planificado: 'info',
  en_ejecucion: 'success',
  suspendido: 'warn',
  cerrado: 'contrast',
  cancelado: 'danger',
};

/** Labels para tipos de proyecto */
export const TIPO_LABELS: Record<TipoProyecto, string> = {
  obra_civil: 'Obra civil',
  consultoria: 'Consultoría',
  manufactura: 'Manufactura',
  servicios: 'Servicios',
  licitacion_publica: 'Licitación pública',
  otro: 'Otro',
};
