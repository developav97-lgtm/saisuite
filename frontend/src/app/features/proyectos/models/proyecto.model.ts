/**
 * SaiSuite — Modelos de Proyecto
 * Espeja exactamente los serializers de Django. snake_case en todo (DEC-010).
 */

export type TipoProyecto =
  | 'civil_works'
  | 'consulting'
  | 'manufacturing'
  | 'services'
  | 'public_tender'
  | 'other';

export type EstadoProyecto =
  | 'draft'
  | 'planned'
  | 'in_progress'
  | 'suspended'
  | 'closed'
  | 'cancelled';

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
  /** NIT/cédula real del cliente (resuelve UUID legacy si aplica) */
  cliente_nit: string;
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
  draft:       'Borrador',
  planned:     'Planificado',
  in_progress: 'En ejecución',
  suspended:   'Suspendido',
  closed:      'Cerrado',
  cancelled:   'Cancelado',
};

/** Severidades Material por estado */
export const ESTADO_SEVERITY: Record<EstadoProyecto, 'info' | 'success' | 'warn' | 'danger' | 'secondary' | 'contrast'> = {
  draft:       'secondary',
  planned:     'info',
  in_progress: 'success',
  suspended:   'warn',
  closed:      'contrast',
  cancelled:   'danger',
};

/** Labels para tipos de proyecto */
export const TIPO_LABELS: Record<TipoProyecto, string> = {
  civil_works:    'Obra civil',
  consulting:     'Consultoría',
  manufacturing:  'Manufactura',
  services:       'Servicios',
  public_tender:  'Licitación pública',
  other:          'Otro',
};

// ── Plantillas de Proyecto ────────────────────────────────────────────────────

export interface PlantillaTarea {
  id: string;
  nombre: string;
  descripcion: string;
  orden: number;
  duracion_dias: number;
  prioridad: number;
  actividad_saiopen_id: string | null;
  /** unidad_medida de la actividad vinculada, null si no hay actividad */
  unidad_medida: string | null;
}

export interface PlantillaFase {
  id: string;
  nombre: string;
  descripcion: string;
  orden: number;
  porcentaje_duracion: string;
  tareas_count: number;
  tareas: PlantillaTarea[];
}

export interface PlantillaProyecto {
  id: string;
  nombre: string;
  descripcion: string;
  tipo: TipoProyecto;
  tipo_display: string;
  icono: string;
  duracion_estimada: number;
  is_active: boolean;
  fases_count: number;
  fases: PlantillaFase[];
}

export interface PlantillaTareaCreate {
  nombre: string;
  descripcion?: string;
  orden: number;
  duracion_dias: number;
  actividad_saiopen_id?: string | null;
}

export interface PlantillaFaseCreate {
  nombre: string;
  descripcion?: string;
  orden: number;
  porcentaje_duracion: number;
  tareas: PlantillaTareaCreate[];
}

export interface PlantillaProyectoCreate {
  nombre: string;
  descripcion?: string;
  tipo: TipoProyecto;
  icono?: string;
  duracion_estimada: number;
  fases: PlantillaFaseCreate[];
}

// Kept for backwards compatibility — no longer used in templates
export const PLANTILLA_CATEGORIA_LABELS: Record<string, string> = {
  construccion:   'Construcción',
  software:       'Desarrollo de Software',
  evento:         'Evento',
  marketing:      'Marketing',
  product_launch: 'Lanzamiento de Producto',
};

export interface CreateFromTemplateRequest {
  template_id: string;
  nombre: string;
  descripcion?: string;
  /** Fecha ISO YYYY-MM-DD */
  planned_start: string;
}

// ── Importación Excel ─────────────────────────────────────────────────────────

export interface ImportExcelResult {
  proyecto: ProyectoDetail;
  stats: {
    fases: number;
    tareas: number;
    dependencias: number;
  };
  warnings: string[];
}
