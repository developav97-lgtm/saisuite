// frontend/src/app/features/ventas/ventas-placeholder.component.ts
import { Component, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
    selector: 'app-ventas-placeholder',
    standalone: true,
    imports: [CommonModule],
    template: `
    <div class="sc-page-header"><h2>CRM</h2></div>
    <div class="sc-page-card">
      <p>Módulo CRM — pendiente de confirmación con Saiopen.</p>
    </div>
  `,
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class VentasPlaceholderComponent { }