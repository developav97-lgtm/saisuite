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
