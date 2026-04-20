# PHASE-MAP — Delegación del Orquestador SaiSuite

**Fuente única de verdad.** El orquestador consulta esta tabla para saber qué invocar en cada fase.
Cualquier cambio de flujo se refleja aquí, no en `SKILL.md`.

---

## Convenciones de invocación

- **Skill**: `Skill(skill="anthropic-skills:saicloud-X")` — skills del plugin Anthropic.
- **Agent**: `Agent(subagent_type="<nombre exacto del frontmatter>", description=..., prompt=...)` — los agentes viven en `.claude/agents/`.
- **Modelo**: `opus` solo para arquitectura/PRD; `sonnet` para todo lo demás.
- **Gate**: condición que detiene la ejecución hasta que se cumpla (aprobación humana o checklist técnico).

---

## Flujo MODULE (completo)

| Fase | Nombre | Rol | Modelo | Skill | Agent (subagent_type) | Gate |
|------|--------|-----|--------|-------|----------------------|------|
| 0 | PRD | Scrum Master | opus | — | Senior Project Manager | PO aprueba PRD |
| 1 | Plan técnico | Scrum Master | opus | `anthropic-skills:saicloud-planificacion` | Backend Architect | PO aprueba PLAN |
| 2 | Contexto | Scrum Master | sonnet | `anthropic-skills:saicloud-contexto` | — | — |
| 3 | Skills/APIs | Scrum Master | sonnet | — | Backend Architect | — |
| 4a | Backend Django | Developer | sonnet | `anthropic-skills:saicloud-backend-django` | Backend Architect | Tests pasan |
| 4b | Frontend Angular | Developer | sonnet | `anthropic-skills:saicloud-frontend-angular` | Frontend Developer | Tests pasan |
| 4c | Tests unitarios | Developer | sonnet | `anthropic-skills:saicloud-pruebas-unitarias` | API Tester | Coverage ≥80 backend, =100 services FE |
| 5 | Iteración | Dev+QA | sonnet | `anthropic-skills:saicloud-iteracion` | Evidence Collector | 0 bugs abiertos |
| 6 | Checkpoint | Scrum Master | sonnet | — | gestor-proyectos | PROGRESS coherente |
| 7 | Revisión final | Scrum Master | sonnet | `anthropic-skills:saicloud-revision-final` | Code Reviewer + Reality Checker | Checklist 100% |
| 8 | Admin Django | Developer | sonnet | `anthropic-skills:saicloud-panel-admin` | Backend Architect | Modelos registrados |
| 9a | Validación UI 4x4 | Dev+QA | sonnet | `anthropic-skills:saicloud-validacion-ui` + `design:accessibility-review` | UI Designer | 4x4 + WCAG AA pasan |
| 9b | Documentación + RAG | Technical Writer | sonnet | `anthropic-skills:saicloud-documentacion` | Technical Writer | RAG chunks OK |
| 10 | Deploy + Licencia | DevOps | sonnet | `anthropic-skills:saicloud-despliegue` | DevOps Automator | Pre-deploy 100% + commit |

---

## Flujo FEATURE (subconjunto)

Fases: 0 → 1 → 4 → 5 → 7 → 9 (sin contexto general ni admin).
Misma tabla aplica, saltando 2, 3, 6, 8, 10.

## Flujo BUGFIX (autónomo, sin gates)

| Paso | Acción | Modelo | Agent |
|------|--------|--------|-------|
| Diag | Reproducir y aislar causa raíz | sonnet | Reality Checker |
| Fix | Aplicar corrección in-situ + actualizar ERRORS.md | sonnet | — (main) |
| Verify | Tests + evidencia visual si UI | sonnet | Evidence Collector |
| Commit | Mensaje `fix(<scope>): <desc>` | sonnet | — (main, comando git inline) |

## Flujo IMPROVEMENT

- Sin gate salvo si es arquitectural (entonces gate en Fase 1).
- Fases: 1 → 4 → 5 → 7.
- Agent principal: `Code Reviewer` (revisión) + rol específico según alcance.

---

## Triggers especiales (invocación condicional)

Cuando el ticket cumple estas condiciones, agregar agents/skills extra en la fase indicada:

| Condición | Fase | Invocar además |
|-----------|------|----------------|
| Endpoints nuevos o auth tocada | 7 | `Agent(Security Engineer)` |
| Queries con JOIN >3 tablas o N+1 | 1 | `Agent(Database Optimizer)` |
| Microservicio Go justificado en PLAN | 4 | `Skill(anthropic-skills:saicloud-microservicio-go)` |
| Workflow n8n nuevo | 4 | `Skill(anthropic-skills:saicloud-n8n-ia)` + `Agent(Workflow Architect)` |
| Integración Saiopen (Firebird) | 1 + 4 | `Skill(anthropic-skills:saicloud-saiopen-agente)` + `Agent(SaiCloud Offline Sync Specialist)` |
| Chat widget / asistente IA | 4b | `Skill(anthropic-skills:saicloud-chat-widget)` |
| Infra AWS nueva (RDS, ECS, S3) | 10 | `Skill(anthropic-skills:saicloud-infraestructura-aws)` |
| Incidente en producción | — | `Agent(Incident Response Commander)` (prioridad máxima, pausa todo) |
| MCP server nuevo | 4 | `Agent(MCP Builder)` |
| Priorización de backlog | 0 | `Agent(gestor-proyectos)` |

---

## Reglas absolutas

1. **Un gate no se salta.** Si la fase tiene gate humano y el PO no ha aprobado, el orquestador detiene ejecución y notifica.
2. **Tests fallan → se corrige antes de avanzar.** Nunca marcar fase como ✅ con tests rojos.
3. **Subagentes siempre con prompt self-contained.** El agent delegado no tiene contexto de la conversación; incluir paths, requisitos, objetivo.
4. **Retrocesos permitidos:** Fase 7 falla → Fase 5. Fase 9 falla UI → Fase 5. Fase 10 falla pre-deploy → Fase 7. Registrar motivo en PROGRESS.
5. **Notificación Gmail al completar cada ticket** (draft a `develop.av97@gmail.com`).

---

## Pseudo-código del orquestador

```
on_user_input(msg):
    ticket = clasificar(msg)              # MODULE | FEATURE | BUGFIX | IMPROVEMENT
    fases = FLOW[ticket.tipo]             # lista de fases
    persistir(PROGRESS-{modulo}.md, ticket)

    for fase in fases:
        config = PHASE_MAP[fase]
        if config.modelo == "opus": cambiar_modelo("opus")

        if config.skill:
            Skill(skill=config.skill)      # invocación real

        for agent_type in config.agents:
            Agent(subagent_type=agent_type, prompt=prompt_contextualizado(fase))

        if config.gate and not gate_pasa(config.gate):
            notificar_po(fase)
            return ESPERANDO_APROBACION

        actualizar(PROGRESS, fase, "✅")

    notificar_gmail(ticket, "COMPLETADO")
```

---

## Agentes disponibles (`.claude/agents/` — 18)

**Ingeniería (8):** Backend Architect · Frontend Developer · Database Optimizer · DevOps Automator · Security Engineer · Technical Writer · Code Reviewer · Incident Response Commander

**Testing/QA (3):** Reality Checker · Evidence Collector · API Tester

**Diseño (2):** UI Designer · UX Researcher

**Producto/PM (2):** Senior Project Manager · gestor-proyectos

**Especializados (3):** MCP Builder · Workflow Architect · SaiCloud Offline Sync Specialist

---

**Última actualización:** 2026-04-19 — ValMen Tech
