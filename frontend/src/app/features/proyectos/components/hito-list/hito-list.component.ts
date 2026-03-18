import {
  ChangeDetectionStrategy, Component, OnInit, TemplateRef, ViewChild,
  inject, input, signal, computed,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDialog, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatChipsModule } from '@angular/material/chips';
import { MatSnackBar } from '@angular/material/snack-bar';
import { HitoService } from '../../services/hito.service';
import { FaseService } from '../../services/fase.service';
import { Hito, HitoCreate } from '../../models/hito.model';
import { FaseList } from '../../models/fase.model';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';

@Component({
  selector: 'app-hito-list',
  templateUrl: './hito-list.component.html',
  styleUrl: './hito-list.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule, ReactiveFormsModule,
    MatTableModule, MatButtonModule, MatIconModule,
    MatFormFieldModule, MatInputModule, MatSelectModule,
    MatCheckboxModule, MatTooltipModule, MatDialogModule,
    MatProgressBarModule, MatChipsModule,
  ],
})
export class HitoListComponent implements OnInit {
  private readonly service     = inject(HitoService);
  private readonly faseService = inject(FaseService);
  private readonly fb          = inject(FormBuilder);
  private readonly dialog      = inject(MatDialog);
  private readonly snackBar    = inject(MatSnackBar);

  readonly proyectoId = input.required<string>();

  readonly hitos   = signal<Hito[]>([]);
  readonly fases   = signal<FaseList[]>([]);
  readonly loading = signal(false);

  readonly displayedColumns = [
    'nombre', 'fase_nombre', 'porcentaje_proyecto',
    'valor_facturar', 'facturable', 'estado_factura', 'acciones',
  ];

  /** Suma de porcentajes ya asignados */
  readonly porcentajeUsado = computed(() =>
    this.hitos().reduce((sum, h) => sum + parseFloat(h.porcentaje_proyecto || '0'), 0)
  );

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  @ViewChild('hitoFormTpl') hitoFormTemplate!: TemplateRef<any>;
  private dialogRef: MatDialogRef<unknown> | null = null;

  readonly form = this.fb.group({
    nombre:              ['', Validators.required],
    descripcion:         [''],
    fase:                [null as string | null],
    porcentaje_proyecto: [null as number | null, [Validators.required, Validators.min(0.01), Validators.max(100)]],
    valor_facturar:      [null as number | null, [Validators.required, Validators.min(0.01)]],
    facturable:          [true],
  });

  ngOnInit(): void {
    this.loadHitos();
    this.loadFases();
  }

  loadHitos(): void {
    this.loading.set(true);
    this.service.list(this.proyectoId()).subscribe({
      next: (data) => { this.hitos.set(data); this.loading.set(false); },
      error: () => { this.loading.set(false); },
    });
  }

  private loadFases(): void {
    this.faseService.listByProyecto(this.proyectoId()).subscribe({
      next: (fases) => this.fases.set(fases),
    });
  }

  abrirDialogNuevo(): void {
    this.form.reset({ facturable: true, fase: null });
    this.dialogRef = this.dialog.open(this.hitoFormTemplate, {
      width: '560px',
      disableClose: false,
    });
  }

  crearHito(): void {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    const val = this.form.getRawValue();

    const disponible = 100 - this.porcentajeUsado();
    if ((val.porcentaje_proyecto ?? 0) > disponible) {
      this.snackBar.open(
        `Solo hay ${disponible.toFixed(2)}% disponible para asignar.`,
        'Cerrar', { duration: 5000, panelClass: ['snack-error'] }
      );
      return;
    }

    const payload: HitoCreate = {
      nombre:              val.nombre!,
      descripcion:         val.descripcion ?? undefined,
      fase:                val.fase ?? null,
      porcentaje_proyecto: val.porcentaje_proyecto!.toString(),
      valor_facturar:      val.valor_facturar!.toString(),
      facturable:          val.facturable ?? true,
    };

    this.service.create(this.proyectoId(), payload).subscribe({
      next: () => {
        this.dialogRef?.close();
        this.loadHitos();
        this.snackBar.open('Hito creado correctamente.', 'Cerrar', {
          duration: 3000, panelClass: ['snack-success'],
        });
      },
      error: (err: { error?: unknown[] | { detail?: string } }) => {
        const e = err?.error;
        const msg = Array.isArray(e)
          ? String(e[0])
          : (e as { detail?: string })?.detail ?? 'Error al crear el hito.';
        this.snackBar.open(msg, 'Cerrar', { duration: 5000, panelClass: ['snack-error'] });
      },
    });
  }

  confirmarGenerarFactura(hito: Hito): void {
    if (hito.facturado) {
      this.snackBar.open('Este hito ya fue facturado.', 'Cerrar', { duration: 3000 });
      return;
    }
    const ref = this.dialog.open(ConfirmDialogComponent, {
      data: {
        header: 'Generar factura',
        message: `¿Confirmar la generación de factura para el hito "${hito.nombre}"?\n\nValor: ${this.formatCurrency(hito.valor_facturar)}`,
        acceptLabel: 'Generar factura',
        acceptColor: 'primary',
      },
      width: '420px',
    });
    ref.afterClosed().subscribe((confirmed: boolean) => {
      if (!confirmed) return;
      this.service.generarFactura(this.proyectoId(), hito.id).subscribe({
        next: (actualizado) => {
          this.hitos.update(list =>
            list.map(h => h.id === actualizado.id ? actualizado : h)
          );
          this.snackBar.open('Factura generada correctamente.', 'Cerrar', {
            duration: 3000, panelClass: ['snack-success'],
          });
        },
        error: (err: { error?: unknown[] | { detail?: string } }) => {
          const e = err?.error;
          const msg = Array.isArray(e)
            ? String(e[0])
            : (e as { detail?: string })?.detail ?? 'No se pudo generar la factura.';
          this.snackBar.open(msg, 'Cerrar', { duration: 5000, panelClass: ['snack-error'] });
        },
      });
    });
  }

  formatCurrency(value: string): string {
    const num = parseFloat(value);
    return isNaN(num)
      ? value
      : num.toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 });
  }

  formatDate(date: string | null): string {
    if (!date) return '—';
    return new Date(date.includes('T') ? date : date + 'T00:00:00').toLocaleDateString('es-CO');
  }
}
