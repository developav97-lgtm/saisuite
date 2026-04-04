# PROMPT CLAUDE CODE CLI — FASE 2: FUNCIONALIDADES ALTA PRIORIDAD
# Módulo Proyectos — Saicloud

**Objetivo:** Implementar las 2 funcionalidades de **Alta Prioridad** del backlog para completar features críticas del Módulo de Proyectos.

**Estimación total:** 12-16 horas  
**Modelo recomendado:** Claude Sonnet 4.6  
**Herramientas:** Browser + Thinking + Multi-agent (3 agentes en paralelo)

---

## 📋 FUNCIONALIDADES A IMPLEMENTAR (2)

### 1. Notificaciones Automáticas de Tareas (4-8h) ⚡ PRIORITARIA

**Ubicación:** Sistema de notificaciones existente (campanita + WebSocket)  
**Estado actual:** Sistema de notificaciones YA implementado y funcionando (Fase 1-9 del Chat)  
**Lo que falta:** Conectar eventos de Tarea al sistema de notificaciones

**Eventos a notificar:**
1. **Tarea creada** → Notificar a: responsable asignado
2. **Tarea asignada/reasignada** → Notificar a: nuevo responsable
3. **Tarea actualizada** (campos críticos) → Notificar a: responsable + seguidores
4. **Tarea completada** → Notificar a: creador + líder del proyecto
5. **Nueva dependencia agregada** → Notificar a: responsable de ambas tareas
6. **Comentario en tarea** → Notificar a: responsable + participantes del hilo

**Campos críticos que activan notificación al cambiar:**
- Estado (status)
- Prioridad (priority)
- Fechas (planned_start, planned_end)
- Responsable (assigned_to)

**Complejidad:** 🟢 BAJA — Sistema ya existe, solo conectar eventos

---

### 2. Nivelación Automática de Recursos (8+h) ⚠️ COMPLEJO

**Ubicación:** Botón "Scheduling" en header del proyecto → Nueva opción "Nivelar Recursos"  
**Estado actual:** Algoritmo backend de nivelación YA implementado  
**Lo que falta:** UI wizard + configuración + preview antes de aplicar

**Funcionalidad:**
- Wizard modal de 3 pasos para configurar nivelación
- Preview de cambios antes de aplicar
- Aplicar nivelación con confirmación
- Historial de nivelaciones (opcional)

**Complejidad:** 🟡 MEDIA-ALTA — UI compleja, algoritmo existe

---

## 🎯 METODOLOGÍA DE EJECUCIÓN

### PASO 1: Leer Contexto Completo

1. **Leer documentos obligatorios:**
   - `CLAUDE.md` — Reglas del proyecto
   - `CHECKLIST-VALIDACION.md` — Validación 4x4
   - `docs/technical/modules/chat/ARQUITECTURA_CHAT.md` — Sistema de notificaciones
   - `DECISIONS.md` — Decisiones arquitectónicas relevantes

2. **Entender el sistema de notificaciones existente:**
   - Modelo `Notificacion` (apps/notifications/models.py)
   - Servicio `NotificacionService` (apps/notifications/services.py)
   - WebSocket events (consumers.py)
   - Frontend: `NotificationService` Angular + campanita

3. **Entender el módulo de Proyectos:**
   - Modelo `Tarea` (apps/proyectos/models.py)
   - Servicio `TareaService` (apps/proyectos/services.py)
   - Algoritmo de scheduling existente

---

## 🔧 FEATURE #1: NOTIFICACIONES AUTOMÁTICAS DE TAREAS

### A. Análisis del Sistema Existente

**Backend:**
```bash
# Verificar modelo Notificacion
view apps/notifications/models.py

# Verificar servicio NotificacionService
view apps/notifications/services.py

# Verificar modelo Tarea
view apps/proyectos/models.py
```

**Frontend:**
```bash
# Verificar servicio Angular
view frontend/src/app/core/services/notification.service.ts

# Verificar componente campanita
view frontend/src/app/core/components/notification-bell/
```

### B. Implementación Backend

#### 1. Tipos de Notificación (nuevo enum)

