/**
 * SaiSuite — TareaFormComponent
 * Formulario crear/editar tarea con Angular Material.
 * En modo crear: recibe proyecto desde query param `?proyecto=<uuid>`.
 * En modo editar: carga la tarea por :id desde la ruta.
 *
 * Campos FK con mat-autocomplete:
 *   - proyecto   → ProyectoService.list({ search }) — server-side con debounce
 *   - fase       → FaseService.listByProyecto()     — client-side filter
 *   - tarea_padre→ TareaService.list({ proyecto })  — client-side filter
 *   - responsable→ AdminService.listUsers()         — client-side filter
 */
import {
  ChangeDetectionStrategy, ChangeDetectorRef, DestroyRef,
  Component, OnInit, inject, signal, computed,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Router, ActivatedRoute } from '@angular/router';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormControl, Validators } from '@angular/forms';
import { debounceTime, distinctUntilChanged, switchMap, startWith, map } from 'rxjs/operators';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatAutocompleteModule, MatAutocompleteSelectedEvent } from '@angular/material/autocomplete';
import { TareaService } from '../../services/tarea.service';
import { ProyectoService } from '../../services/proyecto.service';
import { FaseService } from '../../services/fase.service';
import { ActividadProyectoService } from '../../services/actividad-proyecto.service';
import { AdminService } from '../../../admin/services/admin.service';
import { AdminUser } from '../../../admin/models/admin.models';
import { TerceroService } from '../../../../core/services/tercero.service';
import { TerceroList } from '../../../../core/models/tercero.model';
import { ProyectoList } from '../../models/proyecto.model';
import { FaseList } from '../../models/fase.model';
import { ActividadProyecto } from '../../models/actividad.model';
import { ToastService } from '../../../../core/services/toast.service';
import { NavigationHistoryService } from '../../../../core/services/navigation-history.service';
import {
  Tarea, TareaEstado, TareaFrecuencia, TareaPrioridad,
  TareaCreateDTO, TareaUpdateDTO,
} from '../../models/tarea.model';

interface SelectOption<T> { label: string; value: T; }

@Component({
  selector: 'app-tarea-form',
  templateUrl: './tarea-form.component.html',
  styleUrl: './tarea-form.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule, ReactiveFormsModule,
    MatButtonModule, MatIconModule,
    MatFormFieldModule, MatInputModule, MatSelectModule,
    MatCheckboxModule,
    MatDatepickerModule, MatNativeDateModule,
    MatProgressSpinnerModule, MatTooltipModule,
    MatAutocompleteModule,
  ],
})
export class TareaFormComponent implements OnInit {
  private readonly route                  = inject(ActivatedRoute);
  private readonly router                 = inject(Router);
  private readonly tareaService           = inject(TareaService);
  private readonly proyectoService        = inject(ProyectoService);
  private readonly faseService            = inject(FaseService);
  private readonly actividadProyectoService = inject(ActividadProyectoService);
  private readonly adminService           = inject(AdminService);
  private readonly terceroService         = inject(TerceroService);
  private readonly fb                     = inject(FormBuilder);
  private readonly toast       = inject(ToastService);
  private readonly navHistory              = inject(NavigationHistoryService);
  private readonly cdr                    = inject(ChangeDetectorRef);
  private readonly destroyRef             = inject(DestroyRef);

  readonly editMode              = signal(false);
  readonly tareaId               = signal<string | null>(null);
  readonly saving                = signal(false);
  readonly esRecurrente          = signal(false);
  readonly loadingFases          = signal(false);
  readonly selectedActividadModo  = signal<'solo_estados' | 'timesheet' | 'cantidad' | null>(null);
  readonly selectedActividadUnidad = signal<string>('');

  private static readonly DIA_UNITS = new Set(['dia', 'día', 'dias', 'días', 'day', 'days']);
  readonly esActividadDias = computed(() =>
    TareaFormComponent.DIA_UNITS.has(this.selectedActividadUnidad().toLowerCase().trim()),
  );

  // ── Controles de búsqueda (NO parte del form group) ────────
  readonly proyectoSearch          = new FormControl('');
  readonly faseSearch              = new FormControl('');
  readonly actividadSaiopenSearch  = new FormControl('');
  readonly tareaPadreSearch        = new FormControl('');
  readonly responsableSearch       = new FormControl('');
  readonly clienteSearch           = new FormControl('');

