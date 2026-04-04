import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  CardDataRequest,
  CardDataResponse,
  FilterTercero,
  FilterProyecto,
  FilterDepartamento,
  FilterPeriodo,
} from '../models/report-filter.model';

@Injectable({ providedIn: 'root' })
export class ReportService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/dashboard';

  // ── Card data ───────────────────────────────────────────────

  getCardData(request: CardDataRequest): Observable<CardDataResponse> {
    return this.http.post<CardDataResponse>(`${this.baseUrl}/report/card-data/`, request);
  }

  // ── Filters ─────────────────────────────────────────────────

  searchTerceros(query: string): Observable<FilterTercero[]> {
    const params = new HttpParams().set('q', query);
    return this.http.get<FilterTercero[]>(`${this.baseUrl}/filters/terceros/`, { params });
  }

  getProyectos(): Observable<FilterProyecto[]> {
    return this.http.get<FilterProyecto[]>(`${this.baseUrl}/filters/proyectos/`);
  }

  getDepartamentos(): Observable<FilterDepartamento[]> {
    return this.http.get<FilterDepartamento[]>(`${this.baseUrl}/filters/departamentos/`);
  }

  getPeriodos(): Observable<FilterPeriodo[]> {
    return this.http.get<FilterPeriodo[]>(`${this.baseUrl}/filters/periodos/`);
  }

  // ── PDF Export ──────────────────────────────────────────────

  async exportToPDF(element: HTMLElement, title: string): Promise<void> {
    const html2canvas = (await import('html2canvas')).default;
    const jsPDF = (await import('jspdf')).default;

    const canvas = await html2canvas(element, { scale: 2, useCORS: true });
    const pdf = new jsPDF('p', 'mm', 'letter');
    const imgData = canvas.toDataURL('image/png');
    const pdfWidth = pdf.internal.pageSize.getWidth();
    const pdfHeight = (canvas.height * pdfWidth) / canvas.width;
    pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight);
    pdf.save(`${title}_${new Date().toISOString().split('T')[0]}.pdf`);
  }
}