```python
# apps/notifications/models.py
class NotificationType(models.TextChoices):
    # ... existentes (CHAT, MENTION, etc.)
    
    # NUEVOS tipos para Proyectos
    TASK_CREATED = 'task_created', 'Tarea creada'
    TASK_ASSIGNED = 'task_assigned', 'Tarea asignada'
    TASK_UPDATED = 'task_updated', 'Tarea actualizada'
    TASK_COMPLETED = 'task_completed', 'Tarea completada'
    TASK_DEPENDENCY = 'task_dependency', 'Nueva dependencia'
    TASK_COMMENT = 'task_comment', 'Comentario en tarea'
```

#### 2. Signals para Tareas (NUEVO archivo)

```python
# apps/proyectos/signals.py
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from apps.proyectos.models import Tarea, TareaDependencia, ComentarioTarea
from apps.notifications.services import NotificacionService

@receiver(post_save, sender=Tarea)
def tarea_created_or_updated(sender, instance, created, **kwargs):
    """
    Signal para tarea creada o actualizada.
    """
    if created:
        # Tarea creada → notificar al responsable
        if instance.assigned_to:
            NotificacionService.create_notification(
                user=instance.assigned_to,
                notification_type='task_created',
                title=f'Nueva tarea asignada: {instance.name}',
                message=f'Se te ha asignado la tarea "{instance.name}" en el proyecto {instance.fase.proyecto.name}',
                link=f'/proyectos/{instance.fase.proyecto.id}/tareas/{instance.id}',
                entity_type='tarea',
                entity_id=str(instance.id),
                company=instance.company
            )
    else:
        # Tarea actualizada → verificar campos críticos
        _check_critical_field_changes(instance)

def _check_critical_field_changes(tarea):
    """
    Verifica si campos críticos cambiaron y notifica.
    """
    # Obtener versión anterior de la DB
    try:
        old_tarea = Tarea.objects.get(pk=tarea.pk)
    except Tarea.DoesNotExist:
        return
    
    critical_changes = []
    
    # Estado
    if old_tarea.status != tarea.status:
        critical_changes.append(f'Estado: {old_tarea.get_status_display()} → {tarea.get_status_display()}')
    
    # Prioridad
    if old_tarea.priority != tarea.priority:
        critical_changes.append(f'Prioridad: {old_tarea.get_priority_display()} → {tarea.get_priority_display()}')
    
    # Fechas
    if old_tarea.planned_start != tarea.planned_start:
        critical_changes.append(f'Inicio: {old_tarea.planned_start} → {tarea.planned_start}')
    
    if old_tarea.planned_end != tarea.planned_end:
        critical_changes.append(f'Fin: {old_tarea.planned_end} → {tarea.planned_end}')
    
    # Responsable
    if old_tarea.assigned_to != tarea.assigned_to:
        # Notificar al nuevo responsable
        if tarea.assigned_to:
            NotificacionService.create_notification(
                user=tarea.assigned_to,
                notification_type='task_assigned',
                title=f'Tarea reasignada: {tarea.name}',
                message=f'Se te ha asignado la tarea "{tarea.name}"',
                link=f'/proyectos/{tarea.fase.proyecto.id}/tareas/{tarea.id}',
                entity_type='tarea',
                entity_id=str(tarea.id),
                company=tarea.company
            )
        
        # Notificar al anterior responsable
        if old_tarea.assigned_to:
            NotificacionService.create_notification(
                user=old_tarea.assigned_to,
                notification_type='task_updated',
                title=f'Tarea reasignada: {tarea.name}',
                message=f'La tarea "{tarea.name}" fue reasignada a {tarea.assigned_to.get_full_name()}',
                link=f'/proyectos/{tarea.fase.proyecto.id}/tareas/{tarea.id}',
                entity_type='tarea',
                entity_id=str(tarea.id),
                company=tarea.company
            )
    
    # Si hubo cambios críticos (excepto reasignación ya notificada)
    if critical_changes and old_tarea.assigned_to == tarea.assigned_to:
        if tarea.assigned_to:
            changes_text = '\n'.join(critical_changes)
            NotificacionService.create_notification(
                user=tarea.assigned_to,
                notification_type='task_updated',
                title=f'Tarea actualizada: {tarea.name}',
                message=f'Cambios en la tarea:\n{changes_text}',
                link=f'/proyectos/{tarea.fase.proyecto.id}/tareas/{tarea.id}',
                entity_type='tarea',
                entity_id=str(tarea.id),
                company=tarea.company
            )

@receiver(post_save, sender=TareaDependencia)
def dependencia_created(sender, instance, created, **kwargs):
    """
    Signal para nueva dependencia entre tareas.
    """
    if created:
        # Notificar responsables de ambas tareas
        if instance.tarea_predecesora.assigned_to:
            NotificacionService.create_notification(
                user=instance.tarea_predecesora.assigned_to,
                notification_type='task_dependency',
                title=f'Nueva dependencia: {instance.tarea_sucesora.name}',
                message=f'La tarea "{instance.tarea_sucesora.name}" depende de tu tarea "{instance.tarea_predecesora.name}"',
                link=f'/proyectos/{instance.tarea_predecesora.fase.proyecto.id}/tareas/{instance.tarea_predecesora.id}',
                entity_type='tarea',
                entity_id=str(instance.tarea_predecesora.id),
                company=instance.company
            )
        
        if instance.tarea_sucesora.assigned_to:
            NotificacionService.create_notification(
                user=instance.tarea_sucesora.assigned_to,
                notification_type='task_dependency',
                title=f'Nueva dependencia: {instance.tarea_predecesora.name}',
                message=f'Tu tarea "{instance.tarea_sucesora.name}" depende de "{instance.tarea_predecesora.name}"',
                link=f'/proyectos/{instance.tarea_sucesora.fase.proyecto.id}/tareas/{instance.tarea_sucesora.id}',
                entity_type='tarea',
                entity_id=str(instance.tarea_sucesora.id),
                company=instance.company
            )

# Si existe modelo ComentarioTarea
@receiver(post_save, sender=ComentarioTarea)
def comentario_created(sender, instance, created, **kwargs):
    """
    Signal para nuevo comentario en tarea.
    """
    if created:
        # Notificar al responsable de la tarea (si no es quien comentó)
        if instance.tarea.assigned_to and instance.tarea.assigned_to != instance.author:
            NotificacionService.create_notification(
                user=instance.tarea.assigned_to,
                notification_type='task_comment',
                title=f'Nuevo comentario: {instance.tarea.name}',
                message=f'{instance.author.get_full_name()} comentó en "{instance.tarea.name}"',
                link=f'/proyectos/{instance.tarea.fase.proyecto.id}/tareas/{instance.tarea.id}#comentario-{instance.id}',
                entity_type='tarea',
                entity_id=str(instance.tarea.id),
                company=instance.company
            )
```

