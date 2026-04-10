# WORKFLOW: Orquestador de Módulos Nuevos

**Versión:** 1.0 | **Fecha:** 10 Abril 2026  
**Autor:** Juan David + Cowork  
**Problema que resuelve:** Ejecutar la metodología de 10 fases directamente desde Claude Code, sin intermediario, con tracking persistente y sincronización automática.

---

## 1. Diagnóstico del Problema Actual

### Lo que pasaba antes:

```
┌─────────────────────────────────────────────────────────────┐
│  FLUJO ANTERIOR (Módulo Proyectos)                          │
│                                                             │
│  Juan David ─→ Claude.ai (Chat) ─→ genera prompts          │
│       │              │                                      │
│       │              └─→ Juan David copia prompts           │
│       │                       │                             │
│       │                       └─→ Claude Code (ejecuta)     │
│       │                                                     │
│  ❌ Doble consumo de tokens                                 │
│  ❌ Copiar/pegar prompts (tedioso, propenso a errores)      │
│  ❌ Claude Code no sabe la metodología                      │
│  ❌ Planes se pierden entre turnos                          │
│  ❌ Notion nunca se actualiza                               │
│  ❌ No genera docs RAG ni registra licencia                 │
└─────────────────────────────────────────────────────────────┘
```

### Lo que pasó con el Board:

```
┌─────────────────────────────────────────────────────────────┐
│  FLUJO BOARD (directo en Claude Code)                       │
│                                                             │
│  Juan David ─→ Claude Code (directo)                        │
│                                                             │
│  ✅ Rápido, menos tokens                                    │
│  ❌ Sin metodología                                         │
│  ❌ Sin tracking de progreso                                │
│  ❌ Sin Notion                                              │
│  ❌ Sin documentación                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Flujo Nuevo Propuesto

```
┌──────────────────────────────────────────────────────────────────────┐
│  FLUJO NUEVO: Orquestador en Claude Code                             │
│                                                                      │
│  Juan David entrega PRD/Requerimientos                               │
│       │                                                              │
│       └─→ Claude Code + Skill Orquestador                            │
│               │                                                      │
│               ├─→ Crea PROGRESS-{MODULO}.md (persistente)            │
│               ├─→ Ejecuta Fase 1→10 secuencialmente                  │
│               ├─→ Cada fase: ejecuta + valida + checkea              │
│               ├─→ Al completar fase: actualiza PROGRESS + Notion     │
│               ├─→ Al cerrar sesión: CONTEXT.md + Notion              │
│               ├─→ Al retomar: lee PROGRESS y continúa                │
│               ├─→ Fase 9: genera docs RAG                            │
│               └─→ Fase 10: registra módulo en licencias              │
│                                                                      │
│  ✅ Un solo agente, un solo consumo de tokens                        │
│  ✅ Metodología forzada (no se puede saltar)                         │
│  ✅ Progreso persistente entre sesiones                              │
│  ✅ Notion actualizado automáticamente                               │
│  ✅ Documentación RAG generada                                       │
│  ✅ Licencia registrada                                              │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 3. Componentes del Sistema

### 3.1 Archivo de Progreso Persistente: `PROGRESS-{MODULO}.md`

Este es el **corazón del sistema**. Un archivo por módulo que vive en la raíz del repo y sobrevive entre sesiones. Claude Code lo lee al inicio de cada sesión y sabe exactamente dónde quedó.

