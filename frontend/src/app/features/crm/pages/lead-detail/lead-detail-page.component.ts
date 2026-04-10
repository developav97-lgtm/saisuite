/**
 * SaiSuite — CRM Lead Detail Page
 * Vista detallada de un lead: info, notas y acciones.
 */
import {
  ChangeDetectionStrategy, Component, OnInit, OnDestroy,
  inject, signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatChipsModule } from '@angular/material/chips';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatTabsModule } from '@angular/material/tabs';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatDividerModule } from '@angular/material/divider';
import { Subject, takeUntil, switchMap } from 'rxjs';

import { CrmService } from '../../services/crm.service';
import { CrmLead, CrmActividad } from '../../models/crm.model';
import { ToastService } from '../../../../core/services/toast.service';
import { LeadConvertirDialogComponent } from '../../components/lead-convertir-dialog/lead-convertir-dialog.component';
import { ActividadLeadDialogComponent } from '../../components/actividad-lead-dialog/actividad-lead-dialog.component';
import { CompletarActividadDialogComponent } from '../../components/completar-actividad-dialog/completar-actividad-dialog.component';

@Component({
  selector: 'app-lead-detail-page',
  templateUrl: './lead-detail-page.component.html',
  styleUrl: './lead-detail-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule, RouterModule, ReactiveFormsModule,
    MatButtonModule, MatIconModule, MatProgressBarModule,
    MatChipsModule, MatTooltipModule, MatTabsModule,
    MatFormFieldModule, MatInputModule, MatDialogModule, MatDividerModule,
  ],
})
export class LeadDetailPageComponent implements OnInit, OnDestroy {
  private readonly crm    = inject(CrmService);
  private readonly route  = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly toast  = inject(ToastService);
  private readonly fb     = inject(FormBuilder);
  private readonly dialog = inject(MatDialog);
  private readonly destroy$ = new Subject<void>();

  readonly lead        = signal<CrmLead | null>(null);
  readonly actividades = signal<CrmActividad[]>([]);
  readonly loading     = signal(false);
  readonly saving      = signal(false);

  readonly notaForm = this.fb.group({
    nota: ['', [Validators.required, Validators.minLength(3)]],
  });

  readonly fuenteLabel: Partial<Record<string, string>> = {
    manual: 'Manual',
    webhook: 'Webhook',
    csv: 'CSV/Excel',
    referido: 'Referido',
    otro: 'Otro',
  };

  ngOnInit(): void {
    this.route.params.pipe(
      takeUntil(this.destroy$),
      switchMap(params => {
        this.loading.set(true);
        return this.crm.getLead(params['id']);
      }),
    ).subscribe({
      next: lead => {
        this.lead.set(lead);
        this.loading.set(false);
        this.loadActividades(lead.id);
      },
      error: () => {
        this.toast.error('Error cargando lead');
        this.router.navigate(['/crm/leads']);
      },
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  getScoreColor(score: number): string {
    if (score >= 70) return 'var(--sc-success)';
    if (score >= 40) return 'var(--sc-warning)';
    return 'var(--sc-text-secondary)';
  }

  getScoreLabel(score: number): string {
    if (score >= 70) return 'Caliente';
    if (score >= 40) return 'Tibio';
    return 'Frío';
  }

  openConvertirDialog(): void {
    const lead = this.lead();
    if (!lead) return;
    const ref = this.dialog.open(LeadConvertirDialogComponent, {
      width: '480px',
      data: lead,
    });
    ref.afterClosed().pipe(takeUntil(this.destroy$)).subscribe(result => {
      if (result) {
        this.toast.success('Lead convertido a oportunidad');
        this.router.navigate(['/crm/oportunidades', result.id]);
      }
    });
  }

  guardarNota(): void {
    const lead = this.lead();
    if (!lead || this.notaForm.invalid) {
      this.notaForm.markAllAsTouched();
      return;
    }
    const nuevaNota = this.notaForm.value.nota!;
    const notaActual = lead.notas ? `${lead.notas}\n\n${nuevaNota}` : nuevaNota;
    this.saving.set(true);
    this.crm.updateLead(lead.id, { notas: notaActual })
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: updated => {
          this.lead.set(updated);
          this.notaForm.reset();
          this.toast.success('Nota guardada');
          this.saving.set(false);
        },
        error: () => {
          this.toast.error('Error guardando nota');
          this.saving.set(false);
        },
      });
  }

  private loadActividades(leadId: string): void {
    this.crm.listActividadesLead(leadId).pipe(takeUntil(this.destroy$)).subscribe({
      next: list => this.actividades.set(list),
      error: () => {},
    });
  }

  openActividadDialog(): void {
    const lead = this.lead();
    if (!lead) return;
    const ref = this.dialog.open(ActividadLeadDialogComponent, {
      width: '480px',
      data: { leadId: lead.id },
    });
    ref.afterClosed().pipe(takeUntil(this.destroy$)).subscribe(actividad => {
      if (actividad) {
        this.actividades.update(list => [...list, actividad]);
        this.toast.success('Actividad creada');
      }
    });
  }

  completarActividad(actividad: CrmActividad): void {
    const ref = this.dialog.open(CompletarActividadDialogComponent, {
      width: '420px',
      data: actividad,
    });
    ref.afterClosed().pipe(takeUntil(this.destroy$)).subscribe((resultado: string | undefined) => {
      if (resultado === undefined) return;
      this.crm.completarActividad(actividad.id, resultado)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: act => {
            this.actividades.update(list => list.map(a => a.id === act.id ? act : a));
            this.toast.success('Actividad completada');
          },
          error: () => this.toast.error('Error completando actividad'),
        });
    });
  }

  getTipoIcon(tipo: string): string {
    const map: Record<string, string> = {
      llamada: 'phone', reunion: 'groups', email: 'email',
      tarea: 'task_alt', whatsapp: 'chat', otro: 'more_horiz',
    };
    return map[tipo] ?? 'event';
  }

  goBack(): void {
    this.router.navigate(['/crm/leads']);
  }
}