#### 3. Registrar Signals (apps.py)

```python
# apps/proyectos/apps.py
class ProyectosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.proyectos'
    
    def ready(self):
        import apps.proyectos.signals  # Importar signals
```

#### 4. Tests Unitarios

```python
# apps/proyectos/tests/test_signals.py
import pytest
from django.contrib.auth import get_user_model
from apps.proyectos.models import Tarea, Proyecto, Fase
from apps.notifications.models import Notificacion

User = get_user_model()

@pytest.mark.django_db
class TestTareaSignals:
    
    def test_tarea_created_notifies_assigned_user(self, proyecto, fase, user):
        """Test que crear tarea notifica al responsable."""
        tarea = Tarea.objects.create(
            company=proyecto.company,
            fase=fase,
            name='Test Task',
            assigned_to=user
        )
        
        # Verificar que se creó notificación
        notificacion = Notificacion.objects.filter(
            user=user,
            notification_type='task_created',
            entity_id=str(tarea.id)
        ).first()
        
        assert notificacion is not None
        assert 'Nueva tarea asignada' in notificacion.title
    
    def test_tarea_status_changed_notifies(self, tarea, user):
        """Test que cambiar estado notifica al responsable."""
        tarea.assigned_to = user
        tarea.save()
        
        # Limpiar notificaciones previas
        Notificacion.objects.filter(user=user).delete()
        
        # Cambiar estado
        tarea.status = 'in_progress'
        tarea.save()
        
        # Verificar notificación
        notificacion = Notificacion.objects.filter(
            user=user,
            notification_type='task_updated'
        ).first()
        
        assert notificacion is not None
        assert 'Estado:' in notificacion.message
```

### C. Validación de Notificaciones

**Checklist de validación:**

1. **Crear tarea:**
   - [ ] Responsable recibe notificación inmediata
   - [ ] Campanita muestra badge con contador
   - [ ] Click en notificación navega a la tarea

2. **Reasignar tarea:**
   - [ ] Nuevo responsable recibe notificación
   - [ ] Anterior responsable recibe notificación de reasignación

