# PROMPT CLAUDE CODE CLI — FASE 4: FUNCIONALIDADES MEDIA/BAJA PRIORIDAD
# Módulo Proyectos — Saicloud

**Objetivo:** Implementar las 3 funcionalidades restantes de **Media y Baja Prioridad** para completar el **100% del backlog** del Módulo de Proyectos.

**Estimación total:** 16-24 horas  
**Modelo recomendado:** Claude Sonnet 4.6  
**Herramientas:** Browser + Thinking + Multi-agent (3 agentes en paralelo)

---

## 📋 FUNCIONALIDADES A IMPLEMENTAR (3)

### **Media Prioridad (2)**

#### 1. Exportar Proyecto a PDF (4-8h)

**Ubicación:** Header del detalle del proyecto → Botón "Exportar" → Opción "PDF"  
**Complejidad:** 🟡 MEDIA

**Funcionalidad:**
- Generar informe completo del proyecto en formato PDF
- Incluir: datos generales, fases, tareas, Gantt (imagen SVG), presupuesto, Analytics
- Logo del tenant
- Formato profesional con tabla de contenidos

**Stack técnico:**
- Backend: WeasyPrint (HTML → PDF) o ReportLab
- Template HTML/CSS para el reporte
- Endpoint Django para generar PDF

---

#### 2. Plantillas de Proyecto Predefinidas (4-8h)

**Ubicación:** Crear proyecto → Opción "Desde plantilla"  
**Complejidad:** 🟡 MEDIA

**Funcionalidad:**
- Crear proyectos desde plantillas con estructura predefinida
- Incluir: fases tipo, tareas tipo, dependencias, actividades estándar
- Plantillas base: Construcción, Desarrollo Software, Evento, Marketing Campaign, Product Launch

**Stack técnico:**
- Modelo `PlantillaProyecto`, `PlantillaFase`, `PlantillaTarea`
- Endpoint clonar plantilla → proyecto real
- UI wizard o modal para seleccionar plantilla

---

### **Baja Prioridad (1)**

#### 3. Importar Proyecto desde Excel (8+h)

**Ubicación:** Lista de proyectos → Botón "Importar"  
**Complejidad:** 🔴 ALTA

**Funcionalidad:**
- Cargar proyecto completo desde archivo Excel
- Estructura predefinida: datos proyecto, fases, tareas, recursos, dependencias
- Validación robusta de estructura y datos
- Template Excel de ejemplo descargable

**Stack técnico:**
- Backend: openpyxl para leer Excel
- Validación de estructura + mapeo de columnas
- Transacción atómica (todo o nada)
- Manejo de errores detallado

---

## 🎯 METODOLOGÍA DE EJECUCIÓN

### PASO 1: Leer Contexto Completo

1. **Leer documentos obligatorios:**
   - `CLAUDE.md` — Reglas del proyecto
   - `CHECKLIST-VALIDACION.md` — Validación 4x4
   - `DECISIONS.md` — Decisiones arquitectónicas

2. **Revisar modelos existentes:**
   ```bash
   view apps/proyectos/models.py
   # Verificar: Proyecto, Fase, Tarea, ActividadSaiopen, TerceroProyecto
   ```

---

## 🔧 FEATURE #1: EXPORTAR PROYECTO A PDF

### A. Diseño del Reporte PDF

**Secciones del PDF:**

1. **Portada**
   - Logo del tenant
   - Nombre del proyecto
   - Código del proyecto
   - Fecha de generación
   - Generado por: [Usuario]

2. **Datos Generales**
   - Nombre, código, descripción
   - Cliente
   - Fecha inicio/fin planificada
   - Fecha inicio/fin real
   - Estado
   - Responsable del proyecto

3. **Resumen Ejecutivo**
   - Total fases
   - Total tareas
   - Progreso general
   - KPIs principales (completud, on-time, velocidad)

4. **Fases**
   - Tabla con todas las fases
   - Columnas: Nombre, Estado, Progreso, Fechas

5. **Tareas**
   - Tabla con todas las tareas
   - Columnas: Nombre, Fase, Responsable, Estado, Prioridad, Fechas

6. **Gantt Chart**
   - Imagen SVG del Gantt actual
   - Escala de tiempo visible

7. **Presupuesto**
   - Resumen presupuesto planificado vs real
   - Tabla de costos por categoría

8. **Analytics**
   - Gráficos de progreso
   - Métricas EVM (si disponible)

### B. Implementación Backend

#### 1. Endpoint Django

```python
# apps/proyectos/views.py
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
from apps.proyectos.services import ProyectoExportService

class ProyectoViewSet(viewsets.ModelViewSet):
    # ... código existente ...
    
    @action(detail=True, methods=['get'], url_path='export/pdf')
    def export_pdf(self, request, pk=None):
        """
        Exportar proyecto completo a PDF.
        
        Query params:
        - include_gantt: bool (default True)
        - include_budget: bool (default True)
        - include_analytics: bool (default True)
        """
        proyecto = self.get_object()
        
        # Opciones de exportación
        options = {
            'include_gantt': request.query_params.get('include_gantt', 'true').lower() == 'true',
            'include_budget': request.query_params.get('include_budget', 'true').lower() == 'true',
            'include_analytics': request.query_params.get('include_analytics', 'true').lower() == 'true'
        }
        
        # Generar PDF
        pdf_content = ProyectoExportService.generate_pdf(
            proyecto=proyecto,
            user=request.user,
            options=options
        )
        
        # Retornar PDF
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="proyecto_{proyecto.codigo}.pdf"'
        
        return response
```

#### 2. Servicio de Exportación

