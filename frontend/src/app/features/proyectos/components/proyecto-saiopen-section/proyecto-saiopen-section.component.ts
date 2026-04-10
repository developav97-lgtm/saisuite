import {
  ChangeDetectionStrategy, Component, OnInit,
  inject, input, output, signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDialog } from '@angular/material/dialog';
import {
  ProyectoSaiopenService,
  ProyectoSaiopenDisponible,
} from '../../services/proyecto-saiopen.service';
import { DocumentoContableService } from '../../services/documento-contable.service';
import { ToastService } from '../../../../core/services/toast.service';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';

@Component({
  selector: 'app-proyecto-saiopen-section',
  templateUrl: './proyecto-saiopen-section.component.html',
  styleUrl: './proyecto-saiopen-section.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule, FormsModule,
    MatButtonModule, MatIconModule, MatFormFieldModule,
    MatSelectModule, MatProgressBarModule, MatTooltipModule,
  ],
})
export class ProyectoSaiopenSectionComponent implements OnInit {
  private readonly saiopenSvc = inject(ProyectoSaiopenService);
  private readonly docSvc     = inject(DocumentoContableService);
  private readonly toast      = inject(ToastService);
  private readonly dialog     = inject(MatDialog);

  readonly proyectoId          = input.required<string>();
  readonly saiopenProyectoId   = input<string | null>(null);
  readonly ultimaSincronizacion = input<string | null>(null);

  /** Emite el nuevo saiopen_proyecto_id (o null si se desvincula) */
  readonly vinculoChanged = output<string | null>();
  /** Emite cuando se sincronizaron documentos desde GL — para que el tab Documentos recargue */
  readonly docsSynced = output<void>();

  readonly disponibles      = signal<ProyectoSaiopenDisponible[]>([]);
  readonly selectedCodigo   = signal<string | null>(null);
  readonly loadingDisp      = signal(false);
  readonly vinculando       = signal(false);
  readonly syncingDocs      = signal(false);
  readonly syncingActs      = signal(false);

  ngOnInit(): void {
    if (!this.saiopenProyectoId()) {
      this.loadDisponibles();
    }
  }

  private loadDisponibles(): void {
    this.loadingDisp.set(true);
    this.saiopenSvc.getDisponibles().subscribe({
      next: (data) => { this.disponibles.set(data); this.loadingDisp.set(false); },
      error: () => { this.loadingDisp.set(false); },
    });
  }

  vincular(): void {
    const codigo = this.selectedCodigo();
    if (!codigo) return;
    this.vinculando.set(true);
    this.saiopenSvc.vincular(this.proyectoId(), codigo).subscribe({
      next: (res) => {
        this.vinculando.set(false);
        this.toast.success(`Proyecto vinculado a Saiopen (${res.saiopen_proyecto_id}).`);
        this.vinculoChanged.emit(res.saiopen_proyecto_id);
      },
      error: (err: { error?: { detail?: string } }) => {
        this.vinculando.set(false);
        this.toast.error(err.error?.detail ?? 'No se pudo vincular el proyecto.');
      },
    });
  }

  desvincular(): void {
    const ref = this.dialog.open(ConfirmDialogComponent, {
      data: {
        header: 'Desvincular de Saiopen',
        message: `¿Desvincular este proyecto de "${this.saiopenProyectoId()}"? Los documentos ya importados se conservan.`,
        acceptLabel: 'Desvincular',
        acceptColor: 'warn',
      },
      width: '400px',
    });
    ref.afterClosed().subscribe((confirmed: boolean) => {
      if (!confirmed) return;
      this.saiopenSvc.desvincular(this.proyectoId()).subscribe({
        next: () => {
          this.toast.success('Proyecto desvinculado de Saiopen.');
          this.vinculoChanged.emit(null);
          this.loadDisponibles();
        },
        error: () => this.toast.error('No se pudo desvincular el proyecto.'),
      });
    });
  }

  sincronizarDocumentos(): void {
    this.syncingDocs.set(true);
    this.docSvc.sync(this.proyectoId()).subscribe({
      next: (res) => {
        this.syncingDocs.set(false);
        this.toast.success(
          `Documentos: ${res.created} creados, ${res.updated} actualizados.` +
          (res.errors.length ? ` (${res.errors.length} errores)` : ''),
        );
        this.docsSynced.emit();
      },
      error: () => {
        this.syncingDocs.set(false);
        this.toast.error('Error al sincronizar documentos desde GL.');
      },
    });
  }

  sincronizarActividades(): void {
    this.syncingActs.set(true);
    this.saiopenSvc.syncActividades(this.proyectoId()).subscribe({
      next: (res) => {
        this.syncingActs.set(false);
        this.toast.success(`Actividades: ${res.created} creadas, ${res.updated} actualizadas.`);
      },
      error: () => {
        this.syncingActs.set(false);
        this.toast.error('Error al sincronizar actividades.');
      },
    });
  }

  formatDate(date: string | null): string {
    if (!date) return '—';
    return new Date(date).toLocaleString('es-CO', {
      dateStyle: 'medium', timeStyle: 'short',
    });
  }
}
