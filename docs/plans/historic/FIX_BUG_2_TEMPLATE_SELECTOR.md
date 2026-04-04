# FIX BUG #2: Template Selector sin texto

## Problema
1. Selector solo muestra flecha ↓, sin texto
2. Opción "Desde plantilla" no aparece en lista de proyectos (solo en cards)

## Solución

### 1. Agregar texto al botón en `proyecto-list.component.html`

**Ubicación:** `frontend/src/app/features/proyectos/components/proyecto-list/proyecto-list.component.html`

#### ANTES (solo icono):
```html
<button mat-menu-item (click)="openCreateFromTemplateDialog()">
  <mat-icon>content_copy</mat-icon>
</button>
```

#### DESPUÉS (con label):
```html
<button mat-menu-item (click)="openCreateFromTemplateDialog()">
  <mat-icon>content_copy</mat-icon>
  <span>Desde plantilla</span>
</button>
```

### 2. Hacer visible en AMBAS vistas (lista + cards)

El botón debe estar en el menú principal de acciones, NO solo en un menú contextual de cards.

#### Estructura correcta en `proyecto-list.component.html`:

```html
<!-- Header con acciones -->
<div class="pl-header-actions">
  <!-- Botón principal: Nuevo Proyecto (normal) -->
  <button mat-raised-button color="primary" (click)="openCreateDialog()">
    <mat-icon>add</mat-icon>
    Nuevo Proyecto
  </button>
  
  <!-- Menú desplegable con opciones adicionales -->
  <button mat-icon-button [matMenuTriggerFor]="moreMenu">
    <mat-icon>more_vert</mat-icon>
  </button>
  
  <mat-menu #moreMenu="matMenu">
    <!-- Opción 1: Desde plantilla -->
    <button mat-menu-item (click)="openCreateFromTemplateDialog()">
      <mat-icon>content_copy</mat-icon>
      <span>Desde plantilla</span>
    </button>
    
    <!-- Opción 2: Importar desde Excel -->
    <button mat-menu-item (click)="openImportDialog()">
      <mat-icon>upload_file</mat-icon>
      <span>Importar desde Excel</span>
    </button>
    
    <!-- Opción 3: Exportar lista (si existe) -->
    <button mat-menu-item (click)="exportToExcel()">
      <mat-icon>download</mat-icon>
      <span>Exportar lista</span>
    </button>
  </mat-menu>
</div>
```

### 3. Verificar que los métodos existen en `proyecto-list.component.ts`

```typescript
openCreateFromTemplateDialog() {
  const dialogRef = this.dialog.open(CreateFromTemplateDialogComponent, {
    width: '800px',
    maxHeight: '90vh'
  });
  
  dialogRef.afterClosed().subscribe(result => {
    if (result) {
      // Proyecto creado desde plantilla
      this.snackBar.open('Proyecto creado desde plantilla', 'Cerrar', {
        duration: 3000,
        panelClass: ['snack-success']
      });
      this.loadProyectos(); // Recargar lista
    }
  });
}

openImportDialog() {
  const dialogRef = this.dialog.open(ImportFromExcelDialogComponent, {
    width: '600px'
  });
  
  dialogRef.afterClosed().subscribe(result => {
    if (result) {
      this.snackBar.open('Proyecto importado exitosamente', 'Cerrar', {
        duration: 3000,
        panelClass: ['snack-success']
      });
      this.loadProyectos();
    }
  });
}
```

### 4. Importar componentes en `proyecto-list.component.ts`

```typescript
import { CreateFromTemplateDialogComponent } from '../create-from-template-dialog/create-from-template-dialog.component';
import { ImportFromExcelDialogComponent } from '../import-from-excel-dialog/import-from-excel-dialog.component';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';

@Component({
  // ...
})
export class ProyectoListComponent {
  constructor(
    private dialog: MatDialog,
    private snackBar: MatSnackBar,
    // ... otros servicios
  ) {}
}
```

## Validación 4x4
- [ ] Desktop Light: Texto visible "Desde plantilla" ✅
- [ ] Desktop Dark: Texto visible ✅
- [ ] Mobile Light: Texto visible (puede truncar si es muy largo) ✅
- [ ] Mobile Dark: Texto visible ✅
- [ ] Opción visible TANTO en vista lista como en vista cards ✅

## Archivos modificados
- `frontend/src/app/features/proyectos/components/proyecto-list/proyecto-list.component.html`
- `frontend/src/app/features/proyectos/components/proyecto-list/proyecto-list.component.ts`
