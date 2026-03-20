## DEC-012: Terceros y Consecutivos como Módulos Transversales

**Fecha:** 19 Marzo 2026
**Estado:** ✅ Aprobada e implementada (Terceros) / ⏳ Pendiente (Consecutivos)
**Contexto:** Módulo de Proyectos

### Problema
Durante la implementación del Grupo 3 (Terceros), se detectó que el diseño inicial ubicaba Terceros dentro de la app `proyectos`, lo que implicaba:
- Terceros exclusivos de Proyectos
- No reutilizables en otros módulos (SaiReviews, SaiCash, SaiRoute, etc.)
- Duplicación de datos si otros módulos necesitaban terceros
- API fragmentada

El mismo problema aplica para Consecutivos.

### Opciones Evaluadas

**Opción A: Mantener en app específica (proyectos)**
- ❌ No reutilizable
- ❌ Duplicación de código/datos
- ❌ Inconsistencia entre módulos
- ✅ Más simple inicialmente

**Opción B: Módulos transversales en app `core`** ⭐ SELECCIONADA
- ✅ Reutilizable en todos los módulos
- ✅ Un solo registro de tercero compartido
- ✅ API centralizada `/api/v1/terceros/`
- ✅ Relaciones específicas por módulo
- ❌ Requiere refactorización

### Decisión

**Terceros y Consecutivos se implementan como módulos TRANSVERSALES en app `core`.**

**Arquitectura:**
```
apps/core/  (TRANSVERSAL)
├── models.py
│   ├── Tercero              ← Encabezado
│   ├── TerceroDireccion     ← Líneas (direcciones)
│   └── ConfiguracionConsecutivo  ← Pendiente implementar
├── serializers.py
├── views.py
└── urls.py  → /api/v1/terceros/, /api/v1/consecutivos/

apps/proyectos/  (ESPECÍFICO)
├── models.py
│   └── TerceroProyecto      ← Relación Tercero + Proyecto
└── ...

apps/reviews/  (FUTURO)
└── models.py
    └── TerceroReview        ← Relación Tercero + Review

apps/cash/  (FUTURO)
└── models.py
    └── TerceroCash          ← Relación Tercero + CxC/CxP
```

### Implementación

**Terceros:**
- ✅ Modelo `Tercero` en `apps/core/models.py`
- ✅ Modelo `TerceroDireccion` en `apps/core/models.py`
- ✅ Serializers, Views, URLs en app `core`
- ✅ Service transversal `TerceroService` en frontend
- ✅ Componente reutilizable `tercero-selector` (autocomplete)
- ✅ `TerceroProyecto` en app `proyectos` con FK a `core.Tercero`

**Consecutivos:**
- ⏳ Pendiente implementar como transversal
- ⏳ Modelo `ConfiguracionConsecutivo` en app `core`
- ⏳ Service `generar_consecutivo()` centralizado

### Consecuencias

**Positivas:**
- ✅ Un tercero puede usarse en Proyectos, SaiReviews, SaiCash simultáneamente
- ✅ Consistencia de datos (un cliente es el mismo en todos los módulos)
- ✅ API única `/api/v1/terceros/` para todos
- ✅ Componentes frontend reutilizables
- ✅ Sincronización Saiopen centralizada

**Negativas:**
- ⚠️ Requirió refactorización de código ya generado
- ⚠️ Mayor complejidad inicial

### Criterios de Revisión
- ✅ Terceros funciona en Proyectos
- ⏳ Terceros funciona en al menos un segundo módulo (SaiReviews)
- ⏳ Consecutivos implementado como transversal

### Referencias
- Grupo 3: https://www.notion.so/329ee9c3690a811eab5ecd3fd8105c22
- Cierre Sesión: https://www.notion.so/329ee9c3690a814398b3de9a87fcf5db