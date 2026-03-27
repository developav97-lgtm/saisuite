# PRODUCTION READINESS CHECKLIST
**Fecha:** 27 Marzo 2026
**Evaluador:** Reality Checker
**Scope:** Refactor Backend (Español→Inglés) + Refactor Frontend FASE 2

---

## ✅ CRITERIOS QUE PASAN

### Backend
- [x] **375 tests pasando** — `Ran 375 tests in 71.915s OK`
- [x] **0 errores críticos** en backend
- [x] **Migraciones aplicadas** — 0013 con 13 RenameModel + data migrations
- [x] **Endpoints en inglés funcionando** — `/api/v1/projects/`, `/api/v1/projects/tasks/`
- [x] **Multi-tenant activo** — company_id en todas las queries
- [x] **JWT funcionando** — login, refresh, me endpoint OK
- [x] **Logging estructurado** — sin `print()`, solo `logger.info()`

### Frontend
- [x] **Compilación limpia** — 0 errores TS, solo warnings pre-existentes
- [x] **Angular strict mode** — `strict: true` activo
- [x] **ChangeDetectionStrategy.OnPush** — en todos los componentes nuevos
- [x] **Signals** — usados para estado local en todos los nuevos componentes
- [x] **Lazy loading** — todas las rutas son `loadComponent` / `loadChildren`
- [x] **Auth guard** — redirige a login sin token
- [x] **Dark mode** — funciona en Module Selector, Lista, Cards
- [x] **localStorage persistencia** — `saisuite.tareasView` persiste toggle

### UX / Flujos
- [x] **Login → Module Selector** funciona
- [x] **Sidebar contextual** — muestra nav correcta por módulo
- [x] **Toggle Kanban/Lista** — persiste en localStorage
- [x] **Vista Cards** — muestra métricas (progreso, estado, gerente, cliente, presupuesto)
- [x] **Filtros Cards idénticos a Lista** — 3 campos en una sola línea
- [x] **Detalle Proyecto** con todas las tabs
- [x] **Detalle Tarea** accesible
- [x] **Gantt** renderiza
- [x] **Timesheets** accesibles

---

## ⚠️ OBSERVACIONES (no bloquean producción)

| # | Observación | Impacto | Acción |
|---|---|---|---|
| 1 | Warning `NG8011`: mat-icon en @else con múltiples nodos | Bajo | Fix cosmético en próxima sesión |
| 2 | Warning `NG8113`: `DocumentoDetailDialogComponent` importado sin usar | Bajo | Cleanup en próxima sesión |
| 3 | Cronómetro en tarea requiere configuración de módulo activa | Bajo | Comportamiento esperado |
| 4 | `frappe-gantt` CSS en angular.json — instalado en node_modules local pero requiere verificación en deploy | Medio | Verificar en CI/CD |

---

## 🔴 CRITERIOS PENDIENTES (fuera del scope actual)

| Criterio | Estado | Motivo |
|---|---|---|
| Cobertura de tests backend >= 85% | ⏸️ No medido | Requiere `pytest --cov` (lento, no incluido en smoke) |
| Tests unitarios Angular (`ng test`) | ⏸️ No ejecutados | Karma no configurado en Docker |
| Performance < 3s load | ⏸️ No medido | Requiere Lighthouse |
| SaiVentas y SaiCobros funcionales | ⏸️ Pendiente | Módulos no desarrollados aún |

---

## 📋 PLAN DE ROLLBACK

### Si el backend falla en producción:
```bash
# Revertir al commit anterior al merge
git revert b228697 --no-commit
git commit -m "revert: rollback to pre-english-rename"
docker-compose restart api
```

### Si las migraciones causan problemas:
```bash
# En el servidor de producción
docker exec saisuite-api python manage.py migrate proyectos 0012
# O restaurar desde backup de PostgreSQL
```

### Si el frontend falla:
```bash
# El refactor no toca el build de producción — solo code changes
# Revertir con:
git checkout main~1 -- frontend/src/
```

### Backups
- PostgreSQL: dump diario en `/backups/` (configurado en docker-compose)
- Git: todas las ramas preservadas (`refactor/english-rename` disponible)

---

## VEREDICTO

**Estado:** ✅ LISTO PARA CONTINUAR DESARROLLO

**Condición:** Los 4 criterios pendientes deben completarse antes de un deploy a producción real. Para ambiente de desarrollo y staging, el estado actual es satisfactorio.