```markdown
# PROGRESS: CRM

**Estado:** EN PROGRESO
**Fase actual:** 4 — Implementación
**Inicio:** 2026-04-10
**Última sesión:** 2026-04-12
**PRD origen:** docs/plans/PRD-CRM.md

---

## Fases

| # | Fase | Estado | Fecha inicio | Fecha fin | Notas |
|---|------|--------|-------------|-----------|-------|
| 1 | Planificación | ✅ COMPLETADA | 2026-04-10 | 2026-04-10 | PLAN-CRM.md generado |
| 2 | Gestión Contexto | ✅ COMPLETADA | 2026-04-10 | 2026-04-10 | CONTEXT.md actualizado |
| 3 | Skills/MCP/APIs | ✅ COMPLETADA | 2026-04-10 | 2026-04-10 | No requiere skills nuevos |
| 4 | Implementación | 🔄 EN PROGRESO | 2026-04-11 | — | Backend 70%, Frontend 30% |
| 5 | Iteración | ⏳ PENDIENTE | — | — | — |
| 6 | Protección Ventana | ⏳ PENDIENTE | — | — | — |
| 7 | Revisión Final | ⏳ PENDIENTE | — | — | — |
| 8 | Panel Admin | ⏳ PENDIENTE | — | — | — |
| 9 | Validación UI/UX | ⏳ PENDIENTE | — | — | — |
| 10 | Despliegue + Docs | ⏳ PENDIENTE | — | — | — |

---

## Fase 4: Implementación — Detalle

### Backend (Django)
- [x] models.py — Contact, Deal, Pipeline, Activity
- [x] serializers.py — list + detail
- [x] services.py — CRMService
- [x] views.py — ViewSets
- [x] urls.py — router
- [x] permissions.py — CRMPermission
- [x] tests/test_models.py
- [x] tests/test_services.py — 92% cobertura
- [ ] tests/test_views.py
- [ ] admin.py (se hace en Fase 8)

### Frontend (Angular)
- [x] crm.model.ts
- [x] crm.service.ts
- [ ] contact-list/
- [ ] contact-form/
- [ ] deal-board/
- [ ] pipeline-config/
- [ ] crm.routes.ts

### Decisiones Tomadas
- DEC-057: Pipeline stages configurables por tenant
- DEC-058: Activities como timeline (no calendario)

### Errores Resueltos
- ERR-2026-04-11: N+1 en Deal.contacts → select_related añadido

---

## Sesiones de Trabajo

### Sesión 1 — 2026-04-10
- Completó: Fases 1-3
- Archivos: PLAN-CRM.md, modelos definidos
- Duración: ~2h

### Sesión 2 — 2026-04-11
- Completó: Backend models, serializers, services, views
- Tests backend: 92% cobertura services
- Pendiente: tests views, frontend completo
- Duración: ~3h
```

### 3.2 Skill Orquestador: `saicloud-orquestador`

Nuevo skill para Claude Code que:
- Lee el PRD de entrada
- Crea/actualiza PROGRESS-{MODULO}.md
- Ejecuta cada fase llamando a los skills correspondientes
- Valida gates entre fases
- Actualiza Notion y docs

**Ubicación:** `.claude/skills/saicloud-orquestador/SKILL.md`

### 3.3 Comando de Activación en CLAUDE.md

Agregar a CLAUDE.md:

```markdown
## Comandos de Orquestación

### `nuevo módulo {nombre}`
Trigger: cuando Juan David diga "nuevo módulo CRM" o "empezar módulo X"
1. Leer skill saicloud-orquestador
2. Solicitar PRD o listado de requerimientos
3. Crear PROGRESS-{MODULO}.md
4. Iniciar Fase 1

### `continuar módulo {nombre}`
Trigger: cuando Juan David diga "continuar CRM" o "retomar módulo X"  
1. Leer PROGRESS-{MODULO}.md
2. Identificar fase actual y último checkpoint
3. Mostrar resumen de estado
4. Continuar desde donde quedó

### `estado módulo {nombre}`
Trigger: cuando Juan David pregunte "qué falta del CRM" o "estado módulo X"
1. Leer PROGRESS-{MODULO}.md
2. Mostrar resumen ejecutivo
3. Listar pendientes de la fase actual
```

---

## 4. Flujo Detallado por Fase

### FASE 1: Planificación
**Input:** PRD o listado de requerimientos del usuario  
**Skill:** `saicloud-planificacion`  
**Gate de salida:** PLAN-{MODULO}.md existe y tiene checklist completo