  // ── Opciones de autocomplete (señales mutables) ─────────────
  readonly proyectoOptions          = signal<ProyectoList[]>([]);
  readonly fasesFiltradas           = signal<FaseList[]>([]);
  readonly actividadesFiltradas     = signal<ActividadProyecto[]>([]);
  readonly tareasPadreFiltradas     = signal<Tarea[]>([]);
  readonly responsablesFiltrados    = signal<AdminUser[]>([]);
  readonly clientesFiltrados        = signal<TerceroList[]>([]);

  // Catálogos completos (para filtrado client-side)
  private allFases:          FaseList[]          = [];
  private allActividades:    ActividadProyecto[]  = [];
  private allTareasPadre:    Tarea[]              = [];
  private allUsuarios:       AdminUser[]          = [];
  private allClientes:       TerceroList[]        = [];

  // ── Form group (guarda UUIDs) ───────────────────────────────
  readonly form = this.fb.group({
    nombre:                 ['', [Validators.required, Validators.maxLength(200)]],
    descripcion:            [''],
    proyecto:               [''],           // read-only, derivado de fase
    fase:                   ['', Validators.required],   // obligatoria (DEC-021)
    actividad_proyecto:     [null as string | null],     // catálogo interno
    cantidad_objetivo:      [0],
    cantidad_registrada:    [0],
    tarea_padre:            [null as string | null],
    cliente:                [null as string | null],
    responsable:            [null as string | null],
    prioridad:              [2 as TareaPrioridad],
    estado:                 ['todo' as TareaEstado],
    fecha_inicio:           [null as Date | null],
    fecha_fin:              [null as Date | null],
    fecha_limite:           [null as Date | null],
    horas_estimadas:        [0],
    porcentaje_completado:  [0],
    es_recurrente:          [false],
    frecuencia_recurrencia: [null as TareaFrecuencia | null],
  });

  readonly estadoOptions: SelectOption<TareaEstado>[] = [
    { label: 'Por Hacer',   value: 'todo' },
    { label: 'En Progreso', value: 'in_progress' },
    { label: 'En Revisión', value: 'in_review' },
    { label: 'Bloqueada',   value: 'blocked' },
  ];

  readonly prioridadOptions: SelectOption<TareaPrioridad>[] = [
    { label: 'Baja',    value: 1 },
    { label: 'Normal',  value: 2 },
    { label: 'Alta',    value: 3 },
    { label: 'Urgente', value: 4 },
  ];

  readonly frecuenciaOptions: SelectOption<TareaFrecuencia>[] = [
    { label: 'Diaria',   value: 'diaria' },
    { label: 'Semanal',  value: 'semanal' },
    { label: 'Mensual',  value: 'mensual' },
  ];

