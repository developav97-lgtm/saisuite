/**
 * SaiSuite — CreateFromTemplateDialogComponent
 * Dialog de 2 pasos: seleccionar plantilla → configurar proyecto.
 */
import {
  ChangeDetectionStrategy,
  Component,
  computed,
  inject,
  OnInit,
  signal,
} from '@angular/core';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { provideNativeDateAdapter } from '@angular/material/core';
import { ProyectoService } from '../../services/proyecto.service';
import { PlantillaProyecto } from '../../models/proyecto.model';
import { ToastService } from '../../../../core/services/toast.service';

@Component({
  selector: 'app-create-from-template-dialog',
  templateUrl: './create-from-template-dialog.component.html',
  styleUrl: './create-from-template-dialog.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  providers: [provideNativeDateAdapter()],
  imports: [
    ReactiveFormsModule,
    MatDialogModule,
    MatButtonModule,
    MatIconModule,
    MatProgressBarModule,
    MatFormFieldModule,
    MatInputModule,
    MatDatepickerModule,
  ],
})
export class CreateFromTemplateDialogComponent implements OnInit {
  private readonly proyectoService = inject(ProyectoService);
  private readonly toast           = inject(ToastService);
  private readonly fb              = inject(FormBuilder);
  readonly dialogRef               = inject(MatDialogRef<CreateFromTemplateDialogComponent>);

  readonly templates        = signal<PlantillaProyecto[]>([]);
  readonly selectedTemplate = signal<PlantillaProyecto | null>(null);
  readonly loading          = signal(false);
  readonly step             = signal<1 | 2>(1);

  readonly form = this.fb.group({
    nombre:       ['', [Validators.required, Validators.maxLength(200)]],
    descripcion:  [''],
    planned_start: ['', Validators.required],
  });

  readonly hasTemplates = computed(() => this.templates().length > 0);

  ngOnInit(): void {
    this.loading.set(true);
    this.proyectoService.getTemplates().subscribe({
      next: (list) => { this.templates.set(list); this.loading.set(false); },
      error: () => {
        this.toast.error('No se pudieron cargar las plantillas.');
        this.loading.set(false);
      },
    });
  }

  selectTemplate(t: PlantillaProyecto): void {
    this.selectedTemplate.set(t);
    this.step.set(2);
  }

  goBack(): void {
    this.selectedTemplate.set(null);
    this.step.set(1);
  }

  createProject(): void {
    if (this.form.invalid) return;
    const template = this.selectedTemplate();
    if (!template) return;

    const raw = this.form.getRawValue();
    this.loading.set(true);

    // El datepicker devuelve un Date — convertir a YYYY-MM-DD en hora local
    const dateVal = raw.planned_start as unknown as Date | string;
    let planned_start: string;
    if (dateVal instanceof Date) {
      const y = dateVal.getFullYear();
      const m = String(dateVal.getMonth() + 1).padStart(2, '0');
      const d = String(dateVal.getDate()).padStart(2, '0');
      planned_start = `${y}-${m}-${d}`;
    } else {
      planned_start = raw.planned_start ?? '';
    }

    this.proyectoService.createFromTemplate({
      template_id:   template.id,
      nombre:        raw.nombre!,
      descripcion:   raw.descripcion ?? undefined,
      planned_start,
    }).subscribe({
      next: (proyecto) => {
        this.loading.set(false);
        this.toast.success(`Proyecto "${proyecto.nombre}" creado desde plantilla.`);
        this.dialogRef.close(proyecto);
      },
      error: () => {
        this.toast.error('No se pudo crear el proyecto desde la plantilla.');
        this.loading.set(false);
      },
    });
  }

  cancel(): void {
    this.dialogRef.close(null);
  }
}
