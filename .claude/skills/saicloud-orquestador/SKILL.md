---
name: saicloud-orquestador
description: >
  Orquestador maestro para TODO el desarrollo de SaiSuite. Clasifica tickets
  (MODULE / FEATURE / BUGFIX / IMPROVEMENT), invoca skills del plugin
  anthropic-skills con el Skill tool, delega a agentes de .claude/agents/
  con el Agent tool, y ejecuta de forma autónoma excepto en gates humanos
  (aprobación de PRD y PLAN). Consulta siempre .claude/PHASE-MAP.md como
  fuente de verdad del flujo.
  Activa con: "nuevo módulo", "nueva feature", "fix", "mejora", "continuar",
  "estado", o cualquier instrucción de trabajo sobre el proyecto.
---

# Skill: Orquestador SaiSuite

## Propósito

Punto de entrada ÚNICO para trabajo de desarrollo. Recibe input del PO,
clasifica el ticket, ejecuta el flujo delegando a skills y agentes, y notifica.

**Fuente de verdad del flujo:** [`.claude/PHASE-MAP.md`](../../PHASE-MAP.md).
Este skill describe CÓMO ejecutar; PHASE-MAP dice QUÉ invocar en cada fase.

---

## Roles simulados

| Rol | Quién | Responsabilidad |
|-----|-------|-----------------|
| PO | Juan David | Aprueba PRD/PLAN, recibe notificación final |
| Scrum Master | Claude (Opus en planificación) | Clasifica, planifica, coordina, revisa |
| Developer | Claude (Sonnet) | Implementa código + tests |
| QA | Subagente Sonnet | Valida tests, cobertura, checklists |

**Selección de modelo:** iniciar con `claude --model opusplan` → Opus para `/plan`, Sonnet para ejecución. O manualmente `/model opus` y `/model sonnet`.

---

## Tipos de ticket

| Tipo | Trigger | Flujo (ver PHASE-MAP) | Gate humano | Autonomía |
|------|---------|------------------------|-------------|-----------|
| **MODULE** | "nuevo módulo X" | 0→10 completo | PRD + PLAN | post-aprobación |
| **FEATURE** | "nueva feature", "agregar X a Y" | 0→1→4→5→7→9 | PLAN | post-aprobación |
| **BUGFIX** | "fix", "error", "no funciona" | Diag→Fix→Verify→Commit | ninguno | 100% autónomo |
| **IMPROVEMENT** | "mejorar", "optimizar", "refactor" | 1→4→5→7 | PLAN solo si arquitectural | autónomo |

---

## Kick-off de sesión (obligatorio)

**Al recibir CUALQUIER instrucción de trabajo, ANTES de clasificar ticket:**

1. Buscar `PROGRESS-*.md` en el root del proyecto.
2. Si hay PROGRESS activo con `status: in_progress`, leer su frontmatter:
   - `current_phase`, `next_action`, `blockers`, `last_session`
3. Responder con:
   ```
   📂 Estado detectado
   Módulo activo: {module}
   Fase actual:   {current_phase}
   Última acción: {next_action}
   Bloqueos:      {blockers}

   ¿Continuamos desde aquí o es trabajo nuevo?
   ```
4. Si el usuario confirma continuar → seguir desde `current_phase`.
5. Si es trabajo nuevo → clasificar normalmente.

Este paso protege continuidad entre sesiones. Nunca arrancar trabajo sin verificar PROGRESS.

---

## Ejecución autónoma — pseudo-código

```
on_user_input(msg):
    # Kick-off
    progress = leer_frontmatter_activo("PROGRESS-*.md")
    si progress.status == "in_progress":
        reportar_estado(progress)
        si usuario_confirma_continuar:
            fase_inicial = progress.current_phase
        sino:
            fase_inicial = 0

    ticket = clasificar(msg)
    fases  = FLOW[ticket.tipo]          # de PHASE-MAP

    si MODULE → crear/leer PROGRESS-{MODULO}.md desde .claude/templates/PROGRESS.template.md
    si FEATURE/BUGFIX/IMPROVEMENT → anexar ticket al PROGRESS del módulo

    for fase in fases:
        config = PHASE_MAP[fase]

        # Cambio de modelo si aplica
        si config.modelo == "opus" y modelo_actual != "opus":
            cambiar_modelo("opus")

        # Invocación real del skill del plugin
        si config.skill:
            Skill(skill=config.skill)

        # Delegación a subagente con prompt self-contained
        for agent_type in config.agents:
            Agent(
                subagent_type=agent_type,
                description="Fase {N}: {nombre}",
                prompt=prompt_contextualizado(fase, ticket)
            )

        # Gate (aprobación humana)
        si config.gate_humano y no aprobado(config.gate):
            notificar_po(fase)
            actualizar(PROGRESS, fase, "🛑 ESPERANDO APROBACIÓN")
            return

        # Gate técnico (tests, coverage, checklist)
        si config.gate_tecnico y no pasa(config.gate):
            retroceder_a(fase.anterior)
            continue

        actualizar_frontmatter(PROGRESS, {
            current_phase: fase.siguiente,
            phases_approved: [...aprobadas, fase],
            next_action: prox_accion,
            updated: hoy()
        })

    notificar_gmail(ticket, "COMPLETADO")
```

**Reglas de actualización de frontmatter:**
- Al completar fase → actualizar `current_phase`, `phases_approved`, `next_action`, `updated`
- Al alcanzar gate humano → `status: blocked`, agregar a `blockers`
- Al recibir aprobación PO → `phases_gates.prd` o `.plan` → `true`
- Al terminar → `status: completed`, `current_phase: done`
- Al retroceder → registrar motivo en `blockers` y retroceder `current_phase`

