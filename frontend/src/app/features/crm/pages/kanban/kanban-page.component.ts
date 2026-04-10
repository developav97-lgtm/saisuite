/**
 * SaiSuite — CRM Kanban Page
 * Vista principal del pipeline con Drag & Drop entre etapas.
 */
import {
  ChangeDetectionStrategy, Component, OnInit, OnDestroy,
  inject, signal, computed,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSelectModule } from '@angular/material/select';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatMenuModule } from '@angular/material/menu';
import { MatChipsModule } from '@angular/material/chips';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { FormsModule } from '@angular/forms';
import {
  CdkDragDrop, DragDropModule, moveItemInArray, transferArrayItem,
} from '@angular/cdk/drag-drop';
import { Subject, takeUntil } from 'rxjs';

import { CrmService } from '../../services/crm.service';
import { CrmPipeline, KanbanColumna, KanbanOportunidad } from '../../models/crm.model';
import { ToastService } from '../../../../core/services/toast.service';

@Component({
  selector: 'app-kanban-page',
  templateUrl: './kanban-page.component.html',
  styleUrl: './kanban-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule, FormsModule, DragDropModule,
    MatButtonModule, MatIconModule, MatSelectModule,
    MatFormFieldModule, MatProgressBarModule, MatMenuModule,
    MatChipsModule, MatTooltipModule, MatDialogModule,
  ],
})
export class KanbanPageComponent implements OnInit, OnDestroy {
  private readonly crm    = inject(CrmService);
  private readonly router = inject(Router);
  private readonly toast  = inject(ToastService);
  private readonly destroy$ = new Subject<void>();

  readonly pipelines    = signal<CrmPipeline[]>([]);
  readonly columnas     = signal<KanbanColumna[]>([]);
  readonly loading      = signal(false);
  readonly selectedPipelineId = signal<string>('');

  readonly connectedLists = computed(() =>
    this.columnas().map(c => `etapa-${c.etapa_id}`)
  );

  ngOnInit(): void {
    this.crm.listPipelines().pipe(takeUntil(this.destroy$)).subscribe({
      next: pipelines => {
        this.pipelines.set(pipelines);
        const defaultPipeline = pipelines.find(p => p.es_default) ?? pipelines[0];
        if (defaultPipeline) {
          this.selectedPipelineId.set(defaultPipeline.id);
          this.loadKanban(defaultPipeline.id);
        }
      },
      error: () => this.toast.error('Error cargando pipelines'),
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  onPipelineChange(pipelineId: string): void {
    this.selectedPipelineId.set(pipelineId);
    this.loadKanban(pipelineId);
  }

  private loadKanban(pipelineId: string): void {
    this.loading.set(true);
    this.crm.getKanban(pipelineId).pipe(takeUntil(this.destroy$)).subscribe({
      next: columnas => {
        this.columnas.set(columnas);
        this.loading.set(false);
      },
      error: () => {
        this.toast.error('Error cargando kanban');
        this.loading.set(false);
      },
    });
  }

  onCardDrop(event: CdkDragDrop<KanbanOportunidad[]>, columna: KanbanColumna): void {
    if (event.previousContainer === event.container) {
      const cols = [...this.columnas()];
      const col = cols.find(c => c.etapa_id === columna.etapa_id);
      if (col) {
        const ops = [...col.oportunidades];
        moveItemInArray(ops, event.previousIndex, event.currentIndex);
        col.oportunidades = ops;
        this.columnas.set(cols);
      }
      return;
    }

    // Mover entre etapas
    const cols = [...this.columnas()];
    const sourceId = (event.previousContainer.element.nativeElement as HTMLElement)
      .getAttribute('data-etapa-id');
    const targetId = columna.etapa_id;

    const sourceCol = cols.find(c => c.etapa_id === sourceId);
    const targetCol = cols.find(c => c.etapa_id === targetId);
    if (!sourceCol || !targetCol) return;

    const sourceOps = [...sourceCol.oportunidades];
    const targetOps = [...targetCol.oportunidades];
    const [movedOp] = sourceOps.splice(event.previousIndex, 1);
    targetOps.splice(event.currentIndex, 0, movedOp);
    sourceCol.oportunidades = sourceOps;
    targetCol.oportunidades = targetOps;
    this.columnas.set(cols);

    this.crm.moverEtapa(movedOp.id, targetId).pipe(takeUntil(this.destroy$)).subscribe({
      error: () => {
        this.toast.error('Error moviendo oportunidad');
        this.loadKanban(this.selectedPipelineId());
      },
    });
  }

  openOportunidad(op: KanbanOportunidad): void {
    this.router.navigate(['/crm/oportunidades', op.id]);
  }

  createOportunidad(): void {
    this.router.navigate(['/crm/oportunidades/nueva']);
  }

  formatMoney(val: string): string {
    const n = parseFloat(val || '0');
    return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(n);
  }
}