```
Paso 1.1: Leer PRD/requerimientos
Paso 1.2: Activar skill saicloud-planificacion
Paso 1.3: Generar PLAN-{MODULO}.md en docs/plans/
Paso 1.4: Evaluar Django vs Go (4 criterios)
Paso 1.5: Definir contrato API (endpoints + modelos)
Paso 1.6: Registrar decisiones arquitectónicas en DECISIONS.md
Paso 1.7: Crear estructura en Notion:
          → Página del módulo bajo "Módulos del Proyecto"
          → Subpáginas por fase
Paso 1.8: Actualizar PROGRESS → Fase 1 ✅
Paso 1.9: Pedir aprobación a Juan David antes de continuar
```

**Gate:** Juan David aprueba el plan → avanzar a Fase 2

---

### FASE 2: Gestión de Contexto
**Input:** PLAN-{MODULO}.md aprobado  
**Skill:** `saicloud-contexto`  
**Gate de salida:** CONTEXT.md actualizado con módulo activo

```
Paso 2.1: Leer CONTEXT.md, DECISIONS.md, ERRORS.md actuales
Paso 2.2: Verificar que no hay conflictos con módulos existentes
Paso 2.3: Actualizar CONTEXT.md:
          → Módulo activo: {nombre}
          → Fase: 2/10
          → Referencias al PLAN
Paso 2.4: Verificar modelos existentes que se reutilizarán
Paso 2.5: Mapear dependencias con otros módulos
Paso 2.6: Actualizar PROGRESS → Fase 2 ✅
```

**Gate:** CONTEXT.md actualizado → avanzar a Fase 3

---

### FASE 3: Skills/MCP/APIs
**Input:** PLAN con integraciones identificadas  
**Skill:** Ninguno específico  
**Gate de salida:** Todas las dependencias disponibles

```
Paso 3.1: Revisar integraciones del PLAN
Paso 3.2: Verificar skills existentes cubren necesidades
Paso 3.3: Si se necesita skill nuevo → crearlo
Paso 3.4: Verificar APIs externas (n8n webhooks, etc.)
Paso 3.5: Documentar dependencias en PROGRESS
Paso 3.6: Actualizar PROGRESS → Fase 3 ✅
```

**Gate:** Dependencias verificadas → avanzar a Fase 4

---

### FASE 4: Implementación (Multi-agente)
**Input:** PLAN aprobado + contexto cargado  
**Skills:** `saicloud-backend-django` + `saicloud-frontend-angular` + `saicloud-pruebas-unitarias`  
**Gate de salida:** Código + tests pasando

```
ESTRATEGIA: Ejecutar por feature vertical (backend→tests→frontend→tests)

Para cada feature del PLAN:
  
  Paso 4.X.1: Backend
    → Modelo (verificar Esquema_BD)
    → Migración
    → Serializer (list + detail)
    → Service (lógica de negocio)
    → View + URL
    → Tests (services 80%+, views)
    → Ejecutar pytest → debe pasar
  
  Paso 4.X.2: Frontend
    → Model (interfaz TS, espeja serializer)
    → Service (tipado)
    → Component (OnPush, async pipe, Material)
    → Container (smart component)
    → Routes (lazy loading)
    → Tests (services 100%, components 70%)
    → Ejecutar ng test → debe pasar
  
  Paso 4.X.3: Actualizar PROGRESS con checkbox de cada archivo
  
  Paso 4.X.4: Cada 3 features → checkpoint en PROGRESS
              (protección de ventana lite)

REGLA: Si una feature falla tests → NO avanzar a la siguiente.
       Corregir in-situ (mini-iteración).
```

**Gate:** Todos los tests pasan + PROGRESS actualizado → avanzar a Fase 5

---

### FASE 5: Iteración
**Input:** Código implementado  
**Skill:** `saicloud-iteracion`  
**Gate de salida:** 0 bugs conocidos

```
Paso 5.1: Revisión de código generado (self-review)
Paso 5.2: Verificar N+1 queries (select_related)
Paso 5.3: Verificar unique_together en modelos espejo
Paso 5.4: Verificar unsubscribe en Angular
Paso 5.5: Verificar strict TypeScript (no `any`)
Paso 5.6: Correr TODOS los tests del módulo
Paso 5.7: Verificar cobertura mínima
Paso 5.8: Registrar errores encontrados en ERRORS.md
Paso 5.9: Actualizar PROGRESS → Fase 5 ✅
```

