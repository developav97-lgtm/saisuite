# Manual de Uso — Orquestador SaiSuite

**Proyecto:** SaiSuite (SaaS Multi-tenant para PyMEs)
**Stack:** Django 5 + Angular 18 + PostgreSQL 16 + n8n + AWS
**Fecha:** 10 Abril 2026 | ValMen Tech

---

## 1. Acceso al Agente

### Iniciar Claude Code

```bash
cd ~/Desktop/saisuite
claude --model opusplan
```

Con `opusplan`, Claude usa Opus para planificación (modo `/plan`) y Sonnet para ejecución de código. Es la configuración recomendada para todo el trabajo en SaiSuite.

### Alternativa manual

Si necesitas controlar el modelo tú mismo:

```bash
claude                    # Inicia con el modelo por defecto
/model opus               # Cambiar a Opus (para planificar)
/model sonnet             # Cambiar a Sonnet (para implementar)
```

### Primera acción al iniciar sesión

No necesitas hacer nada especial. Al recibir tu primera instrucción, el orquestador lee automáticamente `CLAUDE.md`, `CONTEXT.md` y el `PROGRESS-{MODULO}.md` relevante para cargar el estado del proyecto.

---

## 2. Tipos de Solicitud

Todo lo que le pidas al agente se clasifica automáticamente en uno de 4 tipos de ticket. No necesitas especificar el tipo — el orquestador lo detecta por el lenguaje que uses.

### 2.1 MODULE — Módulo Nuevo Completo

**Cuándo usarlo:** Cuando necesites un módulo completamente nuevo (ej: SaiCash, SaiRoute, SaiLoyalty).

**Cómo pedirlo:**
```
nuevo módulo SaiCash
```
```
empezar módulo SaiLoyalty, aquí están los requerimientos: [...]
```

**¿Necesito modo plan primero?** No. El orquestador entra automáticamente en Fase 0 (PRD) usando Opus. Te presentará el PRD para aprobación antes de continuar.

**Flujo completo:**
```
Tú: "nuevo módulo SaiCash" + requerimientos
  → Fase 0: Genera PRD → 🛑 Tú apruebas
  → Fase 1: Plan técnico → 🛑 Tú apruebas
  → Fases 2-10: 100% autónomo (implementa, testea, documenta, configura licencias)
  → 📬 Te notifica por Gmail al completar
```

**Fases:** 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 (todas)
**Gates humanos:** Aprobación de PRD (fase 0) + aprobación de PLAN (fase 1)
**Estimación:** Múltiples sesiones

---

### 2.2 FEATURE — Feature Nueva en Módulo Existente

**Cuándo usarlo:** Cuando necesites agregar funcionalidad nueva a un módulo que ya existe.

**Cómo pedirlo:**
```
agregar exportación PDF al módulo proyectos
```
```
nueva feature: sistema de notificaciones push en SaiReviews
```
```
quiero que el dashboard tenga gráficos de tendencia mensual
```

**¿Necesito modo plan primero?** No. El orquestador genera un mini-PRD y plan técnico automáticamente usando Opus, y te pide aprobación del plan antes de implementar.

**Flujo:**
```
Tú: "agregar filtros avanzados al CRM"
  → Fase 0: Mini-PRD (se guarda en PROGRESS)
  → Fase 1: Plan técnico → 🛑 Tú apruebas
  → Fases 4-9: Autónomo (implementa backend + frontend + tests + validación UI)
  → 📬 Te notifica al completar
```

**Fases:** 0 → 1 → 4 → 5 → 7 → 9 (subconjunto)
**Gate humano:** Aprobación de PLAN (fase 1)
**Estimación:** 1-3 sesiones

---

### 2.3 BUGFIX — Corrección de Error

**Cuándo usarlo:** Cuando algo no funciona, hay un error, o un test falla.

**Cómo pedirlo:**
```
hay un error en el formulario de contactos, no guarda los datos
```
```
fix: el endpoint de proyectos devuelve 500 cuando el nombre tiene tildes
```
```
el test de comunicaciones falla con timeout
```
```
corregir el login que no redirige al dashboard
```

**¿Necesito modo plan primero?** No. Los bugfixes son 100% autónomos desde el inicio. El agente diagnostica, corrige, escribe un test que reproduce el bug, verifica que todos los tests pasan, y te notifica.

**Flujo:**
```
Tú: "el formulario de contactos no guarda"
  → Diagnóstico: Lee código, identifica causa raíz
  → Fix: Corrige + escribe test que reproduce el bug
  → Test: Corre TODOS los tests del módulo
  → Review: Self-review + registra en ERRORS.md
  → 📬 Te notifica con causa raíz y solución
```

**Fases:** Diagnóstico → Fix → Test → Review
**Gate humano:** Ninguno — 100% autónomo
**Estimación:** 1 sesión o menos

---

### 2.4 IMPROVEMENT — Mejora o Refactor

