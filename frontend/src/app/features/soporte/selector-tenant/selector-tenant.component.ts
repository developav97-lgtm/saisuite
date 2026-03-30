import {
  ChangeDetectionStrategy,
  Component,
  computed,
  inject,
  signal,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatCardModule } from '@angular/material/card';
import { MatListModule } from '@angular/material/list';
import { MatSnackBar } from '@angular/material/snack-bar';
import { AuthService } from '../../../core/auth/auth.service';
import { SoporteService, TenantBasico } from '../../../core/services/soporte.service';

@Component({
  selector: 'app-selector-tenant',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    FormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatProgressBarModule,
    MatCardModule,
    MatListModule,
  ],
  template: `
    <div class="selector-wrapper">
      <mat-card class="selector-card">
        <mat-card-header>
          <mat-icon mat-card-avatar>support_agent</mat-icon>
          <mat-card-title>Seleccionar Cliente</mat-card-title>
          <mat-card-subtitle>Usuario soporte: {{ user()?.email }}</mat-card-subtitle>
        </mat-card-header>

        @if (loading()) {
          <mat-progress-bar mode="indeterminate"></mat-progress-bar>
        }

        <mat-card-content>
          <mat-form-field appearance="outline" class="search-field">
            <mat-label>Buscar empresa</mat-label>
            <mat-icon matPrefix>search</mat-icon>
            <input matInput [ngModel]="busqueda()" (ngModelChange)="busqueda.set($event)" placeholder="Nombre o NIT">
          </mat-form-field>

          <mat-list class="tenant-list">
            @for (tenant of tenantsFiltrados(); track tenant.id) {
              <mat-list-item class="tenant-item" (click)="seleccionar(tenant)">
                <mat-icon matListItemIcon>business</mat-icon>
                <span matListItemTitle>{{ tenant.name }}</span>
                <span matListItemLine>NIT: {{ tenant.nit }} &middot; {{ tenant.plan }}</span>
                <button mat-icon-button matListItemMeta>
                  <mat-icon>arrow_forward</mat-icon>
                </button>
              </mat-list-item>
            } @empty {
              <div class="empty-state">
                <mat-icon>search_off</mat-icon>
                <p>No se encontraron empresas</p>
              </div>
            }
          </mat-list>
        </mat-card-content>

        <mat-card-actions>
          <button mat-button (click)="logout()">
            <mat-icon>logout</mat-icon>
            Cerrar sesion
          </button>
        </mat-card-actions>
      </mat-card>
    </div>
  `,
  styles: [`
    .selector-wrapper {
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      background: var(--mat-sys-surface-variant, #f5f5f5);
      padding: 1rem;
    }
    .selector-card {
      width: 100%;
      max-width: 600px;
    }
    .search-field {
      width: 100%;
      margin-top: 1rem;
    }
    .tenant-list {
      max-height: 400px;
      overflow-y: auto;
    }
    .tenant-item {
      cursor: pointer;
      border-radius: 4px;
      margin: 2px 0;
      transition: background 0.15s;
      &:hover {
        background: rgba(0, 0, 0, 0.04);
      }
    }
    .empty-state {
      text-align: center;
      padding: 2rem;
      color: rgba(0, 0, 0, 0.4);
      mat-icon {
        font-size: 3rem;
        height: 3rem;
        width: 3rem;
      }
    }
  `],
})
export class SelectorTenantComponent {
  private readonly authService  = inject(AuthService);
  private readonly soporteService = inject(SoporteService);
  private readonly router       = inject(Router);
  private readonly snackBar     = inject(MatSnackBar);

  readonly user    = this.authService.currentUser;
  readonly loading = signal(true);
  readonly tenants = signal<TenantBasico[]>([]);
  readonly busqueda = signal('');

  readonly tenantsFiltrados = computed(() => {
    const q = this.busqueda().toLowerCase().trim();
    if (!q) return this.tenants();
    return this.tenants().filter(
      t => t.name.toLowerCase().includes(q) || t.nit.includes(q),
    );
  });

  constructor() {
    this.soporteService.getTenantsDisponibles().subscribe({
      next: data => {
        this.tenants.set(data);
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        this.snackBar.open('Error cargando empresas', 'Cerrar', {
          panelClass: ['snack-error'],
          duration: 4000,
        });
      },
    });
  }

  seleccionar(tenant: TenantBasico): void {
    this.loading.set(true);
    this.soporteService.seleccionarTenant(tenant.id).subscribe({
      next: () => {
        this.authService.refreshUserProfile().subscribe({
          next: () => {
            this.loading.set(false);
            this.router.navigate(['/dashboard']);
          },
          error: () => {
            this.loading.set(false);
            this.router.navigate(['/dashboard']);
          },
        });
      },
      error: () => {
        this.loading.set(false);
        this.snackBar.open('Error seleccionando empresa', 'Cerrar', {
          panelClass: ['snack-error'],
          duration: 4000,
        });
      },
    });
  }

  logout(): void {
    this.authService.logout();
  }
}