```python
# apps/proyectos/services/export_service.py
from weasyprint import HTML, CSS
from django.template.loader import render_to_string
from django.conf import settings
import base64

class ProyectoExportService:
    
    @staticmethod
    def generate_pdf(proyecto, user, options):
        """
        Genera PDF del proyecto usando WeasyPrint.
        
        Returns:
            bytes: Contenido del PDF
        """
        # Preparar datos para el template
        context = ProyectoExportService._prepare_context(proyecto, user, options)
        
        # Renderizar HTML desde template
        html_string = render_to_string('proyectos/export/pdf_report.html', context)
        
        # CSS para el PDF
        css_string = ProyectoExportService._get_pdf_css()
        
        # Generar PDF
        pdf = HTML(string=html_string).write_pdf(
            stylesheets=[CSS(string=css_string)]
        )
        
        return pdf
    
    @staticmethod
    def _prepare_context(proyecto, user, options):
        """
        Prepara el contexto con todos los datos necesarios.
        """
        from apps/proyectos.serializers import ProyectoDetailSerializer
        
        # Datos del proyecto
        proyecto_data = ProyectoDetailSerializer(proyecto).data
        
        # Fases
        fases = proyecto.fases.all().order_by('orden')
        
        # Tareas
        tareas = Tarea.objects.filter(
            fase__proyecto=proyecto
        ).select_related(
            'fase', 'assigned_to', 'created_by'
        ).order_by('fase__orden', 'orden')
        
        # KPIs
        kpis = proyecto.get_analytics_kpis()
        
        # Gantt SVG (si se incluye)
        gantt_svg = None
        if options['include_gantt']:
            gantt_svg = ProyectoExportService._get_gantt_svg(proyecto)
        
        # Presupuesto (si se incluye)
        budget_data = None
        if options['include_budget']:
            budget_data = proyecto.get_budget_summary()
        
        # Logo del tenant (base64)
        tenant_logo = ProyectoExportService._get_tenant_logo_base64(proyecto.company)
        
        return {
            'proyecto': proyecto_data,
            'fases': fases,
            'tareas': tareas,
            'kpis': kpis,
            'gantt_svg': gantt_svg,
            'budget_data': budget_data,
            'tenant_logo': tenant_logo,
            'generated_by': user.get_full_name(),
            'generated_at': timezone.now(),
            'options': options
        }
    
    @staticmethod
    def _get_gantt_svg(proyecto):
        """
        Genera SVG del Gantt chart.
        Puede ser desde el frontend o generado en backend.
        """
        # Opción 1: Solicitar al frontend via API interno
        # Opción 2: Generar SVG en backend con librería Python
        # Para simplificar, devolver placeholder
        return '<svg>...</svg>'
    
    @staticmethod
    def _get_tenant_logo_base64(company):
        """
        Obtiene el logo del tenant en base64 para embeber en PDF.
        """
        if company.logo:
            import base64
            with open(company.logo.path, 'rb') as f:
                logo_data = f.read()
                return f"data:image/png;base64,{base64.b64encode(logo_data).decode()}"
        return None
    
    @staticmethod
    def _get_pdf_css():
        """
        CSS optimizado para PDF.
        """
        return """
        @page {
            size: A4;
            margin: 2cm;
        }
        
        body {
            font-family: 'Helvetica', 'Arial', sans-serif;
            font-size: 10pt;
            line-height: 1.4;
            color: #333;
        }
        
        h1 {
            font-size: 18pt;
            color: #1a237e;
            page-break-after: avoid;
        }
        
        h2 {
            font-size: 14pt;
            color: #1a237e;
            margin-top: 20px;
            page-break-after: avoid;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 15px;
            page-break-inside: avoid;
        }
        
        th {
            background-color: #1a237e;
            color: white;
            padding: 8px;
            text-align: left;
            font-weight: bold;
        }
        
        td {
            padding: 6px 8px;
            border-bottom: 1px solid #ddd;
        }
        
        tr:nth-child(even) {
            background-color: #f5f5f5;
        }
        
        .cover-page {
            text-align: center;
            page-break-after: always;
        }
        
        .section {
            page-break-inside: avoid;
            margin-bottom: 30px;
        }
        
        .gantt-chart {
            max-width: 100%;
            page-break-inside: avoid;
        }
        """
```

#### 3. Template HTML