3. **Cambiar estado:**
   - [ ] Responsable recibe notificación con cambio
   - [ ] Mensaje indica estado anterior → nuevo

4. **Cambiar prioridad/fechas:**
   - [ ] Notificación con detalles del cambio

5. **Agregar dependencia:**
   - [ ] Ambos responsables reciben notificación

6. **Comentar en tarea:**
   - [ ] Responsable recibe notificación (si no es quien comentó)

**Validación 4x4 (Desktop/Mobile × Light/Dark):**
- [ ] Desktop Light ✅
- [ ] Desktop Dark ✅
- [ ] Mobile Light ✅
- [ ] Mobile Dark ✅

---

## 🔧 FEATURE #2: NIVELACIÓN AUTOMÁTICA DE RECURSOS

### A. Análisis del Algoritmo Existente

```bash
# Verificar si existe algoritmo de nivelación
view apps/proyectos/services.py
# Buscar: resource_leveling, leveling, nivelar, balance_resources

# Verificar modelos relacionados
view apps/proyectos/models.py
# Buscar: Recurso, AsignacionRecurso, CapacidadRecurso
```

### B. Implementación Backend

#### 1. Endpoint de Nivelación

```python
# apps/proyectos/views.py
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.proyectos.services import ResourceLevelingService

class ProyectoViewSet(viewsets.ModelViewSet):
    # ... código existente ...
    
    @action(detail=True, methods=['post'], url_path='resource-leveling/preview')
    def resource_leveling_preview(self, request, pk=None):
        """
        Preview de nivelación de recursos sin aplicar cambios.
        
        Parámetros (JSON body):
        - priority_mode: 'critical_path' | 'priority' | 'deadline'
        - allow_delay: bool (permitir retrasar tareas no críticas)
        - max_delay_days: int (máximo retraso permitido)
        """
        proyecto = self.get_object()
        params = request.data
        
        # Obtener preview del algoritmo
        preview = ResourceLevelingService.preview_leveling(
            proyecto=proyecto,
            priority_mode=params.get('priority_mode', 'critical_path'),
            allow_delay=params.get('allow_delay', True),
            max_delay_days=params.get('max_delay_days', 5)
        )
        
        return Response({
            'changes': preview['changes'],  # Lista de cambios propuestos
            'summary': preview['summary'],  # Resumen de impacto
            'conflicts_resolved': preview['conflicts_resolved']
        })
    
    @action(detail=True, methods=['post'], url_path='resource-leveling/apply')
    def resource_leveling_apply(self, request, pk=None):
        """
        Aplicar nivelación de recursos con los parámetros especificados.
        """
        proyecto = self.get_object()
        params = request.data
        
        # Aplicar nivelación
        result = ResourceLevelingService.apply_leveling(
            proyecto=proyecto,
            priority_mode=params.get('priority_mode', 'critical_path'),
            allow_delay=params.get('allow_delay', True),
            max_delay_days=params.get('max_delay_days', 5),
            user=request.user  # Para auditoría
        )
        
        # Crear notificaciones para afectados
        for tarea_id in result['modified_tasks']:
            tarea = Tarea.objects.get(pk=tarea_id)
            if tarea.assigned_to:
                NotificacionService.create_notification(
                    user=tarea.assigned_to,
                    notification_type='task_updated',
                    title=f'Tarea reprogramada: {tarea.name}',
                    message=f'La tarea fue reprogramada por nivelación de recursos',
                    link=f'/proyectos/{proyecto.id}/tareas/{tarea.id}',
                    entity_type='tarea',
                    entity_id=str(tarea.id),
                    company=proyecto.company
                )
        
        return Response({
            'success': True,
            'modified_tasks_count': len(result['modified_tasks']),
            'message': 'Nivelación aplicada exitosamente'
        })
```

#### 2. Servicio de Nivelación (si no existe)

