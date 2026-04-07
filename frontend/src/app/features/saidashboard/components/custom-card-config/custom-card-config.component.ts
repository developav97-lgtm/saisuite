import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule, ReactiveFormsModule, FormControl, FormGroup, Validators } from '@angular/forms';
import { MatDialogModule, MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { MatChipsModule } from '@angular/material/chips';
import { debounceTime, distinctUntilChanged, switchMap, of } from 'rxjs';
import { ReportService } from '../../services/report.service';
import { FilterTercero, CustomRangoCuentasConfig, NivelCuenta, DireccionMovimiento } from '../../models/report-filter.model';

export interface CustomCardConfigDialogData {
  cardTypeCode: string;
  cardNombre: string;
  initialConfig?: CustomRangoCuentasConfig | null;
}

export interface CustomCardConfigDialogResult {
  config: CustomRangoCuentasConfig;
}

@Component({
  selector: 'app-custom-card-config',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    FormsModule,
    ReactiveFormsModule,
    MatDialogModule,
    MatButtonModule,
    MatIconModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatSlideToggleModule,
    MatTooltipModule,
    MatAutocompleteModule,
    MatChipsModule,
  ],
  template: `
    <h2 mat-dialog-title>
      <mat-icon>tune</mat-icon>
      Configurar: {{ data.cardNombre }}
    </h2>

    <mat-dialog-content class="ccc-content">
      <p class="ccc-hint">
        @if (data.cardTypeCode === 'CUSTOM_RANGO_CUENTAS') {
          Define el rango de cuentas PUC a sumar y la dirección del movimiento.
        } @else if (data.cardTypeCode === 'DISTRIBUCION_POR_PROYECTO') {
          Define el rango de cuentas a distribuir por proyecto contable.
        } @else {
          Define el rango de cuentas y el número de terceros a mostrar.
        }
      </p>

      <div class="ccc-form">
        <!-- Nivel de cuenta -->
        <mat-form-field appearance="outline" subscriptSizing="dynamic">
          <mat-label>Nivel de cuenta</mat-label>
          <mat-select [formControl]="form.controls.nivel_cuenta">
            <mat-option value="titulo">Título (1 dígito)</mat-option>
            <mat-option value="grupo">Grupo (2 dígitos)</mat-option>
            <mat-option value="cuenta">Cuenta (4 dígitos)</mat-option>
            <mat-option value="subcuenta">Subcuenta (6 dígitos)</mat-option>
            <mat-option value="auxiliar">Auxiliar (completo)</mat-option>
          </mat-select>
        </mat-form-field>

        <!-- Rango -->
        <div class="ccc-range">
          <mat-form-field appearance="outline" subscriptSizing="dynamic">
            <mat-label>Código desde</mat-label>
            <input matInput type="number" [formControl]="form.controls.codigo_desde"
                   placeholder="Ej: 1105" />
            @if (form.controls.codigo_desde.hasError('required')) {
              <mat-error>Campo requerido</mat-error>
            }
          </mat-form-field>

          <mat-icon class="ccc-range__arrow">arrow_forward</mat-icon>

          <mat-form-field appearance="outline" subscriptSizing="dynamic">
            <mat-label>Código hasta</mat-label>
            <input matInput type="number" [formControl]="form.controls.codigo_hasta"
                   placeholder="Ej: 1110" />
            @if (form.controls.codigo_hasta.hasError('required')) {
              <mat-error>Campo requerido</mat-error>
            }
          </mat-form-field>
        </div>

        <!-- Dirección -->
        <mat-form-field appearance="outline" subscriptSizing="dynamic">
          <mat-label>Dirección del movimiento</mat-label>
          <mat-select [formControl]="form.controls.direccion">
            <mat-option value="debito">Solo débitos</mat-option>
            <mat-option value="credito">Solo créditos</mat-option>
            <mat-option value="neto">Neto (débito - crédito)</mat-option>
          </mat-select>
        </mat-form-field>

        <!-- Título personalizado -->
        <mat-form-field appearance="outline" subscriptSizing="dynamic">
          <mat-label>Título de la tarjeta</mat-label>
          <input matInput [formControl]="form.controls.titulo_personalizado"
                 maxlength="100" placeholder="Ej: Disponible Bancario" />
          @if (form.controls.titulo_personalizado.hasError('required')) {
            <mat-error>Campo requerido</mat-error>
          }
        </mat-form-field>

        <!-- Agrupar por cuenta individual -->
        @if (data.cardTypeCode === 'CUSTOM_RANGO_CUENTAS') {
          <mat-slide-toggle [formControl]="form.controls.agrupar_por_cuenta" color="primary"
                            matTooltip="Muestra una barra por cada cuenta en el rango en lugar del total">
            Ver cuentas individuales
          </mat-slide-toggle>
        }

        <!-- Agrupar por mes -->
        <mat-slide-toggle [formControl]="form.controls.agrupar_por_mes" color="primary"
                          matTooltip="Muestra la evolución mes a mes en lugar de un total">
          Ver por mes (serie mensual)
        </mat-slide-toggle>

        <!-- Filtro de terceros (autocomplete multi-select) -->
        <div class="ccc-terceros">
          <mat-form-field appearance="outline" subscriptSizing="dynamic">
            <mat-label>Filtrar por tercero (opcional)</mat-label>
            <input matInput
                   [formControl]="terceroSearch"
                   [matAutocomplete]="autoTercero"
                   placeholder="Buscar por nombre o NIT..." />
            <mat-icon matSuffix>person_search</mat-icon>
            <mat-autocomplete #autoTercero="matAutocomplete"
                              [displayWith]="displayTercero"
                              (optionSelected)="addTercero($event.option.value)">
              @for (t of terceroOptions(); track t.id) {
                <mat-option [value]="t">{{ t.nombre }}</mat-option>
              }
              @if (terceroOptions().length === 0 && terceroSearch.value && terceroSearch.value.length >= 2) {
                <mat-option disabled>Sin resultados</mat-option>
              }
            </mat-autocomplete>
          </mat-form-field>

          <!-- Chips de terceros seleccionados -->
          @if (selectedTerceros().length > 0) {
            <mat-chip-set class="ccc-chips">
              @for (t of selectedTerceros(); track t.id) {
                <mat-chip (removed)="removeTercero(t)">
                  {{ t.nombre }}
                  <button matChipRemove><mat-icon>cancel</mat-icon></button>
                </mat-chip>
              }
            </mat-chip-set>
          }
        </div>

        <!-- Top N (para DISTRIBUCION_POR_PROYECTO y MOVIMIENTO_POR_TERCERO) -->
        @if (data.cardTypeCode === 'DISTRIBUCION_POR_PROYECTO' || data.cardTypeCode === 'MOVIMIENTO_POR_TERCERO') {
          <mat-form-field appearance="outline" subscriptSizing="dynamic">
            <mat-label>
              @if (data.cardTypeCode === 'MOVIMIENTO_POR_TERCERO') {
                Máximo de terceros a mostrar
              } @else {
                Máximo de proyectos a mostrar
              }
            </mat-label>
            <input matInput type="number" [formControl]="form.controls.top_n"
                   min="1" max="100" placeholder="20" />
          </mat-form-field>
        }
      </div>
    </mat-dialog-content>

    <mat-dialog-actions align="end">
      <button mat-stroked-button mat-dialog-close>Cancelar</button>
      <button mat-raised-button color="primary" (click)="confirm()"
              [disabled]="form.invalid">
        <mat-icon>check</mat-icon> Confirmar
      </button>
    </mat-dialog-actions>
  `,
  styles: [`
    h2[mat-dialog-title] {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .ccc-content {
      min-width: 380px;
      max-width: 480px;
    }

    .ccc-hint {
      font-size: 0.875rem;
      color: var(--sc-text-secondary);
      margin-bottom: 1rem;
    }

    .ccc-form {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .ccc-range {
      display: flex;
      align-items: center;
      gap: 0.5rem;

      mat-form-field {
        flex: 1;
      }

      &__arrow {
        color: var(--sc-text-secondary);
        flex-shrink: 0;
        margin-top: -1rem;
      }
    }

    .ccc-terceros {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;

      mat-form-field {
        width: 100%;
      }
    }

    .ccc-chips {
      display: flex;
      flex-wrap: wrap;
      gap: 0.25rem;
    }

    @media (max-width: 480px) {
      .ccc-content {
        min-width: unset;
      }
    }
  `],
})
export class CustomCardConfigComponent implements OnInit {
  readonly data = inject<CustomCardConfigDialogData>(MAT_DIALOG_DATA);
  private readonly dialogRef = inject(MatDialogRef<CustomCardConfigComponent>);
  private readonly reportService = inject(ReportService);
  private readonly destroyRef = inject(DestroyRef);

