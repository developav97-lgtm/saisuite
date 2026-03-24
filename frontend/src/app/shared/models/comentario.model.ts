export interface ComentarioAutor {
  id: string;
  full_name: string;
  email: string;
}

export interface Respuesta {
  id: string;
  autor: ComentarioAutor;
  texto: string;
  editado: boolean;
  editado_en: string | null;
  created_at: string;
}

export interface Comentario {
  id: string;
  autor: ComentarioAutor;
  texto: string;
  editado: boolean;
  editado_en: string | null;
  padre: string | null;
  respuestas: Respuesta[];
  menciones: ComentarioAutor[];
  created_at: string;
}

export interface ComentarioListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Comentario[];
}
