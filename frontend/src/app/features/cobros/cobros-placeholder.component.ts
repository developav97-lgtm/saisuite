// frontend/src/app/features/cobros/cobros-placeholder.component.ts
import { Component, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
    selector: 'app-cobros-placeholder',
    standalone: true,
    imports: [CommonModule],
    template: `
    <div class="sc-page-header"><h2>SaiCobros</h2></div>
    <div class="sc-page-card">
      <p>Módulo SaiCobros — pendiente de confirmación con Saiopen.</p>
    </div>
  `,
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CobrosPlaceholderComponent { }