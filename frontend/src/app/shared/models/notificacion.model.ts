export type TipoNotificacion =
  | 'comentario'
  | 'mencion'
  | 'aprobacion'
  | 'aprobacion_resultado'
  | 'asignacion'
  | 'cambio_estado'
  | 'vencimiento'
  | 'sistema'
  | 'chat'
  | 'recordatorio';

export interface Notificacion {
  id: string;
  tipo: TipoNotificacion;
  tipo_display: string;
  titulo: string;
  mensaje: string;
  objeto_model: string;
  objeto_id_str: string;
  url_accion: string;
  ancla: string;
  leida: boolean;
  leida_en: string | null;
  snoozed_until: string | null;
  recordatorio_en: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface NotificacionListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Notificacion[];
}

// ── C.1: Agrupación ────────────────────────────────────────────────────────────
export interface NotificacionGrupo {
  tipo: 'grupo';
  id: string;
  cantidad: number;
  tipo_notificacion: TipoNotificacion;
  titulo: string;
  autores: string[];
  notificaciones_ids: string[];
  url_accion: string;
  ancla: string;
  created_at: string;
  metadata: Record<string, unknown>;
}

export interface NotificacionIndividual {
  tipo: 'individual';
  notificacion: Notificacion;
}

export type NotificacionItem = NotificacionGrupo | NotificacionIndividual;

// ── C.2: Preferencias ──────────────────────────────────────────────────────────
export interface PreferenciaNotificacion {
  id: string;
  tipo: TipoNotificacion;
  tipo_display: string;
  habilitado_app: boolean;
  habilitado_email: boolean;
  habilitado_push: boolean;
  frecuencia: 'inmediata' | 'cada_hora' | 'diaria';
  frecuencia_display: string;
  agrupar: boolean;
  sonido_habilitado: boolean;
  updated_at: string;
}
