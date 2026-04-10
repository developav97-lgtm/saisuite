import {
  ChangeDetectionStrategy, Component, OnInit,
  computed, effect, inject, input, signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { DocumentoContableService } from '../../services/documento-contable.service';
import { FaseService } from '../../services/fase.service';
import { DocumentoContableList, DocumentoContableDetail, TIPO_DOCUMENTO_LABELS } from '../../models/documento-contable.model';
import { FaseList } from '../../models/fase.model';
import { DocumentoDetailDialogComponent } from './documento-detail-dialog/documento-detail-dialog.component';
import { AsientoContableDialogComponent } from './asiento-contable-dialog/asiento-contable-dialog.component';
import { ToastService } from '../../../../core/services/toast.service';

@Component({
  selector: 'app-documento-list',
  templateUrl: './documento-list.component.html',
  styleUrl: './documento-list.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule, FormsModule,
    MatTableModule, MatButtonModule, MatIconModule,
    MatFormFieldModule, MatSelectModule,
    MatProgressBarModule, MatTooltipModule, MatDialogModule,
    DocumentoDetailDialogComponent,
    AsientoContableDialogComponent,
  ],
})
export class DocumentoListComponent implements OnInit {
  private readonly service     = inject(DocumentoContableService);
  private readonly faseService = inject(FaseService);
  private readonly dialog      = inject(MatDialog);
  private readonly toast       = inject(ToastService);

  constructor() {
    // Recarga automática cuando el padre incrementa refreshTrigger (skip valor inicial 0)
    effect(() => {
      if (this.refreshTrigger() > 0) {
        this.loadDocumentos();
      }
    });
  }

  readonly proyectoId      = input.required<string>();
  /** Incrementar para forzar recarga (p.ej. tras sincronizar desde General tab) */
  readonly refreshTrigger  = input<number>(0);

  readonly documentos       = signal<DocumentoContableList[]>([]);
  readonly fases            = signal<FaseList[]>([]);
  readonly loading          = signal(false);
  readonly syncing          = signal(false);
  readonly faseSeleccionada = signal<string | null>(null);
  readonly tipoSeleccionado = signal<string | null>(null);

  /** Valores únicos de tipdoc_descripcion para el filtro */
  readonly tiposUnicos = computed<string[]>(() => {
    const set = new Set<string>();
    for (const d of this.documentos()) {
      if (d.tipdoc_descripcion) set.add(d.tipdoc_descripcion);
    }
    return Array.from(set).sort();
  });

  /** Documentos filtrados por tipo de documento Saiopen */
  readonly documentosFiltrados = computed(() => {
    const tipo = this.tipoSeleccionado();
    if (!tipo) return this.documentos();
    return this.documentos().filter(d => d.tipdoc_descripcion === tipo);
  });

  readonly displayedColumns = [
    'tipdoc_sigla', 'tipo_documento_display', 'numero_documento',
    'fecha_documento', 'tercero_nombre', 'valor_neto', 'acciones',
  ];

  readonly TIPO_DOCUMENTO_LABELS = TIPO_DOCUMENTO_LABELS;

  ngOnInit(): void {
    this.loadFases();
    this.loadDocumentos();
  }

  private loadFases(): void {
    this.faseService.listByProyecto(this.proyectoId()).subscribe({
      next: (fases) => this.fases.set(fases),
    });
  }

  loadDocumentos(): void {
    this.loading.set(true);
    this.service.list(this.proyectoId(), this.faseSeleccionada()).subscribe({
      next: (data) => { this.documentos.set(data); this.loading.set(false); },
      error: () => {
        this.toast.error('Error al cargar documentos.');
        this.loading.set(false);
      },
    });
  }

  onFaseChange(faseId: string | null): void {
    this.faseSeleccionada.set(faseId);
    this.loadDocumentos();
  }

  sincronizarDesdeGL(): void {
    this.syncing.set(true);
    this.service.sync(this.proyectoId()).subscribe({
      next: (res) => {
        this.syncing.set(false);
        this.toast.success(
          `Sincronizado: ${res.created} creados, ${res.updated} actualizados.` +
          (res.errors.length ? ` (${res.errors.length} errores)` : ''),
        );
        this.loadDocumentos();
      },
      error: () => {
        this.syncing.set(false);
        this.toast.error('Error al sincronizar documentos desde GL.');
      },
    });
  }

  verDetalle(doc: DocumentoContableList): void {
    this.service.getById(this.proyectoId(), doc.id).subscribe({
      next: (detalle: DocumentoContableDetail) => {
        this.dialog.open(DocumentoDetailDialogComponent, {
          data: detalle,
          width: '600px',
        });
      },
      error: () => {
        this.toast.error('No se pudo cargar el detalle.');
      },
    });
  }

  verAsiento(doc: DocumentoContableList): void {
    this.service.getLineas(this.proyectoId(), doc.id).subscribe({
      next: (lineas) => {
        this.dialog.open(AsientoContableDialogComponent, {
          data: { doc, lineas },
          width: '900px',
          maxWidth: '98vw',
        });
      },
      error: () => {
        this.toast.error('No se pudo cargar el asiento contable.');
      },
    });
  }

  formatCurrency(value: string): string {
    const num = parseFloat(value);
    return isNaN(num)
      ? value
      : num.toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 });
  }

  formatDate(date: string): string {
    return new Date(date + 'T00:00:00').toLocaleDateString('es-CO');
  }
}