```html
<!-- apps/proyectos/templates/proyectos/export/pdf_report.html -->
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Proyecto {{ proyecto.nombre }}</title>
</head>
<body>
    <!-- PORTADA -->
    <div class="cover-page">
        {% if tenant_logo %}
        <img src="{{ tenant_logo }}" alt="Logo" style="max-width: 200px; margin-bottom: 40px;">
        {% endif %}
        
        <h1 style="font-size: 24pt; margin-bottom: 10px;">{{ proyecto.nombre }}</h1>
        <p style="font-size: 14pt; color: #666;">Código: {{ proyecto.codigo }}</p>
        
        <div style="margin-top: 60px;">
            <p>Generado por: {{ generated_by }}</p>
            <p>Fecha: {{ generated_at|date:"d/m/Y H:i" }}</p>
        </div>
    </div>
    
    <!-- DATOS GENERALES -->
    <div class="section">
        <h1>1. Datos Generales</h1>
        <table>
            <tr>
                <th>Campo</th>
                <th>Valor</th>
            </tr>
            <tr>
                <td>Nombre</td>
                <td>{{ proyecto.nombre }}</td>
            </tr>
            <tr>
                <td>Código</td>
                <td>{{ proyecto.codigo }}</td>
            </tr>
            <tr>
                <td>Estado</td>
                <td>{{ proyecto.get_status_display }}</td>
            </tr>
            <tr>
                <td>Fecha Inicio Planificada</td>
                <td>{{ proyecto.planned_start|date:"d/m/Y" }}</td>
            </tr>
            <tr>
                <td>Fecha Fin Planificada</td>
                <td>{{ proyecto.planned_end|date:"d/m/Y" }}</td>
            </tr>
        </table>
    </div>
    
    <!-- RESUMEN EJECUTIVO -->
    <div class="section">
        <h1>2. Resumen Ejecutivo</h1>
        <table>
            <tr>
                <th>Métrica</th>
                <th>Valor</th>
            </tr>
            <tr>
                <td>Total Fases</td>
                <td>{{ fases|length }}</td>
            </tr>
            <tr>
                <td>Total Tareas</td>
                <td>{{ tareas|length }}</td>
            </tr>
            <tr>
                <td>Progreso General</td>
                <td>{{ proyecto.progreso_global }}%</td>
            </tr>
            {% for kpi in kpis %}
            <tr>
                <td>{{ kpi.name }}</td>
                <td>{{ kpi.value }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>
    
    <!-- FASES -->
    <div class="section">
        <h1>3. Fases del Proyecto</h1>
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Nombre</th>
                    <th>Estado</th>
                    <th>Progreso</th>
                    <th>Fecha Inicio</th>
                    <th>Fecha Fin</th>
                </tr>
            </thead>
            <tbody>
                {% for fase in fases %}
                <tr>
                    <td>{{ forloop.counter }}</td>
                    <td>{{ fase.nombre }}</td>
                    <td>{{ fase.get_status_display }}</td>
                    <td>{{ fase.progreso }}%</td>
                    <td>{{ fase.planned_start|date:"d/m/Y"|default:"-" }}</td>
                    <td>{{ fase.planned_end|date:"d/m/Y"|default:"-" }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    
    <!-- TAREAS -->
    <div class="section">
        <h1>4. Tareas del Proyecto</h1>
        <table>
            <thead>
                <tr>
                    <th>Tarea</th>
                    <th>Fase</th>
                    <th>Responsable</th>
                    <th>Estado</th>
                    <th>Prioridad</th>
                    <th>Fecha Fin</th>
                </tr>
            </thead>
            <tbody>
                {% for tarea in tareas %}
                <tr>
                    <td>{{ tarea.nombre }}</td>
                    <td>{{ tarea.fase.nombre }}</td>
                    <td>{{ tarea.assigned_to.get_full_name|default:"-" }}</td>
                    <td>{{ tarea.get_status_display }}</td>
                    <td>{{ tarea.get_priority_display }}</td>
                    <td>{{ tarea.planned_end|date:"d/m/Y"|default:"-" }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    
    <!-- GANTT (si se incluye) -->
    {% if gantt_svg %}
    <div class="section">
        <h1>5. Diagrama de Gantt</h1>
        <div class="gantt-chart">
            {{ gantt_svg|safe }}
        </div>
    </div>
    {% endif %}
    
    <!-- PRESUPUESTO (si se incluye) -->
    {% if budget_data %}
    <div class="section">
        <h1>6. Presupuesto</h1>
        <table>
            <tr>
                <th>Concepto</th>
                <th>Planificado</th>
                <th>Real</th>
                <th>Varianza</th>
            </tr>
            <tr>
                <td>Mano de Obra</td>
                <td>${{ budget_data.labor_planned|floatformat:2 }}</td>
                <td>${{ budget_data.labor_actual|floatformat:2 }}</td>
                <td>${{ budget_data.labor_variance|floatformat:2 }}</td>
            </tr>
            <tr>
                <td>Gastos Directos</td>
                <td>${{ budget_data.expenses_planned|floatformat:2 }}</td>
                <td>${{ budget_data.expenses_actual|floatformat:2 }}</td>
                <td>${{ budget_data.expenses_variance|floatformat:2 }}</td>
            </tr>
            <tr style="font-weight: bold;">
                <td>TOTAL</td>
                <td>${{ budget_data.total_planned|floatformat:2 }}</td>
                <td>${{ budget_data.total_actual|floatformat:2 }}</td>
                <td>${{ budget_data.total_variance|floatformat:2 }}</td>
            </tr>
        </table>
    </div>
    {% endif %}
</body>
</html>
```

### C. Implementación Frontend

```typescript
// proyecto-detail.component.ts
exportToPDF() {
  this.loading.set(true);
  
  this.proyectoService.exportPDF(this.proyectoId()).subscribe({
    next: (blob) => {
      // Descargar PDF
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `proyecto_${this.proyecto()!.codigo}.pdf`;
      link.click();
      window.URL.revokeObjectURL(url);
      
      this.snackBar.open('PDF generado exitosamente', 'Cerrar', {
        duration: 3000,
        panelClass: ['snack-success']
      });
    },
    error: (err) => {
      console.error('Error al generar PDF:', err);
      this.snackBar.open('Error al generar PDF', 'Cerrar', {
        duration: 3000,
        panelClass: ['snack-error']
      });
    },
    complete: () => {
      this.loading.set(false);
    }
  });
}
```

```typescript
// proyecto.service.ts
exportPDF(proyectoId: string): Observable<Blob> {
  return this.http.get(
    `${this.apiUrl}/proyectos/${proyectoId}/export/pdf/`,
    { responseType: 'blob' }
  );
}
```

```html
<!-- proyecto-detail.component.html -->
<button 
  mat-menu-item 
  (click)="exportToPDF()"
  [disabled]="loading()"
>
  <mat-icon>picture_as_pdf</mat-icon>
  <span>Exportar a PDF</span>
</button>
```

### D. Instalación de WeasyPrint

```bash
# requirements.txt
weasyprint==60.1
```

```bash
# Instalación de dependencias sistema (Ubuntu/Debian)
sudo apt-get install python3-dev python3-pip python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
```

### E. Validación

**Checklist:**
- [ ] PDF se genera correctamente
- [ ] Incluye todas las secciones esperadas
- [ ] Logo del tenant visible
- [ ] Tablas formateadas correctamente
- [ ] Paginación adecuada (no corta contenido)
- [ ] Descarga funciona en navegador
- [ ] Performance aceptable (<10s para proyecto típico)

**Validación 4x4:**
- [ ] Desktop Light: Botón funciona ✅
- [ ] Desktop Dark: Botón funciona ✅
- [ ] Mobile Light: Botón funciona ✅
- [ ] Mobile Dark: Botón funciona ✅

---

## 🔧 FEATURE #2: PLANTILLAS DE PROYECTO

### A. Modelos de Plantilla

