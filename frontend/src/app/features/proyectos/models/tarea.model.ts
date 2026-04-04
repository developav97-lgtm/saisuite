/**
 * SaiSuite — Modelos de Tarea
 * Espeja TareaSerializer, TareaTagSerializer y DTOs de la API.
 * DEC-021: Tarea pertenece a Fase (proyecto es read-only derivado).
 * DEC-022: actividad_saiopen determina modo_medicion (solo_estados|timesheet|cantidad).
 */
import type { ModoMedicion } from './actividad-saiopen.model';

export type TareaEstado =
  | 'todo'
  | 'in_progress'
  | 'in_review'
  | 'blocked'
  | 'completed'
  | 'cancelled';

export type TareaPrioridad = 1 | 2 | 3 | 4; // Baja, Normal, Alta, Urgente

export type TareaFrecuencia = 'diaria' | 'semanal' | 'mensual';

export type TareaTagColor =
  | 'red'
  | 'orange'
  | 'yellow'
  | 'green'
  | 'blue'
  | 'purple'
  | 'pink'
  | 'gray';

export type TipoDependencia = 'FS' | 'SS' | 'FF';

export interface TareaDependenciaTareaDetail {
  id: string;
  nombre: string;
  codigo: string;
}

export interface TareaDependencia {
  id: string;
  tarea_predecesora: string;
  tarea_predecesora_detail: TareaDependenciaTareaDetail;
  tarea_sucesora: string;
  tarea_sucesora_detail: TareaDependenciaTareaDetail;
  tipo_dependencia: TipoDependencia;
  retraso_dias: number;
}

export interface TareaTag {
  id: string;
  company: string;
  nombre: string;
  color: TareaTagColor;
  created_at: string;
  updated_at: string;
}

export interface TareaProyectoDetail {
  id: string;
  nombre: string;
  codigo: string;
}

export interface TareaFaseDetail {
  id: string;
  nombre: string;
  orden: number;
}

export interface TareaUserDetail {
  id: string;
  nombre: string;
  email: string;
}

export interface TareaActividadSaiopenDetail {
  id: string;
  codigo: string;
  nombre: string;
  unidad_medida: ModoMedicion;
}

export interface TareaActividadProyectoDetail {
  id: string;
  actividad_id: string;
  actividad_codigo: string;
  actividad_nombre: string;
  actividad_unidad_medida: string;
}

export interface Tarea {
  id: string;
  codigo: string;
  nombre: string;
  descripcion: string;

  // Relaciones (DEC-021: proyecto es read-only derivado de fase)
  proyecto: string;
  proyecto_detail?: TareaProyectoDetail;
  fase: string;                        // obligatoria
  fase_detail?: TareaFaseDetail | null;
  tarea_padre: string | null;

  // Actividad Saiopen (DEC-022)
  actividad_saiopen: string | null;
  actividad_saiopen_detail?: TareaActividadSaiopenDetail | null;
  // Actividad del Proyecto (catálogo interno)
  actividad_proyecto: string | null;
  actividad_proyecto_detail?: TareaActividadProyectoDetail | null;
  cantidad_objetivo: number;
  cantidad_registrada: number;
  modo_medicion: ModoMedicion;

  // Cliente opcional (DEC-019)
  cliente: string | null;
  cliente_detail?: {
    id: string;
    nombre: string;
    numero_identificacion: string;
  } | null;

  // Asignación
  responsable: string | null;
  responsable_detail?: TareaUserDetail | null;
  followers: string[];
  followers_detail?: TareaUserDetail[];

  // Clasificación
  prioridad: TareaPrioridad;
  tags: string[];
  tags_detail?: TareaTag[];

  // Fechas (ISO date)
  fecha_inicio: string | null;
  fecha_fin: string | null;
  fecha_limite: string | null;

  // Estado y progreso
  estado: TareaEstado;
  porcentaje_completado: number;

  // Timesheet
  horas_estimadas: number;
  horas_registradas: number;

  // Recurrencia
  es_recurrente: boolean;
  frecuencia_recurrencia: TareaFrecuencia | null;
  proxima_generacion: string | null;

  // Dependencias (solo en detalle)
  predecesoras_detail?: TareaDependencia[];
  sucesoras_detail?: TareaDependencia[];

  // Campos calculados (solo lectura)
  es_vencida: boolean;
  tiene_subtareas: boolean;
  nivel_jerarquia: number;
  progreso_porcentaje: number;
  es_camino_critico: boolean;

  // Subtareas anidadas (solo en detalle)
  subtareas_detail?: Tarea[];

  // Timestamps
  created_at: string;
  updated_at: string;
}

export interface TareaCreateDTO {
  nombre: string;
  descripcion?: string;
  fase: string;                        // obligatoria (DEC-021)
  tarea_padre?: string | null;
  actividad_saiopen?: string | null;   // DEC-022
  actividad_proyecto?: string | null;  // catálogo interno
  cantidad_objetivo?: number;
  cantidad_registrada?: number;
  cliente?: string | null;
  responsable?: string | null;
  followers?: string[];
  prioridad?: TareaPrioridad;
  tags?: string[];
  fecha_inicio?: string | null;
  fecha_fin?: string | null;
  fecha_limite?: string | null;
  estado?: Exclude<TareaEstado, 'completed' | 'cancelled'>;
  porcentaje_completado?: number;
  horas_estimadas?: number;
  es_recurrente?: boolean;
  frecuencia_recurrencia?: TareaFrecuencia | null;
}

export type TareaUpdateDTO = Partial<TareaCreateDTO>;

export interface TareaFilters {
  proyecto?: string;
  fase?: string;
  actividad_saiopen?: string;          // DEC-022
  estado?: TareaEstado;
  responsable?: string;
  prioridad?: TareaPrioridad;
  prioridad_min?: number;
  tags?: string;
  search?: string;
  solo_mis_tareas?: boolean;
  vencidas?: boolean;
  sin_responsable?: boolean;
  solo_raiz?: boolean;
  tarea_padre?: string;
  fecha_limite_desde?: string;
  fecha_limite_hasta?: string;
}

export interface FollowerResponse {
  message: string;
  followers_count: number;
}

/** Formato de tarea para Frappe Gantt (espeja el endpoint /gantt-data/) */
export interface GanttTask {
  id: string;
  name: string;
  start: string;        // ISO date string "YYYY-MM-DD"
  end: string;          // ISO date string "YYYY-MM-DD"
  progress: number;     // 0-100
  custom_class: string; // ej. "estado-in_progress"
  dependencies: string; // comma-separated predecessor IDs
}
