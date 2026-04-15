import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  DashboardListItem,
  DashboardDetail,
  DashboardCreate,
  DashboardCard,
  DashboardCardCreate,
  CardLayoutRequest,
  ShareRequest,
  DashboardShare,
  BiSelectableReport,
} from '../models/dashboard.model';
import { ReportFilter } from '../models/report-filter.model';

@Injectable({ providedIn: 'root' })
export class DashboardService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/dashboard';

  // ── Dashboard CRUD ──────────────────────────────────────────

  list(): Observable<DashboardListItem[]> {
    return this.http.get<DashboardListItem[]>(`${this.baseUrl}/`);
  }

  getById(id: string): Observable<DashboardDetail> {
    return this.http.get<DashboardDetail>(`${this.baseUrl}/${id}/`);
  }

  create(data: DashboardCreate): Observable<DashboardListItem> {
    return this.http.post<DashboardListItem>(`${this.baseUrl}/`, data);
  }

  update(id: string, data: Partial<DashboardCreate>): Observable<DashboardDetail> {
    return this.http.put<DashboardDetail>(`${this.baseUrl}/${id}/`, data);
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/${id}/`);
  }

  setDefault(id: string): Observable<{ success: boolean }> {
    return this.http.post<{ success: boolean }>(`${this.baseUrl}/${id}/set-default/`, {});
  }

  toggleFavorite(id: string): Observable<{ es_favorito: boolean }> {
    return this.http.post<{ es_favorito: boolean }>(`${this.baseUrl}/${id}/toggle-favorite/`, {});
  }

  getSharedWithMe(): Observable<DashboardListItem[]> {
    return this.http.get<DashboardListItem[]>(`${this.baseUrl}/compartidos-conmigo/`);
  }

  // ── Cards ───────────────────────────────────────────────────

  getCards(dashboardId: string): Observable<DashboardCard[]> {
    return this.http.get<DashboardCard[]>(`${this.baseUrl}/${dashboardId}/cards/`);
  }

  addCard(dashboardId: string, card: DashboardCardCreate): Observable<DashboardCard> {
    return this.http.post<DashboardCard>(`${this.baseUrl}/${dashboardId}/cards/`, card);
  }

  updateCard(dashboardId: string, cardId: number | string, data: Partial<DashboardCardCreate>): Observable<DashboardCard> {
    return this.http.put<DashboardCard>(`${this.baseUrl}/${dashboardId}/cards/${cardId}/`, data);
  }

  deleteCard(dashboardId: string, cardId: number | string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/${dashboardId}/cards/${cardId}/`);
  }

  saveLayout(dashboardId: string, layout: CardLayoutRequest): Observable<CardLayoutRequest> {
    return this.http.post<CardLayoutRequest>(`${this.baseUrl}/${dashboardId}/cards/layout/`, layout);
  }

  // ── Share ───────────────────────────────────────────────────

  share(dashboardId: string, data: ShareRequest): Observable<DashboardShare> {
    return this.http.post<DashboardShare>(`${this.baseUrl}/${dashboardId}/share/`, data);
  }

  revokeShare(dashboardId: string, userId: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/${dashboardId}/share/${userId}/`);
  }

  // ── Filters ─────────────────────────────────────────────────

  saveDefaultFilters(id: string, filtros: ReportFilter): Observable<DashboardDetail> {
    return this.http.put<DashboardDetail>(`${this.baseUrl}/${id}/filters/`, {
      filtros_default: filtros,
    });
  }

  // ── bi_report cards (Sprint 4) ───────────────────────────────

  /**
   * Ejecuta el reporte BI de una tarjeta aplicando filtros en 3 capas.
   * @param dashboardId UUID del dashboard
   * @param cardId ID entero de la tarjeta
   * @param dashboardFilters Filtros globales del dashboard (fecha, periodo, terceros…)
   */
  executeBiCard(
    dashboardId: string,
    cardId: number,
    dashboardFilters: Record<string, unknown> = {},
  ): Observable<unknown> {
    return this.http.post(
      `${this.baseUrl}/${dashboardId}/cards/${cardId}/bi-execute/`,
      { dashboard_filters: dashboardFilters },
    );
  }

  /**
   * Lista reportes BI del usuario compatibles para usar como tarjeta de dashboard.
   * Solo tipos gráficos (bar, line, pie, area, waterfall, kpi, gauge).
   */
  getSelectableReports(): Observable<BiSelectableReport[]> {
    return this.http.get<BiSelectableReport[]>(`${this.baseUrl}/reportes/seleccionables/`);
  }
}
