# ESTÁNDAR DE DOCUMENTACIÓN — Saicloud
**Versión:** 1.0 | **Fecha:** 2026-04-01 | **DEC-041**

> Este documento define la estructura, ubicación y ciclo de vida de toda la documentación del proyecto Saicloud.
> Todo agente (Claude Code, Cowork) debe respetar estas reglas al crear o mover archivos `.md`.

---

## 1. Archivos permitidos en la raíz del proyecto

Solo estos 5 archivos `.md` viven en la raíz. **Ningún otro.**

| Archivo | Propósito | ¿Modificable por agentes? |
|---------|-----------|--------------------------|
| `CLAUDE.md` | Reglas absolutas del proyecto | ❌ Solo Juan David |
| `CONTEXT.md` | Estado de sesión actual | ✅ Al cerrar sesión |
| `DECISIONS.md` | Decisiones arquitectónicas | ✅ Al tomar decisiones |
| `ERRORS.md` | Errores resueltos | ✅ Al resolver errores |
| `README.md` | Descripción pública del proyecto | ✅ Ocasionalmente |

**Regla:** Si un agente genera un informe, auditoría, changelog, o cualquier otro `.md` en la raíz, debe moverlo inmediatamente a `docs/reports/`.

---

## 2. Estructura de `docs/`

```
docs/
├── base-reference/          ← Docs base del proyecto (referencia permanente)
│   ├── CHECKLIST-VALIDACION.md
│   ├── ESTANDAR-DOCS.md     ← Este archivo
│   ├── README.md
│   └── *.docx               ← Documentos Word de referencia técnica
│
├── standards/               ← Estándares de código y UI/UX
│   └── UI-UX-STANDARDS.md
│
├── plans/                   ← PLANES ACTIVOS (en cola o en ejecución)
│   ├── INDICE-PLANES.md     ← Índice obligatorio — siempre actualizar
│   ├── PLAN-[MODULO].md     ← Un plan por feature/módulo nuevo
│   ├── PROMPT-CLAUDECODE-[MODULO].md  ← Prompt para Claude Code
│   └── historic/            ← PLANES COMPLETADOS
│       └── PLAN-*.md        ← Mover aquí al completar
│
├── technical/               ← Documentación técnica por módulo
│   ├── chat/                ← Docs técnicas del Sistema de Chat
│   ├── proyectos/           ← Docs técnicas del módulo Proyectos
│   ├── agent-go/            ← Docs técnicas del Agente Go
│   └── [modulo]/            ← Una subcarpeta por módulo nuevo
│
├── manuales/                ← Manuales de usuario final
│   ├── MANUAL-CHAT-SAICLOUD.md
│   ├── MANUAL-PROYECTOS-SAICLOUD.md
│   └── [MANUAL-MODULO-X].md
│
├── reports/                 ← Informes de ejecución, auditorías, changelogs
│   ├── INFORME_FASE_*.md    ← Informes de fases completadas
│   ├── INFORME_AUDITORIA_*.md
│   ├── REFACTOR-CHANGELOG.md
│   └── CIERRE_*.md          ← Cierres de módulos
│
├── testing/                 ← Reportes QA, certificaciones, checklists
│   ├── *-CERTIFICATION.md
│   ├── *-QA-REPORT.md
│   └── *-CHECKLIST.md
│
├── demos/                   ← Datos y proyectos de demostración
│   ├── PROYECTO-DEMO-A-*.md
│   └── PROYECTO-DEMO-B-*.md
│
└── saiopen/                 ← Estructuras de tablas Firebird (DLLs y SQL)
    ├── gl.txt, acct.txt, cust.txt ...
    └── sql_gl.txt
```

---

## 3. Ciclo de vida de un plan

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  CREACIÓN           EJECUCIÓN          COMPLETADO              │
│                                                                 │
│  docs/plans/    →   docs/plans/    →   docs/plans/historic/    │
│  PLAN-XXX.md        (sin cambios)      PLAN-XXX.md             │
│  PROMPT-XXX.md                         PROMPT-XXX.md           │
│                                                                 │
│                          ↓                                      │
│                    docs/reports/                               │
│                    INFORME_XXX_FECHA.md                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Paso a paso al completar un plan:**