**Gate:** Tests 100% green + cobertura OK → avanzar a Fase 6

---

### FASE 6: Protección de Ventana
**Input:** Código iterado  
**Skill:** `saicloud-proteccion-ventana`  
**Gate de salida:** Checkpoint completo en PROGRESS

```
Paso 6.1: Generar resumen de todas las decisiones tomadas
Paso 6.2: Verificar consistencia:
          → DECISIONS.md tiene todas las DECs nuevas
          → ERRORS.md tiene todos los errores resueltos
          → PROGRESS refleja estado real
Paso 6.3: Crear checkpoint completo en PROGRESS:
          → Lista de archivos creados/modificados
          → Decisiones clave
          → Estado de cada feature
Paso 6.4: Sincronizar a Notion:
          → Actualizar página del módulo
          → Crear/actualizar DECs en Notion
Paso 6.5: Actualizar PROGRESS → Fase 6 ✅
```

**Gate:** Checkpoint guardado → avanzar a Fase 7

---

### FASE 7: Revisión Final
**Input:** Código completo con checkpoint  
**Skill:** `saicloud-revision-final`  
**Gate de salida:** Checklist de calidad 100%

```
Paso 7.1: Checklist de seguridad:
          [ ] No hay secrets hardcodeados
          [ ] Auth en todos los endpoints
          [ ] CORS configurado
          [ ] company_id en todas las queries
Paso 7.2: Checklist Django:
          [ ] BaseModel en todos los modelos
          [ ] Lógica en services.py (no views)
          [ ] Logger (no print)
          [ ] Transactions en operaciones críticas
Paso 7.3: Checklist Angular:
          [ ] OnPush en componentes presentacionales
          [ ] No console.log
          [ ] Unsubscribe / async pipe
          [ ] Material components (no PrimeNG)
          [ ] @if/@for (no *ngIf/*ngFor)
Paso 7.4: Checklist tests:
          [ ] Backend services ≥80%
          [ ] Backend crítico =100%
          [ ] Frontend services =100%
          [ ] Frontend components ≥70%
Paso 7.5: Si falla algún check → volver a Fase 5 (iteración)
Paso 7.6: Actualizar PROGRESS → Fase 7 ✅
```

**Gate:** Todos los checks pasan → avanzar a Fase 8

---

### FASE 8: Panel Admin
**Input:** Código revisado  
**Skill:** `saicloud-panel-admin`  
**Gate de salida:** admin.py configurado

```
Paso 8.1: Registrar modelos en Django Admin
Paso 8.2: Configurar list_display, search_fields, list_filter
Paso 8.3: Agregar acciones personalizadas si aplica
Paso 8.4: Configurar inlines para relaciones
Paso 8.5: Actualizar PROGRESS → Fase 8 ✅
```

**Gate:** Admin funcional → avanzar a Fase 9

---

### FASE 9: Validación UI/UX + Documentación
**Input:** Código con admin configurado  
**Skills:** `saicloud-validacion-ui` + `saicloud-documentacion`  
**Gate de salida:** Validación 4x4 + docs RAG generados

```
Paso 9.1: Validación 4x4 (Desktop/Mobile × Light/Dark)
          [ ] Desktop + Light
          [ ] Desktop + Dark
          [ ] Mobile + Light
          [ ] Mobile + Dark
Paso 9.2: Validar touch targets ≥44px en mobile
Paso 9.3: Validar tablas con scroll horizontal
Paso 9.4: Validar contraste en ambos temas

Paso 9.5: Generar documentación técnica:
          → docs/technical/{modulo}/API.md
          → docs/technical/{modulo}/ARCHITECTURE.md
Paso 9.6: Generar documentación usuario:
          → docs/manuales/MANUAL-{MODULO}.md
Paso 9.7: Generar chunks RAG para Knowledge Base:
          → docs/technical/{modulo}/RAG-CHUNKS.md
          → Formato: pregunta + respuesta + metadata
Paso 9.8: Actualizar RAG-KB-UPDATED.md con nuevo módulo
Paso 9.9: Sincronizar docs a Notion
Paso 9.10: Actualizar PROGRESS → Fase 9 ✅
```

