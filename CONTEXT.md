# CONTEXT.md - Estado Actual Proyecto Saicloud

**Última actualización:** 19-20 Marzo 2026

## Estado Módulo de Proyectos: 85%

### ✅ Completado (85%)
- Planificación completa (Fases 1-3)
- Infraestructura base (Auth, Shell, Multi-tenant)
- Fase A: Proyecto + Fase
- Fase B: TerceroProyecto, DocumentoContable, Hito
- Actividades (catálogo + asignación)
- **Grupo 5: Licencias & Seguridad** (8 puntos) ✅
- **Grupo 4: Fases & Ejecución** (5 puntos) ✅

### 🔄 En Proceso (10%)
- **Grupo 3: Terceros** (5 puntos) - Correcciones en vistas Angular
  - Arquitectura transversal confirmada (app core)
  - Modelos implementados
  - API funcionando
  - Pendiente: ajustes UX, sincronización Saiopen

### ⏳ Pendiente (5%)
- **Grupo 6: Usuarios & Permisos** (3 puntos) - CRÍTICO
- Grupo 1: Consecutivos (6 puntos)
- Grupo 2: Actividades ajustes (9 puntos)
- Grupo 7: UI/UX General (5 puntos)
- Grupo 8: Features Nuevas (2 puntos)
- Grupo 9: Metodología (2 puntos)

## Arquitectura Clave

### Apps Transversales (app `core`)
- ✅ Company, CompanySettings
- ✅ CompanyLicense, LicensePayment (Grupo 5)
- ✅ **Tercero, TerceroDireccion** (Grupo 3 - NUEVO)
- ⏳ ConfiguracionConsecutivo (pendiente)

### Apps Específicas
- `proyectos`: Proyecto, Fase, Actividad, ActividadProyecto, TerceroProyecto, ConfiguracionModulo
- `users`: User, UserCompany, ActiveSession

## Migraciones Pendientes
1. `apps/companies/0004_*` (licencias)
2. `apps/proyectos/*` (ConfiguracionModulo, Fase update)
3. `apps/core/*` (Tercero, TerceroDireccion)

## Próximos Pasos Inmediatos
1. Ejecutar migraciones pendientes
2. Crear seed data (licencias, config, terceros)
3. Finalizar correcciones Grupo 3
4. Validación manual flujos principales
5. Iniciar Grupo 6 (Permisos)