  ngOnInit(): void {
    this.initRecurrenciaListener();
    this.initProyectoSearch();
    this.initFaseFilter();
    this.initActividadSaiopenFilter();
    this.initTareaPadreFilter();
    this.initResponsableFilter();
    this.initClienteFilter();
    this.loadResponsables();
    this.loadClientes();

    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.editMode.set(true);
      this.tareaId.set(id);
      this.loadTarea(id);
    } else {
      const fid   = this.route.snapshot.queryParamMap.get('fase');
      const pid   = this.route.snapshot.queryParamMap.get('proyecto');
      const padre = this.route.snapshot.queryParamMap.get('padre');
      if (fid)   this.setFaseById(fid);
      else if (pid) this.setProyectoById(pid);
      if (padre) this.setTareaPadreById(padre);
    }
  }

  // ── Inicialización de reactive pipelines ────────────────────

  private initRecurrenciaListener(): void {
    this.form.controls.es_recurrente.valueChanges
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(val => {
        this.esRecurrente.set(!!val);
        const frecCtrl = this.form.controls.frecuencia_recurrencia;
        if (val) {
          frecCtrl.setValidators(Validators.required);
        } else {
          frecCtrl.clearValidators();
          frecCtrl.setValue(null);
        }
        frecCtrl.updateValueAndValidity();
      });
  }

  /** Búsqueda de proyectos server-side con debounce de 300ms. */
  private initProyectoSearch(): void {
    this.proyectoSearch.valueChanges.pipe(
      startWith(''),
      debounceTime(300),
      distinctUntilChanged(),
      switchMap(text =>
        this.proyectoService.list({ search: text ?? '', page_size: 20 }).pipe(
          map(r => r.results),
        )
      ),
      takeUntilDestroyed(this.destroyRef),
    ).subscribe(results => {
      this.proyectoOptions.set(results);
      this.cdr.markForCheck();
    });
  }

  private initFaseFilter(): void {
    this.faseSearch.valueChanges.pipe(
      startWith(''),
      takeUntilDestroyed(this.destroyRef),
    ).subscribe(texto => {
      const q = typeof texto === 'string' ? texto.toLowerCase() : '';
      this.fasesFiltradas.set(
        q ? this.allFases.filter(f => f.nombre.toLowerCase().includes(q)) : this.allFases
      );
      this.cdr.markForCheck();
    });
  }

  private initTareaPadreFilter(): void {
    this.tareaPadreSearch.valueChanges.pipe(
      startWith(''),
      takeUntilDestroyed(this.destroyRef),
    ).subscribe(texto => {
      const q = typeof texto === 'string' ? texto.toLowerCase() : '';
      this.tareasPadreFiltradas.set(
        q
          ? this.allTareasPadre.filter(t =>
              t.nombre.toLowerCase().includes(q) || t.codigo.toLowerCase().includes(q)
            )
          : this.allTareasPadre
      );
      this.cdr.markForCheck();
    });
  }

  private initResponsableFilter(): void {
    this.responsableSearch.valueChanges.pipe(
      startWith(''),
      takeUntilDestroyed(this.destroyRef),
    ).subscribe(texto => {
      const q = typeof texto === 'string' ? texto.toLowerCase() : '';
      this.responsablesFiltrados.set(
        q
          ? this.allUsuarios.filter(u =>
              u.full_name.toLowerCase().includes(q) || u.email.toLowerCase().includes(q)
            )
          : this.allUsuarios
      );
      this.cdr.markForCheck();
    });
  }

  private loadResponsables(): void {
    this.adminService.listUsers().subscribe(res => {
      const users = res.results;
      this.allUsuarios = users;
      this.responsablesFiltrados.set(users);
      this.cdr.markForCheck();
    });
  }

  private initActividadSaiopenFilter(): void {
    this.actividadSaiopenSearch.valueChanges.pipe(
      startWith(''),
      takeUntilDestroyed(this.destroyRef),
    ).subscribe(texto => {
      const q = typeof texto === 'string' ? texto.toLowerCase() : '';
      this.actividadesFiltradas.set(
        q
          ? this.allActividades.filter(a =>
              a.actividad_nombre.toLowerCase().includes(q) ||
              a.actividad_codigo.toLowerCase().includes(q)
            )
          : this.allActividades
      );
      this.cdr.markForCheck();
    });
  }

  private loadActividadesProyecto(proyectoId: string): void {
    this.actividadProyectoService.listByProyecto(proyectoId).subscribe({
      next: (acts) => {
        this.allActividades = acts;
        this.actividadesFiltradas.set(acts);
        this.cdr.markForCheck();
      },
      error: () => this.toast.error('No se pudieron cargar las actividades.'),
    });
  }

  private initClienteFilter(): void {
    this.clienteSearch.valueChanges.pipe(
      startWith(''),
      takeUntilDestroyed(this.destroyRef),
    ).subscribe(texto => {
      const q = typeof texto === 'string' ? texto.toLowerCase() : '';
      this.clientesFiltrados.set(
        q
          ? this.allClientes.filter(c =>
              c.nombre_completo.toLowerCase().includes(q) ||
              c.numero_identificacion.toLowerCase().includes(q)
            )
          : this.allClientes
      );
      this.cdr.markForCheck();
    });
  }

  private loadClientes(): void {
    this.terceroService.listAll({ tipo_tercero: 'cliente', activo: true }).subscribe(clientes => {
      this.allClientes = clientes;
      this.clientesFiltrados.set(clientes);
      this.cdr.markForCheck();
    });
  }

  // ── Helpers para query params en modo crear ─────────────────

  private setFaseById(faseId: string): void {
    this.faseService.getById(faseId).subscribe(f => {
      this.form.controls.fase.setValue(f.id);
      this.form.controls.proyecto.setValue(f.proyecto);
      this.faseSearch.setValue(f.nombre);
      this.faseSearch.disable();
      this.form.controls.fase.disable();
      this.loadFasesYTareas(f.proyecto);
      this.loadActividadesProyecto(f.proyecto);
      this.cdr.markForCheck();
    });
  }

  private setProyectoById(proyectoId: string): void {
    this.proyectoService.getById(proyectoId).subscribe(p => {
      this.form.controls.proyecto.setValue(p.id);
      this.form.controls.proyecto.disable();
      this.proyectoSearch.setValue(`${p.codigo} — ${p.nombre}`);
      this.proyectoSearch.disable();
      this.loadFasesYTareas(p.id);
      this.loadActividadesProyecto(p.id);
      this.cdr.markForCheck();
    });
  }

  private setTareaPadreById(tareaId: string): void {
    this.tareaService.getById(tareaId).subscribe(t => {
      this.form.controls.tarea_padre.setValue(t.id);
      this.tareaPadreSearch.setValue(`${t.codigo} — ${t.nombre}`);
      this.cdr.markForCheck();
    });
  }

  // ── Carga en modo edición ───────────────────────────────────

  private loadTarea(id: string): void {
    this.tareaService.getById(id).subscribe({
      next: (t) => {
        this.form.patchValue({
          nombre:                t.nombre,
          descripcion:           t.descripcion,
          proyecto:              t.proyecto,
          fase:                  t.fase,
          actividad_proyecto:    t.actividad_proyecto,
          cantidad_objetivo:     t.cantidad_objetivo,
          cantidad_registrada:   t.cantidad_registrada,
          tarea_padre:           t.tarea_padre,
          cliente:               t.cliente,
          responsable:           t.responsable,
          prioridad:             t.prioridad,
          estado:                t.estado as TareaEstado,
          horas_estimadas:       t.horas_estimadas,
          porcentaje_completado: t.porcentaje_completado,
          es_recurrente:         t.es_recurrente,
          frecuencia_recurrencia: t.frecuencia_recurrencia,
          fecha_inicio:  t.fecha_inicio  ? new Date(t.fecha_inicio  + 'T00:00:00') : null,
          fecha_fin:     t.fecha_fin     ? new Date(t.fecha_fin     + 'T00:00:00') : null,
          fecha_limite:  t.fecha_limite  ? new Date(t.fecha_limite  + 'T00:00:00') : null,
        });
        this.form.controls.proyecto.disable();

        // Poblar autocompletes con los detalles que trae la tarea
        if (t.proyecto_detail) {
          this.proyectoSearch.setValue(`${t.proyecto_detail.codigo} — ${t.proyecto_detail.nombre}`);
          this.proyectoSearch.disable();
          this.loadFasesYTareas(t.proyecto);
          this.loadActividadesProyecto(t.proyecto);
        }
        if (t.fase_detail) {
          this.faseSearch.setValue(t.fase_detail.nombre);
        }
        if (t.actividad_proyecto_detail) {
          this.actividadSaiopenSearch.setValue(
            `${t.actividad_proyecto_detail.actividad_codigo} — ${t.actividad_proyecto_detail.actividad_nombre}`
          );
          this.selectedActividadModo.set(
            this.resolverModo(t.actividad_proyecto_detail.actividad_unidad_medida)
          );
          this.selectedActividadUnidad.set(t.actividad_proyecto_detail.actividad_unidad_medida ?? '');
        }
        if (t.responsable_detail) {
          this.responsableSearch.setValue(
            `${t.responsable_detail.nombre} (${t.responsable_detail.email})`
          );
        }
        if (t.cliente_detail) {
          this.clienteSearch.setValue(t.cliente_detail.nombre, { emitEvent: false });
        }
        if (t.tarea_padre) {
          this.tareaService.getById(t.tarea_padre).subscribe(padre => {
            this.tareaPadreSearch.setValue(`${padre.codigo} — ${padre.nombre}`);
            this.cdr.markForCheck();
          });
        }

        this.cdr.markForCheck();
      },
      error: () => this.toast.error('No se pudo cargar la tarea.'),
    });
  }

  private loadFasesYTareas(proyectoId: string): void {
    this.loadingFases.set(true);

    this.faseService.listByProyecto(proyectoId).subscribe(fases => {
      this.allFases = fases;
      this.fasesFiltradas.set(fases);
      this.loadingFases.set(false);
      this.cdr.markForCheck();
    });

    this.tareaService.list({ proyecto: proyectoId, solo_raiz: true }).subscribe(tareas => {
      const idActual = this.tareaId();
      this.allTareasPadre = idActual ? tareas.filter(t => t.id !== idActual) : tareas;
      this.tareasPadreFiltradas.set(this.allTareasPadre);
      this.cdr.markForCheck();
    });
  }

  // ── Eventos de selección en autocomplete ────────────────────

  onProyectoSelected(event: MatAutocompleteSelectedEvent): void {
    const proyecto = event.option.value as ProyectoList;
    this.form.controls.proyecto.setValue(proyecto.id);
    // Al cambiar proyecto, limpiar dependientes
    this.form.controls.fase.setValue(null);
    this.form.controls.tarea_padre.setValue(null);
    this.form.controls.actividad_proyecto.setValue(null);
    this.faseSearch.setValue('');
    this.tareaPadreSearch.setValue('');
    this.actividadSaiopenSearch.setValue('');
    this.allFases = [];
    this.allTareasPadre = [];
    this.allActividades = [];
    this.fasesFiltradas.set([]);
    this.tareasPadreFiltradas.set([]);
    this.actividadesFiltradas.set([]);
    this.selectedActividadModo.set(null);
    this.selectedActividadUnidad.set('');
    this.loadFasesYTareas(proyecto.id);
    this.loadActividadesProyecto(proyecto.id);
  }

  onFaseSelected(event: MatAutocompleteSelectedEvent): void {
    const fase = event.option.value as FaseList;
    this.form.controls.fase.setValue(fase.id);
    // Cuando cambia la fase, cargar sus tareas hermanas para tarea_padre
    const proyectoId = this.form.controls.proyecto.value;
    if (proyectoId) this.loadFasesYTareas(proyectoId);
  }

  onActividadSaiopenSelected(event: MatAutocompleteSelectedEvent): void {
    const act = event.option.value as ActividadProyecto;
    this.form.controls.actividad_proyecto.setValue(act.id);
    this.selectedActividadModo.set(this.resolverModo(act.actividad_unidad_medida));
    this.selectedActividadUnidad.set(act.actividad_unidad_medida ?? '');
  }

  onActividadSaiopenBlur(): void {
    const v = this.actividadSaiopenSearch.value;
    if (typeof v === 'string' && !v.trim()) {
      this.form.controls.actividad_proyecto.setValue(null);
      this.selectedActividadModo.set(null);
      this.selectedActividadUnidad.set('');
    }
  }

  private resolverModo(um: string | null | undefined): 'solo_estados' | 'timesheet' | 'cantidad' {
    const u = (um ?? '').toLowerCase().trim();
    if (u === 'hora' || u === 'horas') return 'timesheet';
    if (TareaFormComponent.DIA_UNITS.has(u)) return 'timesheet';
    if (u) return 'cantidad';
    return 'solo_estados';
  }

  onTareaPadreSelected(event: MatAutocompleteSelectedEvent): void {
    const tarea = event.option.value as Tarea;
    this.form.controls.tarea_padre.setValue(tarea.id);
  }

  onResponsableSelected(event: MatAutocompleteSelectedEvent): void {
    const user = event.option.value as AdminUser;
    this.form.controls.responsable.setValue(user.id);
  }

  onClienteSelected(event: MatAutocompleteSelectedEvent): void {
    const cliente = event.option.value as TerceroList;
    this.form.controls.cliente.setValue(cliente.id);
  }

  onClienteBlur(): void {
    const v = this.clienteSearch.value;
    // Si el valor es string vacío (usuario borró el texto), limpiamos la FK
    if (typeof v === 'string' && !v.trim()) {
      this.form.controls.cliente.setValue(null);
    }
  }

  onFaseBlur(): void {
    const v = this.faseSearch.value;
    if (typeof v === 'string' && !v.trim()) {
      this.form.controls.fase.setValue(null);
    }
  }

  onTareaPadreBlur(): void {
    const v = this.tareaPadreSearch.value;
    if (typeof v === 'string' && !v.trim()) {
      this.form.controls.tarea_padre.setValue(null);
    }
  }

  onResponsableBlur(): void {
    const v = this.responsableSearch.value;
    if (typeof v === 'string' && !v.trim()) {
      this.form.controls.responsable.setValue(null);
    }
  }

  // ── displayWith para mat-autocomplete ──────────────────────

  displayProyecto = (p: ProyectoList | string | null): string => {
    if (!p) return '';
    if (typeof p === 'string') return p;
    return `${p.codigo} — ${p.nombre}`;
  };

  displayFase = (f: FaseList | string | null): string => {
    if (!f) return '';
    if (typeof f === 'string') return f;
    return f.nombre;
  };

  displayTarea = (t: Tarea | string | null): string => {
    if (!t) return '';
    if (typeof t === 'string') return t;
    return `${t.codigo} — ${t.nombre}`;
  };

  displayUsuario = (u: AdminUser | string | null): string => {
    if (!u) return '';
    if (typeof u === 'string') return u;
    return `${u.full_name} (${u.email})`;
  };

  displayCliente = (c: TerceroList | string | null): string => {
    if (!c) return '';
    if (typeof c === 'string') return c;
    return c.nombre_completo;
  };

  displayActividad = (a: ActividadProyecto | string | null): string => {
    if (!a) return '';
    if (typeof a === 'string') return a;
    return `${a.actividad_codigo} — ${a.actividad_nombre}`;
  };

  // ── Guardar ─────────────────────────────────────────────────

  guardar(): void {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    this.saving.set(true);
    const val = this.form.getRawValue();

    const payload: TareaCreateDTO = {
      nombre:                val.nombre!,
      descripcion:           val.descripcion ?? '',
      fase:                  val.fase!,            // obligatoria (DEC-021)
      actividad_proyecto:    val.actividad_proyecto || null,
      cantidad_objetivo:     val.cantidad_objetivo ?? 0,
      cantidad_registrada:   val.cantidad_registrada ?? 0,
      tarea_padre:           val.tarea_padre || null,
      cliente:               val.cliente || null,
      responsable:           val.responsable || null,
      prioridad:             val.prioridad as TareaPrioridad,
      estado:                val.estado as Exclude<TareaEstado, 'completed' | 'cancelled'>,
      horas_estimadas:       val.horas_estimadas ?? 0,
      porcentaje_completado: val.porcentaje_completado ?? 0,
      es_recurrente:         val.es_recurrente ?? false,
      frecuencia_recurrencia: val.frecuencia_recurrencia || null,
      fecha_inicio:  this.formatDate(val.fecha_inicio),
      fecha_fin:     this.formatDate(val.fecha_fin),
      fecha_limite:  this.formatDate(val.fecha_limite),
    };

    const id = this.tareaId();
    const obs = id
      ? this.tareaService.update(id, payload as TareaUpdateDTO)
      : this.tareaService.create(payload);

    obs.subscribe({
      next: (t) => {
        this.saving.set(false);
        const accion = id ? 'actualizada' : 'creada';
        this.toast.success(`Tarea "${t.nombre}" ${accion} correctamente.`);
        setTimeout(() => this.volverATareas(), 800);
      },
      error: (err: { error?: unknown }) => {
        this.saving.set(false);
        this.toast.error(this.extractError(err));
        this.cdr.markForCheck();
      },
    });
  }

  cancelar(): void {
    this.volverATareas();
  }

  private volverATareas(): void {
    if (this.navHistory.canGoBack) {
      this.navHistory.goBack('/proyectos/tareas');
      return;
    }
    const returnTo = this.route.snapshot.queryParamMap.get('returnTo');
    if (returnTo?.startsWith('proyecto:')) {
      const parts = returnTo.split(':');
      const proyectoId = parts[1];
      const tabIndex   = parts[3] ? parseInt(parts[3], 10) : null;
      const queryParams = tabIndex !== null && !isNaN(tabIndex) ? { tab: tabIndex } : {};
      this.router.navigate(['/proyectos', proyectoId], { queryParams });
      return;
    }
    const view = localStorage.getItem('saisuite.tareasView') ?? 'kanban';
    if (view === 'kanban') {
      this.router.navigate(['/proyectos/tareas/kanban']);
    } else {
      this.router.navigate(['/proyectos/tareas']);
    }
  }

  private formatDate(date: Date | null): string | null {
    if (!date) return null;
    const d = date instanceof Date ? date : new Date(date);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  }

  private extractError(err: { error?: unknown }): string {
    const e = err.error;
    if (typeof e === 'string') return e;
    if (Array.isArray(e)) return String(e[0]);
    if (e && typeof e === 'object') {
      const vals = Object.values(e as Record<string, unknown>);
      const first = vals[0];
      if (Array.isArray(first)) return String(first[0]);
    }
    return 'Ocurrió un error inesperado.';
  }
}
