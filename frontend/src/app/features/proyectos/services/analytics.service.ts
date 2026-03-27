import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  ProjectKPIs,
  TaskDistribution,
  VelocityResponse,
  BurnRateResponse,
  BurnDownData,
  ResourceUtilization,
  ProjectComparison,
  ProjectTimeline,
  CompareProjectsRequest,
  ExportExcelRequest,
} from '../models/analytics.model';

@Injectable({ providedIn: 'root' })
export class AnalyticsService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/projects';

  getKPIs(projectId: string): Observable<ProjectKPIs> {
    return this.http.get<ProjectKPIs>(`${this.baseUrl}/${projectId}/analytics/kpis/`);
  }

  getTaskDistribution(projectId: string): Observable<TaskDistribution> {
    return this.http.get<TaskDistribution>(`${this.baseUrl}/${projectId}/analytics/task-distribution/`);
  }

  getVelocity(projectId: string, periods = 8): Observable<VelocityResponse> {
    const params = new HttpParams().set('periods', periods.toString());
    return this.http.get<VelocityResponse>(
      `${this.baseUrl}/${projectId}/analytics/velocity/`,
      { params }
    );
  }

  getBurnRate(projectId: string, periods = 8): Observable<BurnRateResponse> {
    const params = new HttpParams().set('periods', periods.toString());
    return this.http.get<BurnRateResponse>(
      `${this.baseUrl}/${projectId}/analytics/burn-rate/`,
      { params }
    );
  }

  getBurnDown(
    projectId: string,
    granularity: 'week' | 'month' = 'week'
  ): Observable<BurnDownData> {
    const params = new HttpParams().set('granularity', granularity);
    return this.http.get<BurnDownData>(
      `${this.baseUrl}/${projectId}/analytics/burn-down/`,
      { params }
    );
  }

  getResourceUtilization(projectId: string): Observable<ResourceUtilization[]> {
    return this.http.get<ResourceUtilization[]>(
      `${this.baseUrl}/${projectId}/analytics/resource-utilization/`
    );
  }

  getTimeline(projectId: string): Observable<ProjectTimeline> {
    return this.http.get<ProjectTimeline>(
      `${this.baseUrl}/${projectId}/analytics/timeline/`
    );
  }

  compareProjects(request: CompareProjectsRequest): Observable<ProjectComparison[]> {
    return this.http.post<ProjectComparison[]>(
      `${this.baseUrl}/analytics/compare/`,
      request
    );
  }

  exportExcel(request: ExportExcelRequest): Observable<Blob> {
    return this.http.post(
      `${this.baseUrl}/analytics/export-excel/`,
      request,
      { responseType: 'blob' }
    );
  }
}