```python
# apps/proyectos/services.py
class ResourceLevelingService:
    
    @staticmethod
    def preview_leveling(proyecto, priority_mode, allow_delay, max_delay_days):
        """
        Genera preview de cambios sin aplicarlos.
        
        Returns:
            {
                'changes': [
                    {
                        'tarea_id': uuid,
                        'tarea_name': str,
                        'current_start': date,
                        'new_start': date,
                        'current_end': date,
                        'new_end': date,
                        'reason': str
                    },
                    ...
                ],
                'summary': {
                    'total_tasks_modified': int,
                    'average_delay_days': float,
                    'overallocations_resolved': int
                },
                'conflicts_resolved': int
            }
        """
        # NOTA: Si el algoritmo ya existe, usarlo aquí
        # Si no existe, implementar lógica básica de nivelación
        pass
    
    @staticmethod
    def apply_leveling(proyecto, priority_mode, allow_delay, max_delay_days, user):
        """
        Aplica nivelación modificando las tareas.
        
        Returns:
            {
                'modified_tasks': [uuid, ...],
                'summary': {...}
            }
        """
        pass
```

### C. Implementación Frontend

#### 1. Wizard Modal (3 pasos)

```typescript
// frontend/src/app/modules/proyectos/components/resource-leveling-wizard/
// resource-leveling-wizard.component.ts

export interface LevelingConfig {
  priorityMode: 'critical_path' | 'priority' | 'deadline';
  allowDelay: boolean;
  maxDelayDays: number;
}

export interface LevelingPreview {
  changes: TareaChange[];
  summary: LevelingSummary;
  conflictsResolved: number;
}

@Component({
  selector: 'app-resource-leveling-wizard',
  templateUrl: './resource-leveling-wizard.component.html',
  styleUrls: ['./resource-leveling-wizard.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class ResourceLevelingWizardComponent {
  currentStep = signal(1);
  config = signal<LevelingConfig>({
    priorityMode: 'critical_path',
    allowDelay: true,
    maxDelayDays: 5
  });
  
  preview = signal<LevelingPreview | null>(null);
  loading = signal(false);
  
  constructor(
    private proyectoService: ProyectoService,
    private dialogRef: MatDialogRef<ResourceLevelingWizardComponent>,
    @Inject(MAT_DIALOG_DATA) public data: { proyectoId: string }
  ) {}
  
  nextStep() {
    if (this.currentStep() === 1) {
      // Validar configuración
      this.currentStep.set(2);
      this.loadPreview();
    } else if (this.currentStep() === 2) {
      this.currentStep.set(3);
    }
  }
  
  previousStep() {
    this.currentStep.update(step => step - 1);
  }
  
  async loadPreview() {
    this.loading.set(true);
    
    const preview = await this.proyectoService.resourceLevelingPreview(
      this.data.proyectoId,
      this.config()
    );
    
    this.preview.set(preview);
    this.loading.set(false);
  }
  
  async applyLeveling() {
    this.loading.set(true);
    
    await this.proyectoService.resourceLevelingApply(
      this.data.proyectoId,
      this.config()
    );
    
    this.dialogRef.close({ success: true });
  }
}
```

#### 2. Template del Wizard

