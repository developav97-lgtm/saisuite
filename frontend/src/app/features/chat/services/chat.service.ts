import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  AIFeedback, AIFeedbackCreate, AIUsageSummary,
  Conversacion, Mensaje, MensajeCreate,
  AutocompleteEntidad, AutocompleteUsuario, PaginatedResponse,
} from '../models/chat.models';

@Injectable({ providedIn: 'root' })
export class ChatService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/chat';

  obtenerConversaciones(): Observable<Conversacion[]> {
    return this.http.get<Conversacion[]>(`${this.baseUrl}/conversaciones/`);
  }

  crearConversacion(destinatarioId: string): Observable<Conversacion> {
    return this.http.post<Conversacion>(`${this.baseUrl}/conversaciones/`, {
      destinatario_id: destinatarioId,
    });
  }

  listarMensajes(conversacionId: string, page = 1): Observable<PaginatedResponse<Mensaje>> {
    const params = new HttpParams().set('page', String(page));
    return this.http.get<PaginatedResponse<Mensaje>>(
      `${this.baseUrl}/conversaciones/${conversacionId}/mensajes/`,
      { params },
    );
  }

  enviarMensaje(conversacionId: string, data: MensajeCreate): Observable<Mensaje> {
    return this.http.post<Mensaje>(
      `${this.baseUrl}/conversaciones/${conversacionId}/mensajes/enviar/`,
      data,
    );
  }

  marcarLeido(mensajeId: string): Observable<{ status: string; leido_at: string }> {
    return this.http.post<{ status: string; leido_at: string }>(
      `${this.baseUrl}/mensajes/${mensajeId}/marcar-leido/`,
      {},
    );
  }

  autocompleteEntidades(query: string, tipo?: string): Observable<AutocompleteEntidad[]> {
    let params = new HttpParams().set('query', query);
    if (tipo) params = params.set('tipo', tipo);
    return this.http.get<AutocompleteEntidad[]>(
      `${this.baseUrl}/autocomplete/entidades/`,
      { params },
    );
  }

  autocompleteUsuarios(query: string): Observable<AutocompleteUsuario[]> {
    const params = new HttpParams().set('query', query);
    return this.http.get<AutocompleteUsuario[]>(
      `${this.baseUrl}/autocomplete/usuarios/`,
      { params },
    );
  }

  uploadArchivo(file: File): Observable<{ archivo_url: string; archivo_nombre: string; archivo_tamaño: number }> {
    const formData = new FormData();
    formData.append('archivo', file, file.name);
    return this.http.post<{ archivo_url: string; archivo_nombre: string; archivo_tamaño: number }>(
      `${this.baseUrl}/upload-archivo/`,
      formData,
    );
  }

  uploadImagen(blob: Blob, fileName: string): Observable<{ imagen_url: string; thumbnail_url: string; width: number; height: number }> {
    const formData = new FormData();
    formData.append('imagen', blob, fileName);
    return this.http.post<{ imagen_url: string; thumbnail_url: string; width: number; height: number }>(
      `${this.baseUrl}/upload-imagen/`,
      formData,
    );
  }

  editarMensaje(mensajeId: string, contenido: string): Observable<Mensaje> {
    return this.http.patch<Mensaje>(
      `${this.baseUrl}/mensajes/${mensajeId}/editar/`,
      { contenido },
    );
  }

  getPresencia(): Observable<Record<string, string>> {
    return this.http.get<Record<string, string>>(`${this.baseUrl}/presencia/`);
  }

  crearConversacionBot(context: string): Observable<Conversacion> {
    return this.http.post<Conversacion>(`${this.baseUrl}/conversaciones/bot/`, { context });
  }

  buscarMensajes(conversacionId: string, query: string): Observable<{ results: Mensaje[]; query: string }> {
    const params = new HttpParams().set('q', query);
    return this.http.get<{ results: Mensaje[]; query: string }>(
      `${this.baseUrl}/conversaciones/${conversacionId}/buscar/`,
      { params },
    );
  }

  enviarFeedbackIA(data: AIFeedbackCreate): Observable<AIFeedback> {
    return this.http.post<AIFeedback>('/api/v1/ai/feedback/', data);
  }

  limpiarChatBot(): Observable<{ deleted: number }> {
    return this.http.delete<{ deleted: number }>(`${this.baseUrl}/conversaciones/bot/limpiar/`);
  }

  getAIUsage(): Observable<AIUsageSummary> {
    return this.http.get<AIUsageSummary>('/api/v1/companies/licenses/me/ai-usage/');
  }
}
