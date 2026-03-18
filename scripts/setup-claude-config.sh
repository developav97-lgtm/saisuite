#!/bin/bash

# Script de configuración de Claude Code
# Ubicación: scripts/setup-claude-config.sh
# Uso: ./scripts/setup-claude-config.sh

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  🤖 CONFIGURACIÓN CLAUDE CODE${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Crear directorio .claude si no existe
echo "📁 Creando directorio .claude..."
mkdir -p .claude
echo -e "${GREEN}✓${NC} .claude/ creado"
echo ""

# Crear config.json
echo "⚙️  Generando .claude/config.json..."
cat > .claude/config.json << 'EOF'
{
  "name": "Saicloud",
  "description": "ERP SaaS multi-tenant - Django + Angular + PostgreSQL + n8n",
  "context_files": [
    "CLAUDE.md",
    "DECISIONS.md",
    "ERRORS.md",
    "CONTEXT.md"
  ],
  "startup_command": "bash scripts/session-banner.sh 2>/dev/null || echo 'Sesión Claude Code iniciada'",
  "mcp_servers": {
    "notion": {
      "enabled": true,
      "description": "Sincronización con documentación Notion"
    }
  }
}
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} .claude/config.json creado exitosamente"
else
    echo -e "${YELLOW}⚠${NC}  Error al crear .claude/config.json"
    exit 1
fi
echo ""

# Crear session-banner.sh
echo "📋 Generando banner de sesión..."
mkdir -p scripts

cat > scripts/session-banner.sh << 'EOF'
#!/bin/bash

# Banner de sesión Claude Code
# Muestra contexto actual del proyecto al iniciar

# Colores
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  🚀 SAICLOUD - SESIÓN CLAUDE CODE${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Estado actual del proyecto
if [ -f "CONTEXT.md" ]; then
    echo -e "${GREEN}📊 ESTADO ACTUAL:${NC}"
    echo "────────────────────────────────────────"
    # Mostrar sección de estado actual
    sed -n '/## Estado actual/,/##/p' CONTEXT.md | head -n -1 | tail -n +2
    echo ""
fi

# Última decisión arquitectónica
if [ -f "DECISIONS.md" ]; then
    echo -e "${GREEN}🎯 ÚLTIMA DECISIÓN ARQUITECTÓNICA:${NC}"
    echo "────────────────────────────────────────"
    # Buscar último DEC-
    LAST_DEC=$(grep -n "^## DEC-" DECISIONS.md | tail -n 1 | cut -d: -f1)
    if [ ! -z "$LAST_DEC" ]; then
        tail -n +$LAST_DEC DECISIONS.md | head -n 10
    else
        echo "Sin decisiones registradas aún"
    fi
    echo ""
fi

# Último error resuelto
if [ -f "ERRORS.md" ]; then
    echo -e "${GREEN}⚠️  ÚLTIMO ERROR RESUELTO:${NC}"
    echo "────────────────────────────────────────"
    # Buscar último ERROR-
    LAST_ERR=$(grep -n "^## ERROR-" ERRORS.md | tail -n 1 | cut -d: -f1)
    if [ ! -z "$LAST_ERR" ]; then
        tail -n +$LAST_ERR ERRORS.md | head -n 6
    else
        echo "Sin errores registrados aún"
    fi
    echo ""
fi

# Features en desarrollo
if [ -d "docs/plans" ]; then
    PLAN_COUNT=$(ls docs/plans/PLAN-*.md 2>/dev/null | wc -l)
    if [ $PLAN_COUNT -gt 0 ]; then
        echo -e "${GREEN}📝 FEATURES PLANIFICADOS: $PLAN_COUNT${NC}"
        echo "────────────────────────────────────────"
        ls docs/plans/PLAN-*.md 2>/dev/null | xargs -n 1 basename | sed 's/PLAN-//g' | sed 's/.md//g' | head -n 5
        echo ""
    fi
fi

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
EOF

chmod +x scripts/session-banner.sh

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} scripts/session-banner.sh creado y ejecutable"
else
    echo -e "${YELLOW}⚠${NC}  Error al crear session-banner.sh"
    exit 1
fi
echo ""

# Verificar archivos de contexto
echo "📋 Verificando archivos de contexto..."
MISSING=0

for file in "CLAUDE.md" "DECISIONS.md" "ERRORS.md" "CONTEXT.md"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file encontrado"
    else
        echo -e "${YELLOW}⚠${NC}  $file no encontrado - creando plantilla..."
        
        case "$file" in
            "CLAUDE.md")
                cat > CLAUDE.md << 'CLAUDEMD'
