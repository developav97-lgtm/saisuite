# FIX BUG #3: Template Excel corrupto + CRUD Plantillas

## Problema 1: Excel corrupto
```
Excel no puede abrir el archivo 'plantilla-proyecto.xlsx' porque el formato o la extensión no son válidos.
```

**Causa:** El archivo no está generado correctamente como Excel válido.

## Solución 1: Generar Excel válido

### 1.1. Crear endpoint para generar template Excel

**Archivo:** `apps/proyectos/views.py`

```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from django.http import HttpResponse

@action(detail=False, methods=['get'], url_path='download-excel-template')
def download_excel_template(self, request):
    """
    Descarga plantilla Excel válida para importar proyectos.
    """
    # Crear workbook
    wb = Workbook()
    
    # === HOJA 1: Datos Proyecto ===
    ws1 = wb.active
    ws1.title = "Datos Proyecto"
    
    # Header style
    header_fill = PatternFill(start_color="1a237e", end_color="1a237e", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    
    # Headers
    ws1['A1'] = "Campo"
    ws1['B1'] = "Valor"
    ws1['A1'].fill = header_fill
    ws1['A1'].font = header_font
    ws1['B1'].fill = header_fill
    ws1['B1'].font = header_font
    
    # Datos de ejemplo
    ws1['A2'] = "Nombre"
    ws1['B2'] = "Proyecto Ejemplo"
    ws1['A3'] = "Código"
    ws1['B3'] = "PRY-EJEMPLO-001"
    ws1['A4'] = "Descripción"
    ws1['B4'] = "Descripción del proyecto de ejemplo"
    ws1['A5'] = "Fecha Inicio"
    ws1['B5'] = "2026-04-01"
    ws1['A6'] = "Fecha Fin"
    ws1['B6'] = "2026-12-31"
    
    # Ancho de columnas
    ws1.column_dimensions['A'].width = 20
    ws1.column_dimensions['B'].width = 40
    
    # === HOJA 2: Fases ===
    ws2 = wb.create_sheet("Fases")
    headers_fases = ["Orden", "Nombre", "Descripción", "Fecha Inicio", "Fecha Fin"]
    ws2.append(headers_fases)
    
    # Estilo header
    for cell in ws2[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')
    
    # Datos de ejemplo
    ws2.append([1, "Fase 1: Planificación", "Fase inicial de planificación", "2026-04-01", "2026-06-01"])
    ws2.append([2, "Fase 2: Ejecución", "Fase de ejecución del proyecto", "2026-06-02", "2026-10-01"])
    ws2.append([3, "Fase 3: Cierre", "Fase de cierre y entrega", "2026-10-02", "2026-12-31"])
    
    # Ancho de columnas
    for col in ['A', 'B', 'C', 'D', 'E']:
        ws2.column_dimensions[col].width = 20
    
    # === HOJA 3: Tareas ===
    ws3 = wb.create_sheet("Tareas")
    headers_tareas = ["Fase", "Orden", "Nombre", "Descripción", "Prioridad", "Fecha Inicio", "Fecha Fin"]
    ws3.append(headers_tareas)
    
    # Estilo header
    for cell in ws3[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')
    
    # Datos de ejemplo
    ws3.append(["Fase 1: Planificación", 1, "Tarea 1.1", "Primera tarea", "high", "2026-04-01", "2026-04-15"])
    ws3.append(["Fase 1: Planificación", 2, "Tarea 1.2", "Segunda tarea", "medium", "2026-04-16", "2026-05-01"])
    ws3.append(["Fase 2: Ejecución", 1, "Tarea 2.1", "Primera tarea ejecución", "high", "2026-06-02", "2026-07-01"])
    
    # Ancho de columnas
    for col in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
        ws3.column_dimensions[col].width = 20
    
    # === HOJA 4: Dependencias (opcional) ===
    ws4 = wb.create_sheet("Dependencias")
    headers_deps = ["Tarea Predecesora", "Tarea Sucesora", "Tipo", "Lag (días)"]
    ws4.append(headers_deps)
    
    # Estilo header
    for cell in ws4[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')
    
    # Datos de ejemplo
    ws4.append(["Tarea 1.1", "Tarea 1.2", "FS", 0])
    ws4.append(["Tarea 1.2", "Tarea 2.1", "FS", 0])
    
    # Ancho de columnas
    for col in ['A', 'B', 'C', 'D']:
        ws4.column_dimensions[col].width = 25
    
    # === HOJA 5: Instrucciones ===
    ws5 = wb.create_sheet("Instrucciones")
    ws5['A1'] = "INSTRUCCIONES DE USO"
    ws5['A1'].font = Font(size=14, bold=True)
    
    instrucciones = [
        "",
        "1. Complete la hoja 'Datos Proyecto' con la información básica del proyecto.",
        "",
        "2. En la hoja 'Fases', liste todas las fases del proyecto en orden.",
        "   - Orden: Número secuencial (1, 2, 3...)",
        "   - Nombre: Nombre descriptivo de la fase",
        "   - Fechas: Formato YYYY-MM-DD (ej: 2026-04-01)",
        "",
        "3. En la hoja 'Tareas', liste todas las tareas por fase.",
        "   - Fase: Debe coincidir EXACTAMENTE con el nombre de la fase",
        "   - Prioridad: high, medium o low",
        "",
        "4. (Opcional) En 'Dependencias', defina relaciones entre tareas.",
        "   - Tipo: FS (Finish-to-Start), SS (Start-to-Start), FF (Finish-to-Finish), SF (Start-to-Finish)",
        "   - Lag: Días de demora entre tareas",
        "",
        "5. Guarde el archivo y súbalo en la opción 'Importar desde Excel'.",
        "",
        "IMPORTANTE:",
        "- No modifique los nombres de las hojas",
        "- No elimine las columnas de encabezado",
        "- Use el formato de fecha YYYY-MM-DD",
        "- Los nombres de fases en 'Tareas' deben coincidir con 'Fases'"
    ]
    
    for i, texto in enumerate(instrucciones, start=2):
        ws5[f'A{i}'] = texto
    
    ws5.column_dimensions['A'].width = 80
    
    # === Generar respuesta ===
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="plantilla-proyecto.xlsx"'
    
    wb.save(response)
    return response
```

