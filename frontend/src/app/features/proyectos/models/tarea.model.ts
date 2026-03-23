/**
 * SaiSuite — Modelos de Tarea
 * Espeja TareaSerializer, TareaTagSerializer y DTOs de la API.
 */

export type TareaEstado =
  | 'por_hacer'
  | 'en_progreso'
  | 'en_revision'
  | 'bloqueada'
  | 'completada'
  | 'cancelada';

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

export interface Tarea {
  id: string;
  codigo: string;
  nombre: string;
  descripcion: string;

  // Relaciones
  proyecto: string;
  proyecto_detail?: TareaProyectoDetail;
  fase: string | null;
  fase_detail?: TareaFaseDetail | null;
  tarea_padre: string | null;

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

  // Campos calculados (solo lectura)
  es_vencida: boolean;
  tiene_subtareas: boolean;
  nivel_jerarquia: number;

  // Subtareas anidadas (solo en detalle)
  subtareas_detail?: Tarea[];

  // Timestamps
  created_at: string;
  updated_at: string;
}

export interface TareaCreateDTO {
  nombre: string;
  descripcion?: string;
  proyecto: string;
  fase?: string | null;
  tarea_padre?: string | null;
  cliente?: string | null;
  responsable?: string | null;
  followers?: string[];
  prioridad?: TareaPrioridad;
  tags?: string[];
  fecha_inicio?: string | null;
  fecha_fin?: string | null;
  fecha_limite?: string | null;
  estado?: Exclude<TareaEstado, 'completada' | 'cancelada'>;
  porcentaje_completado?: number;
  horas_estimadas?: number;
  es_recurrente?: boolean;
  frecuencia_recurrencia?: TareaFrecuencia | null;
}

export type TareaUpdateDTO = Partial<TareaCreateDTO>;

export interface TareaFilters {
  proyecto?: string;
  estado?: TareaEstado;
  responsable?: string;
  prioridad?: TareaPrioridad;
  prioridad_min?: number;
  tags?: string;
  fase?: string;
  search?: string;
  solo_mis_tareas?: boolean;
  vencidas?: boolean;
  sin_responsable?: boolean;
  sin_fase?: boolean;
  solo_raiz?: boolean;
  tarea_padre?: string;
  fecha_limite_desde?: string;
  fecha_limite_hasta?: string;
}

export interface FollowerResponse {
  message: string;
  followers_count: number;
}
