import {
  ChangeDetectionStrategy, Component, ElementRef, OnInit,
  ViewChild, computed, inject, signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatTableModule } from '@angular/material/table';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatChipsModule } from '@angular/material/chips';
import { MatDividerModule } from '@angular/material/divider';
import { MatCardModule } from '@angular/material/card';
import { KnowledgeBaseService } from '../services/knowledge-base.service';
import { ToastService } from '../../../core/services/toast.service';
import { ConfirmDialogComponent } from '../../../shared/components/confirm-dialog/confirm-dialog.component';
import { AuthService } from '../../../core/auth/auth.service';
import { KnowledgeSource } from '../models/admin.models';

const MODULE_OPTIONS = [
  { value: 'general',       label: 'General' },
  { value: 'dashboard',     label: 'SaiDashboard' },
  { value: 'proyectos',     label: 'Proyectos' },
  { value: 'terceros',      label: 'Terceros' },
  { value: 'contabilidad',  label: 'Contabilidad' },
];

const CATEGORY_OPTIONS = [
  { value: 'manual',  label: 'Manual' },
  { value: 'norma',   label: 'Norma' },
  { value: 'faq',     label: 'FAQ' },
  { value: 'guia',    label: 'Guía' },
  { value: 'custom',  label: 'Custom' },
];

const MODULE_LABELS: Record<string, string | undefined> = {
  general:      'General',
  dashboard:    'SaiDashboard',
  proyectos:    'Proyectos',
  terceros:     'Terceros',
  contabilidad: 'Contabilidad',
};

const CATEGORY_LABELS: Record<string, string | undefined> = {
  manual: 'Manual',
  norma:  'Norma',
  faq:    'FAQ',
  guia:   'Guía',
  custom: 'Custom',
};

const CHANNEL_LABELS: Record<string, string | undefined> = {
  drive:  'Google Drive',
  upload: 'Panel Admin',
  cli:    'CLI',
};

