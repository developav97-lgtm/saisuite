// frontend/src/app/features/ventas/ventas.routes.ts
import { Routes } from '@angular/router';
import { VentasPlaceholderComponent } from './ventas-placeholder.component';

export const VENTAS_ROUTES: Routes = [
    { path: '', component: VentasPlaceholderComponent },
    { path: '**', component: VentasPlaceholderComponent },
];