import { ChangeDetectionStrategy, Component, OnInit, inject, signal, computed } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormControl, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar } from '@angular/material/snack-bar';
import { toSignal } from '@angular/core/rxjs-interop';
import { startWith, map } from 'rxjs/operators';
import { ProyectoService } from '../../services/proyecto.service';
import { ProyectoDetail, TipoProyecto, TIPO_LABELS } from '../../models/proyecto.model';
import { AdminService } from '../../../admin/services/admin.service';
import { AdminUser } from '../../../admin/models/admin.models';

interface SelectOption { label: string; value: string; }

@Component({
  selector: 'app-proyecto-form',
  templateUrl: './proyecto-form.component.html',
  styleUrl: './proyecto-form.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule, ReactiveFormsModule,
    MatButtonModule, MatFormFieldModule, MatInputModule,
    MatSelectModule, MatAutocompleteModule,
    MatDatepickerModule, MatNativeDateModule,
    MatCardModule, MatIconModule, MatProgressSpinnerModule,
  ],
})
export class ProyectoFormComponent implements OnInit {
  private readonly route           = inject(ActivatedRoute);
  private readonly router          = inject(Router);
  private readonly proyectoService = inject(ProyectoService);
  private readonly fb              = inject(FormBuilder);
  private readonly snackBar        = inject(MatSnackBar);

  private readonly adminService    = inject(AdminService);

  readonly editMode   = signal(false);
  readonly proyectoId = signal<string | null>(null);
  readonly saving     = signal(false);
  readonly usuarios   = signal<AdminUser[]>([]);

  // Controles de texto para el autocomplete (muestran el nombre, el form guarda el UUID)
  readonly gerenteSearch     = new FormControl('');
  readonly coordinadorSearch = new FormControl('');

  // Listas filtradas según lo que escribe el usuario
  private readonly gerenteInput$     = this.gerenteSearch.valueChanges.pipe(startWith(''));
  private readonly coordinadorInput$ = this.coordinadorSearch.valueChanges.pipe(startWith(''));

  readonly filteredGerentes     = toSignal(
    this.gerenteInput$.pipe(map(q => this._filter(q ?? ''))),
    { initialValue: [] as AdminUser[] },
  );
  readonly filteredCoordinadores = toSignal(
    this.coordinadorInput$.pipe(map(q => this._filter(q ?? ''))),
    { initialValue: [] as AdminUser[] },
  );

  private _filter(query: string): AdminUser[] {
    const q = query.toLowerCase();
    return this.usuarios().filter(u =>
      (u.full_name || u.email).toLowerCase().includes(q) || u.email.toLowerCase().includes(q),
    );
  }

  /** Muestra el nombre en el input tras seleccionar */
  displayUser = (userId: string | null): string => {
    if (!userId) return '';
    const u = this.usuarios().find(x => x.id === userId);
    return u ? (u.full_name || u.email) : userId;
  };

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
    // Cargar usuarios para los autocompletes de equipo
    this.adminService.listUsers().subscribe({
      next: (users) => {
        this.usuarios.set(users.filter(u => u.is_active));
        // Si ya hay valores en el form (modo edición que cargó antes), sincronizar el texto
        const gId = this.form.controls.gerente.value;
        const cId = this.form.controls.coordinador.value;
        if (gId) this.gerenteSearch.setValue(this.displayUser(gId), { emitEvent: false });
        if (cId) this.coordinadorSearch.setValue(this.displayUser(cId), { emitEvent: false });
      },
      error: () => { /* silencioso */ },
    });

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

  onGerenteSelected(userId: string): void {
    this.form.controls.gerente.setValue(userId);
  }

  onCoordinadorSelected(userId: string | null): void {
    this.form.controls.coordinador.setValue(userId);
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
