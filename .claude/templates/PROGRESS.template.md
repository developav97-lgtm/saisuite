---
module: <NOMBRE_MODULO>
ticket_type: MODULE      # MODULE | FEATURE | BUGFIX | IMPROVEMENT
ticket_id: <TICKET-XXX>
status: in_progress      # pending | in_progress | blocked | completed | rolled_back
current_phase: 0         # fase actual (0-10 para MODULE)
phases_approved:         # fases completadas con ✅
  - []
phases_gates:            # gates humanos aprobados por PO
  prd: false             # true tras aprobación Fase 0 (solo MODULE)
  plan: false            # true tras aprobación Fase 1 (MODULE/FEATURE)
  staging: false         # true tras validación en staging
last_session: <SESSION-MODULO-YYYY-MM-DD.md>
next_action: <descripción 1 línea de lo siguiente a hacer>
blockers: []             # lista de bloqueos activos
created: YYYY-MM-DD
updated: YYYY-MM-DD
owner: Juan David
---

# PROGRESS — <Módulo>

> **Leer primero:** frontmatter arriba. Indica fase actual, aprobaciones y próxima acción.
> El orquestador consulta este archivo al inicio de cada sesión para reanudar trabajo.

---

## Resumen ejecutivo

- **Objetivo:** <qué resuelve este módulo/feature>
- **Alcance:** <qué SÍ y qué NO entra>
- **Estimación:** <sesiones estimadas>
- **Dependencias:** <otros módulos, integraciones, APIs externas>

---

## Fases (MODULE completo)

### Fase 0 — PRD
- [ ] PRD generado → `docs/plans/PRD-<modulo>.md`
- [ ] 🛑 Aprobación del PO
- **Agent:** Senior Project Manager
- **Notas:**

### Fase 1 — Plan técnico
- [ ] PLAN generado → `docs/plans/PLAN-<modulo>.md`
- [ ] DECs registrados en `DECISIONS.md`
- [ ] 🛑 Aprobación del PO
- **Skill:** `anthropic-skills:saicloud-planificacion`
- **Agent:** Backend Architect
- **Notas:**

### Fase 2 — Contexto
- [ ] CONTEXT.md actualizado
- **Skill:** `anthropic-skills:saicloud-contexto`

### Fase 3 — Skills/APIs
- [ ] POCs / spikes validados
- **Agent:** Backend Architect

### Fase 4 — Implementación
- [ ] 4a Backend (models → migration → serializers → services → views → urls)
- [ ] 4b Frontend (model.ts → service.ts → components → routes)
- [ ] 4c Tests unitarios (coverage backend ≥80, services FE 100)
- **Skills:** `anthropic-skills:saicloud-backend-django`, `anthropic-skills:saicloud-frontend-angular`, `anthropic-skills:saicloud-pruebas-unitarias`
- **Agents:** Backend Architect, Frontend Developer, API Tester

### Fase 5 — Iteración
- [ ] Self-review checklist
- [ ] Bugs resueltos
- **Skill:** `anthropic-skills:saicloud-iteracion`
- **Agent:** Evidence Collector

### Fase 6 — Checkpoint
- [ ] PROGRESS coherente
- [ ] NOTION-SYNC-<MODULO>-<FECHA>.md generado
- **Agent:** gestor-proyectos

### Fase 7 — Revisión final
- [ ] Checklist de seguridad + Django + Angular + tests + API
- **Skill:** `anthropic-skills:saicloud-revision-final`
- **Agents:** Code Reviewer + Reality Checker

### Fase 8 — Admin Django
- [ ] Modelos registrados
- [ ] Filtros, búsqueda, acciones
- **Skill:** `anthropic-skills:saicloud-panel-admin`

### Fase 9 — UI/UX + Documentación
- [ ] 9a Validación 4x4 + WCAG AA
- [ ] 9b Documentación técnica y manual de usuario
- [ ] RAG chunks generados → `docs/technical/<modulo>/RAG-CHUNKS.md`
- **Skills:** `anthropic-skills:saicloud-validacion-ui`, `anthropic-skills:saicloud-documentacion`
- **Agents:** UI Designer, Technical Writer

### Fase 10 — Deploy + Licencia
- [ ] Docker verificado
- [ ] Registro en `CompanyModule.Module`
- [ ] Migración creada
- [ ] ModuleGuard + menú agregados
- [ ] Staging validado
- [ ] 🛑 Aprobación final PO para prod
- [ ] Deploy prod
- [ ] Notificación Gmail enviada
- **Skill:** `anthropic-skills:saicloud-despliegue`
- **Agent:** DevOps Automator

---

## Log de fases completadas

| Fecha | Fase | Duración | Notas |
|-------|------|----------|-------|
| | | | |

---

## Decisiones tomadas en este módulo

| ID | Decisión | Razón | Fecha |
|----|----------|-------|-------|
| DEC-XXX | | | |

*(Las DECs se archivan también en `DECISIONS.md` raíz)*

---

## Bloqueos activos

*(Vacío si no hay bloqueos. Formato: "❌ BLOQUEADO — {descripción} — {fecha}")*

---

## Sesiones de trabajo

| Fecha | Archivo | Foco | Resultado |
|-------|---------|------|-----------|
| | `SESSION-<modulo>-<fecha>.md` | | |

---

## Tests y cobertura

| Componente | Coverage | Última medición |
|------------|----------|-----------------|
| Backend services | — | — |
| Backend models | — | — |
| Frontend services | — | — |
| Frontend components | — | — |

---

## Post-deploy

- **Deploy staging:** <fecha>
- **Deploy prod:** <fecha>
- **Incidentes:** <link a ERRORS.md si aplica>
- **Rollback plan:** <procedimiento si falla>

---

**Generado desde:** `.claude/templates/PROGRESS.template.md`
**Mantener actualizado:** cada cambio de fase debe reflejarse en el frontmatter Y en el cuerpo.
