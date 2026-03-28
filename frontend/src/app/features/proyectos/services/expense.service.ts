import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  ProjectExpense,
  ProjectExpenseWrite,
  ExpenseFilters,
} from '../models/budget.model';

@Injectable({ providedIn: 'root' })
export class ExpenseService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/v1/projects';

  getExpenses(projectId: string, filters?: ExpenseFilters): Observable<ProjectExpense[]> {
    let params = new HttpParams();
    if (filters?.category)   params = params.set('category', filters.category);
    if (filters?.start_date) params = params.set('start_date', filters.start_date);
    if (filters?.end_date)   params = params.set('end_date', filters.end_date);
    if (filters?.billable !== undefined) {
      params = params.set('billable', filters.billable.toString());
    }
    return this.http.get<ProjectExpense[]>(
      `${this.base}/${projectId}/expenses/`,
      { params },
    );
  }

  createExpense(projectId: string, data: ProjectExpenseWrite): Observable<ProjectExpense> {
    return this.http.post<ProjectExpense>(`${this.base}/${projectId}/expenses/`, data);
  }

  getExpense(expenseId: string): Observable<ProjectExpense> {
    return this.http.get<ProjectExpense>(`${this.base}/expenses/${expenseId}/`);
  }

  updateExpense(expenseId: string, data: Partial<ProjectExpenseWrite>): Observable<ProjectExpense> {
    return this.http.patch<ProjectExpense>(`${this.base}/expenses/${expenseId}/`, data);
  }

  deleteExpense(expenseId: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/expenses/${expenseId}/`);
  }

  approveExpense(expenseId: string): Observable<ProjectExpense> {
    return this.http.post<ProjectExpense>(
      `${this.base}/expenses/${expenseId}/approve/`,
      {},
    );
  }
}