### 1.2. Registrar ruta en `urls.py`

El action con `url_path='download-excel-template'` ya se registra automáticamente como:
```
GET /api/proyectos/download-excel-template/
```

### 1.3. Actualizar frontend para usar nuevo endpoint

**Archivo:** `import-from-excel-dialog.component.ts`

```typescript
downloadTemplate() {
  // Cambiar de archivo estático a endpoint dinámico
  const url = `${environment.apiUrl}/proyectos/download-excel-template/`;
  window.open(url, '_blank');
}
```

---

## Problema 2: No hay UI para crear plantillas

**Causa:** Solo hay fixtures, no hay CRUD de plantillas en Admin.

## Solución 2: Admin de Plantillas

### 2.1. Registrar modelos en Django Admin

**Archivo:** `apps/proyectos/admin.py`

```python
from django.contrib import admin
from .models import (
    PlantillaProyecto,
    PlantillaFase,
    PlantillaTarea,
    PlantillaDependencia
)

class PlantillaFaseInline(admin.TabularInline):
    model = PlantillaFase
    extra = 1
    fields = ['orden', 'nombre', 'descripcion', 'porcentaje_duracion']
    ordering = ['orden']

class PlantillaTareaInline(admin.TabularInline):
    model = PlantillaTarea
    extra = 1
    fields = ['orden', 'nombre', 'duracion_dias', 'priority']
    ordering = ['orden']

@admin.register(PlantillaProyecto)
class PlantillaProyectoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'categoria', 'duracion_estimada', 'is_active', 'created_at']
    list_filter = ['categoria', 'is_active']
    search_fields = ['nombre', 'descripcion']
    inlines = [PlantillaFaseInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'descripcion', 'categoria', 'icono')
        }),
        ('Configuración', {
            'fields': ('duracion_estimada', 'is_active')
        }),
    )

@admin.register(PlantillaFase)
class PlantillaFaseAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'plantilla_proyecto', 'orden', 'porcentaje_duracion']
    list_filter = ['plantilla_proyecto']
    search_fields = ['nombre', 'plantilla_proyecto__nombre']
    ordering = ['plantilla_proyecto', 'orden']
    inlines = [PlantillaTareaInline]

@admin.register(PlantillaTarea)
class PlantillaTareaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'plantilla_fase', 'orden', 'duracion_dias', 'priority']
    list_filter = ['priority', 'plantilla_fase__plantilla_proyecto']
    search_fields = ['nombre', 'plantilla_fase__nombre']
    ordering = ['plantilla_fase', 'orden']

@admin.register(PlantillaDependencia)
class PlantillaDependenciaAdmin(admin.ModelAdmin):
    list_display = ['tarea_predecesora', 'tarea_sucesora', 'tipo_dependencia', 'lag_time']
    list_filter = ['tipo_dependencia']
    search_fields = [
        'tarea_predecesora__nombre',
        'tarea_sucesora__nombre'
    ]
```

