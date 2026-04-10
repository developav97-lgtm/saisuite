/**
 * SaiSuite — CRM Oportunidad Form Page
 * Crear o editar una oportunidad.
 */
import {
  ChangeDetectionStrategy, Component, OnInit, OnDestroy,
  inject, signal, computed,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { provideNativeDateAdapter } from '@angular/material/core';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatCardModule } from '@angular/material/card';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { Subject, takeUntil, debounceTime, distinctUntilChanged, switchMap, of } from 'rxjs';

import { CrmService } from '../../services/crm.service';
import { CrmPipeline, CrmEtapa } from '../../models/crm.model';
import { TerceroService } from '../../../../core/services/tercero.service';
import { TerceroList } from '../../../../core/models/tercero.model';
import { ToastService } from '../../../../core/services/toast.service';
import { ScMoneyInputDirective } from '../../../../shared/directives';

@Component({
  selector: 'app-oportunidad-form-page',
  templateUrl: './oportunidad-form-page.component.html',
  styleUrl: './oportunidad-form-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  providers: [provideNativeDateAdapter()],
  imports: [
    CommonModule, RouterModule, ReactiveFormsModule,
    MatButtonModule, MatIconModule, MatFormFieldModule,
    MatInputModule, MatSelectModule, MatDatepickerModule,
    MatProgressBarModule, MatCardModule,
    MatAutocompleteModule, ScMoneyInputDirective,
  ],
})
export class OportunidadFormPageComponent implements OnInit, OnDestroy {
  private readonly crm      = inject(CrmService);
  private readonly terceros = inject(TerceroService);
  private readonly route    = inject(ActivatedRoute);
  private readonly router   = inject(Router);
  private readonly toast    = inject(ToastService);
  private readonly fb       = inject(FormBuilder);
  private readonly destroy$ = new Subject<void>();

  readonly pipelines        = signal<CrmPipeline[]>([]);
  readonly etapas           = signal<CrmEtapa[]>([]);
  readonly contactosSuger   = signal<TerceroList[]>([]);
  readonly loading          = signal(false);
  readonly saving           = signal(false);
  readonly editId           = signal<string | null>(null);

  private readonly contactoSearch$ = new Subject<string>();

  readonly form = this.fb.group({
    titulo:                ['', [Validators.required, Validators.minLength(3)]],
    pipeline:              ['', Validators.required],
    etapa:                 ['', Validators.required],
    contacto:              [null as string | null],
    contacto_search:       [''],
    valor_esperado:        ['0', [Validators.required, Validators.min(0)]],
    probabilidad:          ['10', [Validators.required, Validators.min(0), Validators.max(100)]],
    fecha_cierre_estimada: [null as Date | null],
  });

  get isEdit(): boolean { return !!this.editId(); }
  get pageTitle(): string { return this.isEdit ? 'Editar Oportunidad' : 'Nueva Oportunidad'; }

  ngOnInit(): void {
    this.crm.listPipelines().pipe(takeUntil(this.destroy$)).subscribe(pipelines => {
      this.pipelines.set(pipelines);
      const def = pipelines.find(p => p.es_default) ?? pipelines[0];
      if (def && !this.isEdit) {
        this.form.patchValue({ pipeline: def.id });
        this.onPipelineChange(def.id);
      }
    });

    // Autocomplete de contactos (terceros)
    this.contactoSearch$.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      switchMap(term => term.length >= 2
        ? this.terceros.listAll({ search: term })
        : of([])),
      takeUntil(this.destroy$),
    ).subscribe(list => this.contactosSuger.set(list));

    // Edición
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.editId.set(id);
      this.loading.set(true);
      this.crm.getOportunidad(id).pipe(takeUntil(this.destroy$)).subscribe({
        next: op => {
          this.form.patchValue({
            titulo:           op.titulo,
            pipeline:         op.pipeline,
            etapa:            op.etapa,
            contacto:         op.contacto,
            contacto_search:  op.contacto_nombre ?? '',
            valor_esperado:   op.valor_esperado,
            probabilidad:     op.probabilidad,
            fecha_cierre_estimada: op.fecha_cierre_estimada
              ? new Date(op.fecha_cierre_estimada) : null,
          });
          this.onPipelineChange(op.pipeline);
          this.loading.set(false);
        },
        error: () => {
          this.toast.error('Error cargando oportunidad');
          this.loading.set(false);
        },
      });
    }
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  onPipelineChange(pipelineId: string): void {
    const pipeline = this.pipelines().find(p => p.id === pipelineId);
    if (!pipeline) return;
    const etapas = pipeline.etapas.filter(e => !e.es_ganado && !e.es_perdido);
    this.etapas.set(etapas);
    // Si la etapa actual no pertenece a este pipeline, seleccionar la primera
    const etapaActual = this.form.value.etapa;
    if (!etapas.find(e => e.id === etapaActual) && etapas.length) {
      this.form.patchValue({ etapa: etapas[0].id });
    }
  }

  onContactoSearch(term: string): void {
    this.contactoSearch$.next(term);
    if (!term) this.form.patchValue({ contacto: null });
  }

  onContactoSelected(tercero: TerceroList): void {
    this.form.patchValue({
      contacto: tercero.id,
      contacto_search: tercero.nombre_completo,
    });
    this.contactosSuger.set([]);
  }

  save(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.saving.set(true);
    const val = this.form.value;
    const fechaCierre = val.fecha_cierre_estimada
      ? (val.fecha_cierre_estimada as Date).toISOString().split('T')[0]
      : null;

    const data = {
      titulo:                val.titulo!,
      pipeline:              val.pipeline!,
      etapa:                 val.etapa!,
      contacto:              val.contacto ?? null,
      valor_esperado:        val.valor_esperado!,
      probabilidad:          val.probabilidad!,
      fecha_cierre_estimada: fechaCierre,
    };

    const op$ = this.isEdit
      ? this.crm.updateOportunidad(this.editId()!, data)
      : this.crm.createOportunidad(data);

    op$.pipe(takeUntil(this.destroy$)).subscribe({
      next: op => {
        this.toast.success(this.isEdit ? 'Oportunidad actualizada' : 'Oportunidad creada');
        this.router.navigate(['/crm/oportunidades', op.id]);
      },
      error: (err) => {
        this.toast.error(err?.error?.detail ?? 'Error guardando oportunidad');
        this.saving.set(false);
      },
    });
  }

  cancel(): void {
    this.router.navigate(['/crm']);
  }
}