**Cuándo usarlo:** Cuando algo funciona pero quieres mejorarlo, optimizarlo o refactorizarlo.

**Cómo pedirlo:**
```
optimizar las queries del dashboard, están lentas
```
```
refactorizar el servicio de notificaciones para que sea más mantenible
```
```
mejorar la validación de formularios en el módulo proyectos
```

**¿Necesito modo plan primero?** Depende. Si la mejora afecta la arquitectura (ej: cambiar cómo se manejan permisos en todo el sistema), el orquestador genera un plan y te pide aprobación. Si es una mejora localizada, ejecuta de forma autónoma.

**Flujo:**
```
Tú: "optimizar las queries del dashboard"
  → Fase 1: Plan ligero (qué se mejora, por qué, cómo)
  → 🛑 Gate solo si afecta arquitectura
  → Fase 4: Implementa mejora
  → Fase 5: Verifica que nada se rompió
  → Fase 7: Review de calidad
  → 📬 Te notifica al completar
```

**Fases:** 1 → 4 → 5 → 7
**Gate humano:** Solo si afecta arquitectura
**Estimación:** 1-2 sesiones

---

## 3. Respuesta del Orquestador

Al recibir cualquier solicitud, el orquestador responde con una clasificación antes de empezar:

```
🎫 Ticket clasificado:

Tipo: FEATURE
Módulo: Proyectos
Descripción: Agregar exportación PDF de reportes
Modelo: Opus → Sonnet
Fases: 0 → 1 → 4 → 5 → 7 → 9
Autonomía: Requiere aprobación de PLAN

Generando mini-PRD...
```

Si no está seguro del tipo, te preguntará antes de continuar.

---

## 4. Comandos Especiales

| Comando | Qué hace |
|---------|----------|
| `continuar módulo {nombre}` | Retoma trabajo pendiente donde lo dejaste |
| `estado módulo {nombre}` | Muestra el progreso actual del módulo |
| `cerrar sesión` | Guarda estado en CONTEXT.md, actualiza PROGRESS, notifica pendientes |

### Retomar trabajo

Cuando inicies una nueva sesión de Claude Code y quieras continuar donde quedaste:

```
continuar módulo proyectos
```

El orquestador lee `PROGRESS-PROYECTOS.md`, identifica la última fase completada y el ticket activo, y continúa desde ahí.

### Ver estado

```
estado módulo proyectos
```

Te muestra: fase actual, tickets pendientes, último avance, y lo que sigue.

---

## 5. Gestión de Contexto

### /compact — Cuándo usarlo

Las conversaciones largas consumen contexto. El orquestador ejecuta `/compact` automáticamente en estos momentos:

- Al completar cada fase del flujo
- Cada 15-20 turnos de conversación
- Cada 3 features implementadas dentro de la Fase 4

Si necesitas hacerlo manualmente:

```
/compact Foco en Fase 4 del módulo Proyectos. Completado: modelos + serializers + services
```

Siempre incluye el foco para que el compact retenga lo relevante.

### Subagentes

Para investigación o exploración que no debe contaminar tu contexto principal, el orquestador usa subagentes con `context: fork`. No necesitas gestionarlo tú — es automático.

### Respuestas

El agente escribe código completo directamente en los archivos. Las explicaciones en el chat son breves. El detalle completo queda en `PROGRESS-{MODULO}.md`.

---

## 6. Archivos Generados

| Archivo | Cuándo se genera | Contenido |
|---------|-----------------|-----------|
| `PROGRESS-{MODULO}.md` | Al crear primer ticket de un módulo | Tracking de fases, tickets, sesiones |
| `docs/plans/PRD-{MODULO}.md` | Fase 0 de MODULE | Documento de requerimientos del producto |
| `docs/plans/PLAN-{MODULO}.md` | Fase 1 de MODULE | Plan técnico con endpoints, modelos, estructura |
| `docs/plans/FEATURE-{MOD}-{nombre}.md` | Fase 1 de FEATURE | Plan técnico de la feature |
| `SESSION-{MODULO}-{FECHA}.md` | Inicio de sesión de implementación | Log de lo trabajado en la sesión |
| `NOTION-SYNC-{MODULO}-{FECHA}.md` | Fase 6 (Checkpoint) | Archivo para que Cowork sincronice a Notion |
| `docs/technical/{modulo}/RAG-CHUNKS.md` | Fase 9 | Chunks para base de conocimiento del chat IA |
| `DECISIONS.md` | Cuando hay decisiones arquitectónicas | Registro DEC-XXX |
| `ERRORS.md` | Cuando se resuelve un bug | Catálogo de errores con causa raíz y fix |

---

## 7. Notificaciones

Al completar cada ticket, el orquestador genera un borrador de Gmail a `develop.av97@gmail.com` con el resumen:

```
Asunto: ✅ Saicloud — FEATURE completado: Exportación PDF reportes

Ticket: PROY-005
Tipo: FEATURE
Módulo: Proyectos

Resumen:
- Endpoint POST /api/proyectos/{id}/export-pdf/
- Componente ExportPdfDialogComponent con selección de formato
- Tests: 12 nuevos, todos passing
- Cobertura backend: 87%, frontend: 74%

Próximos pasos sugeridos: Integrar con el sistema de notificaciones
```

Si el Gmail MCP no está disponible, el resumen se guarda en PROGRESS y en Apple Notes.

---

## 8. Reglas Path-Scoped

El proyecto usa reglas que se cargan automáticamente cuando el agente toca archivos en ciertas rutas. No necesitas activarlas — es transparente:

| Regla | Se activa cuando se toca | Qué contiene |
|-------|--------------------------|--------------|
| `.claude/rules/backend/django.md` | `backend/**/*.py` | Convenciones Django 5, multi-tenant, BaseModel |
| `.claude/rules/frontend/angular.md` | `frontend/**/*.ts` | Angular 18, Material, OnPush, strict |
| `.claude/rules/general/architecture.md` | `docs/plans/**` | Evaluación Django vs Go, restricciones |
| `.claude/rules/general/context-management.md` | `PROGRESS-*.md` | Formato de respuestas, /compact, sesiones |

Esto asegura que el agente siempre siga las convenciones correctas sin que tú tengas que recordárselo.

---

## 9. Ejemplo Completo: Feature de Principio a Fin

### Paso 1 — Tú solicitas

```
agregar sistema de etiquetas (tags) a los proyectos, que se puedan crear, asignar y filtrar por tags
```

### Paso 2 — Orquestador clasifica

```
🎫 Ticket clasificado:

Tipo: FEATURE
Módulo: Proyectos
Descripción: Sistema de etiquetas (tags) con CRUD y filtrado
Modelo: Opus → Sonnet
Fases: 0 → 1 → 4 → 5 → 7 → 9
Autonomía: Requiere aprobación de PLAN

Generando mini-PRD...
```

### Paso 3 — Genera plan (Opus)

El agente genera `docs/plans/FEATURE-PROYECTOS-tags.md` con el plan técnico: modelos (Tag, ProjectTag), endpoints, componentes Angular, y te lo presenta para aprobación.

### Paso 4 — Tú apruebas

```
aprobado, adelante
```

### Paso 5 — Implementación autónoma (Sonnet)

A partir de aquí el agente trabaja solo:

1. **Backend:** `Tag` model → migración → `TagSerializer` → `TagService` → `TagViewSet` → URLs → tests pytest
2. **Frontend:** `tag.model.ts` → `tag.service.ts` → `TagChipComponent` → `TagFilterComponent` → rutas → tests
3. **Iteración:** Self-review, verifica cobertura
4. **Revisión final:** Checklist completo de calidad
5. **UI/UX:** Validación 4x4, genera RAG chunks

### Paso 6 — Notificación

Recibes borrador de Gmail con el resumen completo. El ticket en `PROGRESS-PROYECTOS.md` se marca como ✅ COMPLETADO.

---

## 10. Tabla de Referencia Rápida

| Quiero... | Digo... | Tipo | ¿Modo plan? | ¿Gate? |
|-----------|---------|------|-------------|--------|
| Módulo nuevo completo | "nuevo módulo X" | MODULE | Auto (Opus) | PRD + PLAN |
| Feature en módulo existente | "agregar X a Y" | FEATURE | Auto (Opus) | PLAN |
| Corregir un error | "fix: descripción" | BUGFIX | No necesita | Ninguno |
| Mejorar algo existente | "mejorar/optimizar X" | IMPROVEMENT | Solo si es arquitectural | Condicional |
| Retomar trabajo | "continuar módulo X" | — | No | No |
| Ver estado | "estado módulo X" | — | No | No |
| Cerrar sesión | "cerrar sesión" | — | No | No |

---

## 11. Tips

**Sé específico con los requerimientos.** Mientras más contexto des en la solicitud inicial, mejor será el PRD/PLAN generado. Incluye: qué usuarios lo usan, qué datos maneja, cómo se relaciona con módulos existentes.

**Revisa el plan antes de aprobar.** El plan define los endpoints, modelos y componentes. Si algo no te convence, pide ajustes antes de aprobar — es mucho más barato cambiar un plan que refactorizar código.

**No interrumpas la ejecución autónoma.** Una vez aprobado el plan, el agente implementa todo solo. Si necesitas hacer un cambio, espera a que termine el ticket actual y luego crea un nuevo ticket de IMPROVEMENT o BUGFIX.

**Usa `/compact` si la conversación se siente lenta.** Si notas que el agente responde más lento o pierde contexto, ejecuta `/compact` con un foco claro.

**Revisa `PROGRESS-{MODULO}.md` para el estado real.** Es la fuente de verdad del estado de cada módulo, no la conversación.

---

*Manual generado: 10 Abril 2026 — ValMen Tech*
*Proyecto: SaiSuite | Orquestador v2.0*
