#!/bin/bash

# Script de verificación de documentación
# Ubicación: scripts/verify-docs.sh
# Uso: ./scripts/verify-docs.sh {nombre-feature}

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Verificar argumento
if [ -z "$1" ]; then
    echo -e "${RED}❌ Error: Debes especificar el nombre del feature${NC}"
    echo ""
    echo "Uso:"
    echo "  $0 {nombre-feature}"
    echo ""
    echo "Ejemplo:"
    echo "  $0 gestion-clientes"
    echo ""
    exit 1
fi

FEATURE=$1
ERRORS=0
WARNINGS=0

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  📚 VERIFICACIÓN DE DOCUMENTACIÓN${NC}"
echo -e "${BLUE}  Feature: ${FEATURE}${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Función auxiliar
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $2"
        return 0
    else
        echo -e "${RED}✗${NC} $2 ${YELLOW}(faltante)${NC}"
        ERRORS=$((ERRORS+1))
        return 1
    fi
}

warn() {
    echo -e "${YELLOW}⚠${NC}  $1"
    WARNINGS=$((WARNINGS+1))
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. PLAN DEL FEATURE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo -e "${BLUE}📋 1. Planificación${NC}"
echo "────────────────────────────────────────"
PLAN_FILE="docs/plans/PLAN-${FEATURE}.md"
check_file "$PLAN_FILE" "Plan del feature (PLAN-${FEATURE}.md)"

if [ -f "$PLAN_FILE" ]; then
    # Verificar que tenga secciones críticas
    if grep -q "## Endpoints" "$PLAN_FILE"; then
        echo -e "  ${GREEN}→${NC} Sección 'Endpoints' encontrada"
    else
        warn "Falta sección '## Endpoints' en el plan"
    fi
    
    if grep -q "## Modelos" "$PLAN_FILE"; then
        echo -e "  ${GREEN}→${NC} Sección 'Modelos' encontrada"
    else
        warn "Falta sección '## Modelos' en el plan"
    fi
    
    if grep -q "## Checklist" "$PLAN_FILE"; then
        echo -e "  ${GREEN}→${NC} Sección 'Checklist' encontrada"
    else
        warn "Falta sección '## Checklist' en el plan"
    fi
fi
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. DOCUMENTACIÓN TÉCNICA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo -e "${BLUE}🔧 2. Documentación Técnica${NC}"
echo "────────────────────────────────────────"

# OpenAPI Spec
OPENAPI_FILE="docs/technical/api/${FEATURE}.openapi.yaml"
check_file "$OPENAPI_FILE" "OpenAPI Specification"

if [ -f "$OPENAPI_FILE" ]; then
    # Verificar contenido básico
    if grep -q "openapi:" "$OPENAPI_FILE"; then
        echo -e "  ${GREEN}→${NC} Header OpenAPI válido"
    else
        warn "OpenAPI spec parece incompleto"
    fi
    
    if grep -q "paths:" "$OPENAPI_FILE"; then
        PATH_COUNT=$(grep -c "^\s*\/api\/" "$OPENAPI_FILE")
        echo -e "  ${GREEN}→${NC} $PATH_COUNT endpoints documentados"
    else
        warn "No se encontraron paths en OpenAPI spec"
    fi
fi

# Architecture Doc
ARCH_FILE="docs/technical/architecture/${FEATURE}-architecture.md"
check_file "$ARCH_FILE" "Documentación de Arquitectura"

if [ -f "$ARCH_FILE" ]; then
    # Verificar secciones
    if grep -q "## Diagrama" "$ARCH_FILE" || grep -q "## Flujo" "$ARCH_FILE"; then
        echo -e "  ${GREEN}→${NC} Incluye diagramas/flujos"
    else
        warn "No se encontraron diagramas en architecture doc"
    fi
    
    if grep -q "## Modelos" "$ARCH_FILE"; then
        echo -e "  ${GREEN}→${NC} Sección 'Modelos de Datos' presente"
    else
        warn "Falta sección 'Modelos de Datos'"
    fi
fi
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. DOCUMENTACIÓN DE USUARIO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo -e "${BLUE}📖 3. Documentación de Usuario${NC}"
echo "────────────────────────────────────────"

# Guía de Usuario
GUIDE_FILE="docs/user/guides/${FEATURE}-guia.md"
check_file "$GUIDE_FILE" "Guía de Usuario"

if [ -f "$GUIDE_FILE" ]; then
    # Contar secciones con "Paso"
    STEP_COUNT=$(grep -c "### Paso" "$GUIDE_FILE")
    if [ $STEP_COUNT -gt 0 ]; then
        echo -e "  ${GREEN}→${NC} $STEP_COUNT pasos documentados"
    else
        warn "No se encontraron pasos (### Paso X) en la guía"
    fi
    
    # Verificar que tenga ejemplos
    if grep -q "Ejemplo:" "$GUIDE_FILE" || grep -q "ejemplo" "$GUIDE_FILE"; then
        echo -e "  ${GREEN}→${NC} Incluye ejemplos"
    else
        warn "La guía no tiene ejemplos claros"
    fi
fi

# FAQ
FAQ_FILE="docs/user/faqs/${FEATURE}-faq.md"
check_file "$FAQ_FILE" "FAQ (Preguntas Frecuentes)"

if [ -f "$FAQ_FILE" ]; then
    # Contar preguntas (formato ### ¿...)
    FAQ_COUNT=$(grep -c "^###.*¿" "$FAQ_FILE")
    if [ $FAQ_COUNT -ge 5 ]; then
        echo -e "  ${GREEN}→${NC} $FAQ_COUNT preguntas en FAQ"
    elif [ $FAQ_COUNT -gt 0 ]; then
        echo -e "  ${YELLOW}→${NC} Solo $FAQ_COUNT preguntas (recomendado: 5+)"
        WARNINGS=$((WARNINGS+1))
    else
        warn "FAQ no tiene preguntas en formato estándar"
    fi
fi
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. BASE DE CONOCIMIENTO (RAG)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo -e "${BLUE}🤖 4. Base de Conocimiento (RAG)${NC}"
echo "────────────────────────────────────────"

CHUNKS_FILE="docs/knowledge-base/chunks/${FEATURE}.json"
check_file "$CHUNKS_FILE" "Chunks JSON para embeddings"

if [ -f "$CHUNKS_FILE" ]; then
    # Verificar que sea JSON válido
    if command -v python3 &> /dev/null; then
        if python3 -c "import json; json.load(open('$CHUNKS_FILE'))" 2>/dev/null; then
            echo -e "  ${GREEN}→${NC} JSON válido"
            
            # Contar chunks
            CHUNK_COUNT=$(python3 -c "import json; data=json.load(open('$CHUNKS_FILE')); print(len(data.get('chunks', [])))")
            
            if [ "$CHUNK_COUNT" -ge 15 ]; then
                echo -e "  ${GREEN}→${NC} $CHUNK_COUNT chunks (excelente, mínimo 15)"
            elif [ "$CHUNK_COUNT" -ge 10 ]; then
                echo -e "  ${YELLOW}→${NC} $CHUNK_COUNT chunks (aceptable, recomendado 15+)"
                WARNINGS=$((WARNINGS+1))
            else
                echo -e "  ${RED}→${NC} Solo $CHUNK_COUNT chunks (insuficiente, mínimo 10)"
                ERRORS=$((ERRORS+1))
            fi
            
            # Verificar estructura de chunks
            HAS_ID=$(python3 -c "import json; data=json.load(open('$CHUNKS_FILE')); print('id' in data['chunks'][0] if data.get('chunks') else False)" 2>/dev/null)
            HAS_CONTENT=$(python3 -c "import json; data=json.load(open('$CHUNKS_FILE')); print('content' in data['chunks'][0] if data.get('chunks') else False)" 2>/dev/null)
            HAS_KEYWORDS=$(python3 -c "import json; data=json.load(open('$CHUNKS_FILE')); print('keywords' in data['chunks'][0] if data.get('chunks') else False)" 2>/dev/null)
            
            if [ "$HAS_ID" = "True" ] && [ "$HAS_CONTENT" = "True" ] && [ "$HAS_KEYWORDS" = "True" ]; then
                echo -e "  ${GREEN}→${NC} Estructura de chunks válida (id, content, keywords)"
            else
                warn "Estructura de chunks incompleta"
            fi
        else
            echo -e "${RED}✗${NC} JSON inválido o corrupto"
            ERRORS=$((ERRORS+1))
        fi
    elif command -v jq &> /dev/null; then
        if jq empty "$CHUNKS_FILE" 2>/dev/null; then
            echo -e "  ${GREEN}→${NC} JSON válido"
            CHUNK_COUNT=$(jq '.chunks | length' "$CHUNKS_FILE")
            
            if [ "$CHUNK_COUNT" -ge 15 ]; then
                echo -e "  ${GREEN}→${NC} $CHUNK_COUNT chunks (excelente)"
            elif [ "$CHUNK_COUNT" -ge 10 ]; then
                echo -e "  ${YELLOW}→${NC} $CHUNK_COUNT chunks (aceptable)"
                WARNINGS=$((WARNINGS+1))
            else
                echo -e "  ${RED}→${NC} Solo $CHUNK_COUNT chunks (insuficiente)"
                ERRORS=$((ERRORS+1))
            fi
        else
            echo -e "${RED}✗${NC} JSON inválido"
            ERRORS=$((ERRORS+1))
        fi
    else
        warn "No se puede validar JSON (python3 o jq no disponibles)"
    fi
fi
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. SINCRONIZACIÓN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo -e "${BLUE}🔄 5. Sincronización${NC}"
echo "────────────────────────────────────────"

# Verificar log de sincronización
if [ -f "docs/sync-log.json" ]; then
    echo -e "${GREEN}✓${NC} Log de sincronización existe"
    
    if command -v python3 &> /dev/null; then
        # Verificar si este feature está en el log
        FEATURE_IN_LOG=$(python3 -c "import json; data=json.load(open('docs/sync-log.json')); print('$FEATURE' in data.get('features', {}))" 2>/dev/null)
        
        if [ "$FEATURE_IN_LOG" = "True" ]; then
            LAST_SYNC=$(python3 -c "import json; data=json.load(open('docs/sync-log.json')); print(data['features']['$FEATURE'].get('last_sync', 'N/A'))")
            echo -e "  ${GREEN}→${NC} Última sincronización: $LAST_SYNC"
        else
            warn "Feature no sincronizado con Notion aún"
        fi
    fi
else
    warn "docs/sync-log.json no encontrado (se creará al sincronizar)"
fi
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RESUMEN FINAL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  📊 RESUMEN${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ DOCUMENTACIÓN COMPLETA PARA '${FEATURE}'${NC}"
    echo ""
    echo "Todos los documentos necesarios están presentes y válidos."
    echo ""
    echo "Este feature está listo para:"
    echo "  • Deploy a producción"
    echo "  • Sincronización con chat IA"
    echo "  • Entrega a usuarios"
    echo ""
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  DOCUMENTACIÓN ACEPTABLE - $WARNINGS ADVERTENCIAS${NC}"
    echo ""
    echo "La documentación está funcional pero hay mejoras recomendadas."
    echo "Revisa las advertencias arriba."
    echo ""
    exit 0
else
    echo -e "${RED}❌ DOCUMENTACIÓN INCOMPLETA - $ERRORS ARCHIVOS FALTANTES${NC}"
    echo ""
    echo "Archivos faltantes o incompletos:"
    echo ""
    
    # Listar qué falta
    [ ! -f "$PLAN_FILE" ] && echo "  • $PLAN_FILE"
    [ ! -f "$OPENAPI_FILE" ] && echo "  • $OPENAPI_FILE"
    [ ! -f "$ARCH_FILE" ] && echo "  • $ARCH_FILE"
    [ ! -f "$GUIDE_FILE" ] && echo "  • $GUIDE_FILE"
    [ ! -f "$FAQ_FILE" ] && echo "  • $FAQ_FILE"
    [ ! -f "$CHUNKS_FILE" ] && echo "  • $CHUNKS_FILE"
    
    echo ""
    echo "Para generar documentación completa, ejecuta:"
    echo ""
    echo "  ${BLUE}claude code${NC}"
    echo ""
    echo "  Prompt:"
    echo "  ${YELLOW}\"Lee skill saicloud-documentacion y genera${NC}"
    echo "  ${YELLOW}documentación completa para el feature '${FEATURE}'\"${NC}"
    echo ""
    exit 1
fi