```python
# apps/proyectos/models.py

class PlantillaProyecto(BaseModel):
    """
    Plantilla predefinida de proyecto.
    """
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    categoria = models.CharField(
        max_length=50,
        choices=[
            ('construccion', 'Construcción'),
            ('software', 'Desarrollo Software'),
            ('evento', 'Evento'),
            ('marketing', 'Marketing Campaign'),
            ('product_launch', 'Product Launch')
        ]
    )
    icono = models.CharField(max_length=50, blank=True)  # Material icon name
    is_active = models.BooleanField(default=True)
    
    # Duración estimada en días
    duracion_estimada = models.IntegerField(default=30)
    
    class Meta:
        verbose_name = 'Plantilla de Proyecto'
        verbose_name_plural = 'Plantillas de Proyecto'
        ordering = ['categoria', 'nombre']
    
    def __str__(self):
        return f"{self.get_categoria_display()} - {self.nombre}"


class PlantillaFase(BaseModel):
    """
    Fase tipo dentro de una plantilla de proyecto.
    """
    plantilla_proyecto = models.ForeignKey(
        PlantillaProyecto,
        on_delete=models.CASCADE,
        related_name='fases_plantilla'
    )
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    orden = models.IntegerField(default=0)
    
    # Porcentaje del total de duración
    porcentaje_duracion = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="% de duración respecto al total del proyecto"
    )
    
    class Meta:
        verbose_name = 'Plantilla de Fase'
        verbose_name_plural = 'Plantillas de Fase'
        ordering = ['plantilla_proyecto', 'orden']
        unique_together = [['plantilla_proyecto', 'orden']]
    
    def __str__(self):
        return f"{self.plantilla_proyecto.nombre} - {self.nombre}"


class PlantillaTarea(BaseModel):
    """
    Tarea tipo dentro de una fase de plantilla.
    """
    plantilla_fase = models.ForeignKey(
        PlantillaFase,
        on_delete=models.CASCADE,
        related_name='tareas_plantilla'
    )
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    orden = models.IntegerField(default=0)
    
    # Duración estimada en días
    duracion_dias = models.IntegerField(default=1)
    
    # Prioridad por defecto
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium'
    )
    
    # Actividad Saiopen asociada (opcional)
    actividad_saiopen = models.ForeignKey(
        'ActividadSaiopen',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='plantillas_tarea'
    )
    
    class Meta:
        verbose_name = 'Plantilla de Tarea'
        verbose_name_plural = 'Plantillas de Tarea'
        ordering = ['plantilla_fase', 'orden']
        unique_together = [['plantilla_fase', 'orden']]
    
    def __str__(self):
        return f"{self.plantilla_fase.nombre} - {self.nombre}"


class PlantillaDependencia(BaseModel):
    """
    Dependencia entre tareas de plantilla.
    """
    tarea_predecesora = models.ForeignKey(
        PlantillaTarea,
        on_delete=models.CASCADE,
        related_name='dependencias_sucesoras_plantilla'
    )
    tarea_sucesora = models.ForeignKey(
        PlantillaTarea,
        on_delete=models.CASCADE,
        related_name='dependencias_predecesoras_plantilla'
    )
    tipo_dependencia = models.CharField(
        max_length=5,
        choices=DEPENDENCY_TYPE_CHOICES,
        default='FS'
    )
    lag_time = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = 'Dependencia de Plantilla'
        verbose_name_plural = 'Dependencias de Plantilla'
        unique_together = [['tarea_predecesora', 'tarea_sucesora']]
```

### B. Servicio de Clonación

```python
# apps/proyectos/services/template_service.py

class PlantillaProyectoService:
    
    @staticmethod
    @transaction.atomic
    def create_from_template(
        template_id: str,
        nombre: str,
        company,
        user,
        planned_start: date,
        **kwargs
    ) -> Proyecto:
        """
        Crea un proyecto desde una plantilla.
        
        Args:
            template_id: ID de la plantilla
            nombre: Nombre del nuevo proyecto
            company: Empresa
            user: Usuario creador
            planned_start: Fecha de inicio planificada
            **kwargs: Otros campos del proyecto
        
        Returns:
            Proyecto creado con todas sus fases y tareas
        """
        template = PlantillaProyecto.objects.get(pk=template_id)
        
        # Crear proyecto base
        proyecto = Proyecto.objects.create(
            company=company,
            nombre=nombre,
            descripcion=kwargs.get('descripcion', template.descripcion),
            planned_start=planned_start,
            planned_end=planned_start + timedelta(days=template.duracion_estimada),
            created_by=user,
            **{k: v for k, v in kwargs.items() if k != 'descripcion'}
        )
        
        # Mapeo de IDs: plantilla → real
        fase_map = {}
        tarea_map = {}
        
        # Clonar fases
        for fase_template in template.fases_plantilla.all():
            # Calcular fechas de la fase
            fase_duration = int(template.duracion_estimada * (fase_template.porcentaje_duracion / 100))
            fase_start = planned_start
            if fase_map:
                # Empezar después de la última fase
                last_fase = list(fase_map.values())[-1]
                fase_start = last_fase.planned_end + timedelta(days=1)
            
            fase = Fase.objects.create(
                company=company,
                proyecto=proyecto,
                nombre=fase_template.nombre,
                descripcion=fase_template.descripcion,
                orden=fase_template.orden,
                planned_start=fase_start,
                planned_end=fase_start + timedelta(days=fase_duration),
                created_by=user
            )
            
            fase_map[fase_template.id] = fase
            
            # Clonar tareas de la fase
            for tarea_template in fase_template.tareas_plantilla.all():
                tarea_start = fase.planned_start
                if tarea_map:
                    # Calcular start según dependencias (simplificado)
                    # En producción, calcular con algoritmo de scheduling
                    tarea_start = fase.planned_start + timedelta(days=tarea_template.orden * tarea_template.duracion_dias)
                
                tarea = Tarea.objects.create(
                    company=company,
                    fase=fase,
                    nombre=tarea_template.nombre,
                    descripcion=tarea_template.descripcion,
                    orden=tarea_template.orden,
                    priority=tarea_template.priority,
                    planned_start=tarea_start,
                    planned_end=tarea_start + timedelta(days=tarea_template.duracion_dias),
                    created_by=user
                )
                
                # Asignar actividad Saiopen si existe
                if tarea_template.actividad_saiopen:
                    ActividadProyecto.objects.create(
                        company=company,
                        proyecto=proyecto,
                        tarea=tarea,
                        actividad=tarea_template.actividad_saiopen,
                        cantidad_planificada=1,
                        created_by=user
                    )
                
                tarea_map[tarea_template.id] = tarea
        
        # Clonar dependencias
        for dep_template in PlantillaDependencia.objects.filter(
            tarea_predecesora__plantilla_fase__plantilla_proyecto=template
        ):
            TareaDependencia.objects.create(
                company=company,
                tarea_predecesora=tarea_map[dep_template.tarea_predecesora.id],
                tarea_sucesora=tarea_map[dep_template.tarea_sucesora.id],
                tipo_dependencia=dep_template.tipo_dependencia,
                lag_time=dep_template.lag_time,
                created_by=user
            )
        
        return proyecto
```

### C. Endpoint y Serializers