### 2.2. Cargar fixtures base

```bash
python manage.py load_base_templates --company <uuid-de-tu-tenant>
```

### 2.3. Acceso en Django Admin

1. Ir a: `http://localhost:8000/admin/proyectos/plantillaproyecto/`
2. Crear/editar plantillas desde la interfaz admin
3. Fases y tareas se crean inline dentro de cada plantilla

---

## Problema 3: Falta logo del tenant en PDF

### Solución: Agregar campo logo en modelo Company

**Archivo:** `apps/core/models.py` (o donde esté el modelo Company)

```python
class Company(BaseModel):
    # ... campos existentes ...
    
    logo = models.ImageField(
        upload_to='company_logos/',
        null=True,
        blank=True,
        help_text="Logo de la empresa para reportes PDF"
    )
```

**Migración:**
```bash
python manage.py makemigrations
python manage.py migrate
```

**Actualizar en Admin:**
```python
# apps/core/admin.py
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'nit', 'is_active', 'created_at']
    fields = ['name', 'nit', 'logo', 'is_active']  # Agregar logo
```

**Subir logo:**
1. Ir a `/admin/core/company/`
2. Editar tu empresa
3. Subir imagen de logo
4. Guardar

---

## Validación completa

### Bug #1: Excel Template
- [ ] Endpoint `/download-excel-template/` funciona
- [ ] Excel se descarga correctamente
- [ ] Excel se abre sin errores
- [ ] Contiene 5 hojas: Datos Proyecto, Fases, Tareas, Dependencias, Instrucciones
- [ ] Headers con estilo azul corporativo
- [ ] Datos de ejemplo presentes

### Bug #2: CRUD Plantillas
- [ ] Modelos registrados en Django Admin
- [ ] Se pueden crear plantillas desde admin
- [ ] Inlines de Fases y Tareas funcionan
- [ ] Fixtures cargan correctamente
- [ ] Plantillas visibles en frontend

### Bug #3: Logo en PDF
- [ ] Campo `logo` agregado a Company
- [ ] Logo visible en Django Admin
- [ ] Logo se carga en PDF correctamente
- [ ] PDF muestra logo del tenant

## Archivos modificados
- `apps/proyectos/views.py` (nuevo endpoint download_excel_template)
- `apps/proyectos/admin.py` (registrar PlantillaProyecto*)
- `apps/core/models.py` (campo logo en Company)
- `apps/core/admin.py` (mostrar logo en admin)
- `frontend/.../import-from-excel-dialog.component.ts` (usar nuevo endpoint)

## Comando de migración
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py load_base_templates --company <uuid>
```
