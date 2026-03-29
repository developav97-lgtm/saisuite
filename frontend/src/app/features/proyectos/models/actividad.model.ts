/**
 * SaiSuite — Modelos de Actividad
 * Espeja exactamente los serializers de Django. snake_case en todo.
 */

// Valores que espera el backend (ActivityType en models.py)
export type TipoActividad = 'labor' | 'material' | 'equipment' | 'subcontract' | 'milestone';

/** Actividad en listado — campos mínimos para tabla */
export interface ActividadList {
  id: string;
  codigo: string;
  nombre: string;
  tipo: TipoActividad;
  tipo_display: string;
  unidad_medida: string;
  /** Decimal serializado como string desde DRF */
  costo_unitario_base: string;
  activo: boolean;
  created_at: string;
}

/** Actividad en detalle — todos los campos */
export interface ActividadDetail extends ActividadList {
  descripcion: string;
  saiopen_actividad_id: string | null;
  sincronizado_con_saiopen: boolean;
  updated_at: string;
}

/** Payload para crear/actualizar actividad */
export interface ActividadCreate {
  codigo?: string;
  nombre: string;
  descripcion?: string;
  tipo: TipoActividad;
  unidad_medida: string;
  costo_unitario_base: string;
  consecutivo_id?: string | null;
}

/** Actividad asignada a un proyecto */
export interface ActividadProyecto {
  id: string;
  proyecto: string;
  actividad: string;
  actividad_codigo: string;
  actividad_nombre: string;
  actividad_unidad_medida: string;
  actividad_tipo: TipoActividad;
  fase: string | null;
  fase_nombre: string | null;
  cantidad_planificada: string;
  cantidad_ejecutada: string;
  costo_unitario: string;
  presupuesto_total: string;
  porcentaje_avance: string;
  created_at: string;
}

/** Payload para asignar/actualizar actividad en proyecto */
export interface ActividadProyectoCreate {
  actividad: string;       // UUID de Actividad
  fase?: string | null;    // UUID de Fase (opcional)
  cantidad_planificada: string;
  cantidad_ejecutada?: string;
  costo_unitario?: string; // Si omite, el backend usa costo_unitario_base
  porcentaje_avance?: string;
}

export const TIPO_ACTIVIDAD_LABELS: Record<TipoActividad, string> = {
  labor:       'Mano de obra',
  material:    'Material',
  equipment:   'Equipo',
  subcontract: 'Subcontrato',
  milestone:   'Hito',
};
