# CLAUDE.md — SaiSuite
# ValMen Tech × Saiopen | Django 5 + Angular 18 + PostgreSQL 16 + n8n + AWS

SaiSuite es una plataforma SaaS multi-tenant para el ecosistema Saiopen (ERP Windows/Firebird).
Reglas detalladas por área están en `.claude/rules/` (se cargan automáticamente por path).

---

## Reglas críticas (aplican SIEMPRE)

**Backend:** Lógica en `services.py` (nunca views/modelos). BaseModel (UUID pk, company FK). Nunca `print()`, usar logger. Nunca secrets hardcodeados.
**Frontend:** `strict: true`, OnPush, `async pipe`, Angular Material (NUNCA PrimeNG/Bootstrap/Tailwind), `@if`/`@for` (NUNCA `*ngIf`/`*ngFor`), variables CSS `var(--sc-*)`.
**BD:** company_id en TODO, UUID v4, dinero `NUMERIC(15,2)`, Firebird `sai_key` + `unique_together`.
**Tests:** Junto con código. Backend services ≥80%. Frontend services =100%, components ≥70%.
**Commits:** `<tipo>(<scope>): <desc>`. Nunca `.env` en git.
**Idioma:** SIEMPRE responder en español. Planes, documentos y respuestas en español. El código fuente puede estar en inglés.

Reglas completas: `.claude/rules/backend/django.md`, `.claude/rules/frontend/angular.md`

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
├── .claude/rules/       # Reglas path-scoped (backend/, frontend/, general/)
├── CLAUDE.md            # Este archivo
├── CONTEXT.md           # Estado actual
├── DECISIONS.md         # Decisiones DEC-XXX
├── ERRORS.md            # Errores resueltos
└── PROGRESS-*.md        # Tracking por módulo
```

---

## Orden de generación (features)

```
1. models.py → 2. makemigrations → 3. serializers.py → 4. services.py
5. views.py + urls.py → 6. tests/ → 7. model.ts → 8. service.ts
9. components (OnPush, Material) → 10. routes (lazy) → 11. Validación 4x4
```

---

## Orquestador (punto de entrada ÚNICO para todo el desarrollo)

**Skill:** `.claude/skills/saicloud-orquestador/SKILL.md` — Leer SIEMPRE al recibir trabajo.

**Tipos de ticket:**
| Tipo | Trigger | Fases | Autonomía |
|------|---------|-------|-----------|
| MODULE | "nuevo módulo X" | 0→10 completas | Autónomo post-aprobación PRD+PLAN |
| FEATURE | "nueva feature", "agregar X" | 0→1→4→5→7→9 | Autónomo post-aprobación PLAN |
| BUGFIX | "fix", "error", "no funciona" | Diagnóstico→Fix→Test→Review | 100% autónomo |
| IMPROVEMENT | "mejorar", "optimizar" | 1→4→5→7 | Autónomo (gate solo si es arquitectural) |

**Roles:** PO (Juan David) → Scrum Master (Opus) → Developer (Sonnet) → QA (subagente Sonnet)
**Modelo:** Configurar con `claude --model opusplan` (Opus planifica, Sonnet ejecuta)
**Progreso:** `PROGRESS-{MODULO}.md` con sistema de tickets (ID, tipo, estado, fase)
**Notificación:** Gmail draft a develop.av97@gmail.com al completar cada ticket
**Licencias:** Fase 10 registra en `CompanyModule.Module` + `ModuleGuard` + menú
**Notion:** Genera `NOTION-SYNC-{MODULO}-{FECHA}.md` → Cowork sincroniza
**RAG:** Fase 9 genera `docs/technical/{modulo}/RAG-CHUNKS.md`

---

## Gestión de contexto

**Regla de /compact:** Ejecutar `/compact` al completar cada fase del orquestador, o cada 15-20 turnos. Incluir foco: `/compact Foco en {fase actual} del módulo {X}`.
**Respuestas:** Código completo en archivos. Explicaciones breves en chat. Detalle en PROGRESS.
**Subagentes:** Usar `context: fork` para investigación/exploración que no contamina contexto principal.
**DECISIONS.md:** Archivar decisiones pre-DEC-040 a `docs/plans/historic/DECISIONS-ARCHIVE.md` cuando supere 400 líneas.

---

## Errores frecuentes

Lógica en views, olvidar `select_related`, `sai_key` sin `unique_together`, `any` en TS, suscripción sin unsubscribe, no validar mobile, hardcodear colores.
Lista completa: `ERRORS.md`

---

**Última actualización:** 10 Abril 2026 — ValMen Tech
