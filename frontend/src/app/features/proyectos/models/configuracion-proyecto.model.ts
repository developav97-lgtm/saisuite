/**
 * SaiSuite — Modelo ConfiguracionModulo (proyectos)
 * Espeja ConfiguracionModuloSerializer de la API.
 */

export type ModoTimesheet = 'manual' | 'cronometro' | 'ambos' | 'desactivado';

export interface ConfiguracionProyecto {
  requiere_sync_saiopen_para_ejecucion: boolean;
  dias_alerta_vencimiento: number;
  modo_timesheet: ModoTimesheet;
}