@Component({
  selector: 'app-knowledge-base',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule, ReactiveFormsModule,
    MatButtonModule, MatIconModule, MatInputModule, MatFormFieldModule,
    MatSelectModule, MatTableModule, MatTooltipModule, MatProgressBarModule,
    MatDialogModule, MatChipsModule, MatDividerModule, MatCardModule,
  ],
  template: `
    <div class="kb-container">
      <!-- Header -->
      <div class="kb-header">
        <div class="kb-header__title">
          <mat-icon>auto_awesome</mat-icon>
          <div>
            <h2>Base de Conocimiento IA</h2>
            <p class="kb-header__sub">Documentos indexados que usa SaiBot para responder preguntas</p>
          </div>
        </div>
        @if (isSuperAdmin()) {
          <button mat-stroked-button
                  [disabled]="reindexing()"
                  (click)="reindex()"
                  matTooltip="Re-indexa todos los archivos de docs/">
            <mat-icon>refresh</mat-icon>
            {{ reindexing() ? 'Re-indexando...' : 'Re-indexar todo' }}
          </button>
        }
      </div>

      <mat-divider />

      <!-- Upload Card -->
      <mat-card class="kb-upload-card">
        <mat-card-header>
          <mat-icon mat-card-avatar>upload_file</mat-icon>
          <mat-card-title>Subir nuevo documento</mat-card-title>
          <mat-card-subtitle>PDF, Word, Markdown o TXT — máx. 10 MB</mat-card-subtitle>
        </mat-card-header>

        <mat-card-content>
          <div class="kb-upload-form" [formGroup]="uploadForm">
            <!-- Selector de archivo -->
            <div class="kb-file-row">
              <input #fileInput type="file"
                     accept=".pdf,.docx,.md,.txt"
                     style="display:none"
                     (change)="onFileSelected($event)" />
              <button mat-stroked-button type="button" (click)="fileInput.click()">
                <mat-icon>attach_file</mat-icon>
                {{ selectedFile() ? selectedFile()!.name : 'Seleccionar archivo' }}
              </button>
              @if (selectedFile()) {
                <mat-chip>{{ (selectedFile()!.size / 1024).toFixed(0) }} KB</mat-chip>
              }
            </div>

            <!-- Módulo y Categoría -->
            <mat-form-field appearance="outline" class="kb-select">
              <mat-label>Módulo</mat-label>
              <mat-select formControlName="module">
                @for (opt of MODULE_OPTIONS; track opt.value) {
                  <mat-option [value]="opt.value">{{ opt.label }}</mat-option>
                }
              </mat-select>
            </mat-form-field>

            <mat-form-field appearance="outline" class="kb-select">
              <mat-label>Categoría</mat-label>
              <mat-select formControlName="category">
                @for (opt of CATEGORY_OPTIONS; track opt.value) {
                  <mat-option [value]="opt.value">{{ opt.label }}</mat-option>
                }
              </mat-select>
            </mat-form-field>
          </div>
        </mat-card-content>

        <mat-card-actions align="end">
          <button mat-raised-button color="primary"
                  [disabled]="!selectedFile() || uploadForm.invalid || uploading()"
                  (click)="upload()">
            <mat-icon>cloud_upload</mat-icon>
            {{ uploading() ? 'Subiendo...' : 'Indexar documento' }}
          </button>
        </mat-card-actions>

        @if (uploading()) {
          <mat-progress-bar mode="indeterminate" />
        }
      </mat-card>

      <!-- Table -->
      <div class="kb-table-section">
        <h3>Fuentes indexadas ({{ sources().length }})</h3>

        @if (loading()) {
          <mat-progress-bar mode="indeterminate" />
        }

        @if (!loading() && sources().length === 0) {
          <div class="kb-empty">
            <mat-icon>inbox</mat-icon>
            <p>No hay documentos indexados aún.</p>
            <p class="kb-empty__sub">Sube un archivo arriba o ejecuta el comando de re-indexación.</p>
          </div>
        }

        @if (sources().length > 0) {
          <div class="table-responsive">
            <table mat-table [dataSource]="sources()" class="kb-table">

              <!-- Archivo -->
              <ng-container matColumnDef="file_name">
                <th mat-header-cell *matHeaderCellDef>Archivo</th>
                <td mat-cell *matCellDef="let s">
                  <div class="kb-file-cell">
                    <mat-icon class="kb-file-icon">{{ formatIcon(s.original_format) }}</mat-icon>
                    <span class="kb-file-name">{{ s.file_name }}</span>
                    <mat-chip class="kb-channel-chip">{{ CHANNEL_LABELS[s.source_channel] ?? s.source_channel }}</mat-chip>
                  </div>
                </td>
              </ng-container>

              <!-- Módulo -->
              <ng-container matColumnDef="module">
                <th mat-header-cell *matHeaderCellDef>Módulo</th>
                <td mat-cell *matCellDef="let s">{{ MODULE_LABELS[s.module] ?? s.module }}</td>
              </ng-container>

              <!-- Categoría -->
              <ng-container matColumnDef="category">
                <th mat-header-cell *matHeaderCellDef>Categoría</th>
                <td mat-cell *matCellDef="let s">{{ CATEGORY_LABELS[s.category] ?? s.category }}</td>
              </ng-container>

              <!-- Chunks -->
              <ng-container matColumnDef="chunks">
                <th mat-header-cell *matHeaderCellDef class="col-num">Chunks</th>
                <td mat-cell *matCellDef="let s" class="col-num">{{ s.chunk_count }}</td>
              </ng-container>

              <!-- Tokens -->
              <ng-container matColumnDef="tokens">
                <th mat-header-cell *matHeaderCellDef class="col-num">Tokens</th>
                <td mat-cell *matCellDef="let s" class="col-num">{{ s.total_tokens | number }}</td>
              </ng-container>

              <!-- Última indexación -->
              <ng-container matColumnDef="indexed_at">
                <th mat-header-cell *matHeaderCellDef>Indexado</th>
                <td mat-cell *matCellDef="let s">{{ s.last_indexed_at | date:'dd/MM/yyyy HH:mm' }}</td>
              </ng-container>

              <!-- Acciones -->
              <ng-container matColumnDef="actions">
                <th mat-header-cell *matHeaderCellDef></th>
                <td mat-cell *matCellDef="let s">
                  <button mat-icon-button color="warn"
                          matTooltip="Eliminar fuente y sus chunks"
                          (click)="confirmDelete(s)">
                    <mat-icon>delete_outline</mat-icon>
                  </button>
                </td>
              </ng-container>

              <tr mat-header-row *matHeaderRowDef="displayedColumns"></tr>
              <tr mat-row *matRowDef="let row; columns: displayedColumns;"></tr>
            </table>
          </div>
        }
      </div>
    </div>
  `,
  styles: [`
    .kb-container {
      padding: 24px;
      max-width: 1100px;
    }

    .kb-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 20px;
      flex-wrap: wrap;
      gap: 12px;
    }

    .kb-header__title {
      display: flex;
      align-items: center;
      gap: 12px;

      mat-icon {
        font-size: 32px;
        width: 32px;
        height: 32px;
        color: var(--sc-primary);
      }

      h2 {
        margin: 0;
        font-size: 1.4rem;
        font-weight: 600;
      }
    }

    .kb-header__sub {
      margin: 4px 0 0;
      font-size: 0.85rem;
      color: var(--sc-text-muted);
    }

    mat-divider {
      margin-bottom: 24px;
    }

    .kb-upload-card {
      margin-bottom: 32px;
    }

    .kb-upload-form {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
      padding-top: 8px;
    }

    .kb-file-row {
      display: flex;
      align-items: center;
      gap: 8px;
      flex: 1;
      min-width: 200px;
    }

    .kb-select {
      width: 160px;
    }

    .kb-table-section {
      h3 {
        margin: 0 0 12px;
        font-size: 1rem;
        font-weight: 500;
        color: var(--sc-text-muted);
      }
    }

    .table-responsive {
      display: block;
      width: 100%;
      overflow-x: auto;
      -webkit-overflow-scrolling: touch;
    }

    .kb-table {
      width: 100%;
      min-width: 700px;
    }

    .kb-file-cell {
      display: flex;
      align-items: center;
      gap: 8px;
      max-width: 320px;
    }

    .kb-file-icon {
      font-size: 18px;
      width: 18px;
      height: 18px;
      flex-shrink: 0;
      color: var(--sc-text-muted);
    }

    .kb-file-name {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .kb-channel-chip {
      font-size: 11px;
      height: 20px;
      flex-shrink: 0;
    }

    .col-num {
      text-align: right;
    }

    .kb-empty {
      text-align: center;
      padding: 48px 24px;
      color: var(--sc-text-muted);

      mat-icon {
        font-size: 48px;
        width: 48px;
        height: 48px;
        margin-bottom: 12px;
        opacity: 0.4;
      }

      p {
        margin: 4px 0;
      }
    }

    .kb-empty__sub {
      font-size: 0.85rem;
      opacity: 0.7;
    }

    @media (max-width: 768px) {
      .kb-container {
        padding: 16px;
      }

      .kb-upload-form {
        flex-direction: column;
        align-items: stretch;
      }

      .kb-select {
        width: 100%;
      }

      button, .mat-icon-button {
        min-height: 44px;
      }
    }
  `],
})
export class KnowledgeBaseComponent implements OnInit {
  @ViewChild('fileInput') private fileInput!: ElementRef<HTMLInputElement>;

