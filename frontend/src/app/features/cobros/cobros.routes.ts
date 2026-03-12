// frontend/src/app/features/cobros/cobros.routes.ts
import { Routes } from '@angular/router';
import { CobrosPlaceholderComponent } from './cobros-placeholder.component';

export const COBROS_ROUTES: Routes = [
    { path: '', component: CobrosPlaceholderComponent },
    { path: '**', component: CobrosPlaceholderComponent },
];