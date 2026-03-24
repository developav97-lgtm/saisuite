import {
  ChangeDetectionStrategy, Component, OnInit, OnDestroy,
  inject, input, output, signal, computed, effect,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormControl } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatIconModule } from '@angular/material/icon';
import {
  Subject, debounceTime, distinctUntilChanged, switchMap,
  takeUntil, catchError, of, map,
} from 'rxjs';
import { TerceroService } from '../../../core/services/tercero.service';
import { TerceroList } from '../../../core/models/tercero.model';

export interface TerceroSeleccionado {
  id: string;
  numero_identificacion: string;
  nombre_completo: string;
}

@Component({
  selector: 'app-tercero-selector',
  templateUrl: './tercero-selector.component.html',
  styleUrl: './tercero-selector.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule, ReactiveFormsModule,
    MatFormFieldModule, MatInputModule,
    MatAutocompleteModule, MatProgressSpinnerModule, MatIconModule,
  ],
})
export class TerceroSelectorComponent implements OnInit, OnDestroy {
  private readonly terceroService = inject(TerceroService);
  private readonly destroy$ = new Subject<void>();

  /** Texto inicial que se muestra en el input (modo edición) */
  readonly initialDisplayText = input<string>('');
  /** Label del campo */
  readonly label = input<string>('Buscar tercero (nombre o NIT)');

  readonly terceroSeleccionado = output<TerceroSeleccionado | null>();

  readonly searchControl = new FormControl('');
  readonly opciones      = signal<TerceroList[]>([]);
  readonly buscando      = signal(false);
  readonly seleccionado  = signal<TerceroList | null>(null);
  readonly sinResultados = computed(() => !this.buscando() && this.opciones().length === 0);

  constructor() {
    // Reacciona de forma reactiva al initialDisplayText (puede llegar después del ngOnInit
    // si el padre carga datos de forma asíncrona)
    effect(() => {
      const text = this.initialDisplayText();
      if (text && !this.seleccionado()) {
        this.searchControl.setValue(text, { emitEvent: false });
      }
    });
  }

  ngOnInit(): void {
    this.searchControl.valueChanges.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      switchMap(query => {
        // Cuando mat-autocomplete selecciona una opción, el valor puede ser
        // un objeto TerceroList en lugar de string — ignorar esos casos
        if (typeof query !== 'string') return of([]);
        const q = query.trim();
        if (q.length < 2) {
          this.opciones.set([]);
          return of([]);
        }
        this.buscando.set(true);
        return this.terceroService.list({ search: q, activo: true, page_size: 20 }).pipe(
          map(r => r.results),
          catchError(() => of([])),
        );
      }),
      takeUntil(this.destroy$),
    ).subscribe(resultados => {
      this.opciones.set(resultados as TerceroList[]);
      this.buscando.set(false);
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  displayFn(tercero: TerceroList | string | null): string {
    if (!tercero) return '';
    if (typeof tercero === 'string') return tercero;
    return `${tercero.nombre_completo} (${tercero.numero_identificacion})`;
  }

  onOpcionSeleccionada(tercero: TerceroList): void {
    this.seleccionado.set(tercero);
    this.terceroSeleccionado.emit({
      id: tercero.id,
      numero_identificacion: tercero.numero_identificacion,
      nombre_completo: tercero.nombre_completo,
    });
  }

  limpiar(): void {
    this.seleccionado.set(null);
    this.searchControl.setValue('');
    this.opciones.set([]);
    this.terceroSeleccionado.emit(null);
  }
}
