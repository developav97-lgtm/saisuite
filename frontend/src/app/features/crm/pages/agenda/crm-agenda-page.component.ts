/**
 * SaiSuite — CRM Agenda Page
 * Vista de actividades globales del CRM agrupadas por día.
 */
import {
  ChangeDetectionStrategy, Component, OnInit, OnDestroy,
  inject, signal, computed,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatChipsModule } from '@angular/material/chips';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { Subject, takeUntil } from 'rxjs';

import { CrmService } from '../../services/crm.service';
import { CrmActividadAgenda } from '../../models/crm.model';
import { ToastService } from '../../../../core/services/toast.service';
import { CompletarActividadDialogComponent } from '../../components/completar-actividad-dialog/completar-actividad-dialog.component';

interface DiaAgenda {
  fecha: Date;
  label: string;
  actividades: CrmActividadAgenda[];
}

@Component({
  selector: 'app-crm-agenda-page',
  templateUrl: './crm-agenda-page.component.html',
  styleUrl: './crm-agenda-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule, RouterModule, FormsModule,
    MatButtonModule, MatIconModule, MatCheckboxModule,
    MatProgressBarModule, MatChipsModule, MatTooltipModule, MatDialogModule,
  ],
})
export class CrmAgendaPageComponent implements OnInit, OnDestroy {
  private readonly crm     = inject(CrmService);
  private readonly toast   = inject(ToastService);
  private readonly dialog  = inject(MatDialog);
  private readonly destroy$ = new Subject<void>();

  readonly actividades     = signal<CrmActividadAgenda[]>([]);
  readonly loading         = signal(false);
  soloPendientes           = true;

  // Semana actual
  readonly semanaInicio = signal<Date>(this.getInicioSemana(new Date()));

  readonly semanaLabel = computed(() => {
    const ini = this.semanaInicio();
    const fin = new Date(ini);
    fin.setDate(fin.getDate() + 6);
    return `${this.formatShort(ini)} — ${this.formatShort(fin)}`;
  });

  readonly diasAgenda = computed<DiaAgenda[]>(() => {
    const ini = this.semanaInicio();
    const dias: DiaAgenda[] = [];
    for (let i = 0; i < 7; i++) {
      const d = new Date(ini);
      d.setDate(d.getDate() + i);
      const dateStr = this.toDateStr(d);
      dias.push({
        fecha: d,
        label: d.toLocaleDateString('es-CO', { weekday: 'long', day: 'numeric', month: 'long' }),
        actividades: this.actividades().filter(a =>
          a.fecha_programada.startsWith(dateStr)
        ),
      });
    }
    return dias;
  });

  readonly diasConActividades = computed(() =>
    this.diasAgenda().filter(d => d.actividades.length > 0)
  );

  ngOnInit(): void {
    this.loadAgenda();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadAgenda(): void {
    this.loading.set(true);
    const ini = this.semanaInicio();
    const fin = new Date(ini);
    fin.setDate(fin.getDate() + 6);

    this.crm.getAgenda({
      fecha_desde:    this.toDateStr(ini),
      fecha_hasta:    this.toDateStr(fin),
      solo_pendientes: this.soloPendientes || undefined,
    }).pipe(takeUntil(this.destroy$)).subscribe({
      next: list => {
        this.actividades.set(list);
        this.loading.set(false);
      },
      error: () => {
        this.toast.error('Error cargando agenda');
        this.loading.set(false);
      },
    });
  }

  semanaAnterior(): void {
    const d = new Date(this.semanaInicio());
    d.setDate(d.getDate() - 7);
    this.semanaInicio.set(d);
    this.loadAgenda();
  }

  semanaSiguiente(): void {
    const d = new Date(this.semanaInicio());
    d.setDate(d.getDate() + 7);
    this.semanaInicio.set(d);
    this.loadAgenda();
  }

  hoy(): void {
    this.semanaInicio.set(this.getInicioSemana(new Date()));
    this.loadAgenda();
  }

  onFiltroChange(): void {
    this.loadAgenda();
  }

  completar(act: CrmActividadAgenda): void {
    const ref = this.dialog.open(CompletarActividadDialogComponent, {
      width: '420px',
      data: act,
    });
    ref.afterClosed().pipe(takeUntil(this.destroy$)).subscribe((resultado: string | undefined) => {
      if (resultado === undefined) return;
      this.crm.completarActividad(act.id, resultado)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: updated => {
            this.actividades.update(list =>
              list.map(a => a.id === updated.id ? { ...a, ...updated } : a)
            );
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

  getContextoRoute(act: CrmActividadAgenda): string[] {
    if (act.contexto_tipo === 'oportunidad') return ['/crm/oportunidades', act.oportunidad!];
    if (act.contexto_tipo === 'lead') return ['/crm/leads', act.lead!];
    return [];
  }

  private getInicioSemana(d: Date): Date {
    const day = d.getDay(); // 0=dom
    const diff = day === 0 ? -6 : 1 - day; // lunes
    const ini = new Date(d);
    ini.setDate(d.getDate() + diff);
    ini.setHours(0, 0, 0, 0);
    return ini;
  }

  private toDateStr(d: Date): string {
    return d.toISOString().split('T')[0];
  }

  private formatShort(d: Date): string {
    return d.toLocaleDateString('es-CO', { day: 'numeric', month: 'short' });
  }
}