```html
<!-- resource-leveling-wizard.component.html -->
<h2 mat-dialog-title>Nivelación de Recursos</h2>

<mat-dialog-content>
  <!-- PASO 1: Configuración -->
  @if (currentStep() === 1) {
    <div class="step-content">
      <h3>Paso 1: Configuración</h3>
      
      <mat-form-field appearance="outline" class="full-width">
        <mat-label>Modo de prioridad</mat-label>
        <mat-select [(ngModel)]="config().priorityMode">
          <mat-option value="critical_path">Ruta crítica</mat-option>
          <mat-option value="priority">Prioridad de tarea</mat-option>
          <mat-option value="deadline">Fecha límite</mat-option>
        </mat-select>
        <mat-hint>Criterio para decidir qué tareas priorizar</mat-hint>
      </mat-form-field>
      
      <mat-checkbox [(ngModel)]="config().allowDelay">
        Permitir retrasar tareas no críticas
      </mat-checkbox>
      
      @if (config().allowDelay) {
        <mat-form-field appearance="outline" class="full-width">
          <mat-label>Máximo retraso permitido (días)</mat-label>
          <input matInput type="number" [(ngModel)]="config().maxDelayDays" min="1" max="30">
          <mat-hint>Días máximos que se puede retrasar una tarea</mat-hint>
        </mat-form-field>
      }
    </div>
  }
  
  <!-- PASO 2: Preview de cambios -->
  @if (currentStep() === 2) {
    <div class="step-content">
      <h3>Paso 2: Vista previa de cambios</h3>
      
      @if (loading()) {
        <mat-progress-bar mode="indeterminate"></mat-progress-bar>
      }
      
      @if (preview()) {
        <div class="preview-summary">
          <mat-card>
            <mat-card-content>
              <p><strong>Tareas modificadas:</strong> {{ preview()!.summary.totalTasksModified }}</p>
              <p><strong>Promedio de retraso:</strong> {{ preview()!.summary.averageDelayDays | number:'1.1-1' }} días</p>
              <p><strong>Conflictos resueltos:</strong> {{ preview()!.conflictsResolved }}</p>
            </mat-card-content>
          </mat-card>
        </div>
        
        <h4>Cambios propuestos:</h4>
        <div class="table-responsive">
          <table mat-table [dataSource]="preview()!.changes">
            <ng-container matColumnDef="tarea">
              <th mat-header-cell *matHeaderCellDef>Tarea</th>
              <td mat-cell *matCellDef="let change">{{ change.tareaName }}</td>
            </ng-container>
            
            <ng-container matColumnDef="currentDates">
              <th mat-header-cell *matHeaderCellDef>Fechas actuales</th>
              <td mat-cell *matCellDef="let change">
                {{ change.currentStart | date:'short' }} - {{ change.currentEnd | date:'short' }}
              </td>
            </ng-container>
            
            <ng-container matColumnDef="newDates">
              <th mat-header-cell *matHeaderCellDef>Fechas nuevas</th>
              <td mat-cell *matCellDef="let change">
                {{ change.newStart | date:'short' }} - {{ change.newEnd | date:'short' }}
              </td>
            </ng-container>
            
            <ng-container matColumnDef="reason">
              <th mat-header-cell *matHeaderCellDef>Razón</th>
              <td mat-cell *matCellDef="let change">{{ change.reason }}</td>
            </ng-container>
            
            <tr mat-header-row *matHeaderRowDef="['tarea', 'currentDates', 'newDates', 'reason']"></tr>
            <tr mat-row *matRowDef="let row; columns: ['tarea', 'currentDates', 'newDates', 'reason']"></tr>
          </table>
        </div>
      }
    </div>
  }
  
  <!-- PASO 3: Confirmación -->
  @if (currentStep() === 3) {
    <div class="step-content">
      <h3>Paso 3: Confirmación</h3>
      
      <mat-card class="warning-card">
        <mat-card-content>
          <mat-icon color="warn">warning</mat-icon>
          <p>
            ¿Estás seguro de aplicar la nivelación de recursos?
            Esto modificará las fechas de <strong>{{ preview()!.summary.totalTasksModified }}</strong> tareas.
          </p>
          <p>
            Los responsables de las tareas modificadas recibirán una notificación.
          </p>
        </mat-card-content>
      </mat-card>
    </div>
  }
</mat-dialog-content>

<mat-dialog-actions align="end">
  @if (currentStep() > 1) {
    <button mat-button (click)="previousStep()">Anterior</button>
  }
  
  <button mat-button (click)="dialogRef.close()">Cancelar</button>
  
  @if (currentStep() < 3) {
    <button mat-raised-button color="primary" (click)="nextStep()">
      Siguiente
    </button>
  }
  
  @if (currentStep() === 3) {
    <button 
      mat-raised-button 
      color="primary" 
      (click)="applyLeveling()"
      [disabled]="loading()"
    >
      @if (loading()) {
        <mat-spinner diameter="20"></mat-spinner>
      } @else {
        Aplicar Nivelación
      }
    </button>
  }
</mat-dialog-actions>
```

### D. Integración con Header del Proyecto

```typescript
// proyecto-detail.component.ts
openResourceLevelingWizard() {
  const dialogRef = this.dialog.open(ResourceLevelingWizardComponent, {
    width: '800px',
    data: { proyectoId: this.proyectoId }
  });
  
  dialogRef.afterClosed().subscribe(result => {
    if (result?.success) {
      this.snackBar.open('Nivelación aplicada exitosamente', 'Cerrar', {
        duration: 3000,
        panelClass: ['snack-success']
      });
      
      // Recargar datos del proyecto
      this.loadProyecto();
    }
  });
}
```

```html
<!-- proyecto-detail.component.html -->
<button 
  mat-menu-item 
  (click)="openResourceLevelingWizard()"
  [disabled]="!canEditProyecto()"
>
  <mat-icon>balance</mat-icon>
  <span>Nivelar Recursos</span>
</button>
```