```python
# apps/proyectos/views.py

@action(detail=False, methods=['get'], url_path='templates')
def list_templates(self, request):
    """
    Lista todas las plantillas de proyecto disponibles.
    """
    templates = PlantillaProyecto.objects.filter(is_active=True)
    serializer = PlantillaProyectoSerializer(templates, many=True)
    return Response(serializer.data)

@action(detail=False, methods=['post'], url_path='create-from-template')
def create_from_template(self, request):
    """
    Crear proyecto desde plantilla.
    
    Body:
    {
        "template_id": "uuid",
        "nombre": "Nuevo Proyecto",
        "descripcion": "...",
        "planned_start": "2026-04-01",
        "cliente_id": "uuid" (opcional)
    }
    """
    serializer = CreateFromTemplateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    proyecto = PlantillaProyectoService.create_from_template(
        template_id=serializer.validated_data['template_id'],
        nombre=serializer.validated_data['nombre'],
        company=request.user.company,
        user=request.user,
        planned_start=serializer.validated_data['planned_start'],
        descripcion=serializer.validated_data.get('descripcion', ''),
        cliente_id=serializer.validated_data.get('cliente_id')
    )
    
    return Response(
        ProyectoDetailSerializer(proyecto).data,
        status=status.HTTP_201_CREATED
    )
```

### D. Frontend - Selección de Plantilla

```typescript
// create-from-template-dialog.component.ts

@Component({
  selector: 'app-create-from-template-dialog',
  templateUrl: './create-from-template-dialog.component.html',
  styleUrls: ['./create-from-template-dialog.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class CreateFromTemplateDialogComponent implements OnInit {
  templates = signal<PlantillaProyecto[]>([]);
  selectedTemplate = signal<PlantillaProyecto | null>(null);
  loading = signal(false);
  
  form = this.fb.group({
    nombre: ['', [Validators.required, Validators.maxLength(200)]],
    descripcion: [''],
    planned_start: [new Date(), Validators.required],
    cliente_id: [null]
  });
  
  constructor(
    private fb: FormBuilder,
    private proyectoService: ProyectoService,
    private dialogRef: MatDialogRef<CreateFromTemplateDialogComponent>,
    private snackBar: MatSnackBar
  ) {}
  
  ngOnInit() {
    this.loadTemplates();
  }
  
  loadTemplates() {
    this.loading.set(true);
    this.proyectoService.getTemplates().subscribe({
      next: (templates) => {
        this.templates.set(templates);
        this.loading.set(false);
      },
      error: (err) => {
        console.error('Error loading templates:', err);
        this.loading.set(false);
      }
    });
  }
  
  selectTemplate(template: PlantillaProyecto) {
    this.selectedTemplate.set(template);
    this.form.patchValue({
      descripcion: template.descripcion
    });
  }
  
  createProject() {
    if (!this.selectedTemplate() || this.form.invalid) return;
    
    this.loading.set(true);
    
    const data = {
      template_id: this.selectedTemplate()!.id,
      ...this.form.value
    };
    
    this.proyectoService.createFromTemplate(data).subscribe({
      next: (proyecto) => {
        this.snackBar.open('Proyecto creado desde plantilla', 'Cerrar', {
          duration: 3000,
          panelClass: ['snack-success']
        });
        this.dialogRef.close(proyecto);
      },
      error: (err) => {
        console.error('Error creating project:', err);
        this.snackBar.open('Error al crear proyecto', 'Cerrar', {
          duration: 3000,
          panelClass: ['snack-error']
        });
        this.loading.set(false);
      }
    });
  }
}
```

```html
<!-- create-from-template-dialog.component.html -->
<h2 mat-dialog-title>Crear Proyecto desde Plantilla</h2>

<mat-dialog-content>
  @if (loading()) {
    <mat-progress-bar mode="indeterminate"></mat-progress-bar>
  }
  
  <!-- Paso 1: Seleccionar plantilla -->
  @if (!selectedTemplate()) {
    <h3>Selecciona una plantilla</h3>
    
    <div class="templates-grid">
      @for (template of templates(); track template.id) {
        <mat-card class="template-card" (click)="selectTemplate(template)">
          <mat-card-header>
            <mat-icon mat-card-avatar>{{ template.icono || 'folder' }}</mat-icon>
            <mat-card-title>{{ template.nombre }}</mat-card-title>
            <mat-card-subtitle>{{ template.get_categoria_display }}</mat-card-subtitle>
          </mat-card-header>
          <mat-card-content>
            <p>{{ template.descripcion }}</p>
            <p class="template-meta">
              <mat-icon>schedule</mat-icon>
              {{ template.duracion_estimada }} días estimados
            </p>
          </mat-card-content>
        </mat-card>
      }
    </div>
  }
  
  <!-- Paso 2: Configurar proyecto -->
  @if (selectedTemplate()) {
    <div class="selected-template">
      <p>
        <strong>Plantilla seleccionada:</strong> {{ selectedTemplate()!.nombre }}
        <button mat-icon-button (click)="selectedTemplate.set(null)">
          <mat-icon>close</mat-icon>
        </button>
      </p>
    </div>
    
    <form [formGroup]="form">
      <mat-form-field appearance="outline" class="full-width">
        <mat-label>Nombre del Proyecto</mat-label>
        <input matInput formControlName="nombre" required>
        @if (form.get('nombre')?.hasError('required')) {
          <mat-error>El nombre es requerido</mat-error>
        }
      </mat-form-field>
      
      <mat-form-field appearance="outline" class="full-width">
        <mat-label>Descripción</mat-label>
        <textarea matInput formControlName="descripcion" rows="3"></textarea>
      </mat-form-field>
      
      <mat-form-field appearance="outline" class="full-width">
        <mat-label>Fecha de Inicio</mat-label>
        <input matInput [matDatepicker]="picker" formControlName="planned_start" required>
        <mat-datepicker-toggle matSuffix [for]="picker"></mat-datepicker-toggle>
        <mat-datepicker #picker></mat-datepicker>
      </mat-form-field>
    </form>
  }
</mat-dialog-content>

<mat-dialog-actions align="end">
  <button mat-button (click)="dialogRef.close()">Cancelar</button>
  
  @if (selectedTemplate()) {
    <button 
      mat-raised-button 
      color="primary" 
      (click)="createProject()"
      [disabled]="form.invalid || loading()"
    >
      Crear Proyecto
    </button>
  }
</mat-dialog-actions>
```

### E. Fixtures de Plantillas Base

