/**
 * SaiSuite — Oportunidad Detail Page
 * Vista detallada de una oportunidad con tabs: Timeline, Actividades, Cotizaciones.
 */
import {
  ChangeDetectionStrategy, Component, OnInit, OnDestroy,
  inject, signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { MatTabsModule } from '@angular/material/tabs';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatChipsModule } from '@angular/material/chips';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatMenuModule } from '@angular/material/menu';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { Subject, takeUntil, switchMap } from 'rxjs';

import { CrmService } from '../../services/crm.service';
import {
  CrmOportunidad, CrmTimelineEvent, CrmActividad, CrmCotizacion,
} from '../../models/crm.model';
import { ToastService } from '../../../../core/services/toast.service';
import { ActividadDialogComponent } from '../../components/actividad-dialog/actividad-dialog.component';
import { PerderDialogComponent } from '../../components/perder-dialog/perder-dialog.component';
import { CompletarActividadDialogComponent } from '../../components/completar-actividad-dialog/completar-actividad-dialog.component';

@Component({
  selector: 'app-oportunidad-detail-page',
  templateUrl: './oportunidad-detail-page.component.html',
  styleUrl: './oportunidad-detail-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule, RouterModule, ReactiveFormsModule,
    MatTabsModule, MatButtonModule, MatIconModule,
    MatFormFieldModule, MatInputModule, MatProgressBarModule,
    MatChipsModule, MatTooltipModule, MatMenuModule, MatDialogModule,
  ],
})
export class OportunidadDetailPageComponent implements OnInit, OnDestroy {
  private readonly crm    = inject(CrmService);
  private readonly route  = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly toast  = inject(ToastService);
  private readonly fb     = inject(FormBuilder);
  private readonly dialog = inject(MatDialog);
  private readonly destroy$ = new Subject<void>();

  readonly oportunidad   = signal<CrmOportunidad | null>(null);
  readonly timeline      = signal<CrmTimelineEvent[]>([]);
  readonly actividades   = signal<CrmActividad[]>([]);
  readonly cotizaciones  = signal<CrmCotizacion[]>([]);
  readonly loading       = signal(false);
  readonly addingNota    = signal(false);

  readonly notaForm = this.fb.group({
    descripcion: ['', [Validators.required, Validators.minLength(3)]],
  });

  readonly tipoIconMap: Record<string, string> = {
    nota: 'sticky_note_2',
    cambio_etapa: 'swap_horiz',
    actividad_comp: 'task_alt',
    email_enviado: 'email',
    cotizacion: 'receipt_long',
    sistema: 'settings',
  };

  ngOnInit(): void {
    this.route.params.pipe(
      takeUntil(this.destroy$),
      switchMap(params => {
        this.loading.set(true);
        return this.crm.getOportunidad(params['id']);
      }),
    ).subscribe({
      next: op => {
        this.oportunidad.set(op);
        this.loading.set(false);
        this.loadRelated(op.id);
      },
      error: () => {
        this.toast.error('Error cargando oportunidad');
        this.loading.set(false);
      },
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadRelated(id: string): void {
    this.crm.getTimeline(id).pipe(takeUntil(this.destroy$)).subscribe(ev => this.timeline.set(ev));
    this.crm.listActividades(id).pipe(takeUntil(this.destroy$)).subscribe(ac => this.actividades.set(ac));
    this.crm.listCotizaciones(id).pipe(takeUntil(this.destroy$)).subscribe(ct => this.cotizaciones.set(ct));
  }

  agregarNota(): void {
    if (this.notaForm.invalid || !this.oportunidad()) return;
    this.addingNota.set(true);
    const descripcion = this.notaForm.value.descripcion!;
    this.crm.agregarNota(this.oportunidad()!.id, descripcion)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: evento => {
          this.timeline.update(ev => [evento, ...ev]);
          this.notaForm.reset();
          this.addingNota.set(false);
        },
        error: () => {
          this.toast.error('Error agregando nota');
          this.addingNota.set(false);
        },
      });
  }

  ganar(): void {
    if (!this.oportunidad()) return;
    this.crm.ganarOportunidad(this.oportunidad()!.id)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: op => {
          this.oportunidad.set(op);
          this.toast.success('¡Oportunidad ganada!');
        },
        error: (err) => this.toast.error(err?.error?.detail ?? 'Error ganando oportunidad'),
      });
  }

  perder(): void {
    const ref = this.dialog.open(PerderDialogComponent, { width: '420px' });
    ref.afterClosed().pipe(takeUntil(this.destroy$)).subscribe((motivo: string | undefined) => {
      if (!motivo) return;
      this.crm.perderOportunidad(this.oportunidad()!.id, motivo)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: op => {
            this.oportunidad.set(op);
            this.toast.info('Oportunidad marcada como perdida');
          },
          error: () => this.toast.error('Error actualizando oportunidad'),
        });
    });
  }

  createCotizacion(): void {
    const op = this.oportunidad();
    if (!op) return;
    this.crm.createCotizacion(op.id, { titulo: `Cotización ${op.titulo}` })
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: cot => {
          this.router.navigate(['/crm/cotizaciones', cot.id]);
        },
        error: () => this.toast.error('Error creando cotización'),
      });
  }

  openActividadDialog(): void {
    const op = this.oportunidad();
    if (!op) return;
    const ref = this.dialog.open(ActividadDialogComponent, {
      width: '480px',
      data: { oportunidadId: op.id },
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
            this.actividades.update(list =>
              list.map(a => a.id === act.id ? act : a)
            );
            this.toast.success('Actividad completada');
          },
          error: () => this.toast.error('Error completando actividad'),
        });
    });
  }

  formatMoney(val: string): string {
    const n = parseFloat(val || '0');
    return new Intl.NumberFormat('es-CO', {
      style: 'currency', currency: 'COP', maximumFractionDigits: 0,
    }).format(n);
  }

  goBack(): void {
    this.router.navigate(['/crm']);
  }
}