  private readonly kbService = inject(KnowledgeBaseService);
  private readonly toast     = inject(ToastService);
  private readonly dialog    = inject(MatDialog);
  private readonly auth      = inject(AuthService);
  private readonly fb        = inject(FormBuilder);

  readonly loading    = signal(false);
  readonly uploading  = signal(false);
  readonly reindexing = signal(false);
  readonly sources    = signal<KnowledgeSource[]>([]);
  readonly selectedFile = signal<File | null>(null);

  readonly isSuperAdmin = computed(() => {
    const u = this.auth.currentUser();
    return u?.is_superadmin || u?.role === 'valmen_admin';
  });

  readonly MODULE_OPTIONS   = MODULE_OPTIONS;
  readonly CATEGORY_OPTIONS = CATEGORY_OPTIONS;
  readonly MODULE_LABELS    = MODULE_LABELS;
  readonly CATEGORY_LABELS  = CATEGORY_LABELS;
  readonly CHANNEL_LABELS   = CHANNEL_LABELS;

  readonly displayedColumns = ['file_name', 'module', 'category', 'chunks', 'tokens', 'indexed_at', 'actions'];

  readonly uploadForm = this.fb.group({
    module:   ['general', Validators.required],
    category: ['manual',  Validators.required],
  });

  ngOnInit(): void {
    this.loadSources();
  }

