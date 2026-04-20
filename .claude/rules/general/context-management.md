---
paths:
  - "PROGRESS-*.md"
  - "CONTEXT.md"
  - "SESSION-*.md"
---

# Gestión de Contexto — Reglas para mantener precisión en sesiones largas

## Principio: Código en archivos, brevedad en chat, detalle en PROGRESS

### Formato de respuestas durante implementación

**HACER:**
- Escribir código completo directamente en los archivos del proyecto
- Responder en chat con resumen breve: "✅ models.py creado (Contact, Deal, Pipeline). 3 modelos, 12 campos."
- Poner detalle de decisiones y estado en PROGRESS-{MODULO}.md
- Si el usuario pide explicación, darla. Si no, ser conciso.

**NO HACER:**
- Pegar bloques enormes de código en el chat (escribirlos en archivo)
- Explicar cada línea si no fue solicitado
- Repetir reglas del CLAUDE.md en cada respuesta

### Estrategia de /compact

Ejecutar `/compact` en estos momentos:
1. Al completar cada fase del orquestador
2. Cada 15-20 turnos de conversación
3. Antes de iniciar una fase compleja (Fase 4: Implementación)
4. Cuando el contexto se sienta "pesado" (respuestas vagas o incompletas)

**Siempre con foco:** `/compact Foco en Fase {N} del módulo {X}. Estado: {resumen de 1 línea}`

### Documentos de sesión: SESSION-{MODULO}-{FECHA}.md

Para sesiones de implementación largas (Fase 4), crear un documento de sesión
que funciona como "memoria de trabajo" de la sesión actual:

```markdown
# SESSION: {MODULO} — {FECHA}

## Objetivo de esta sesión
{Qué se va a implementar hoy}

## Decisiones tomadas en esta sesión
- {decisión 1}: {razón}
- {decisión 2}: {razón}

## Archivos creados/modificados
- [x] backend/apps/{modulo}/models.py — {resumen}
- [x] backend/apps/{modulo}/services.py — {resumen}
- [ ] frontend/src/app/features/{modulo}/... — pendiente

## Problemas encontrados
- {problema}: {solución aplicada}

## Para la próxima sesión
- {pendiente 1}
- {pendiente 2}
```

Este archivo:
- Se crea al inicio de cada sesión de trabajo
- Se actualiza al cerrar la sesión
- Permite retomar sin releer toda la conversación anterior
- Se archiva en `docs/plans/historic/` al cerrar el módulo

### Uso de subagentes para investigación

Cuando necesites investigar algo que NO es parte de la implementación actual
(revisar un módulo existente, buscar un patrón, verificar una dependencia),
usar un subagente con `context: fork` para no contaminar el contexto principal.

Ejemplo: "Necesito ver cómo está implementado el ModuleGuard" → subagente lee,
retorna resumen de 5 líneas, el contexto principal no se infla.

### Delegación en el marco agentic

El orquestador delega trabajo a 3 niveles. Decide cuál usar según el caso:

| Mecanismo | Cuándo | Contexto | Ejemplo |
|-----------|--------|----------|---------|
| `Skill(anthropic-skills:X)` | Necesito seguir una metodología/checklist ya definida | Inline — suma instrucciones al contexto actual | `Skill(anthropic-skills:saicloud-planificacion)` para Fase 1 |
| `Agent(subagent_type=X)` | Trabajo que puede hacerse aislado sin contaminar contexto | Forked — retorna solo el resumen final | `Agent(Backend Architect, prompt="diseña modelos para módulo X")` |
| Ejecución inline (main) | Edición puntual, respuesta rápida, coordinación | Todo visible | Edit/Write directo sobre archivos |

**Reglas:**
- **Siempre usar Agent** cuando la tarea es investigación, QA o revisión — el resumen cabe en el contexto principal sin arrastrar el proceso.
- **Siempre usar Skill** cuando el flujo requiere seguir una secuencia documentada (PRD, PLAN, deploy) — el skill inyecta la checklist correcta.
- **Nunca inline** bloques largos de exploración — siempre delegar a Agent para que el contexto principal quede limpio.
- **Prompts de Agent self-contained:** el subagente no ve la conversación — incluir paths, requisitos, objetivo completo.

### Cuándo archivar DECISIONS.md

Si DECISIONS.md supera 400 líneas (~50 decisiones):
1. Mover DEC-001 a DEC-039 a `docs/plans/historic/DECISIONS-ARCHIVE.md`
2. Dejar en DECISIONS.md solo las decisiones activas (DEC-040+)
3. Agregar nota al inicio: "Decisiones anteriores: docs/plans/historic/DECISIONS-ARCHIVE.md"

Esto reduce ~5,000 tokens de contexto permanente.