**Telemetría (obligatoria):** invocar `.claude/scripts/telemetry.sh <ticket_id> <event> <extras_json>` en estos momentos:
| Evento | Cuándo | Extras recomendados |
|--------|--------|---------------------|
| `ticket_start` | Al clasificar ticket | `{"type":"MODULE|FEATURE|BUGFIX|IMPROVEMENT","module":"..."}` |
| `phase_start` | Al iniciar una fase | `{"phase":"4b","skill":"...","agent":"..."}` |
| `phase_complete` | Al marcar fase ✅ | `{"phase":"4b","issues_found":N}` |
| `gate_hit` | Al llegar a gate humano | `{"gate":"plan"}` |
| `gate_approved` | Al recibir aprobación PO | `{"gate":"plan"}` |
| `agent_invoked` | Tras cada Agent() | `{"subagent":"Backend Architect","tokens":N}` |
| `blocker` | Al registrar bloqueo | `{"reason":"..."}` |
| `rollback` | Al retroceder | `{"from":"7","to":"5","reason":"..."}` |
| `ticket_complete` | Al finalizar | `{"bugs_fixed":N,"build_status":"ok|fail"}` |

Ver métricas: `.claude/scripts/telemetry-stats.sh` (distribución de eventos + duración promedio por fase).

---

## Prompt template de clasificación

Al recibir cualquier instrucción de Juan David, responder primero:

```
🎫 Ticket clasificado

Tipo:     {MODULE | FEATURE | BUGFIX | IMPROVEMENT}
Módulo:   {nombre}
Título:   {resumen}
Flujo:    {fases según PHASE-MAP}
Modelo:   {opus inicial | sonnet}
Gate:     {PRD/PLAN/ninguno}

→ Iniciando Fase {N}: {nombre}
```

Luego ejecutar la primera fase.

---

## Gestión de contexto

| Tipo ticket | `/compact` | PROGRESS | Subagentes |
|-------------|-----------|----------|------------|
| MODULE | Cada fase completada + cada 15-20 turnos | `PROGRESS-{MODULO}.md` | `context: fork` para investigación |
| FEATURE | Tras backend, antes de frontend | Anexar ticket al PROGRESS del módulo | Según PHASE-MAP |
| BUGFIX | Solo si debug largo | Registrar causa/fix en ERRORS.md | Reality Checker + Evidence Collector |
| IMPROVEMENT | Si toca >5 archivos | PROGRESS del módulo | Code Reviewer |

**Política de respuestas (siempre):**
- Código → en archivos, nunca bloques enteros en chat
- Explicaciones → ≤10 líneas inline
- Detalle técnico → `PROGRESS-{MODULO}.md`
- Sin resúmenes finales redundantes

---

## Gates que nunca se saltan

| Gate | Aplica a | Si falla |
|------|----------|----------|
| PO aprueba PRD | MODULE Fase 0→1 | Ajustar PRD |
| PO aprueba PLAN | MODULE/FEATURE Fase 1→2 | Ajustar PLAN |
| Tests pasan | Fase 4 por feature | Corregir antes de avanzar |
| Coverage mínima | Fase 5→6 | Escribir más tests |
| Checklist revisión | Fase 7→8 | Volver a Fase 5 |
| UI 4x4 + RAG | Fase 9→10 | Corregir, completar |
| Pre-deploy 100% | Fase 10 | Volver a Fase 7 |

---

## Triggers especiales

Ver tabla en `PHASE-MAP.md` sección "Triggers especiales (invocación condicional)".
Ejemplos: Security Engineer si hay auth nueva, Database Optimizer si hay queries críticas, Incident Response Commander si es incidente producción.

---

## Manejo de bloqueos

Si durante ejecución autónoma surge un problema que no se puede resolver:

1. Registrar en PROGRESS como `❌ BLOQUEADO — {motivo}`
2. Documentar opciones evaluadas
3. Notificar al PO vía Gmail draft
4. Continuar con el siguiente ticket si hay más trabajo pendiente

---

## Integración con CLAUDE.md y reglas

Respetar SIEMPRE:
- `.claude/rules/backend/django.md` — lógica en services.py, BaseModel, etc.
- `.claude/rules/frontend/angular.md` — Material, OnPush, `@if/@for`, `strict: true`
- `.claude/rules/general/architecture.md`
- `.claude/rules/general/context-management.md`
- `.claude/rules/general/generation-order.md` — orden de creación de archivos
- `CLAUDE.md` — reglas críticas globales

---

## Notion y RAG

- Cada ticket completado genera `NOTION-SYNC-{MODULO}-{FECHA}.md` — Cowork sincroniza.
- Fase 9b genera `docs/technical/{modulo}/RAG-CHUNKS.md` para el chat IA.

---

## Notificación final

Al completar un ticket, crear draft Gmail a `develop.av97@gmail.com`:

```
Asunto: [SaiSuite] Ticket {ID} {TIPO} — {estado}

Módulo:   {nombre}
Título:   {resumen}
Fases:    {X/Y completadas}
Tests:    {resultados resumidos}
Archivos: {N modificados / {N creados}
Link:     PROGRESS-{MODULO}.md

{Notas adicionales}
```

---

**Versión:** 3.0 | **Actualizado:** 2026-04-19 | **ValMen Tech**
**Complementa:** `.claude/PHASE-MAP.md` (fuente de verdad del flujo)