```python
# apps/proyectos/fixtures/plantillas.json

[
  {
    "model": "proyectos.plantillaproyecto",
    "pk": "uuid-plantilla-construccion",
    "fields": {
      "nombre": "Proyecto de Construcción",
      "descripcion": "Plantilla estándar para proyectos de construcción",
      "categoria": "construccion",
      "icono": "construction",
      "duracion_estimada": 180,
      "is_active": true
    }
  },
  {
    "model": "proyectos.plantillafase",
    "pk": "uuid-fase-1",
    "fields": {
      "plantilla_proyecto": "uuid-plantilla-construccion",
      "nombre": "Planificación",
      "descripcion": "Fase inicial de planificación y diseño",
      "orden": 1,
      "porcentaje_duracion": 15
    }
  },
  {
    "model": "proyectos.plantillatarea",
    "pk": "uuid-tarea-1",
    "fields": {
      "plantilla_fase": "uuid-fase-1",
      "nombre": "Levantamiento topográfico",
      "descripcion": "Realizar levantamiento del terreno",
      "orden": 1,
      "duracion_dias": 5,
      "priority": "high"
    }
  }
  // ... más plantillas
]
```

### F. Validación

**Checklist:**
- [ ] Plantillas cargan correctamente
- [ ] Modal de selección funciona
- [ ] Proyecto se crea con todas las fases y tareas
- [ ] Dependencias se clonan correctamente
- [ ] Fechas calculadas lógicamente
- [ ] Actividades Saiopen asociadas

**Validación 4x4:**
- [ ] Desktop Light/Dark: Modal se ve bien ✅
- [ ] Mobile Light/Dark: Cards responsive ✅

---

## 🔧 FEATURE #3: IMPORTAR DESDE EXCEL

**NOTA:** Esta feature es la más compleja (8+h). Se recomienda implementar DESPUÉS de las anteriores.

### A. Estructura del Excel

```
Hoja 1: Datos Proyecto
| Campo         | Valor                    |
|---------------|--------------------------|
| Nombre        | Proyecto Importado       |
| Código        | PRY-001                  |
| Descripción   | Descripción del proyecto |
| Fecha Inicio  | 2026-04-01               |
| Fecha Fin     | 2026-12-31               |

Hoja 2: Fases
| Orden | Nombre           | Descripción       | Fecha Inicio | Fecha Fin  |
|-------|------------------|-------------------|--------------|------------|
| 1     | Fase 1           | Descripción F1    | 2026-04-01   | 2026-06-01 |
| 2     | Fase 2           | Descripción F2    | 2026-06-02   | 2026-09-01 |

Hoja 3: Tareas
| Fase  | Orden | Nombre    | Descripción | Prioridad | Fecha Inicio | Fecha Fin  |
|-------|-------|-----------|-------------|-----------|--------------|------------|
| Fase 1| 1     | Tarea 1.1 | Desc T1.1   | high      | 2026-04-01   | 2026-04-15 |
| Fase 1| 2     | Tarea 1.2 | Desc T1.2   | medium    | 2026-04-16   | 2026-05-01 |

Hoja 4: Dependencias
| Tarea Predecesora | Tarea Sucesora | Tipo | Lag (días) |
|-------------------|----------------|------|------------|
| Tarea 1.1         | Tarea 1.2      | FS   | 0          |
```

### B. Servicio de Importación

