// frontend/src/app/features/dashboard/dashboard.component.ts
import { Component, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
    selector: 'app-dashboard',
    standalone: true,
    imports: [CommonModule],
    template: `
    <div class="sc-page-header">
      <h2>Dashboard</h2>
    </div>
    <div class="sc-page-card">
      <p>Bienvenido a Saicloud. Los módulos estarán disponibles próximamente.</p>
    </div>
  `,
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DashboardComponent { }