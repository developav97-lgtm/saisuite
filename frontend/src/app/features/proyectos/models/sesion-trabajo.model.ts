/**
 * SaiSuite — Modelos de SesionTrabajo
 * Espeja SesionTrabajoSerializer de la API.
 */

export interface Pausa {
  inicio: string;
  fin: string | null;
}

export interface SesionTrabajoTareaDetail {
  id: string;
  codigo: string;
  nombre: string;
}

export interface SesionTrabajoUsuarioDetail {
  id: string;
  email: string;
  full_name: string;
}

export type SesionTrabajoEstado = 'activa' | 'pausada' | 'finalizada';

export interface SesionTrabajo {
  id: string;
  tarea: string;
  tarea_detail: SesionTrabajoTareaDetail;
  usuario: string;
  usuario_detail: SesionTrabajoUsuarioDetail;
  inicio: string;
  fin: string | null;
  pausas: Pausa[];
  duracion_segundos: number;
  duracion_horas: string; // el backend devuelve string decimal (Decimal serializado)
  estado: SesionTrabajoEstado;
  notas: string;
  created_at: string;
  updated_at: string;
}
