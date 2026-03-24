/**
 * SaiSuite — Modelos de ActividadSaiopen (DEC-020)
 * Catálogo de actividades de Saiopen. Determina el modo de medición de tareas.
 */

/** Modo de medición — determina la UI adaptativa en el detalle de Tarea (DEC-022). */
export type ModoMedicion = 'solo_estados' | 'timesheet' | 'cantidad';

export interface ActividadSaiopen {
  id: string;
  codigo: string;
  nombre: string;
  unidad_medida: ModoMedicion;
  unidad_medida_display: string;
  costo_unitario_base: string;
  activo: boolean;
}

export interface ActividadSaiopenDetail extends ActividadSaiopen {
  descripcion: string;
  saiopen_actividad_id: string | null;
  sincronizado_con_saiopen: boolean;
  created_at: string;
  updated_at: string;
}

export interface ActividadSaiopenCreateDTO {
  codigo?: string;
  nombre: string;
  descripcion?: string;
  unidad_medida: ModoMedicion;
  costo_unitario_base?: number;
}

export type ActividadSaiopenUpdateDTO = Partial<ActividadSaiopenCreateDTO>;