**Gate:** Docs generados + UI validada → avanzar a Fase 10

---

### FASE 10: Despliegue + Registro de Licencia
**Input:** Todo validado  
**Skills:** `saicloud-despliegue` + custom  
**Gate de salida:** Módulo deployable y registrado en licencias

```
Paso 10.1: Verificar/actualizar Docker config
Paso 10.2: Verificar variables de entorno

Paso 10.3: REGISTRAR MÓDULO EN SISTEMA DE LICENCIAS:
          → Agregar choice en CompanyModule.Module:
            {MODULO} = '{modulo}', '{NombreDisplay}'
          → Crear migración
          → Actualizar LicensePackageItem choices
          → Agregar guard en frontend routing
          → Actualizar menú de navegación con verificación de licencia

Paso 10.4: Pre-deploy checklist (Tarea 3 de Cowork):
          [ ] CONTEXT.md actualizado
          [ ] DECISIONS.md completo
          [ ] ERRORS.md existe
          [ ] Plans actualizados
          [ ] Notion sincronizado
          [ ] Sin conflictos de merge
          [ ] Próximo paso definido

Paso 10.5: Actualizar CONTEXT.md con módulo completado
Paso 10.6: Crear página de cierre en Notion
Paso 10.7: Marcar PROGRESS → COMPLETADO

Paso 10.8: Generar resumen final:
          → Archivos creados: N
          → Tests: N (X% cobertura)
          → Decisiones: N DECs
          → Errores resueltos: N
          → Tiempo total: N sesiones
```

---

## 5. Reglas del Orquestador

### Gates Obligatorios (NUNCA saltarse)

| De → A | Gate |
|--------|------|
| 1 → 2 | Juan David aprueba PLAN |
| 3 → 4 | Dependencias verificadas |
| 4 → 5 | Todos los tests pasan |
| 5 → 6 | 0 bugs conocidos + cobertura OK |
| 7 → 8 | Checklist calidad 100% |
| 9 → 10 | UI validada 4x4 + docs RAG |

### Manejo de Sesiones

```
Al INICIAR sesión:
1. Leer PROGRESS-{MODULO}.md
2. Mostrar: "Módulo {X} — Fase {N}/10 — {estado}"
3. Mostrar pendientes de la fase actual
4. Continuar desde donde quedó

Al CERRAR sesión:
1. Actualizar PROGRESS con estado actual
2. Actualizar CONTEXT.md
3. Sincronizar DECISIONS.md nuevas a Notion
4. Crear cierre de sesión en Notion
5. Mostrar resumen de la sesión
```

### Regla de Retroceso

Si una fase falla su gate:
- Fase 7 falla → volver a Fase 5 (iterar)
- Fase 9 falla UI → volver a Fase 5 (corregir)
- Fase 10 falla pre-deploy → volver a Fase 7 (revisión)

El PROGRESS registra los retrocesos para aprendizaje.

---

## 6. Integración con Notion (via Cowork)

### Opción A: Claude Code tiene MCP Notion (ideal)

Si Claude Code tiene acceso al MCP de Notion, el orquestador actualiza directamente:

```
→ Crear página módulo: notion-create-pages bajo módulos_page_id
→ Actualizar fase: notion-update-content en página del módulo
→ Crear DEC: notion-create-pages bajo decisiones_page_id
→ Cierre sesión: notion-create-pages bajo metodología_page_id
```

### Opción B: Delegación a Cowork (actual)

Si Claude Code NO tiene Notion, genera un archivo de instrucciones:

