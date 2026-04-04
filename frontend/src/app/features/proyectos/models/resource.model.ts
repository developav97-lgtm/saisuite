/**
 * SaiSuite — Modelos de Resource Management (Feature #4)
 * Espeja ResourceAssignmentListSerializer, ResourceCapacitySerializer,
 * ResourceAvailabilitySerializer, WorkloadSummarySerializer y
 * TeamAvailabilityUserSerializer.
 */

// ── AvailabilityType choices ────────────────────────────────────────────────

export type AvailabilityType =
  | 'vacation'
  | 'sick_leave'
  | 'holiday'
  | 'training'
  | 'other';

export const AVAILABILITY_TYPE_LABELS: Record<AvailabilityType, string> = {
  vacation:   'Vacaciones',
  sick_leave: 'Incapacidad',
  holiday:    'Festivo',
  training:   'Capacitación',
  other:      'Otro',
};

// ── ResourceAssignment ───────────────────────────────────────────────────────

export interface ResourceAssignmentList {
  id: string;
  tarea: string;
  usuario: string;
  usuario_nombre: string;
  usuario_email: string;
  porcentaje_asignacion: string;
  fecha_inicio: string;
  fecha_fin: string;
  notas: string;
  activo: boolean;
  created_at: string;
}

export interface ResourceAssignmentDetail {
  id: string;
  tarea: string;
  tarea_detail: {
    id: string;
    codigo: string;
    nombre: string;
    estado: string;
  };
  usuario: string;
  usuario_detail: {
    id: string;
    email: string;
    nombre: string;
  };
  porcentaje_asignacion: string;
  fecha_inicio: string;
  fecha_fin: string;
  notas: string;
  activo: boolean;
  created_at: string;
  updated_at: string;
}

export interface ResourceAssignmentCreate {
  usuario_id: string;
  porcentaje_asignacion: string;
  fecha_inicio: string;
  fecha_fin: string;
  notas?: string;
}

// ── ResourceCapacity ─────────────────────────────────────────────────────────

export interface ResourceCapacity {
  id: string;
  usuario: string;
  usuario_nombre: string;
  horas_por_semana: string;
  fecha_inicio: string;
  fecha_fin: string | null;
  activo: boolean;
  created_at: string;
  updated_at: string;
}

export interface ResourceCapacityCreate {
  usuario: string;
  horas_por_semana: string;
  fecha_inicio: string;
  fecha_fin?: string | null;
}

// ── ResourceAvailability ──────────────────────────────────────────────────────

export interface ResourceAvailability {
  id: string;
  usuario: string;
  usuario_nombre: string;
  tipo: AvailabilityType;
  tipo_display: string;
  fecha_inicio: string;
  fecha_fin: string;
  descripcion: string;
  aprobado: boolean;
  aprobado_por: string | null;
  aprobado_por_nombre: string | null;
  fecha_aprobacion: string | null;
  activo: boolean;
  created_at: string;
  updated_at: string;
}

export interface ResourceAvailabilityCreate {
  usuario_id: string;
  tipo: AvailabilityType;
  fecha_inicio: string;
  fecha_fin: string;
  descripcion?: string;
}

// ── Overallocation ────────────────────────────────────────────────────────────

export interface OverallocationConflict {
  fecha: string;
  porcentaje_total: string;
  asignaciones: {
    id: string;
    tarea_id: string;
    codigo: string;
    nombre: string;
    porcentaje: string;
  }[];
}

export interface OverallocationResult {
  conflictos: OverallocationConflict[];
  total: number;
}

// ── UserWorkload ──────────────────────────────────────────────────────────────

export interface UserWorkload {
  usuario_id: string;
  periodo_inicio: string;
  periodo_fin: string;
  horas_capacidad: string;
  horas_asignadas: string;
  horas_registradas: string;
  porcentaje_utilizacion: string;
  conflictos: { fecha: string; porcentaje_total: string }[];
}

// ── TeamAvailabilityTimeline ───────────────────────────────────────────────────

export interface TeamAvailabilityUser {
  usuario_id: string;
  usuario_nombre: string;
  usuario_email: string;
  asignaciones: {
    id: string;
    tarea_id: string;
    tarea_codigo: string;
    tarea_nombre: string;
    tarea_estado: string;
    porcentaje_asignacion: string | null;
    fecha_inicio: string;
    fecha_fin: string;
  }[];
  ausencias: {
    id: string;
    tipo: AvailabilityType;
    tipo_display: string;
    fecha_inicio: string;
    fecha_fin: string;
    descripcion: string;
  }[];
}

// ── UserCalendar ──────────────────────────────────────────────────────────────

export interface UserCalendarEvent {
  id: string;
  tarea_id: string;
  tarea_codigo: string;
  tarea_nombre: string;
  proyecto_id: string;
  proyecto_codigo: string;
  porcentaje_asignacion: string;
  fecha_inicio: string;
  fecha_fin: string;
  notas: string;
}

export interface UserCalendarAbsence {
  id: string;
  tipo: AvailabilityType;
  tipo_display: string;
  fecha_inicio: string;
  fecha_fin: string;
  descripcion: string;
}

export interface UserCalendar {
  usuario_id: string;
  periodo_inicio: string;
  periodo_fin: string;
  asignaciones: UserCalendarEvent[];
  ausencias: UserCalendarAbsence[];
}