### E. Validación de Nivelación

**Checklist de validación:**

1. **Wizard - Paso 1:**
   - [ ] Formulario muestra opciones correctamente
   - [ ] Validación de campos (max delay > 0)
   - [ ] Botón "Siguiente" funciona

2. **Wizard - Paso 2:**
   - [ ] Preview carga correctamente
   - [ ] Tabla muestra cambios propuestos
   - [ ] Resumen muestra métricas
   - [ ] Botón "Anterior" vuelve al paso 1

3. **Wizard - Paso 3:**
   - [ ] Confirmación muestra warning
   - [ ] Botón "Aplicar" ejecuta nivelación
   - [ ] Loading state funciona
   - [ ] Notificaciones enviadas a afectados

4. **Post-aplicación:**
   - [ ] Gantt refleja nuevas fechas
   - [ ] Tareas muestran fechas actualizadas
   - [ ] Responsables reciben notificaciones

**Validación 4x4 (Desktop/Mobile × Light/Dark):**
- [ ] Desktop Light ✅
- [ ] Desktop Dark ✅
- [ ] Mobile Light ✅
- [ ] Mobile Dark ✅

---

## 📝 ORDEN DE EJECUCIÓN RECOMENDADO

### Día 1 (4-6h): Notificaciones Automáticas

1. Tipos de notificación (30min)
2. Signals para Tarea (2h)
3. Tests unitarios (1h)
4. Validación en navegador (1-2h)

### Día 2-3 (8-10h): Nivelación de Recursos

1. Endpoint de nivelación (2h)
2. Servicio de nivelación (si no existe: 4h)
3. Wizard frontend - Paso 1 (1h)
4. Wizard frontend - Paso 2 (2h)
5. Wizard frontend - Paso 3 (1h)
6. Integración + validación (2h)

---

## 📦 ENTREGABLES

Al finalizar la Fase 2, debes tener:

1. ✅ **Feature #1 completada:** Notificaciones automáticas de tareas
2. ✅ **Feature #2 completada:** Nivelación automática de recursos
3. ✅ **Tests unitarios PASS** (cobertura >80%)
4. ✅ **Validación 4x4** en ambas features
5. ✅ **Informe completo:** `INFORME_FASE_2_FUNCIONALIDADES.md`
6. ✅ **Tareas Notion actualizadas** (estado: Completado)

---

## 🎯 CRITERIO DE ÉXITO

La Fase 2 está completa cuando:

- ✅ Notificaciones automáticas funcionan para todos los eventos
- ✅ Wizard de nivelación permite configurar + preview + aplicar
- ✅ Notificaciones se envían a afectados por nivelación
- ✅ Sin regresiones en funcionalidad existente
- ✅ Validación 4x4 completa en ambas features
- ✅ Tests unitarios >80% cobertura

---

## ⚠️ REGLAS CRÍTICAS

1. **SIEMPRE usar el sistema de notificaciones existente**
   - NO reinventar la rueda
   - NO crear nuevo sistema paralelo
   - SÍ reutilizar `NotificacionService`

2. **SIEMPRE validar 4x4**
   - Desktop/Mobile × Light/Dark
   - NO saltarse validación mobile

3. **SIEMPRE usar signals de Django**
   - NO lógica de notificación en views/services
   - SÍ signals para desacoplamiento

4. **SIEMPRE confirmar antes de modificar datos**
   - Preview obligatorio en nivelación
   - Confirmación explícita del usuario

5. **SIEMPRE notificar a afectados**
   - Nivelación → notificar responsables
   - Cambios críticos → notificar involucrados

---

## 📞 REFERENCIAS

- **Sistema de notificaciones:** `docs/technical/modules/chat/ARQUITECTURA_CHAT.md`
- **Checklist validación:** `docs/base-reference/CHECKLIST-VALIDACION.md`
- **Backlog Notion:** https://www.notion.so/0f5116945f4346ffa18fee534371923c
- **Módulo Proyectos:** https://www.notion.so/327ee9c3690a81f296a2ec384b557049
- **Django Signals:** https://docs.djangoproject.com/en/5.0/topics/signals/
- **Angular Material Dialog:** https://material.angular.io/components/dialog/overview

---

**¡Ejecuta la Fase 2 y completa las funcionalidades críticas!** 🚀