1. Mover `docs/plans/PLAN-[NOMBRE].md` → `docs/plans/historic/`
2. Mover `docs/plans/PROMPT-CLAUDECODE-[NOMBRE].md` → `docs/plans/historic/`
3. Actualizar `docs/plans/INDICE-PLANES.md`:
   - Mover la entrada de **ACTIVOS** a **COMPLETADOS**
   - Agregar fecha de completado
4. Generar `docs/reports/INFORME_[NOMBRE]_[YYYY-MM-DD].md` con:
   - Resumen de lo implementado
   - Tests ejecutados y cobertura
   - Decisiones tomadas durante ejecución
   - Issues encontrados y resueltos
5. Actualizar `CONTEXT.md` con el nuevo estado
6. Actualizar `DECISIONS.md` si se tomaron decisiones durante la ejecución

---

## 4. Nomenclatura de archivos

| Tipo | Prefijo/Formato | Ejemplo |
|------|----------------|---------|
| Plan activo | `PLAN-[MODULO-FEATURE].md` | `PLAN-SAIDASHBOARD.md` |
| Prompt Claude Code | `PROMPT-CLAUDECODE-[MODULO].md` | `PROMPT-CLAUDECODE-SAIDASHBOARD.md` |
| Informe de ejecución | `INFORME_[MODULO]_[YYYY-MM-DD].md` | `INFORME_SAIDASHBOARD_2026-04-15.md` |
| Manual de usuario | `MANUAL-[MODULO]-SAICLOUD.md` | `MANUAL-DASHBOARD-SAICLOUD.md` |
| Doc técnica | `[MODULO]-[TIPO].md` | `SAIDASHBOARD-API-DOCS.md` |
| Auditoría | `AUDITORIA-[MODULO]-[YYYY-MM-DD].md` | `AUDITORIA-PROYECTOS-2026-03-28.md` |
| Cierre de módulo | `CIERRE-[MODULO]-[YYYY-MM-DD].md` | `CIERRE-CHAT-2026-03-30.md` |

---

## 5. Reglas para agentes (Claude Code / Cowork)

### ✅ SIEMPRE
- Antes de crear un archivo `.md`, verificar en qué carpeta corresponde según esta guía
- Al generar un informe de ejecución, guardarlo directamente en `docs/reports/`
- Al completar una feature, actualizar `docs/plans/INDICE-PLANES.md`
- Documentación técnica de un módulo nuevo → crear subcarpeta en `docs/technical/[modulo]/`

### ❌ NUNCA
- Crear `.md` de informes, auditorías o changelogs en la raíz del proyecto
- Dejar planes completados en `docs/plans/` sin mover a `historic/`
- Crear carpetas nuevas en `docs/` sin seguir la estructura de este estándar
- Mezclar tipos de documentos (ej: manuales de usuario en `technical/`)

---

## 6. Referencia rápida por tipo de archivo

| ¿Qué genero? | ¿Dónde va? |
|-------------|-----------|
| Plan de una nueva feature | `docs/plans/PLAN-XXX.md` |
| Prompt para Claude Code | `docs/plans/PROMPT-CLAUDECODE-XXX.md` |
| Plan ya ejecutado | `docs/plans/historic/` |
| Informe de fases/ejecución | `docs/reports/` |
| Auditoría o changelog | `docs/reports/` |
| Cierre de módulo | `docs/reports/` |
| API docs de un módulo | `docs/technical/[modulo]/` |
| Arquitectura técnica | `docs/technical/[modulo]/` |
| Manual de usuario | `docs/manuales/` |
| Reporte QA / certificación | `docs/testing/` |
| Datos de demostración | `docs/demos/` |
| Estándar o checklist permanente | `docs/base-reference/` |
| Estructura de tablas Saiopen | `docs/saiopen/` |

---

*Mantenido por ValMen Tech — Proyecto Saicloud*
*Cualquier cambio a esta estructura debe registrarse en `DECISIONS.md` como DEC-XXX*
