import { Routes } from '@angular/router';

export const CONTABILIDAD_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./pages/gl-viewer/gl-viewer-page.component').then(
        m => m.GlViewerPageComponent
      ),
  },
];