  readonly terceroOptions = signal<FilterTercero[]>([]);
  readonly selectedTerceros = signal<FilterTercero[]>([]);

  readonly terceroSearch = new FormControl('');

  readonly form = new FormGroup({
    nivel_cuenta: new FormControl<NivelCuenta>('cuenta', { nonNullable: true }),
    codigo_desde: new FormControl<number | null>(null, [Validators.required]),
    codigo_hasta: new FormControl<number | null>(null, [Validators.required]),
    direccion: new FormControl<DireccionMovimiento>('neto', { nonNullable: true }),
    titulo_personalizado: new FormControl('', {
      nonNullable: true,
      validators: [Validators.required, Validators.maxLength(100)],
    }),
    agrupar_por_cuenta: new FormControl(false, { nonNullable: true }),
    agrupar_por_mes: new FormControl(false, { nonNullable: true }),
    top_n: new FormControl<number | null>(null),
  });

  ngOnInit(): void {
    const initial = this.data.initialConfig;
    if (initial) {
      this.form.patchValue({
        nivel_cuenta: initial.nivel_cuenta,
        codigo_desde: initial.codigo_desde,
        codigo_hasta: initial.codigo_hasta,
        direccion: initial.direccion,
        titulo_personalizado: initial.titulo_personalizado,
        agrupar_por_cuenta: initial.agrupar_por_cuenta ?? false,
        agrupar_por_mes: initial.agrupar_por_mes,
        top_n: initial.top_n ?? null,
      });

      // Restaurar terceros seleccionados si los hay
      if (initial.tercero_ids?.length) {
        const terceros = initial.tercero_ids.map(id => ({
          id,
          nombre: id, // placeholder hasta buscar; en práctica ya viene guardado
        }));
        this.selectedTerceros.set(terceros);
      }
    }

    // Autocomplete de terceros
    this.terceroSearch.valueChanges.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      switchMap(q => {
        if (!q || typeof q !== 'string' || q.length < 2) return of([]);
        return this.reportService.searchTerceros(q);
      }),
      takeUntilDestroyed(this.destroyRef),
    ).subscribe(opts => this.terceroOptions.set(opts));
  }

  displayTercero(t: FilterTercero | null): string {
    return t?.nombre ?? '';
  }

  addTercero(t: FilterTercero): void {
    if (!t?.id) return;
    const already = this.selectedTerceros().some(s => s.id === t.id);
    if (!already) {
      this.selectedTerceros.update(list => [...list, t]);
    }
    // Limpiar el input después de seleccionar
    this.terceroSearch.setValue('', { emitEvent: false });
    this.terceroOptions.set([]);
  }

  removeTercero(t: FilterTercero): void {
    this.selectedTerceros.update(list => list.filter(s => s.id !== t.id));
  }

  confirm(): void {
    if (this.form.invalid) return;

    const v = this.form.getRawValue();
    const terceroIds = this.selectedTerceros().map(t => t.id);
    const config: CustomRangoCuentasConfig = {
      nivel_cuenta: v.nivel_cuenta,
      codigo_desde: v.codigo_desde!,
      codigo_hasta: v.codigo_hasta!,
      direccion: v.direccion,
      titulo_personalizado: v.titulo_personalizado,
      agrupar_por_cuenta: v.agrupar_por_cuenta,
      agrupar_por_mes: v.agrupar_por_mes,
      top_n: v.top_n ?? null,
      ...(terceroIds.length > 0 ? { tercero_ids: terceroIds } : {}),
    };
    this.dialogRef.close({ config } as CustomCardConfigDialogResult);
  }
}
