/**
 * SaiSuite — CRM Lead Form Page
 * Crear o editar un lead.
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
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatCardModule } from '@angular/material/card';
import { Subject, takeUntil } from 'rxjs';

import { CrmService } from '../../services/crm.service';
import { CrmPipeline, FuenteLead } from '../../models/crm.model';
import { ToastService } from '../../../../core/services/toast.service';

@Component({
  selector: 'app-lead-form-page',
  templateUrl: './lead-form-page.component.html',
  styleUrl: './lead-form-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule, RouterModule, ReactiveFormsModule,
    MatButtonModule, MatIconModule, MatFormFieldModule,
    MatInputModule, MatSelectModule, MatProgressBarModule, MatCardModule,
  ],
})
export class LeadFormPageComponent implements OnInit, OnDestroy {
  private readonly crm    = inject(CrmService);
  private readonly route  = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly toast  = inject(ToastService);
  private readonly fb     = inject(FormBuilder);
  private readonly destroy$ = new Subject<void>();

  readonly pipelines = signal<CrmPipeline[]>([]);
  readonly loading   = signal(false);
  readonly saving    = signal(false);
  readonly editId    = signal<string | null>(null);

  readonly form = this.fb.group({
    nombre:   ['', [Validators.required, Validators.minLength(2)]],
    empresa:  [''],
    email:    ['', Validators.email],
    telefono: [''],
    cargo:    [''],
    fuente:   ['manual' as FuenteLead, Validators.required],
    pipeline: [null as string | null],
    notas:    [''],
  });

  readonly fuenteOpciones: { value: FuenteLead; label: string }[] = [
    { value: 'manual',   label: 'Manual' },
    { value: 'webhook',  label: 'Webhook' },
    { value: 'csv',      label: 'CSV/Excel' },
    { value: 'referido', label: 'Referido' },
    { value: 'otro',     label: 'Otro' },
  ];

  get isEdit(): boolean { return !!this.editId(); }
  get pageTitle(): string { return this.isEdit ? 'Editar Lead' : 'Nuevo Lead'; }

  ngOnInit(): void {
    this.crm.listPipelines().pipe(takeUntil(this.destroy$)).subscribe(p => this.pipelines.set(p));

    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.editId.set(id);
      this.loading.set(true);
      this.crm.getLead(id).pipe(takeUntil(this.destroy$)).subscribe({
        next: lead => {
          this.form.patchValue({
            nombre:   lead.nombre,
            empresa:  lead.empresa,
            email:    lead.email,
            telefono: lead.telefono,
            cargo:    lead.cargo,
            fuente:   lead.fuente,
            pipeline: lead.pipeline,
            notas:    lead.notas,
          });
          this.loading.set(false);
        },
        error: () => {
          this.toast.error('Error cargando lead');
          this.loading.set(false);
        },
      });
    }
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  save(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.saving.set(true);
    const val = this.form.value;
    const data = {
      nombre:   val.nombre!,
      empresa:  val.empresa ?? '',
      email:    val.email ?? '',
      telefono: val.telefono ?? '',
      cargo:    val.cargo ?? '',
      fuente:   val.fuente as FuenteLead,
      pipeline: val.pipeline ?? undefined,
      notas:    val.notas ?? '',
    };

    const op$ = this.isEdit
      ? this.crm.updateLead(this.editId()!, data)
      : this.crm.createLead(data);

    op$.pipe(takeUntil(this.destroy$)).subscribe({
      next: () => {
        this.toast.success(this.isEdit ? 'Lead actualizado' : 'Lead creado');
        this.router.navigate(['/crm/leads']);
      },
      error: () => {
        this.toast.error('Error guardando lead');
        this.saving.set(false);
      },
    });
  }

  cancel(): void {
    this.router.navigate(['/crm/leads']);
  }
}
