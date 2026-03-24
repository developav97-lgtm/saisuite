/**
 * SaiSuite — SelectorDependenciasComponent
 * Permite agregar/quitar dependencias predecesoras sobre una tarea.
 * Usa Angular Material (DEC-011): mat-autocomplete, mat-select, mat-chip-set.
 */
import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  input,
  output,
  signal,
  computed,
  inject,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormControl } from '@angular/forms';
import { debounceTime, distinctUntilChanged, switchMap, catchError } from 'rxjs/operators';
import { of } from 'rxjs';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { TareaService } from '../../services/tarea.service';
import { Tarea, TareaDependencia, TipoDependencia } from '../../models/tarea.model';

const TIPO_LABELS: Record<TipoDependencia, string> = {
  FS: 'Finish to Start (FS)',
  SS: 'Start to Start (SS)',
  FF: 'Finish to Finish (FF)',
};

@Component({
  selector: 'sc-selector-dependencias',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    MatAutocompleteModule,
    MatButtonModule,
    MatChipsModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatSelectModule,
    MatTooltipModule,
    MatProgressSpinnerModule,
  ],
  template: `
    <div class="sc-selector-dep">

      <!-- Lista de predecesoras actuales -->
      @if (predecesoras().length > 0) {
        <mat-chip-set class="sc-chip-set">
          @for (dep of predecesoras(); track dep.id) {
            <mat-chip
              [removable]="true"
              (removed)="quitarDependencia(dep)"
              class="sc-dep-chip"
            >
              <mat-icon matChipAvatar>arrow_back</mat-icon>
              {{ dep.tarea_predecesora_detail.codigo }}
              — {{ dep.tarea_predecesora_detail.nombre }}
              <span class="sc-dep-tipo">[{{ dep.tipo_dependencia }}]</span>
              @if (dep.retraso_dias !== 0) {
                <span class="sc-dep-lag">+{{ dep.retraso_dias }}d</span>
              }
              <button matChipRemove [attr.aria-label]="'Quitar dependencia de ' + dep.tarea_predecesora_detail.nombre">
                <mat-icon>cancel</mat-icon>
              </button>
            </mat-chip>
          }
        </mat-chip-set>
      }

      <!-- Formulario para agregar nueva predecesora -->
      <div class="sc-add-dep-form">
        <mat-form-field appearance="outline" class="sc-autocomplete-field">
          <mat-label>Buscar tarea predecesora</mat-label>
          <input
            matInput
            [formControl]="busquedaCtrl"
            [matAutocomplete]="auto"
            placeholder="Nombre o código de la tarea..."
          />
          <mat-icon matSuffix>search</mat-icon>
          <mat-autocomplete #auto="matAutocomplete" [displayWith]="displayTarea">
            @if (buscando()) {
              <mat-option disabled>
                <mat-spinner diameter="20" />
              </mat-option>
            }
            @for (tarea of resultadosBusqueda(); track tarea.id) {
              <mat-option [value]="tarea">
                <span class="sc-opt-codigo">{{ tarea.codigo }}</span>
                {{ tarea.nombre }}
              </mat-option>
            }
            @if (!buscando() && busquedaCtrl.value && resultadosBusqueda().length === 0) {
              <mat-option disabled>Sin resultados</mat-option>
            }
          </mat-autocomplete>
        </mat-form-field>

        <mat-form-field appearance="outline" class="sc-tipo-field">
          <mat-label>Tipo</mat-label>
          <mat-select [(ngModel)]="tipoSeleccionado">
            @for (entry of tiposOpciones; track entry.value) {
              <mat-option [value]="entry.value">{{ entry.label }}</mat-option>
            }
          </mat-select>
        </mat-form-field>

        <mat-form-field appearance="outline" class="sc-lag-field">
          <mat-label>Retraso (días)</mat-label>
          <input matInput type="number" [(ngModel)]="retrasoDias" min="-365" max="365" />
        </mat-form-field>

        <button
          mat-flat-button
          color="primary"
          [disabled]="!tareaSeleccionada() || guardando()"
          (click)="agregarDependencia()"
          class="sc-btn-agregar"
        >
          @if (guardando()) {
            <mat-spinner diameter="18" />
          } @else {
            <ng-container>
              <mat-icon>add_link</mat-icon>
              Agregar
            </ng-container>
          }
        </button>
      </div>

    </div>
  `,
  styles: [`
    .sc-selector-dep {
      display: flex;
      flex-direction: column;
      gap: var(--sc-spacing-sm, 8px);
    }
    .sc-chip-set {
      flex-wrap: wrap;
    }
    .sc-dep-chip {
      font-size: 13px;
    }
    .sc-dep-tipo {
      margin-left: 4px;
      opacity: 0.7;
      font-size: 11px;
    }
    .sc-dep-lag {
      margin-left: 4px;
      color: var(--sc-color-warning, #fb8c00);
      font-size: 11px;
    }
    .sc-add-dep-form {
      display: flex;
      align-items: flex-start;
      gap: 8px;
      flex-wrap: wrap;
    }
    .sc-autocomplete-field {
      flex: 2;
      min-width: 220px;
    }
    .sc-tipo-field {
      flex: 1;
      min-width: 160px;
    }
    .sc-lag-field {
      flex: 0 0 100px;
    }
    .sc-btn-agregar {
      margin-top: 4px;
      height: 56px;
    }
    .sc-opt-codigo {
      font-weight: 600;
      margin-right: 6px;
      color: var(--sc-color-primary, #1565c0);
    }
  `],
})
export class SelectorDependenciasComponent implements OnInit {