```python
# apps/proyectos/services/import_service.py

import openpyxl
from datetime import datetime

class ProyectoImportService:
    
    @staticmethod
    @transaction.atomic
    def import_from_excel(file, company, user):
        """
        Importa proyecto completo desde Excel.
        
        Args:
            file: UploadedFile object
            company: Company
            user: User
        
        Returns:
            dict: {'success': bool, 'proyecto': Proyecto, 'errors': []}
        """
        errors = []
        
        try:
            # Cargar workbook
            wb = openpyxl.load_workbook(file, data_only=True)
            
            # Validar estructura
            required_sheets = ['Datos Proyecto', 'Fases', 'Tareas']
            for sheet_name in required_sheets:
                if sheet_name not in wb.sheetnames:
                    errors.append(f"Falta hoja requerida: {sheet_name}")
            
            if errors:
                return {'success': False, 'errors': errors}
            
            # 1. Leer datos del proyecto
            proyecto_data = ProyectoImportService._read_proyecto_data(wb['Datos Proyecto'])
            
            # 2. Crear proyecto
            proyecto = Proyecto.objects.create(
                company=company,
                nombre=proyecto_data['nombre'],
                codigo=proyecto_data.get('codigo'),
                descripcion=proyecto_data.get('descripcion', ''),
                planned_start=proyecto_data['fecha_inicio'],
                planned_end=proyecto_data['fecha_fin'],
                created_by=user
            )
            
            # 3. Leer y crear fases
            fases_data = ProyectoImportService._read_fases_data(wb['Fases'])
            fase_map = {}  # nombre → objeto
            
            for fase_data in fases_data:
                fase = Fase.objects.create(
                    company=company,
                    proyecto=proyecto,
                    nombre=fase_data['nombre'],
                    descripcion=fase_data.get('descripcion', ''),
                    orden=fase_data['orden'],
                    planned_start=fase_data['fecha_inicio'],
                    planned_end=fase_data['fecha_fin'],
                    created_by=user
                )
                fase_map[fase_data['nombre']] = fase
            
            # 4. Leer y crear tareas
            tareas_data = ProyectoImportService._read_tareas_data(wb['Tareas'])
            tarea_map = {}  # nombre → objeto
            
            for tarea_data in tareas_data:
                fase_nombre = tarea_data['fase']
                if fase_nombre not in fase_map:
                    errors.append(f"Fase no encontrada: {fase_nombre}")
                    continue
                
                tarea = Tarea.objects.create(
                    company=company,
                    fase=fase_map[fase_nombre],
                    nombre=tarea_data['nombre'],
                    descripcion=tarea_data.get('descripcion', ''),
                    orden=tarea_data['orden'],
                    priority=tarea_data.get('prioridad', 'medium'),
                    planned_start=tarea_data['fecha_inicio'],
                    planned_end=tarea_data['fecha_fin'],
                    created_by=user
                )
                tarea_map[tarea_data['nombre']] = tarea
            
            # 5. Leer y crear dependencias (si existe hoja)
            if 'Dependencias' in wb.sheetnames:
                deps_data = ProyectoImportService._read_dependencias_data(wb['Dependencias'])
                
                for dep_data in deps_data:
                    pred_nombre = dep_data['tarea_predecesora']
                    suc_nombre = dep_data['tarea_sucesora']
                    
                    if pred_nombre not in tarea_map or suc_nombre not in tarea_map:
                        errors.append(f"Dependencia inválida: {pred_nombre} → {suc_nombre}")
                        continue
                    
                    TareaDependencia.objects.create(
                        company=company,
                        tarea_predecesora=tarea_map[pred_nombre],
                        tarea_sucesora=tarea_map[suc_nombre],
                        tipo_dependencia=dep_data.get('tipo', 'FS'),
                        lag_time=dep_data.get('lag', 0),
                        created_by=user
                    )
            
            return {
                'success': True,
                'proyecto': proyecto,
                'errors': errors,
                'stats': {
                    'fases': len(fase_map),
                    'tareas': len(tarea_map),
                    'dependencias': TareaDependencia.objects.filter(
                        tarea_predecesora__fase__proyecto=proyecto
                    ).count()
                }
            }
            
        except Exception as e:
            logger.exception("Error importing project from Excel")
            return {
                'success': False,
                'errors': [f"Error general: {str(e)}"]
            }
    
    @staticmethod
    def _read_proyecto_data(sheet):
        """
        Lee datos del proyecto desde hoja de Excel.
        Formato: | Campo | Valor |
        """
        data = {}
        for row in sheet.iter_rows(min_row=2, values_only=True):
            campo, valor = row[0], row[1]
            if campo:
                campo_lower = campo.lower().strip()
                if 'nombre' in campo_lower:
                    data['nombre'] = str(valor)
                elif 'código' in campo_lower or 'codigo' in campo_lower:
                    data['codigo'] = str(valor) if valor else None
                elif 'descripción' in campo_lower or 'descripcion' in campo_lower:
                    data['descripcion'] = str(valor) if valor else ''
                elif 'fecha inicio' in campo_lower:
                    data['fecha_inicio'] = ProyectoImportService._parse_date(valor)
                elif 'fecha fin' in campo_lower:
                    data['fecha_fin'] = ProyectoImportService._parse_date(valor)
        
        # Validar campos requeridos
        required = ['nombre', 'fecha_inicio', 'fecha_fin']
        for field in required:
            if field not in data:
                raise ValueError(f"Campo requerido faltante: {field}")
        
        return data
    
    @staticmethod
    def _read_fases_data(sheet):
        """
        Lee fases desde hoja de Excel.
        Formato: | Orden | Nombre | Descripción | Fecha Inicio | Fecha Fin |
        """
        fases = []
        header_row = next(sheet.iter_rows(min_row=1, max_row=1, values_only=True))
        
        for row in sheet.iter_rows(min_row=2, values_only=True):
            if not row[0]:  # Skip empty rows
                continue
            
            fase = {
                'orden': int(row[0]),
                'nombre': str(row[1]),
                'descripcion': str(row[2]) if row[2] else '',
                'fecha_inicio': ProyectoImportService._parse_date(row[3]),
                'fecha_fin': ProyectoImportService._parse_date(row[4])
            }
            fases.append(fase)
        
        return fases
    
    @staticmethod
    def _read_tareas_data(sheet):
        """
        Lee tareas desde hoja de Excel.
        """
        tareas = []
        for row in sheet.iter_rows(min_row=2, values_only=True):
            if not row[0]:
                continue
            
            tarea = {
                'fase': str(row[0]),
                'orden': int(row[1]),
                'nombre': str(row[2]),
                'descripcion': str(row[3]) if row[3] else '',
                'prioridad': str(row[4]).lower() if row[4] else 'medium',
                'fecha_inicio': ProyectoImportService._parse_date(row[5]),
                'fecha_fin': ProyectoImportService._parse_date(row[6])
            }
            tareas.append(tarea)
        
        return tareas
    
    @staticmethod
    def _read_dependencias_data(sheet):
        """
        Lee dependencias desde hoja de Excel.
        """
        dependencias = []
        for row in sheet.iter_rows(min_row=2, values_only=True):
            if not row[0]:
                continue
            
            dep = {
                'tarea_predecesora': str(row[0]),
                'tarea_sucesora': str(row[1]),
                'tipo': str(row[2]).upper() if row[2] else 'FS',
                'lag': int(row[3]) if row[3] else 0
            }
            dependencias.append(dep)
        
        return dependencias
    
    @staticmethod
    def _parse_date(value):
        """
        Parsea fecha desde Excel (puede ser datetime o string).
        """
        if isinstance(value, datetime):
            return value.date()
        elif isinstance(value, str):
            # Intentar parsear string
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']:
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
            raise ValueError(f"Formato de fecha inválido: {value}")
        else:
            raise ValueError(f"Tipo de fecha inválido: {type(value)}")
```

### C. Endpoint de Importación

```python
# apps/proyectos/views.py

@action(detail=False, methods=['post'], url_path='import-from-excel')
def import_from_excel(self, request):
    """
    Importar proyecto desde archivo Excel.
    
    Body (multipart/form-data):
    - file: archivo Excel
    """
    if 'file' not in request.FILES:
        return Response(
            {'error': 'Archivo requerido'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    file = request.FILES['file']
    
    # Validar extensión
    if not file.name.endswith(('.xlsx', '.xls')):
        return Response(
            {'error': 'Archivo debe ser Excel (.xlsx o .xls)'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Importar
    result = ProyectoImportService.import_from_excel(
        file=file,
        company=request.user.company,
        user=request.user
    )
    
    if result['success']:
        return Response({
            'success': True,
            'proyecto': ProyectoDetailSerializer(result['proyecto']).data,
            'stats': result['stats'],
            'warnings': result['errors']  # Errores no fatales
        }, status=status.HTTP_201_CREATED)
    else:
        return Response({
            'success': False,
            'errors': result['errors']
        }, status=status.HTTP_400_BAD_REQUEST)
```

### D. Frontend - Upload de Excel