# CLAUDE.md - Instrucciones del Proyecto Saicloud

## Stack Tecnológico
- Backend: Django + DRF + PostgreSQL
- Frontend: Angular 18 (standalone components)
- UI Framework: PrimeNG
- Automatización: n8n
- Auth: JWT

## Convenciones
- Modelos heredan de BaseModel
- Lógica de negocio en services.py
- PKs UUID para modelos de API
- Lazy loading en Angular
- Change detection OnPush

## Estructura
- backend/apps/{dominio}/
- frontend/src/app/features/{feature}/
- docs/ (technical, user, knowledge-base)
- n8n/workflows/

## Metodología
Seguir las 10 fases secuenciales (ver metodología diagram).
No saltarse fases. Documentar decisiones en DECISIONS.md.
CLAUDEMD
                echo -e "${GREEN}✓${NC} CLAUDE.md creado con plantilla"
                ;;
            "DECISIONS.md")
                cat > DECISIONS.md << 'DECMD'
# Decisiones Arquitectónicas

## DEC-001: Stack Tecnológico Base
**Fecha:** $(date +%Y-%m-%d)
**Decisión:** Django + Angular + PostgreSQL + n8n
**Razón:** Stack probado, ecosistema maduro, flexible para SaaS multi-tenant

## DEC-002: PrimeNG como UI Framework
**Fecha:** $(date +%Y-%m-%d)
**Decisión:** PrimeNG es el framework UI definitivo
**Razón:** Componentes enterprise, tema personalizable, soporte activo
DECMD
                echo -e "${GREEN}✓${NC} DECISIONS.md creado con plantilla"
                ;;
            "ERRORS.md")
                cat > ERRORS.md << 'ERRMD'
# Registro de Errores Resueltos

Este archivo documenta errores encontrados y sus soluciones para evitar recurrencia.

## ERROR-001: Ejemplo de formato
**Fecha:** $(date +%Y-%m-%d)
**Error:** Descripción del error
**Causa:** Razón del error
**Solución:** Cómo se resolvió
**Prevención:** Cómo evitarlo en el futuro
ERRMD
                echo -e "${GREEN}✓${NC} ERRORS.md creado con plantilla"
                ;;
            "CONTEXT.md")
                cat > CONTEXT.md << 'CTXMD'
# Contexto Actual del Proyecto

## Estado actual
- Infraestructura: En configuración
- Fase: Pre-construcción (Phase 0)
- Último deploy: N/A

## Archivos modificados hoy
- Ninguno aún

## Próximo paso
- Completar configuración inicial
- Ejecutar verify-setup.sh
- Planificar primer feature
CTXMD
                echo -e "${GREEN}✓${NC} CONTEXT.md creado con plantilla"
                ;;
        esac
        MISSING=$((MISSING+1))
    fi
done

if [ $MISSING -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}ℹ${NC}  Se crearon $MISSING archivo(s) de contexto con plantillas"
    echo "   Personalízalos según tu proyecto"
fi
echo ""

# Verificar que sea JSON válido
echo "✅ Validando configuración..."
if command -v python3 &> /dev/null; then
    if python3 -m json.tool .claude/config.json > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} .claude/config.json es JSON válido"
    else
        echo -e "${YELLOW}⚠${NC}  Error de sintaxis en .claude/config.json"
        exit 1
    fi
elif command -v jq &> /dev/null; then
    if jq empty .claude/config.json > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} .claude/config.json es JSON válido"
    else
        echo -e "${YELLOW}⚠${NC}  Error de sintaxis en .claude/config.json"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠${NC}  No se puede validar JSON (python3 o jq no disponibles)"
fi
echo ""

# Resumen
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ CONFIGURACIÓN COMPLETADA${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Archivos creados:"
echo "  • .claude/config.json"
echo "  • scripts/session-banner.sh"
if [ $MISSING -gt 0 ]; then
    echo "  • $MISSING archivo(s) de contexto (plantillas)"
fi
echo ""
echo "Próximos pasos:"
echo "  1. Revisa y personaliza los archivos de contexto si es necesario"
echo "  2. Ejecuta: ${BLUE}./scripts/verify-setup.sh${NC}"
echo "  3. Inicia Claude Code: ${BLUE}claude code${NC}"
echo ""