  // ── Inputs / Outputs ─────────────────────────────────────────────────────
  readonly tarea = input.required<Tarea>();
  readonly dependenciaAgregada = output<TareaDependencia>();
  readonly dependenciaEliminada = output<string>();

  // ── DI ───────────────────────────────────────────────────────────────────
  private readonly tareaService = inject(TareaService);
  private readonly snackBar     = inject(MatSnackBar);

  // ── Estado ───────────────────────────────────────────────────────────────
  readonly busquedaCtrl   = new FormControl<string | Tarea>('');
  readonly buscando       = signal(false);
  readonly guardando      = signal(false);
  readonly resultadosBusqueda = signal<Tarea[]>([]);

  tipoSeleccionado: TipoDependencia = 'FS';
  retrasoDias: number = 0;

  readonly tiposOpciones = (Object.entries(TIPO_LABELS) as [TipoDependencia, string][]).map(
    ([value, label]) => ({ value, label })
  );

  readonly tareaSeleccionada = computed<Tarea | null>(() => {
    const v = this.busquedaCtrl.value;
    return v && typeof v === 'object' ? v : null;
  });

  readonly predecesoras = computed<TareaDependencia[]>(() =>
    this.tarea().predecesoras_detail ?? []
  );

  // ── Lifecycle ─────────────────────────────────────────────────────────────
  ngOnInit(): void {
    this.busquedaCtrl.valueChanges.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      switchMap(query => {
        if (!query || typeof query !== 'string' || query.length < 2) {
          this.resultadosBusqueda.set([]);
          return of([]);
        }
        this.buscando.set(true);
        return this.tareaService.list({
          proyecto: this.tarea().proyecto,
          search: query,
        }).pipe(catchError(() => of([])));
      }),
      takeUntilDestroyed(),
    ).subscribe(tareas => {
      const tareaActualId = this.tarea().id;
      const yaRelacionadas = new Set([
        ...this.predecesoras().map(d => d.tarea_predecesora),
        ...(this.tarea().sucesoras_detail ?? []).map(d => d.tarea_sucesora),
        tareaActualId,
      ]);
      this.resultadosBusqueda.set(
        tareas.filter(t => !yaRelacionadas.has(t.id))
      );
      this.buscando.set(false);
    });
  }

  displayTarea(tarea: Tarea | string | null): string {
    if (!tarea || typeof tarea === 'string') return '';
    return `${tarea.codigo} — ${tarea.nombre}`;
  }

  agregarDependencia(): void {
    const pred = this.tareaSeleccionada();
    if (!pred) return;

    this.guardando.set(true);
    this.tareaService.crearDependencia(
      this.tarea().id,
      pred.id,
      this.tipoSeleccionado,
      this.retrasoDias,
    ).subscribe({
      next: dep => {
        this.dependenciaAgregada.emit(dep);
        this.busquedaCtrl.reset('');
        this.tipoSeleccionado = 'FS';
        this.retrasoDias = 0;
        this.snackBar.open('Dependencia agregada', 'OK', {
          duration: 3000,
          panelClass: ['snack-success'],
        });
        this.guardando.set(false);
      },
      error: err => {
        const msg = err?.error?.detail
          || err?.error?.[Object.keys(err.error ?? {})[0]]
          || 'No se pudo crear la dependencia';
        this.snackBar.open(String(msg), 'Cerrar', {
          duration: 5000,
          panelClass: ['snack-error'],
        });
        this.guardando.set(false);
      },
    });
  }

  quitarDependencia(dep: TareaDependencia): void {
    this.tareaService.eliminarDependencia(this.tarea().id, dep.id).subscribe({
      next: () => {
        this.dependenciaEliminada.emit(dep.id);
        this.snackBar.open('Dependencia eliminada', 'OK', {
          duration: 3000,
          panelClass: ['snack-success'],
        });
      },
      error: () => {
        this.snackBar.open('Error al eliminar la dependencia', 'Cerrar', {
          duration: 4000,
          panelClass: ['snack-error'],
        });
      },
    });
  }
}