```markdown
# NOTION-SYNC-{MODULO}-{FECHA}.md

## Acciones pendientes para Cowork:

1. Crear página "Módulo CRM" bajo ID 327ee9c3690a81f296a2ec384b557049
   Contenido: [incluido abajo]

2. Crear DEC-057 bajo ID 323ee9c3-690a-817e-9919-cf7f810289fe
   Contenido: [incluido abajo]

3. Crear cierre sesión bajo ID 31dee9c3-690a-8166-8fc3-cd5080240bb7
   Contenido: [incluido abajo]
```

Cowork lee este archivo y ejecuta las sincronizaciones.

### Opción C: Hooks post-sesión

Agregar a `.claude/config.json`:
```json
{
  "hooks": {
    "post_session": "python scripts/sync-notion.py"
  }
}
```

---

## 7. Generación de Documentación RAG

En Fase 9, el orquestador genera chunks de conocimiento para el bot IA:

### Formato de chunk RAG:

```markdown
---
module: crm
category: feature
subcategory: contacts
keywords: [contacto, cliente, crear, editar]
---

## ¿Cómo creo un nuevo contacto?

Para crear un nuevo contacto en el CRM:
1. Ve al menú lateral → CRM → Contactos
2. Haz clic en "Nuevo Contacto"
3. Completa los campos obligatorios: Nombre, Email, Teléfono
4. Selecciona la empresa asociada (opcional)
5. Haz clic en "Guardar"

**Permisos necesarios:** Rol `seller` o superior.
**Módulo requerido:** CRM (debe estar activo en la licencia).
```

### Archivos generados:
- `docs/technical/{modulo}/RAG-CHUNKS.md` — chunks técnicos
- `docs/manuales/MANUAL-{MODULO}.md` — manual de usuario (se convierte a chunks)
- Actualización de `docs/technical/RAG-KB-UPDATED.md` — índice general

---

## 8. Registro en Sistema de Licencias

En Fase 10, el orquestador:

### Backend:
```python
# companies/models.py → CompanyModule.Module
class Module(models.TextChoices):
    CRM        = 'crm',        'CRM'
    SOPORTE    = 'soporte',    'Soporte'
    DASHBOARD  = 'dashboard',  'SaiDashboard'
    PROYECTOS  = 'proyectos',  'SaiProyectos'
    # ← NUEVO MÓDULO AQUÍ
    {MODULO}   = '{modulo}',   'Sai{Nombre}'
```

### Frontend:
```typescript
// core/guards/module.guard.ts → agregar ruta
{ path: '{modulo}', canActivate: [ModuleGuard], data: { module: '{modulo}' } }

// shared/components/nav/ → agregar ítem de menú con verificación de licencia
```

### Migración:
```bash
python manage.py makemigrations companies -n "add_{modulo}_module_choice"
```

---

## 9. Diagrama de Flujo Completo

