/**
 * SaiSuite — Modelos de Timesheet
 * Espeja TimesheetEntrySerializer y SesionTrabajoSerializer de la API.
 */

export interface TimesheetUsuario {
  id: string;
  nombre: string;
  email?: string;
}

export interface TimesheetTarea {
  id: string;
  codigo: string;
  nombre: string;
}

export interface TimesheetEntry {
  id: string;
  tarea: string;                       // UUID
  tarea_detail: TimesheetTarea;
  usuario: string;                     // UUID
  usuario_detail: TimesheetUsuario;
  fecha: string;                       // ISO date YYYY-MM-DD
  horas: number;
  descripcion: string;
  validado: boolean;
  validado_por?: string | null;
  validado_por_detail?: TimesheetUsuario | null;
  fecha_validacion?: string | null;
  created_at: string;
  updated_at: string;
}

export interface TimesheetEntryCreate {
  tarea_id: string;
  fecha: string;
  horas: number;
  descripcion?: string;
}

export interface TimesheetFilters {
  tarea?: string;
  validado?: boolean;
  fecha_inicio?: string;
  fecha_fin?: string;
}

/** Sesión de trabajo con cronómetro (espeja SesionTrabajoSerializer) */
export interface Pausa {
  inicio: string;   // ISO datetime
  fin?: string | null;
}

export interface SesionTrabajo {
  id: string;
  tarea: string;
  tarea_detail: TimesheetTarea;
  usuario: string;
  usuario_detail: TimesheetUsuario;
  inicio: string;
  fin?: string | null;
  pausas: Pausa[];
  duracion_segundos: number;
  duracion_horas: string;
  estado: 'activa' | 'pausada' | 'finalizada';
  notas: string;
  created_at: string;
  updated_at: string;
}

/** Vista semanal — filas agrupadas por tarea */
export interface TimesheetSemanalRow {
  tarea: TimesheetTarea;
  horasPorDia: Record<string, number>;   // fecha ISO → horas
  totalSemana: number;
}
