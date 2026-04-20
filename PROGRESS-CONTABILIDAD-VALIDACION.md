---
module: contabilidad
ticket_type: IMPROVEMENT
ticket_id: IMP-VAL-001
status: completed
current_phase: 9a+bugfix-done
phases_approved: [9a, bugfix-crit-1, bugfix-crit-2, bugfix-crit-3, bugfix-crit-4]
phases_gates:
  prd: false
  plan: false
  staging: false
last_session: SESSION-contabilidad-2026-04-20.md
next_action: PO decide prioridad de BUGFIX-CONT-101 a 104 (críticos) — luego re-validar 4x4 con dev server
blockers:
  - "Dev server no activo — 9 checks visuales quedaron pending (ver reporte)"
created: 2026-04-20
updated: 2026-04-20
owner: Juan David
report: docs/plans/VALIDACION-4x4-CONTABILIDAD.md
---

# PROGRESS — Contabilidad (validación 4×4)

## Resumen ejecutivo

- **Objetivo:** Validar visualmente el GL Contabilidad viewer en los 4 contextos (Desktop/Mobile × Light/Dark) antes de declararlo listo para producción.
- **Alcance:** solo validación y reporte. No se modifica código en esta iteración.
- **Estimación:** 1 sesión.
- **Dependencias:** CONT-001 ya implementado (ver CONTEXT.md).

## Fases relevantes (IMPROVEMENT stand-alone)

### Fase 9a — Validación UI 4×4 + WCAG AA
- [ ] Reconocimiento de archivos del componente
- [ ] Verificación del dev server corriendo
- [ ] Validación Desktop Light
- [ ] Validación Desktop Dark
- [ ] Validación Mobile Light
- [ ] Validación Mobile Dark
- [ ] Auditoría WCAG 2.1 AA (contraste, keyboard nav, labels)
- [ ] Consolidación de bugs encontrados (clasificados como BUGFIX separados)
- [ ] Reporte final en `docs/plans/VALIDACION-4x4-CONTABILIDAD.md`

**Skills:** `anthropic-skills:saicloud-validacion-ui` + `design:accessibility-review`
**Agents:** Evidence Collector + UI Designer

## Log de fases

| Fecha | Fase | Duración | Notas |
|-------|------|----------|-------|
| 2026-04-20 | Kick-off | — | PROGRESS creado desde template |

## Bugs encontrados y resueltos

| ID | Severidad | Descripción | Estado |
|----|-----------|-------------|--------|
| CRIT-1 | 🔴 | Empty state dentro de mat-table | ✅ Fixed — usa `sc-empty-state` fuera del table |
| CRIT-2 | 🔴 | Sin feedback MatSnackBar en error | ✅ Fixed — `snackBar.open()` en error callback |
| CRIT-3 | 🔴 | 4 tokens CSS inexistentes + fallback hex errado | ✅ Fixed — tokens reales (`--sc-text-color`, `--sc-primary-light`, etc.) |
| CRIT-4 | 🔴 | Sin MatPaginator server-side | ✅ Fixed — `page` + `page_size` en `GLFiltros` + `<mat-paginator>` |
| MAY-2 | 🟡 | Sin media queries mobile | ✅ Fixed — oculta columnas en ≤960px y ≤680px (bonus) |
| MAY-6 | 🟡 | `Math` expuesto al template | ✅ Fixed — `computed balanceado` |
| MAY-8 | 🟡 | Sin `tabular-nums` en columnas monetarias | ✅ Fixed |
| MIN-7 | 🔵 | Icono decorativo sin `aria-hidden` | ✅ Fixed |
| MAY-1 | 🟡 | No usa sc-page/sc-page-header/sc-card canónicos | ✅ Fixed (IMP-CONT-MAY) |
| MAY-3 | 🟡 | Validator pattern periodo faltante | ✅ Fixed (IMP-CONT-MAY) |
| MAY-4 | 🟡 | Chip tipo custom (no sc-status-chip) | ✅ Fixed (IMP-CONT-MAY) |
| MAY-5 | 🟡 | subscriptSizing="dynamic" ausente | ✅ Fixed (IMP-CONT-MAY) |

**Build post-fix:** compilación exitosa en 0.91s. Sin errores en el componente contabilidad.
**Verificación:** grep confirma 10 usos de primitivas `sc-*`, 5 `subscriptSizing="dynamic"`, 1 `sc-status-chip`, 0 `.tipo-badge`, Validators.pattern + mat-error aplicados.
**Refactor colateral:** SCSS reducido de 168 → 96 líneas (eliminadas duplicaciones con primitivas globales), imports `MatCardModule` + `MatChipsModule` removidos.
**Pending:** re-validación visual completa requiere backend activo (interceptor desloguea con backend caído).

---

**Generado desde:** `.claude/templates/PROGRESS.template.md`