```typescript
// import-from-excel-dialog.component.ts

@Component({
  selector: 'app-import-from-excel-dialog',
  templateUrl: './import-from-excel-dialog.component.html',
  styleUrls: ['./import-from-excel-dialog.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class ImportFromExcelDialogComponent {
  selectedFile = signal<File | null>(null);
  loading = signal(false);
  
  constructor(
    private proyectoService: ProyectoService,
    private dialogRef: MatDialogRef<ImportFromExcelDialogComponent>,
    private snackBar: MatSnackBar
  ) {}
  
  onFileSelected(event: any) {
    const file = event.target.files[0];
    if (file) {
      this.selectedFile.set(file);
    }
  }
  
  downloadTemplate() {
    // Descargar template Excel de ejemplo
    window.open('/assets/templates/plantilla-proyecto.xlsx', '_blank');
  }
  
  importProject() {
    if (!this.selectedFile()) return;
    
    this.loading.set(true);
    
    const formData = new FormData();
    formData.append('file', this.selectedFile()!);
    
    this.proyectoService.importFromExcel(formData).subscribe({
      next: (result) => {
        this.snackBar.open(`Proyecto importado: ${result.stats.fases} fases, ${result.stats.tareas} tareas`, 'Cerrar', {
          duration: 5000,
          panelClass: ['snack-success']
        });
        
        if (result.warnings?.length > 0) {
          console.warn('Import warnings:', result.warnings);
        }
        
        this.dialogRef.close(result.proyecto);
      },
      error: (err) => {
        console.error('Import error:', err);
        const errorMsg = err.error?.errors?.join(', ') || 'Error al importar proyecto';
        this.snackBar.open(errorMsg, 'Cerrar', {
          duration: 5000,
          panelClass: ['snack-error']
        });
        this.loading.set(false);
      }
    });
  }
}
```

```html
<!-- import-from-excel-dialog.component.html -->
<h2 mat-dialog-title>Importar Proyecto desde Excel</h2>

<mat-dialog-content>
  <div class="upload-section">
    <p>Selecciona un archivo Excel con la estructura del proyecto.</p>
    
    <button mat-stroked-button (click)="downloadTemplate()">
      <mat-icon>download</mat-icon>
      Descargar Plantilla de Ejemplo
    </button>
    
    <div class="file-input-wrapper">
      <input 
        type="file" 
        #fileInput 
        accept=".xlsx,.xls" 
        (change)="onFileSelected($event)"
        hidden
      >
      <button mat-raised-button (click)="fileInput.click()">
        <mat-icon>upload_file</mat-icon>
        Seleccionar Archivo
      </button>
    </div>
    
    @if (selectedFile()) {
      <div class="selected-file">
        <mat-icon>description</mat-icon>
        <span>{{ selectedFile()!.name }}</span>
        <button mat-icon-button (click)="selectedFile.set(null)">
          <mat-icon>close</mat-icon>
        </button>
      </div>
    }
  </div>
  
  @if (loading()) {
    <mat-progress-bar mode="indeterminate"></mat-progress-bar>
    <p class="importing-text">Importando proyecto...</p>
  }
</mat-dialog-content>

<mat-dialog-actions align="end">
  <button mat-button (click)="dialogRef.close()">Cancelar</button>
  <button 
    mat-raised-button 
    color="primary" 
    (click)="importProject()"
    [disabled]="!selectedFile() || loading()"
  >
    Importar
  </button>
</mat-dialog-actions>
```

### E. Validación

**Checklist:**
- [ ] Template Excel descargable
- [ ] Upload de archivo funciona
- [ ] Validación de estructura Excel
- [ ] Proyecto se crea correctamente
- [ ] Fases y tareas importadas
- [ ] Dependencias correctas
- [ ] Manejo de errores claro
- [ ] Mensajes de éxito/error

**Validación 4x4:**
- [ ] Desktop Light/Dark: Modal se ve bien ✅
- [ ] Mobile Light/Dark: Upload funciona ✅

---

## 📝 ORDEN DE EJECUCIÓN RECOMENDADO

### Día 1-2 (4-8h): Exportar a PDF

1. Modelo de datos + endpoint (2h)
2. Template HTML + CSS (2-3h)
3. Frontend + validación (2-3h)

### Día 3-4 (4-8h): Plantillas de Proyecto

1. Modelos de plantilla (1h)
2. Servicio de clonación (2-3h)
3. Frontend + fixtures (2-3h)
4. Validación (1h)

### Día 5-7 (8+h): Importar desde Excel

1. Servicio de importación (3-4h)
2. Endpoint + validaciones (2h)
3. Frontend + template Excel (2-3h)
4. Validación exhaustiva (2h)

---

## 📦 ENTREGABLES

Al finalizar la Fase 4, debes tener:

1. ✅ **Feature #1:** Exportar proyecto a PDF funcional
2. ✅ **Feature #2:** Plantillas de proyecto con 3-5 plantillas base
3. ✅ **Feature #3:** Importar desde Excel con validación robusta
4. ✅ **Template Excel** de ejemplo descargable
5. ✅ **Informe:** `INFORME_FASE_4_FUNCIONALIDADES.md`
6. ✅ **Notion actualizado** (3 tareas completadas)
7. ✅ **100% del backlog completado** (18/18 tareas) 🎉

---

## 🎯 CRITERIO DE ÉXITO

La Fase 4 está completa cuando:

- ✅ PDF se genera correctamente con todas las secciones
- ✅ Al menos 3 plantillas de proyecto funcionan
- ✅ Importación desde Excel valida y crea proyectos completos
- ✅ Template Excel de ejemplo disponible
- ✅ Validación 4x4 completa en todas las features
- ✅ Sin regresiones en funcionalidad existente
- ✅ **18/18 tareas del backlog completadas**

---

## ⚠️ REGLAS CRÍTICAS

1. **WeasyPrint:** Instalación correcta de dependencias sistema
2. **Transacciones:** SIEMPRE usar `@transaction.atomic` en imports
3. **Validación:** Excel import DEBE validar antes de crear nada
4. **Plantillas:** Fixtures en `fixtures/` directory
5. **Template Excel:** Debe incluir instrucciones claras
6. **Manejo de errores:** Mensajes claros al usuario

---

## 📞 REFERENCIAS

- **WeasyPrint:** https://doc.courtbouillon.org/weasyprint/
- **openpyxl:** https://openpyxl.readthedocs.io/
- **Checklist validación:** `docs/base-reference/CHECKLIST-VALIDACION.md`
- **Backlog Notion:** https://www.notion.so/0f5116945f4346ffa18fee534371923c

---

**¡Ejecuta la Fase 4 y completa el 100% del backlog!** 🎉🏆