```
                    ┌─────────────────────┐
                    │  Juan David entrega  │
                    │  PRD / Requerimientos│
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  "nuevo módulo CRM"  │
                    │  (comando en CC)     │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │ Orquestador crea    │
                    │ PROGRESS-CRM.md     │
                    └──────────┬──────────┘
                               │
              ┌────────────────▼────────────────┐
              │         FASE 1: PLANIFICACIÓN    │
              │  skill: saicloud-planificacion   │
              │  output: PLAN-CRM.md             │
              │  gate: Juan David aprueba ✋      │
              └────────────────┬────────────────┘
                               │ ✅
              ┌────────────────▼────────────────┐
              │    FASE 2: GESTIÓN DE CONTEXTO   │
              │  skill: saicloud-contexto        │
              │  output: CONTEXT.md actualizado   │
              └────────────────┬────────────────┘
                               │ ✅
              ┌────────────────▼────────────────┐
              │    FASE 3: SKILLS/MCP/APIs       │
              │  verificar dependencias          │
              └────────────────┬────────────────┘
                               │ ✅
              ┌────────────────▼────────────────┐
              │    FASE 4: IMPLEMENTACIÓN        │
              │  skills: backend + frontend      │
              │  + pruebas-unitarias             │
              │  Feature por feature vertical    │
              │  gate: tests pasan ✅             │
              └────────────────┬────────────────┘
                               │ ✅
              ┌────────────────▼────────────────┐
              │    FASE 5: ITERACIÓN             │
              │  skill: saicloud-iteracion       │
              │  self-review + bug fixing        │
              │  gate: 0 bugs + cobertura OK     │
              └────────────────┬────────────────┘
                               │ ✅
              ┌────────────────▼────────────────┐
              │    FASE 6: PROTECCIÓN VENTANA    │
              │  checkpoint + sync Notion        │
              └────────────────┬────────────────┘
                               │ ✅
              ┌────────────────▼────────────────┐
              │    FASE 7: REVISIÓN FINAL        │◄──────┐
              │  checklist calidad completo      │       │
              │  gate: 100% checks              │       │
              └────────────────┬────────────────┘       │
                               │ ✅                      │
              ┌────────────────▼────────────────┐       │
              │    FASE 8: PANEL ADMIN           │       │
              │  admin.py configurado            │       │
              └────────────────┬────────────────┘       │
                               │ ✅                      │ falla
              ┌────────────────▼────────────────┐       │
              │    FASE 9: VALIDACIÓN UI/UX      │───────┘
              │  + DOCUMENTACIÓN RAG             │
              │  validación 4x4                  │
              │  chunks RAG generados            │
              │  manual usuario generado         │
              └────────────────┬────────────────┘
                               │ ✅
              ┌────────────────▼────────────────┐
              │    FASE 10: DEPLOY + LICENCIA    │
              │  Docker + registro en licencias  │
              │  Notion: cierre de módulo        │
              │  PROGRESS → COMPLETADO           │
              └────────────────┬────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │  MÓDULO COMPLETADO   │
                    │  🎉                  │
                    └─────────────────────┘
```

---

## 10. Ejemplo Real: CRM

```
Juan David: "nuevo módulo CRM" + entrega listado de requerimientos

Claude Code:
  1. Lee skill orquestador
  2. Lee requerimientos
  3. Crea PROGRESS-CRM.md
  4. Fase 1: Genera PLAN-CRM.md
     → "Juan David, aquí está el plan. ¿Apruebas?"
  5. JD aprueba
  6. Fases 2-3: Contexto + dependencias
  7. Fase 4: Implementa feature por feature
     → Cada feature: backend→tests→frontend→tests
     → Actualiza PROGRESS con cada checkbox
  8. Fase 5: Self-review, corrige bugs
  9. Fase 6: Checkpoint, sync Notion
  10. Fase 7: Checklist calidad completo
  11. Fase 8: Admin configurado
  12. Fase 9: Validación 4x4 + docs RAG + manual
  13. Fase 10: Docker + CompanyModule.Module += CRM + guard + menú

Resultado:
  - PROGRESS-CRM.md → COMPLETADO
  - PLAN-CRM.md en docs/plans/
  - Código en backend/apps/crm/ + frontend/src/app/features/crm/
  - Tests con cobertura >80%
  - Admin configurado
  - Docs RAG generados
  - Módulo registrado en licencias
  - Notion actualizado
```

---

## 11. Implementación Técnica

### Archivos a crear/modificar:

| Archivo | Acción | Propósito |
|---------|--------|-----------|
| `.claude/skills/saicloud-orquestador/SKILL.md` | CREAR | Skill principal del orquestador |
| `CLAUDE.md` | MODIFICAR | Agregar comandos de orquestación |
| `scripts/create-progress.sh` | CREAR | Template para PROGRESS-{MODULO}.md |
| `docs/plans/WORKFLOW-ORQUESTADOR-MODULOS.md` | CREAR | Este documento |

### Prioridad de implementación:

1. **Crear skill orquestador** ← lo más importante
2. **Actualizar CLAUDE.md** con comandos
3. **Crear template PROGRESS**
4. **Probar con módulo CRM**

---

*Documento creado: 10 Abril 2026*  
*Siguiente paso: Crear el skill saicloud-orquestador/SKILL.md*