  loadSources(): void {
    this.loading.set(true);
    this.kbService.listSources().subscribe({
      next: sources => {
        this.sources.set(sources);
        this.loading.set(false);
      },
      error: () => {
        this.toast.error('Error al cargar las fuentes de conocimiento');
        this.loading.set(false);
      },
    });
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.selectedFile.set(input.files?.[0] ?? null);
  }

  upload(): void {
    const file = this.selectedFile();
    if (!file || this.uploadForm.invalid) return;

    const { module, category } = this.uploadForm.value;
    this.uploading.set(true);

    this.kbService.uploadFile(file, module!, category!).subscribe({
      next: result => {
        const msg = result.status === 'unchanged'
          ? `"${result.file_name}" sin cambios (hash idéntico)`
          : `"${result.file_name}" indexado — ${result.chunks_created} chunks, ${result.total_tokens} tokens`;
        this.toast.success(msg);
        this.uploading.set(false);
        this.selectedFile.set(null);
        if (this.fileInput) this.fileInput.nativeElement.value = '';
        this.loadSources();
      },
      error: () => {
        this.toast.error('Error al indexar el archivo');
        this.uploading.set(false);
      },
    });
  }

  confirmDelete(source: KnowledgeSource): void {
    this.dialog.open(ConfirmDialogComponent, {
      data: {
        header: 'Eliminar fuente de conocimiento',
        message: `¿Eliminar "${source.file_name}" y sus ${source.chunk_count} chunks?\nEsta acción no se puede deshacer.`,
        acceptLabel: 'Eliminar',
        acceptColor: 'warn',
      },
    }).afterClosed().subscribe(confirmed => {
      if (!confirmed) return;
      this.kbService.deleteSource(source.id).subscribe({
        next: result => {
          this.toast.success(`"${result.file_name}" eliminado — ${result.chunks_deleted} chunks borrados`);
          this.sources.update(s => s.filter(x => x.id !== source.id));
        },
        error: () => this.toast.error('Error al eliminar la fuente'),
      });
    });
  }

  reindex(): void {
    this.reindexing.set(true);
    this.kbService.reindex().subscribe({
      next: () => {
        this.toast.success('Re-indexación completada');
        this.reindexing.set(false);
        this.loadSources();
      },
      error: () => {
        this.toast.error('Error durante la re-indexación');
        this.reindexing.set(false);
      },
    });
  }

  formatIcon(format: string): string {
    const map: Record<string, string> = {
      pdf:  'picture_as_pdf',
      docx: 'description',
      md:   'article',
      txt:  'text_snippet',
    };
    return map[format] ?? 'insert_drive_file';
  }
}
