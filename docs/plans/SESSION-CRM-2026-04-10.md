# SESSION: CRM — 2026-04-10

## Objetivo de esta sesión
Implementar módulo CRM completo (MVP v1.0): 7 features verticales backend + frontend.

## Decisiones tomadas en esta sesión
- DEC-057 a DEC-062 registradas en DECISIONS.md
- Todos los modelos en un solo models.py (patrón del proyecto)
- Permisos sobre roles existentes (company_admin, seller, viewer)
- Cotización → Saiopen solo al aceptar

## Archivos creados/modificados

### Backend
- [ ] backend/apps/crm/__init__.py
- [ ] backend/apps/crm/apps.py
- [ ] backend/apps/crm/models.py
- [ ] backend/apps/crm/serializers.py
- [ ] backend/apps/crm/cotizacion_serializers.py
- [ ] backend/apps/crm/services.py
- [ ] backend/apps/crm/cotizacion_services.py
- [ ] backend/apps/crm/producto_services.py
- [ ] backend/apps/crm/scoring_services.py
- [ ] backend/apps/crm/views.py
- [ ] backend/apps/crm/cotizacion_views.py
- [ ] backend/apps/crm/urls.py
- [ ] backend/apps/crm/admin.py
- [ ] backend/apps/crm/permissions.py
- [ ] backend/apps/crm/signals.py
- [ ] backend/apps/crm/filters.py
- [ ] backend/apps/crm/tests/test_services.py
- [ ] backend/apps/crm/tests/test_cotizacion_services.py
- [ ] backend/apps/crm/tests/test_scoring_services.py
- [ ] backend/apps/crm/tests/test_views.py
- [ ] config/settings/base.py (agregar 'apps.crm')
- [ ] config/urls.py (agregar ruta crm)

### Frontend
- [ ] frontend/src/app/features/crm/crm.routes.ts
- [ ] frontend/src/app/features/crm/models/*.ts
- [ ] frontend/src/app/features/crm/services/*.ts
- [ ] frontend/src/app/features/crm/pages/**/*.ts

## Problemas encontrados
(se llenan durante la sesión)

## Para la próxima sesión
(se llenan al cerrar)
