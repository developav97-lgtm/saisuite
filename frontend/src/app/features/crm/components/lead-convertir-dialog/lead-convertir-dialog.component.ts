/**
 * SaiSuite — Lead Convertir Dialog
 * Convierte un lead en oportunidad: selecciona pipeline/etapa, asignado y tercero.
 */
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { MatDialogModule, MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatDividerModule } from '@angular/material/divider';
import { MatIconModule } from '@angular/material/icon';

import { CrmService } from '../../services/crm.service';
import { CrmLead, CrmPipeline, CrmEtapa } from '../../models/crm.model';
import { ToastService } from '../../../../core/services/toast.service';
import { ScMoneyInputDirective } from '../../../../shared/directives';
import { AdminService } from '../../../../features/admin/services/admin.service';
import { AdminUser } from '../../../../features/admin/models/admin.models';

@Component({
  selector: 'app-lead-convertir-dialog',
  templateUrl: './lead-convertir-dialog.component.html',
  styleUrl: './lead-convertir-dialog.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule, ReactiveFormsModule, MatDialogModule,
    MatButtonModule, MatFormFieldModule, MatInputModule,
    MatSelectModule, MatProgressBarModule, ScMoneyInputDirective,
    MatCheckboxModule, MatDividerModule, MatIconModule,
  ],
})
export class LeadConvertirDialogComponent implements OnInit {
  private readonly crm       = inject(CrmService);
  private readonly adminSvc  = inject(AdminService);
  private readonly toast     = inject(ToastService);
  private readonly dialogRef = inject(MatDialogRef<LeadConvertirDialogComponent>);
  private readonly fb        = inject(FormBuilder);
  readonly lead              = inject<CrmLead>(MAT_DIALOG_DATA);

  readonly pipelines = signal<CrmPipeline[]>([]);
  readonly etapas    = signal<CrmEtapa[]>([]);
  readonly usuarios  = signal<AdminUser[]>([]);
  readonly loading   = signal(false);

  readonly form = this.fb.group({
    etapa_id:       ['', Validators.required],
    valor_esperado: ['0'],
    asignado_a_id:  [this.lead.asignado_a ?? null as string | null],
    crear_tercero:  [!!this.lead.nombre],
  });

  ngOnInit(): void {
    this.crm.listPipelines().subscribe({
      next: pipelines => {
        this.pipelines.set(pipelines);
        const def = pipelines.find(p => p.es_default) ?? pipelines[0];
        if (def) this.onPipelineChange(def.id);
      },
    });

    this.adminSvc.listUsers({ is_active: true, page_size: 100 }).subscribe({
      next: resp => this.usuarios.set(resp.results),
    });
  }

  onPipelineChange(pipelineId: string): void {
    const pipeline = this.pipelines().find(p => p.id === pipelineId);
    if (pipeline) {
      const etapasValidas = pipeline.etapas.filter(e => !e.es_ganado && !e.es_perdido);
      this.etapas.set(etapasValidas);
      if (etapasValidas.length) {
        this.form.patchValue({ etapa_id: etapasValidas[0].id });
      }
    }
  }

  convertir(): void {
    if (this.form.invalid) return;
    this.loading.set(true);
    const val = this.form.value;
    this.crm.convertirLead(this.lead.id, {
      etapa_id:       val.etapa_id!,
      valor_esperado: val.valor_esperado || '0',
      asignado_a_id:  val.asignado_a_id ?? undefined,
      crear_tercero:  val.crear_tercero ?? false,
    }).subscribe({
      next: oportunidad => {
        this.loading.set(false);
        this.dialogRef.close(oportunidad);
      },
      error: () => {
        this.toast.error('Error convirtiendo lead');
        this.loading.set(false);
      },
    });
  }
}
