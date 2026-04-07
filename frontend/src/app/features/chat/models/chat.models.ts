export interface Conversacion {
  id: string;
  participante_1: string;
  participante_1_nombre: string;
  participante_1_email: string;
  participante_2: string;
  participante_2_nombre: string;
  participante_2_email: string;
  ultimo_mensaje: string | null;
  ultimo_mensaje_contenido: string | null;
  ultimo_mensaje_at: string | null;
  mensajes_sin_leer: number;
  bot_context?: string;
  created_at: string;
  updated_at: string;
}

export interface Mensaje {
  id: string;
  conversacion: string;
  remitente: string;
  remitente_nombre: string;
  remitente_email: string;
  contenido: string;
  contenido_html: string;
  imagen_url: string;
  thumbnail_url?: string;
  responde_a: string | null;
  responde_a_contenido: string | null;
  responde_a_remitente_nombre?: string | null;
  editado: boolean;
  editado_at: string | null;
  leido_por_destinatario: boolean;
  leido_at: string | null;
  archivo_url?: string;
  archivo_nombre?: string;
  archivo_tamaño?: number;
  created_at: string;
  updated_at: string;
}

export interface MensajeCreate {
  contenido?: string;
  imagen_url?: string;
  thumbnail_url?: string;
  responde_a_id?: string;
  archivo_url?: string;
  archivo_nombre?: string;
  archivo_tamaño?: number;
}

export interface AutocompleteEntidad {
  id: string;
  codigo: string;
  nombre: string;
  tipo: string;
}

export interface AutocompleteUsuario {
  id: string;
  nombre: string;
  email: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ChatTypingEvent {
  conversacion_id: string;
  user_id: string;
  user_name: string;
}

export interface ChatReadEvent {
  mensaje_id: string;
  leido_at: string;
  leido_por: string;
}
