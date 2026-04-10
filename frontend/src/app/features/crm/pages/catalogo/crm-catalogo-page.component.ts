/**
 * SaiSuite — CRM Catálogo Page
 * Lista de productos del catálogo CRM (sincronizados desde SaiOpen).
 * Pensado para acceso rápido (QuickAccessDialog) o navegación directa.
 */
import {
  ChangeDetectionStrategy, Component, OnInit, OnDestroy,
  inject, signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatTableModule, MatTableDataSource } from '@angular/material/table';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';
import { Subject, takeUntil, debounceTime, distinctUntilChanged } from 'rxjs';

import { CrmService } from '../../services/crm.service';
import { CrmProducto } from '../../models/crm.model';
import { ToastService } from '../../../../core/services/toast.service';

@Component({
  selector: 'app-crm-catalogo-page',
  templateUrl: './crm-catalogo-page.component.html',
  styleUrl: './crm-catalogo-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule, FormsModule,
    MatTableModule, MatFormFieldModule, MatInputModule,
    MatProgressBarModule, MatIconModule, MatChipsModule,
  ],
})
export class CrmCatalogoPageComponent implements OnInit, OnDestroy {
  private readonly crm    = inject(CrmService);
  private readonly toast  = inject(ToastService);
  private readonly destroy$ = new Subject<void>();
  private readonly searchChange$ = new Subject<string>();

  readonly productos   = signal<CrmProducto[]>([]);
  readonly loading     = signal(false);
  readonly searchTerm  = signal('');

  readonly dataSource = new MatTableDataSource<CrmProducto>();

  readonly displayedColumns = ['codigo', 'nombre', 'precio_base', 'impuesto', 'unidad_venta'];

  ngOnInit(): void {
    this.searchChange$.pipe(
      debounceTime(350),
      distinctUntilChanged(),
      takeUntil(this.destroy$),
    ).subscribe(term => this.loadProductos(term));

    this.loadProductos();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  onSearchChange(value: string): void {
    this.searchTerm.set(value);
    this.searchChange$.next(value);
  }

  private loadProductos(search?: string): void {
    this.loading.set(true);
    this.crm.listProductos({ search }).pipe(takeUntil(this.destroy$)).subscribe({
      next: list => {
        this.productos.set(list);
        this.dataSource.data = list;
        this.loading.set(false);
      },
      error: () => {
        this.toast.error('Error cargando catálogo');
        this.loading.set(false);
      },
    });
  }

  formatPrecio(precio: string): string {
    const n = parseFloat(precio || '0');
    return new Intl.NumberFormat('es-CO', {
      style: 'currency', currency: 'COP', maximumFractionDigits: 0,
    }).format(n);
  }
}
