# CLAUDE.md — SaiSuite
# ValMen Tech × Saiopen | Django 5 + Angular 18 + PostgreSQL 16 + n8n + AWS

SaiSuite es una plataforma SaaS multi-tenant para el ecosistema Saiopen (ERP Windows/Firebird).

**Idioma:** Todas las respuestas, planes y documentos en español. El código puede estar en inglés.

---

## Marco Agentic (punto único de entrada)

**Orquestador:** `.claude/skills/saicloud-orquestador/SKILL.md` — Leer SIEMPRE al recibir cualquier instrucción de trabajo.
**Flujo ejecutable:** `.claude/PHASE-MAP.md` — tabla Fase → Skill → Agent → Gate.
**Agentes disponibles:** `.claude/agents/` (18 agentes project-scoped).
**Skills del plugin:** prefijo `anthropic-skills:saicloud-*` (invocar con `Skill` tool).

El orquestador clasifica cada ticket en `MODULE | FEATURE | BUGFIX | IMPROVEMENT`, invoca skills/agents según PHASE-MAP, y solo detiene ejecución en gates humanos (aprobación de PRD y PLAN).

---

## Reglas críticas (aplican SIEMPRE)

**Backend:** Lógica en `services.py` (nunca views/modelos). BaseModel (UUID pk, company FK). Nunca `print()`, usar logger. Nunca secrets hardcodeados.
**Frontend:** `strict: true`, OnPush, `async pipe`, Angular Material (NUNCA PrimeNG/Bootstrap/Tailwind), `@if`/`@for` (NUNCA `*ngIf`/`*ngFor`), variables CSS `var(--sc-*)`.
**BD:** company_id en TODO, UUID v4, dinero `NUMERIC(15,2)`, Firebird `sai_key` + `unique_together`.
**Tests:** Junto con código. Backend services ≥80%. Frontend services =100%, components ≥70%.
**Commits:** `<tipo>(<scope>): <desc>`. Nunca `.env` en git.

Reglas detalladas:
- `.claude/rules/backend/django.md`
- `.claude/rules/frontend/angular.md`
- `.claude/rules/general/architecture.md`
- `.claude/rules/general/generation-order.md`
- `.claude/rules/general/context-management.md`

---

## Documentación de referencia

| Tarea | Documento |
|---|---|
| Modelos | `docs/base-reference/Esquema_BD_SaiSuite_v1.docx` |
| Código | `docs/base-reference/Estandares_Codigo_SaiSuite_v1.docx` |
| Componentes Angular | `docs/standards/UI-UX-STANDARDS.md` |
| Validar funcionalidad | `docs/base-reference/CHECKLIST-VALIDACION.md` |
| Feature nueva | `docs/base-reference/Flujo_Feature_SaiSuite_v1.docx` |

Leer también: `ERRORS.md`, `DECISIONS.md`, `CONTEXT.md`

---

## Estructura del proyecto

```
saisuite/
├── backend/apps/        # core, companies, users, ai, chat, proyectos, dashboard, sync_agent, integrations
├── frontend/src/app/    # core/, shared/, features/ (lazy loading)
├── agent/               # Agente Python Windows ↔ Firebird ↔ SQS
├── docs/                # plans/, technical/, manuales/, standards/
├── .claude/
│   ├── agents/          # 18 subagentes project-scoped
│   ├── skills/          # saicloud-orquestador, brevity-mode
│   ├── rules/           # backend/, frontend/, general/
│   └── PHASE-MAP.md     # fuente de verdad del flujo
├── CLAUDE.md
├── CONTEXT.md           # estado actual
├── DECISIONS.md         # decisiones DEC-XXX
├── ERRORS.md            # errores resueltos
└── PROGRESS-*.md        # tracking por módulo
```

---

## Gestión de contexto

- Ejecutar `/compact` al completar cada fase del orquestador o cada 15-20 turnos. Incluir foco: `/compact Foco en {fase} módulo {X}`.
- Código siempre en archivos; explicaciones ≤10 líneas; detalle en `PROGRESS-{MODULO}.md`.
- Subagentes usan `context: fork` — no contaminan el contexto principal.
- Archivar decisiones a `docs/plans/historic/` cuando DECISIONS.md supere 400 líneas.

---

## Modo de respuesta (ahorro de tokens)

**Siempre:**
- Sin frases de cortesía ("Claro", "Por supuesto", "Entendido")
- Sin repetir lo que dijo el usuario
- Sin explicar lo que vas a hacer antes de hacerlo — hazlo
- Sin bullets explicativos si el código habla por sí mismo
- Confirmaciones en una línea

**Modo Caverna** (`"caverna ON"`): texto ≤8 palabras, estilo telegrama. Desactivar con `"caverna OFF"`.
Skill: `.claude/skills/brevity-mode/SKILL.md`.

---

**Última actualización:** 2026-04-19 — ValMen Tech
