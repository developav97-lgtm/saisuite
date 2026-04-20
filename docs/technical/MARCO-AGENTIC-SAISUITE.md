# Marco Agentic SaiSuite — Manual del flujo de trabajo

**Versión:** 1.0 | **Fecha:** 2026-04-19 | **Autor:** ValMen Tech

Manual operativo del marco de delegación y administración de agentes de Claude Code en el proyecto SaiSuite. Cubre cómo el orquestador clasifica trabajo, invoca skills, delega a subagentes, y ejecuta de forma casi autónoma.

---

## Índice

1. [Arquitectura del marco](#1-arquitectura-del-marco)
2. [Componentes](#2-componentes)
3. [Flujo de trabajo end-to-end](#3-flujo-de-trabajo-end-to-end)
4. [Delegación: Skill vs Agent vs inline](#4-delegación-skill-vs-agent-vs-inline)
5. [Tipos de ticket y fases](#5-tipos-de-ticket-y-fases)
6. [Gates humanos y técnicos](#6-gates-humanos-y-técnicos)
7. [Gestión de contexto](#7-gestión-de-contexto)
8. [Administración de agentes](#8-administración-de-agentes)
9. [Administración de skills](#9-administración-de-skills)
10. [Troubleshooting](#10-troubleshooting)
11. [Extender el marco](#11-extender-el-marco)

---

## 1. Arquitectura del marco

```
┌─────────────────────────────────────────────────────────────────┐
│                    INPUT DEL PO (Juan David)                     │
│   "nuevo módulo X" | "agregar feature Y" | "fix Z" | etc.       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                ┌──────────────────────────┐
                │    CLAUDE.md (97 líneas)  │◄─── Reglas globales + puntero
                │    Punto de entrada       │     al marco agentic
                └────────────┬─────────────┘
                             │
                             ▼
         ┌────────────────────────────────────────────┐
         │   ORQUESTADOR (skill saicloud-orquestador) │
         │   .claude/skills/saicloud-orquestador/     │
         │                                            │
         │   1. Clasifica ticket                      │
         │   2. Lee flujo desde PHASE-MAP.md          │
         │   3. Ejecuta fase por fase                 │
         └────────────┬───────────────────────────────┘
                      │
                      ▼
           ┌──────────────────────────┐
           │   PHASE-MAP.md           │
           │   (fuente de verdad)     │
           └────────┬─────────────────┘
                    │
        ┌───────────┴──────────────┐
        ▼                          ▼
┌───────────────────┐    ┌──────────────────────┐
│   Skill tool      │    │   Agent tool         │
│   (metodología)   │    │   (delegación aislada)│
│                   │    │                      │
│ anthropic-skills: │    │ .claude/agents/      │
│ saicloud-*        │    │ 24 subagentes        │
└───────────────────┘    └──────────────────────┘
```

### Principios de diseño

1. **Punto de entrada único** — todo el trabajo pasa por el orquestador. No hay atajos.
2. **Separación datos/código** — `PHASE-MAP.md` tiene el QUÉ invocar; `SKILL.md` del orquestador tiene el CÓMO ejecutar.
3. **Delegación explícita** — el orquestador invoca Skills y Agents con llamadas reales (`Skill()`, `Agent()`), no narrativa.
4. **Contexto protegido** — investigación y QA siempre en subagentes con `context: fork`.
5. **Autonomía post-aprobación** — el PO solo aprueba PRD y PLAN; el resto se ejecuta automáticamente.

---

## 2. Componentes

### 2.1 CLAUDE.md (punto de entrada)

Archivo raíz (97 líneas) que se carga en toda sesión. Contiene:

- Reglas críticas globales (backend, frontend, BD, tests, commits)
- Referencias al marco agentic
- Estructura del proyecto
- Política de gestión de contexto
- Modo de respuesta (ahorro de tokens)

**No contiene** detalles del flujo — esos viven en PHASE-MAP y el orquestador.

### 2.2 Orquestador (`.claude/skills/saicloud-orquestador/SKILL.md`)

Skill que se activa con cualquier trigger de trabajo:
- `"nuevo módulo"`, `"nueva feature"`, `"fix"`, `"mejorar"`, `"continuar"`, `"estado"`

Responsabilidades:
- Clasificar ticket (`MODULE | FEATURE | BUGFIX | IMPROVEMENT`)
- Leer flujo desde `PHASE-MAP.md`
- Ejecutar fases secuencialmente
- Invocar Skills/Agents según el mapa
- Gestionar gates humanos y técnicos
- Notificar al PO al completar

### 2.3 PHASE-MAP.md (fuente de verdad)

Tabla central (133 líneas) con columnas:

| Fase | Nombre | Rol | Modelo | Skill | Agent | Gate |

Más:
- Flujos alternativos (FEATURE, BUGFIX, IMPROVEMENT)
- Triggers especiales (Security, DB, Go, n8n, AWS)
- Reglas absolutas y retrocesos
- Pseudo-código del loop ejecutor
- Listado de agentes disponibles

**Regla:** cualquier cambio de flujo se refleja aquí primero. El orquestador nunca hardcodea decisiones.

### 2.4 Subagentes (`.claude/agents/` — 18 agentes)

Organizados por dominio:

**Ingeniería (8):**
- `Backend Architect` — diseño de APIs, BD, microservicios
- `Frontend Developer` — Angular, UI implementation
- `Database Optimizer` — schemas, queries, indexes
- `DevOps Automator` — CI/CD, infra
- `Security Engineer` — threat modeling, auth, OWASP
- `Technical Writer` — docs, README, tutoriales
- `Code Reviewer` — revisión de PRs
- `Incident Response Commander` — outages, producción

**Testing/QA (3):**
- `Reality Checker` — certificación basada en evidencia, default "NEEDS WORK"
- `Evidence Collector` — QA screenshot-obsesionado
- `API Tester` — validación REST

**Diseño (2):**
- `UI Designer` — sistemas visuales, pixel-perfect
- `UX Researcher` — user research, usability

**Producto/PM (2):**
- `Senior Project Manager` — specs → tasks, PRDs
- `gestor-proyectos` — gestión PMP + Scrum SaiCloud

**Especializados (3):**
- `MCP Builder` — Model Context Protocol servers
- `Workflow Architect` — diseño de workflows n8n
- `SaiCloud Offline Sync Specialist` — sync bidireccional

> WCAG AA se valida vía skill `design:accessibility-review`. Performance testing se delega inline cuando aplica. Git workflow inline con CLI.

### 2.5 Skills del plugin (`anthropic-skills:saicloud-*`)

17 skills del plugin Anthropic con metodología específica:

- `saicloud-planificacion`, `saicloud-contexto`, `saicloud-proteccion-ventana`
- `saicloud-backend-django`, `saicloud-frontend-angular`, `saicloud-pruebas-unitarias`
- `saicloud-iteracion`, `saicloud-revision-final`, `saicloud-panel-admin`
- `saicloud-validacion-ui`, `saicloud-documentacion`, `saicloud-despliegue`
- `saicloud-n8n-ia`, `saicloud-chat-widget`, `saicloud-saiopen-agente`
- `saicloud-infraestructura-aws`, `saicloud-microservicio-go`

Se invocan con `Skill(skill="anthropic-skills:saicloud-X")`.

### 2.6 Enforcement automatizado (`.claude/scripts/` + hooks)

Scripts invocados por hooks de Claude Code (configurados en `.claude/settings.json`):

| Script | Hook | Qué hace |
|--------|------|----------|
| `session-start.sh` | `SessionStart` | Lee PROGRESS activo y muestra estado (módulo, fase, próxima acción) al iniciar sesión |
| `pre-push-guard.sh` | `PreToolUse:Bash` | Bloquea `git push`/`deploy` si el marco tiene errores o no hay Fase 7 ✅ |
| `validate-marco.sh` | Manual + usado por pre-push | 9 checks: archivos existen, agentes válidos, referencias coherentes, tamaños bajo límite |

**Kick-off automático:** al abrir sesión, si hay `PROGRESS-{MODULO}.md` con `status: in_progress`, el hook imprime el estado y el orquestador sabe desde dónde continuar sin intervención.

**Enforcement de gates:** `git push origin main` falla con exit 2 si el PROGRESS del módulo activo no tiene Fase 7 aprobada. Claude Code respeta el bloqueo y reporta la razón al PO.

Ejecución manual del validador:
```bash
.claude/scripts/validate-marco.sh              # completo
.claude/scripts/validate-marco.sh --quick      # rápido (skip verbose)
.claude/scripts/validate-marco.sh --fix-perms  # corrige permisos de scripts
```

### 2.7 Templates (`.claude/templates/`)

Plantillas canónicas para artefactos persistentes:

| Template | Uso |
|----------|-----|
| `PROGRESS.template.md` | Base para crear `PROGRESS-{MODULO}.md` con frontmatter YAML |
| `SESSION.template.md` | Base para `SESSION-{MODULO}-{FECHA}.md` (memoria de sesión) |

El frontmatter del PROGRESS es la **fuente de verdad del estado** consumida por los hooks:

```yaml
---
module: facturacion
ticket_type: MODULE
status: in_progress          # in_progress | blocked | completed
current_phase: 4b
phases_approved: [0, 1, 2, 3, 4a]
phases_gates:
  prd: true
  plan: true
  staging: false
next_action: implementar Invoice.service.ts
blockers: []
---
```

### 2.8 Rules (`.claude/rules/`)

Reglas path-scoped que Claude Code carga automáticamente:

- `backend/django.md` — BaseModel, services.py, tests, logger
- `frontend/angular.md` — Material, OnPush, `@if/@for`, strict
- `general/architecture.md` — multi-tenancy, convenciones
- `general/generation-order.md` — orden de creación de archivos
- `general/context-management.md` — `/compact`, SESSION files, delegación

---

## 3. Flujo de trabajo end-to-end

### 3.1 Ejemplo: MODULE nuevo

```
PO: "nuevo módulo: facturación electrónica"
│
├─► Orquestador: clasifica como MODULE
│   Responde: "🎫 Ticket MODULE — módulo: facturación ..."
│
├─► FASE 0 — PRD (Opus + Senior Project Manager)
│   · Skill: —
│   · Agent: Senior Project Manager
│   · Output: docs/plans/PRD-facturacion.md
│   · 🛑 GATE: PO aprueba PRD
│
├─► FASE 1 — Plan técnico (Opus + Backend Architect)
│   · Skill: anthropic-skills:saicloud-planificacion
│   · Agent: Backend Architect
│   · Output: docs/plans/PLAN-facturacion.md + DECs
│   · 🛑 GATE: PO aprueba PLAN
│
├─► FASE 2 — Contexto (Sonnet)
│   · Skill: anthropic-skills:saicloud-contexto
│   · Agent: —
│   · Output: CONTEXT.md actualizado
│
├─► FASE 3 — Skills/APIs (Sonnet + Rapid Prototyper)
│   · Output: POCs de integraciones externas
│
├─► FASE 4a — Backend (Sonnet + Backend Architect)
│   · Skill: anthropic-skills:saicloud-backend-django
│   · ✓ GATE: pytest pasa, coverage ≥80
│
├─► FASE 4b — Frontend (Sonnet + Frontend Developer)
│   · Skill: anthropic-skills:saicloud-frontend-angular
│   · ✓ GATE: ng test pasa, coverage services 100
│
├─► FASE 4c — Tests (Sonnet + API Tester)
│   · Skill: anthropic-skills:saicloud-pruebas-unitarias
│   · ✓ GATE: coverage mínimas cumplidas
│
├─► FASE 5 — Iteración (Sonnet + Evidence Collector)
│   · Skill: anthropic-skills:saicloud-iteracion
│   · ✓ GATE: 0 bugs abiertos
│
├─► FASE 6 — Checkpoint (Sonnet + Project Shepherd)
│   · Output: PROGRESS coherente, NOTION-SYNC generado
│
├─► FASE 7 — Revisión final (Sonnet + Code Reviewer + Reality Checker)
│   · Skill: anthropic-skills:saicloud-revision-final
│   · ✓ GATE: checklist 100%
│
├─► FASE 8 — Admin Django (Sonnet + Backend Architect)
│   · Skill: anthropic-skills:saicloud-panel-admin
│
├─► FASE 9a — Validación UI (Sonnet + UI Designer + Accessibility Auditor)
│   · Skill: anthropic-skills:saicloud-validacion-ui
│   · ✓ GATE: 4x4 pasa
│
├─► FASE 9b — Documentación + RAG (Sonnet + Technical Writer)
│   · Skill: anthropic-skills:saicloud-documentacion
│   · Output: docs/technical/facturacion/ + RAG-CHUNKS.md
│
├─► FASE 10 — Deploy + Licencia (Sonnet + DevOps Automator)
│   · Skill: anthropic-skills:saicloud-despliegue
│   · ✓ GATE: pre-deploy 100%
│
└─► 📬 Notificación Gmail a develop.av97@gmail.com
    PROGRESS-FACTURACION.md → ✅ COMPLETADO
```

### 3.2 Ejemplo: BUGFIX autónomo

```
PO: "fix: el login no valida email vacío"
│
├─► Orquestador: clasifica como BUGFIX (sin gates humanos)
│
├─► DIAG — Reality Checker
│   Agent(subagent_type="Reality Checker",
│         prompt="Reproducir: login sin email → qué hace actualmente.
│                 Archivo: backend/apps/users/views.py
│                 Buscar causa raíz.")
│
├─► FIX — Sonnet inline
│   · Edita backend/apps/users/services.py con validación
│   · Agrega test backend/apps/users/tests/test_login.py
│   · pytest → verde
│   · Actualiza ERRORS.md con DEC
│
├─► VERIFY — Evidence Collector
│   Agent(subagent_type="Evidence Collector",
│         prompt="Validar fix de login email vacío.
│                 Correr pytest + ng test. Screenshot UI del error.
│                 Reportar PASS/FAIL.")
│
├─► COMMIT — Git Workflow Master
│   Agent(subagent_type="Git Workflow Master",
│         prompt="Crear commit: fix(users): validar email vacío en login.
│                 Archivos modificados: services.py, test_login.py, ERRORS.md")
│
└─► ✅ Ticket BUGFIX-042 cerrado
```

---

## 4. Delegación: Skill vs Agent vs inline

### Decisión rápida

| Situación | Usar | Razón |
|-----------|------|-------|
| Seguir metodología/checklist ya definida | **Skill** | Inyecta la secuencia correcta (PRD, PLAN, deploy) |
| Trabajo aislado que puede ejecutarse independiente | **Agent** | Forked context — solo el resumen vuelve |
| Investigación de código amplia | **Agent** (Explore) | Protege contexto principal |
| QA, revisión de PR, auditoría | **Agent** (Reality Checker, Code Reviewer) | Imparcial + resumen corto |
| Edit puntual de archivo | **Inline** | Edit/Write directo |
| Coordinación entre fases | **Inline** | Orquestador necesita ver todo |

### Reglas absolutas

- **Prompts de Agent son self-contained.** El subagente no ve la conversación — hay que incluir paths, objetivo, requisitos.
- **Nunca ejecutar exploración larga inline.** Siempre delegar a Agent para mantener el contexto principal limpio.
- **Skills no anidan Skills.** Un skill puede recomendar otro, pero las llamadas son secuenciales, no recursivas.
- **Agent no invoca skills principales.** Solo lee, analiza, retorna resumen. Las decisiones de flujo vuelven al orquestador.

### Ejemplos de prompts bien formados

**✅ Agent prompt correcto:**
```
Agent(
  subagent_type="Backend Architect",
  description="Diseño modelos facturación",
  prompt="Diseñar modelos Django para módulo facturación electrónica SaiSuite.
          Requisitos del PLAN: backend/apps/facturacion/PLAN.md
          Restricciones:
          - BaseModel obligatorio (UUID pk, company FK)
          - Integración Saiopen vía sai_key + unique_together con company_id
          - Campos fiscales NUMERIC(15,2)
          Entregar: propuesta de models.py con Invoice, InvoiceItem, Series.
          Formato: archivo .md con diagrama ER + código models.py completo.
          Ubicación: docs/plans/PLAN-facturacion-modelos.md"
)
```

**❌ Agent prompt malo:**
```
Agent(subagent_type="Backend Architect", prompt="diseña los modelos")
```
(El subagente no sabe qué módulo, qué restricciones, qué entregar, dónde).

---

## 5. Tipos de ticket y fases

### 5.1 MODULE — Módulo nuevo completo

- **Trigger:** `"nuevo módulo X"`, entrega de PRD/requerimientos
- **Fases:** 0 → 10 completas
- **Modelo:** Opus (0-3) → Sonnet (4-10)
- **Gate humano:** PRD (fase 0) + PLAN (fase 1)
- **Duración:** múltiples sesiones
- **PROGRESS:** `PROGRESS-{MODULO}.md` persistente

### 5.2 FEATURE — Feature nueva en módulo existente

- **Trigger:** `"nueva feature"`, `"agregar X al módulo Y"`
- **Fases:** 0 → 1 → 4 → 5 → 7 → 9
- **Modelo:** Opus (0-1) → Sonnet (4-9)
- **Gate humano:** PLAN (fase 1)
- **Duración:** 1-3 sesiones
- **PROGRESS:** se anexa al del módulo

### 5.3 BUGFIX — Corrección de bug

- **Trigger:** `"fix"`, `"error"`, `"no funciona"`, `"el test falla"`
- **Pasos:** Diag → Fix → Verify → Commit
- **Modelo:** Sonnet completo
- **Gate humano:** ninguno (100% autónomo)
- **Duración:** ≤1 sesión
- **Output:** fix + entry en ERRORS.md

### 5.4 IMPROVEMENT — Refactor/optimización

- **Trigger:** `"mejorar"`, `"optimizar"`, `"refactorizar"`
- **Fases:** 1 → 4 → 5 → 7
- **Modelo:** Sonnet (Opus solo si es arquitectural)
- **Gate humano:** PLAN solo si afecta arquitectura
- **Duración:** 1-2 sesiones

---

## 6. Gates humanos y técnicos

### Gates humanos (requieren aprobación PO)

| Gate | Aplica a | Acción si aprobado | Acción si rechazado |
|------|----------|-------------------|---------------------|
| PRD | MODULE fase 0 | Avanzar a fase 1 | Ajustar PRD, notificar |
| PLAN | MODULE/FEATURE fase 1 | Avanzar a fase 2 | Ajustar PLAN, notificar |

**Protocolo:** el orquestador escribe `PROGRESS → 🛑 ESPERANDO APROBACIÓN {gate}`, crea draft Gmail, y se detiene. No continúa hasta recibir respuesta explícita del PO.

### Gates técnicos (automáticos)

| Gate | Aplica a | Cómo se valida |
|------|----------|----------------|
| Tests pasan | Fase 4 por feature | `pytest` + `ng test` retornan 0 |
| Coverage | Fase 5 → 6 | `coverage report` ≥ umbrales |
| Checklist revisión | Fase 7 → 8 | Skill `saicloud-revision-final` todos los items |
| UI 4x4 | Fase 9a → 9b | Skill `saicloud-validacion-ui` + Accessibility Auditor |
| Pre-deploy | Fase 10 | Skill `saicloud-despliegue` checklist completo |

**Si falla:** el orquestador retrocede a la fase anterior indicada en PHASE-MAP (ej. Fase 7 falla → Fase 5). Nunca avanza con gate rojo.

### Retrocesos permitidos

- Fase 7 falla → volver a Fase 5
- Fase 9 UI falla → volver a Fase 5
- Fase 10 pre-deploy falla → volver a Fase 7

Todo retroceso se registra en PROGRESS con motivo.

---

## 7. Gestión de contexto

### Estrategia de `/compact`

| Momento | Comando |
|---------|---------|
| Al completar cada fase | `/compact Foco en Fase {N} módulo {X}. Estado: {resumen}` |
| Cada 15-20 turnos | `/compact Foco en {actividad actual}` |
| Antes de Fase 4 (implementación larga) | `/compact Preparando implementación módulo X` |
| Cuando respuestas se sientan vagas | `/compact Reset con foco en {tarea}` |

### Archivos de memoria persistente

| Archivo | Rol | Cuándo actualizar |
|---------|-----|-------------------|
| `PROGRESS-{MODULO}.md` | Tracking del módulo | Cada fase ✅ o bloqueo |
| `CONTEXT.md` | Estado actual del proyecto | Al cerrar feature/módulo |
| `DECISIONS.md` | Decisiones DEC-XXX | Al tomar decisión arquitectural |
| `ERRORS.md` | Bugs resueltos + causa | Al cerrar cada BUGFIX |
| `SESSION-{MODULO}-{FECHA}.md` | Memoria de trabajo de la sesión | Durante Fase 4 larga |

### Política de respuestas

- **Código** → directamente en archivos, nunca pegar bloques largos en chat
- **Explicaciones** → ≤10 líneas inline
- **Detalle técnico** → `PROGRESS-{MODULO}.md`
- **Sin resúmenes finales** redundantes
- **Sin repetir** lo que dijo el usuario

### Delegación y contexto

```
Contexto principal (main)
│
├─► Skill(anthropic-skills:X) ──► suma al contexto actual (inline)
│
└─► Agent(subagent_type=X) ──────► context: fork
                                    retorna solo el resumen
                                    contexto principal intacto
```

**Regla:** si una tarea puede hacerse aislada (exploración, QA, análisis), **siempre** delegar a Agent.

---

## 8. Administración de agentes

### Ubicación de agentes

```
.claude/agents/         ← Project-scoped (24 agentes, versionados en git)
~/.claude/agents/       ← User-scoped (fallback, compartido entre proyectos)
```

**Precedencia:** project-scoped gana sobre user-scoped si hay mismo nombre.

### Agregar un nuevo agente

1. Crear archivo `.claude/agents/<categoria>-<nombre>.md` con frontmatter:

```markdown
---
name: Nombre Exacto Para Subagent Type
description: Qué hace este agente, cuándo usarlo
tools: all-tools  # o lista específica
color: blue
---

# Identidad y misión

{Contexto del rol y responsabilidad}

## Capacidades clave
- ...

## Cómo trabaja
- ...
```

2. Agregar entrada en `PHASE-MAP.md` si se usa en alguna fase.
3. Probar: nueva sesión → `Agent(subagent_type="Nombre Exacto...")`.

### Modificar agente existente

1. Editar el `.md` directamente.
2. Ajustar PHASE-MAP si cambia el rol.
3. Verificar que `name:` no cambió (rompería invocaciones existentes).

### Deprecar un agente

1. Remover entradas en PHASE-MAP.
2. Buscar referencias: `grep -rn "subagent_type=\"Nombre\"" .`
3. Eliminar el archivo una vez limpio.

### Agentes críticos del flujo (no borrar)

- `Backend Architect`, `Frontend Developer` — Fase 4
- `Reality Checker`, `Evidence Collector` — BUGFIX + gates
- `Code Reviewer` — Fase 7
- `DevOps Automator` — Fase 10
- `Senior Project Manager`, `Project Shepherd` — Fases 0, 6

---

## 9. Administración de skills

### Tipos de skills disponibles

| Tipo | Prefijo | Ubicación |
|------|---------|-----------|
| Project-scoped | — | `.claude/skills/<nombre>/SKILL.md` |
| Plugin Anthropic | `anthropic-skills:` | Pre-instalado, invocable por nombre |
| Plugin externos | `plugin-name:` | Varios |

### Invocación

```
Skill(skill="anthropic-skills:saicloud-planificacion")
Skill(skill="saicloud-orquestador")   # local project
Skill(skill="brevity-mode")            # local project
```

### Agregar skill project-scoped nuevo

1. Crear `.claude/skills/<nombre>/SKILL.md` con frontmatter:

```markdown
---
name: nombre-skill
description: >
  Qué hace. Cuándo activar. Triggers.
---

# Contenido del skill
```

2. Agregar a PHASE-MAP si aplica a alguna fase.
3. Actualizar orquestador `SKILL.md` si cambia el flujo.

### Cuándo crear skill propio vs usar `anthropic-skills:*`

- **Usar plugin** si ya existe un skill del plugin que hace lo mismo. Cero duplicación.
- **Crear propio** solo si necesitas lógica específica del proyecto que el plugin no cubre.

---

## 10. Troubleshooting

### Problema: agente no responde

**Causa:** el nombre en `subagent_type` no coincide con el frontmatter `name:` del archivo.

**Solución:**
```bash
grep -r "^name:" .claude/agents/ | grep -i "<nombre>"
```
Copiar el nombre exacto (con espacios y capitalización).

### Problema: skill `not found`

**Causa:** prefijo incorrecto o skill no instalado.

**Solución:** listar skills disponibles en la sesión (aparecen en `<system-reminder>` al inicio). Validar prefijo:
- `anthropic-skills:saicloud-X` — plugin Anthropic
- `saicloud-orquestador` — project local (sin prefijo)

### Problema: orquestador no clasifica correctamente

**Causa:** trigger ambiguo o skill no activado.

**Solución:**
- Usar trigger explícito: `"nuevo módulo facturación"` en vez de `"necesito agregar algo"`.
- Forzar skill: `Skill(skill="saicloud-orquestador")` manualmente.

### Problema: gate humano se salta

**Causa:** bug — NUNCA debe pasar.

**Solución:** si el orquestador avanza sin aprobación, revisar `SKILL.md` sección "Gates que nunca se saltan" y reforzar al PO que debe aprobar explícitamente.

### Problema: contexto se llena rápido

**Diagnóstico:**
- ¿Se están ejecutando exploraciones inline en vez de Agent? (revisar último turno)
- ¿Falta `/compact` tras fases completas?
- ¿CLAUDE.md/PHASE-MAP crecieron por encima de lo razonable?

**Solución:**
1. `/compact Foco en {actividad}` inmediato.
2. Para próximas exploraciones, usar `Agent(subagent_type="Explore")` en lugar de Grep/Read masivo inline.

### Problema: tests fallan en Fase 4

**Protocolo:**
1. Orquestador NO avanza.
2. Invoca `Agent(Evidence Collector, prompt="reporta qué falló")`.
3. Con el reporte, aplica fix inline.
4. Re-corre tests.
5. Solo marca Fase 4 ✅ cuando verde.

---

## 11. Extender el marco

### Caso: agregar una nueva fase al flujo MODULE

1. Editar `PHASE-MAP.md` — agregar fila con Fase, Rol, Modelo, Skill, Agent, Gate.
2. Editar `SKILL.md` del orquestador si requiere lógica de invocación distinta.
3. Si hay retrocesos nuevos, agregar regla en sección "Retrocesos permitidos".
4. Probar con un MODULE ficticio antes de confiar en producción.

### Caso: agregar skill project-scoped para algo recurrente

1. Identificar la secuencia repetida (3+ usos del mismo patrón).
2. Crear `.claude/skills/<nombre>/SKILL.md`.
3. Actualizar PHASE-MAP si aplica a alguna fase.
4. Documentar aquí en este manual.

### Caso: agregar un agente nuevo de agency-agents u otra fuente

1. Copiar el `.md` a `.claude/agents/`.
2. Validar frontmatter (`name:`, `description:`, `tools:`).
3. Agregar a la tabla de sección 2.4 de este manual.
4. Actualizar PHASE-MAP si reemplaza o complementa un agente existente.

### Caso: escalar a múltiples módulos en paralelo

El orquestador por defecto es secuencial. Para paralelizar:

- Abrir sesiones de Claude Code separadas (un terminal por módulo).
- Cada sesión tiene su propio `PROGRESS-{MODULO}.md`.
- Los tickets no se mezclan porque PROGRESS es por módulo.
- El backend/frontend pueden trabajarse en paralelo vía `Agent` delegations en la misma sesión, pero con cuidado de contexto.

---

## Apéndice A — Convenciones de prompts a subagentes

Plantilla recomendada:

```
Agent(
  subagent_type="<Nombre exacto del frontmatter>",
  description="<3-5 palabras del task>",
  prompt="""
  OBJETIVO: {una línea clara}

  CONTEXTO:
  - Módulo: {nombre}
  - Archivos relevantes: {paths absolutos}
  - Requisitos del PLAN: {paths}
  - Restricciones SaiSuite: {solo las aplicables}

  TAREA:
  {pasos concretos}

  ENTREGAR:
  - {output 1} en {path}
  - {output 2} en formato {md | código | resumen}

  NO HACER:
  - {cosas explícitas a evitar}
  """
)
```

---

## Apéndice B — Comandos rápidos

```bash
# Verificar agentes project-scoped
ls .claude/agents/ | wc -l  # debe ser 24+

# Verificar que no hay referencias rotas a skills
grep -rn "\.claude/skills/saicloud-planificacion" . | grep -v PHASE-MAP

# Validar tamaño CLAUDE.md
wc -l CLAUDE.md  # objetivo ≤100 líneas

# Listar skills del plugin disponibles
# (aparecen en system-reminder al iniciar sesión)

# Backup de agents antes de modificar
cp -r .claude/agents /tmp/agents-backup-$(date +%s)
```

---

## Apéndice C — Archivos clave del marco

| Archivo | Rol | Tamaño |
|---------|-----|--------|
| `CLAUDE.md` | Entrada + reglas globales | ~97 líneas |
| `.claude/PHASE-MAP.md` | Fuente de verdad del flujo | ~133 líneas |
| `.claude/skills/saicloud-orquestador/SKILL.md` | Lógica del orquestador | ~206 líneas |
| `.claude/skills/brevity-mode/SKILL.md` | Modo Caverna | ~73 líneas |
| `.claude/rules/backend/django.md` | Reglas backend | ~37 líneas |
| `.claude/rules/frontend/angular.md` | Reglas frontend | ~49 líneas |
| `.claude/rules/general/architecture.md` | Reglas arquitectura | ~30 líneas |
| `.claude/rules/general/generation-order.md` | Orden de creación | ~43 líneas |
| `.claude/rules/general/context-management.md` | Gestión de contexto | ~101 líneas |
| `.claude/agents/*.md` | 24 subagentes | varía |
| `docs/technical/MARCO-AGENTIC-SAISUITE.md` | Este manual | — |

---

**Mantenimiento de este manual:** actualizar cuando se agreguen fases, agentes, skills, o cambien las reglas del marco. Es la referencia canónica — cualquier divergencia con PHASE-MAP o SKILL.md debe resolverse reescribiendo aquí y propagando.

**Última revisión:** 2026-04-19 — ValMen Tech
