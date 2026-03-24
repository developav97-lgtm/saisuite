/**
 * SaiSuite — Modelos de Fase
 */

export type EstadoFase = 'planificada' | 'activa' | 'completada' | 'cancelada';

/** Fase en listado */
export interface FaseList {
  id: string;
  nombre: string;
  orden: number;
  estado: EstadoFase;
  porcentaje_avance: string;
  /** Suma de todos los presupuestos de categoría */
  presupuesto_total: string;
  activo: boolean;
  created_at: string;
}

/** Fase en detalle — todos los campos */
export interface FaseDetail extends FaseList {
  proyecto: string; // UUID
  descripcion: string;
  fecha_inicio_planificada: string;
  fecha_fin_planificada: string;
  fecha_inicio_real: string | null;
  fecha_fin_real: string | null;
  presupuesto_mano_obra: string;
  presupuesto_materiales: string;
  presupuesto_subcontratos: string;
  presupuesto_equipos: string;
  presupuesto_otros: string;
  updated_at: string;
}

/** Payload para crear/actualizar fase */
export interface FaseCreate {
  nombre: string;
  descripcion?: string;
  orden?: number;
  fecha_inicio_planificada: string;
  fecha_fin_planificada: string;
  fecha_inicio_real?: string | null;
  fecha_fin_real?: string | null;
  presupuesto_mano_obra?: string;
  presupuesto_materiales?: string;
  presupuesto_subcontratos?: string;
  presupuesto_equipos?: string;
  presupuesto_otros?: string;
  porcentaje_avance?: string;
}
