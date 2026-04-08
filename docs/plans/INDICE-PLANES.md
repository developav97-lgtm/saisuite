# ÍNDICE DE PLANES — Saicloud
> Última actualización: 2026-04-07
> **Regla:** Este índice se actualiza cada vez que se agrega, inicia o completa un plan.

---

## 🟢 PLANES ACTIVOS (en cola o en ejecución)

| Plan | Módulo | Descripción | Estado | Modelo sugerido |
|------|--------|-------------|--------|-----------------|
| [PLAN-IA-CENTRALIZADA.md](PLAN-IA-CENTRALIZADA.md) | IA / Todos | Asistente IA centralizado: RAG + pgvector + DataCollectors + Learning | 🟡 Planificado | Opus → Sonnet |
| [PROMPT-CLAUDECODE-IA-CENTRALIZADA.md](PROMPT-CLAUDECODE-IA-CENTRALIZADA.md) | IA / Todos | Prompts multi-agente para 3 sprints | 🟡 Planificado | — |
| [PLAN-SAIDASHBOARD.md](PLAN-SAIDASHBOARD.md) | SaiDashboard | Dashboard BI financiero + Agente Go multi-DB + CFO Virtual IA | 🟡 En cola | Opus |
| [PROMPT-CLAUDECODE-SAIDASHBOARD.md](PROMPT-CLAUDECODE-SAIDASHBOARD.md) | SaiDashboard | Prompt listo para pegar en Claude Code | 🟡 En cola | — |

---

## ✅ PLANES COMPLETADOS (ver `historic/`)

| Plan | Módulo | Feature | Completado |
|------|--------|---------|-----------|
| [PLAN-modulo-proyectos.md](historic/PLAN-modulo-proyectos.md) | Proyectos | MVP módulo proyectos | 2026-03 |
| [FEATURE-5-EXECUTION-PLAN.md](historic/FEATURE-5-EXECUTION-PLAN.md) | Proyectos | Feature #5 | 2026-03 |
| [FEATURE-5-TASK-BREAKDOWN.md](historic/FEATURE-5-TASK-BREAKDOWN.md) | Proyectos | Feature #5 tareas | 2026-03 |
| [FEATURE-6-EXECUTION-PLAN.md](historic/FEATURE-6-EXECUTION-PLAN.md) | Proyectos | Feature #6 | 2026-03 |
| [FEATURE-6-TASK-BREAKDOWN.md](historic/FEATURE-6-TASK-BREAKDOWN.md) | Proyectos | Feature #6 tareas | 2026-03 |
| [FEATURE-7-EXECUTION-PLAN.md](historic/FEATURE-7-EXECUTION-PLAN.md) | Proyectos | Feature #7 | 2026-03 |
| [FEATURE-7-TASK-BREAKDOWN.md](historic/FEATURE-7-TASK-BREAKDOWN.md) | Proyectos | Feature #7 tareas | 2026-03 |
| [REFACTOR-TASK-BREAKDOWN.md](historic/REFACTOR-TASK-BREAKDOWN.md) | Proyectos | Refactor ES→EN | 2026-03 |
| [MIGRATION-PLAN-ES-TO-EN.md](historic/MIGRATION-PLAN-ES-TO-EN.md) | Proyectos | Migración nombres | 2026-03 |
| [PLAN-REFINED-FEATURE-4-RESOURCE-MANAGEMENT.md](historic/PLAN-REFINED-FEATURE-4-RESOURCE-MANAGEMENT.md) | Proyectos | Feature #4 recursos | 2026-03 |
| [UI-REDESIGN-NAVIGATION.md](historic/UI-REDESIGN-NAVIGATION.md) | Global | Redesign navegación | 2026-03 |
| [PLAN-CORRECCION-COMPLETO.md](historic/PLAN-CORRECCION-COMPLETO.md) | Proyectos | Corrección 34 gaps | 2026-03 |
| [PLAN-CORRECCION-GAPS.md](historic/PLAN-CORRECCION-GAPS.md) | Proyectos | Gaps adicionales | 2026-03 |
| [FASE-A-COMPLETADA.md](historic/FASE-A-COMPLETADA.md) | Proyectos | Fase A mobile | 2026-03 |
| [FIX_BUG_1_PDF_EXPORT.md](historic/FIX_BUG_1_PDF_EXPORT.md) | Proyectos | Fix bug PDF | 2026-03 |
| [FIX_BUG_2_TEMPLATE_SELECTOR.md](historic/FIX_BUG_2_TEMPLATE_SELECTOR.md) | Proyectos | Fix template | 2026-03 |
| [FIX_BUG_3_EXCEL_TEMPLATE.md](historic/FIX_BUG_3_EXCEL_TEMPLATE.md) | Proyectos | Fix Excel | 2026-03 |
| [REFACTOR-PRECHECKLIST.md](historic/REFACTOR-PRECHECKLIST.md) | Proyectos | Pre-checklist refactor | 2026-03 |
| [PROMPT_FASE_1_MOBILE.md] (historic/PROMPT_FASE_4_FUNCIONALIDADES.md) | Proyectos | Prompts mobile/funcs | 2026-03 |

---

## 📋 CÓMO USAR ESTE ÍNDICE

### Al crear un plan nuevo:
1. Crear `docs/plans/PLAN-[NOMBRE-MODULO].md`
2. Crear `docs/plans/PROMPT-CLAUDECODE-[NOMBRE].md` con las instrucciones para Claude Code
3. Agregar entrada en la tabla **PLANES ACTIVOS** arriba

### Al completar un plan:
1. Mover `PLAN-[NOMBRE].md` y `PROMPT-[NOMBRE].md` a `docs/plans/historic/`
2. Actualizar la entrada en este índice: moverla a **PLANES COMPLETADOS**
3. Generar `docs/reports/INFORME_[NOMBRE]_[FECHA].md` con resumen de lo ejecutado
4. Actualizar `CONTEXT.md` con el nuevo estado del módulo
