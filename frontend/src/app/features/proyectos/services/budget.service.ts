import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  ProjectBudget,
  ProjectBudgetWrite,
  BudgetVariance,
  BudgetAlert,
  BudgetSnapshot,
  CostSummary,
  CostBreakdownByResource,
  CostBreakdownByTask,
  EvmMetrics,
  InvoiceData,
  CostFilters,
} from '../models/budget.model';

@Injectable({ providedIn: 'root' })
export class BudgetService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/v1/projects';

  // ── Budget CRUD ────────────────────────────────────────────────────────────

  getBudget(projectId: string): Observable<ProjectBudget> {
    return this.http.get<ProjectBudget>(`${this.base}/${projectId}/budget/`);
  }

  createBudget(projectId: string, data: ProjectBudgetWrite): Observable<ProjectBudget> {
    return this.http.post<ProjectBudget>(`${this.base}/${projectId}/budget/`, data);
  }

  updateBudget(projectId: string, data: Partial<ProjectBudgetWrite>): Observable<ProjectBudget> {
    return this.http.patch<ProjectBudget>(`${this.base}/${projectId}/budget/`, data);
  }

  approveBudget(projectId: string, approvedBudget: string): Observable<ProjectBudget> {
    return this.http.post<ProjectBudget>(
      `${this.base}/${projectId}/budget/approve/`,
      { approved_budget: approvedBudget },
    );
  }

  // ── Budget analysis ────────────────────────────────────────────────────────

  getVariance(projectId: string): Observable<BudgetVariance> {
    return this.http.get<BudgetVariance>(`${this.base}/${projectId}/budget/variance/`);
  }

  getAlerts(projectId: string): Observable<BudgetAlert[]> {
    return this.http.get<BudgetAlert[]>(`${this.base}/${projectId}/budget/alerts/`);
  }

  // ── Snapshots ──────────────────────────────────────────────────────────────

  getSnapshots(projectId: string): Observable<BudgetSnapshot[]> {
    return this.http.get<BudgetSnapshot[]>(`${this.base}/${projectId}/budget/snapshots/`);
  }

  createSnapshot(projectId: string): Observable<BudgetSnapshot> {
    return this.http.post<BudgetSnapshot>(`${this.base}/${projectId}/budget/snapshots/`, {});
  }

  // ── Cost summaries ─────────────────────────────────────────────────────────

  getTotalCost(projectId: string, filters?: CostFilters): Observable<CostSummary> {
    let params = new HttpParams();
    if (filters?.start_date) params = params.set('start_date', filters.start_date);
    if (filters?.end_date)   params = params.set('end_date', filters.end_date);
    return this.http.get<CostSummary>(`${this.base}/${projectId}/costs/total/`, { params });
  }

  getCostByResource(projectId: string): Observable<CostBreakdownByResource[]> {
    return this.http.get<CostBreakdownByResource[]>(
      `${this.base}/${projectId}/costs/by-resource/`,
    );
  }

  getCostByTask(projectId: string): Observable<CostBreakdownByTask[]> {
    return this.http.get<CostBreakdownByTask[]>(
      `${this.base}/${projectId}/costs/by-task/`,
    );
  }

  getEvmMetrics(projectId: string, asOfDate?: string): Observable<EvmMetrics> {
    let params = new HttpParams();
    if (asOfDate) params = params.set('as_of_date', asOfDate);
    return this.http.get<EvmMetrics>(`${this.base}/${projectId}/costs/evm/`, { params });
  }

  // ── Invoice ────────────────────────────────────────────────────────────────

  getInvoiceData(projectId: string): Observable<InvoiceData> {
    return this.http.get<InvoiceData>(`${this.base}/${projectId}/invoice-data/`);
  }
}
