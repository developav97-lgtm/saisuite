import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBar } from '@angular/material/snack-bar';
import { ProyectoService } from '../../services/proyecto.service';
import { ProyectoDetail, TipoProyecto, TIPO_LABELS } from '../../models/proyecto.model';

interface SelectOption { label: string; value: string; }

@Component({
  selector: 'app-proyecto-form',
  templateUrl: './proyecto-form.component.html',
  styleUrl: './proyecto-form.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule, ReactiveFormsModule,
    MatButtonModule, MatFormFieldModule, MatInputModule,
    MatSelectModule, MatDatepickerModule, MatNativeDateModule,
    MatCardModule, MatIconModule,
  ],
})
export class ProyectoFormComponent implements OnInit {
  private readonly route           = inject(ActivatedRoute);
  private readonly router          = inject(Router);
  private readonly proyectoService = inject(ProyectoService);
  private readonly fb              = inject(FormBuilder);
  private readonly snackBar        = inject(MatSnackBar);

  readonly editMode   = signal(false);
  readonly proyectoId = signal<string | null>(null);
  readonly saving     = signal(false);

  readonly tipoOptions: SelectOption[] = Object.entries(TIPO_LABELS).map(([value, label]) => ({ label, value }));

  readonly form = this.fb.group({
    codigo:                   [''],
    nombre:                   ['', Validators.required],
    tipo:                     [null as TipoProyecto | null, Validators.required],
    cliente_id:               ['', Validators.required],
    cliente_nombre:           ['', Validators.required],
    gerente:                  ['', Validators.required],
    coordinador:              [null as string | null],
    fecha_inicio_planificada: [null as Date | null, Validators.required],
    fecha_fin_planificada:    [null as Date | null, Validators.required],
    presupuesto_total:        [0, [Validators.required, Validators.min(0)]],
    porcentaje_administracion:[10],
    porcentaje_imprevistos:   [5],
    porcentaje_utilidad:      [10],
  });

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) { this.editMode.set(true); this.proyectoId.set(id); this.loadProyecto(id); }
  }

  private loadProyecto(id: string): void {
    this.proyectoService.getById(id).subscribe({
      next: (p: ProyectoDetail) => {
        this.form.patchValue({
          codigo: p.codigo, nombre: p.nombre, tipo: p.tipo,
          cliente_id: p.cliente_id, cliente_nombre: p.cliente_nombre,
          gerente: p.gerente.id, coordinador: p.coordinador?.id || null,
          fecha_inicio_planificada: p.fecha_inicio_planificada ? new Date(p.fecha_inicio_planificada + 'T00:00:00') : null,
          fecha_fin_planificada:    p.fecha_fin_planificada    ? new Date(p.fecha_fin_planificada    + 'T00:00:00') : null,
          presupuesto_total: parseFloat(p.presupuesto_total),
          porcentaje_administracion: parseFloat(p.porcentaje_administracion),
          porcentaje_imprevistos:    parseFloat(p.porcentaje_imprevistos),
          porcentaje_utilidad:       parseFloat(p.porcentaje_utilidad),
        });
      },
      error: () => this.snackBar.open('No se pudo cargar el proyecto.', 'Cerrar', { duration: 4000, panelClass: ['snack-error'] }),
    });
  }

  guardar(): void {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    this.saving.set(true);
    const val = this.form.getRawValue();
    const payload = {
      codigo: val.codigo || undefined,
      nombre: val.nombre!, tipo: val.tipo!,
      cliente_id: val.cliente_id!, cliente_nombre: val.cliente_nombre!,
      gerente: val.gerente!, coordinador: val.coordinador || null,
      fecha_inicio_planificada: this.formatDate(val.fecha_inicio_planificada),
      fecha_fin_planificada:    this.formatDate(val.fecha_fin_planificada),
      presupuesto_total: val.presupuesto_total?.toString() ?? '0',
      porcentaje_administracion: val.porcentaje_administracion?.toString() ?? '10',
      porcentaje_imprevistos:    val.porcentaje_imprevistos?.toString() ?? '5',
      porcentaje_utilidad:       val.porcentaje_utilidad?.toString() ?? '10',
    };
    const id = this.proyectoId();
    const obs = id ? this.proyectoService.update(id, payload) : this.proyectoService.create(payload);
    obs.subscribe({
      next: (p) => {
        this.saving.set(false);
        this.snackBar.open(`Proyecto "${p.nombre}" ${id ? 'actualizado' : 'creado'}.`, 'Cerrar', { duration: 3000, panelClass: ['snack-success'] });
        setTimeout(() => this.router.navigate(['/proyectos', p.id]), 1000);
      },
      error: (err) => {
        this.saving.set(false);
        this.snackBar.open(this.extractError(err), 'Cerrar', { duration: 5000, panelClass: ['snack-error'] });
      },
    });
  }

  cancelar(): void {
    const id = this.proyectoId();
    if (id) this.router.navigate(['/proyectos', id]); else this.router.navigate(['/proyectos']);
  }

  private formatDate(date: Date | null | string): string {
    if (!date) return '';
    const d = date instanceof Date ? date : new Date(date);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  }

  private extractError(err: unknown): string {
    const e = err as { error?: unknown };
    if (typeof e.error === 'string') return e.error;
    if (Array.isArray(e.error)) return e.error[0] as string;
    if (typeof e.error === 'object' && e.error) {
      const vals = Object.values(e.error as Record<string, unknown>);
      const first = vals[0];
      if (Array.isArray(first)) return first[0] as string;
    }
    return 'Ocurrió un error inesperado.';
  }
}
