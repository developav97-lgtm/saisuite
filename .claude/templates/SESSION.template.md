---
module: <NOMBRE_MODULO>
session_date: YYYY-MM-DD
session_number: <N>
phase: <fase en la que se trabajó>
duration_minutes: <estimado>
outcome: in_progress   # in_progress | completed | blocked | paused
---

# SESSION — <Módulo> — <Fecha>

## Objetivo de esta sesión

<1 línea: qué se va a lograr hoy>

## Estado al inicio

*(copiar del frontmatter de `PROGRESS-<MODULO>.md`)*
- Fase actual: <N>
- Último commit: <hash o descripción>
- Siguiente acción: <línea next_action del PROGRESS>

## Decisiones tomadas en esta sesión

- **<DEC-XXX>:** <decisión> — <razón>

## Archivos creados/modificados

- [x] `<path>` — <qué se hizo>
- [ ] `<path>` — <pendiente>

## Tests ejecutados

| Comando | Resultado | Notas |
|---------|-----------|-------|
| `pytest backend/apps/<app>` | ✅ / ❌ | |
| `ng test <app>` | ✅ / ❌ | |

## Problemas encontrados y solucionados

- **Problema:** <descripción>
- **Causa raíz:** <análisis>
- **Solución:** <cambio aplicado>
- **Registrado en ERRORS.md:** sí/no

## Pendientes para la próxima sesión

1. <pendiente 1>
2. <pendiente 2>

## Estado al final

- Fase: <N>
- Próxima acción: <actualizar también en PROGRESS.md frontmatter>
- Bloqueos: <lista o "ninguno">
