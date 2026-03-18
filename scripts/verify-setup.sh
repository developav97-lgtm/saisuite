#!/bin/bash

# Script de verificación completa de Saicloud
# Ubicación: scripts/verify-setup.sh
# Uso: ./scripts/verify-setup.sh

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  🔍 VERIFICACIÓN COMPLETA SAICLOUD${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

ERRORS=0
WARNINGS=0

# Función de verificación
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

check_dir() {
    if [ -d "$1" ]; then
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
# 1. ARCHIVOS DE CONTEXTO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo -e "${BLUE}📋 1. Archivos de Contexto${NC}"
echo "────────────────────────────────────────"
check_file "CLAUDE.md" "CLAUDE.md"
check_file "DECISIONS.md" "DECISIONS.md"
check_file "ERRORS.md" "ERRORS.md"
check_file "CONTEXT.md" "CONTEXT.md"

# Verificar que no estén vacíos
if [ -f "DECISIONS.md" ]; then
    DECISION_COUNT=$(grep -c "^## DEC-" 2>/dev/null || echo "0" DECISIONS.md 2>/dev/null || echo "0")
    if [ "$DECISION_COUNT" -eq 0 ]; then
        warn "DECISIONS.md existe pero no tiene decisiones (DEC-XXX)"
    else
        echo -e "  ${GREEN}→${NC} $DECISION_COUNT decisiones documentadas"
    fi
fi

if [ -f "ERRORS.md" ]; then
    ERROR_COUNT=$(grep -c "^## ERROR-" 2>/dev/null || echo "0" ERRORS.md 2>/dev/null || echo "0")
    if [ "$ERROR_COUNT" -eq 0 ]; then
        warn "ERRORS.md existe pero no tiene errores documentados"
    else
        echo -e "  ${GREEN}→${NC} $ERROR_COUNT errores resueltos documentados"
    fi
fi
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. ESTRUCTURA DE DOCUMENTACIÓN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo -e "${BLUE}📚 2. Estructura de Documentación${NC}"
echo "────────────────────────────────────────"
check_dir "docs" "docs/"
check_dir "docs/technical" "docs/technical/"
check_dir "docs/technical/api" "docs/technical/api/"
check_dir "docs/technical/architecture" "docs/technical/architecture/"
check_dir "docs/user" "docs/user/"
check_dir "docs/user/guides" "docs/user/guides/"
check_dir "docs/user/faqs" "docs/user/faqs/"
check_dir "docs/knowledge-base" "docs/knowledge-base/"
check_dir "docs/knowledge-base/chunks" "docs/knowledge-base/chunks/"
check_dir "docs/plans" "docs/plans/"

# Contar documentos existentes
if [ -d "docs/plans" ]; then
    PLAN_COUNT=$(ls docs/plans/PLAN-*.md 2>/dev/null | wc -l)
    echo -e "  ${GREEN}→${NC} $PLAN_COUNT planes de features encontrados"
fi
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. CONFIGURACIÓN DOCKER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo -e "${BLUE}🐳 3. Configuración Docker${NC}"
echo "────────────────────────────────────────"
check_file "docker-compose.yml" "docker-compose.yml"

# Verificar si Docker está corriendo
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker instalado"
    
    # Verificar si docker-compose está disponible
    if docker compose version &> /dev/null; then
        echo -e "${GREEN}✓${NC} Docker Compose disponible"
        
        # Verificar servicios corriendo
        if docker compose ps &> /dev/null 2>&1; then
            RUNNING=$(docker compose ps --services --filter "status=running" 2>/dev/null | wc -l)
            TOTAL=$(docker compose ps --services 2>/dev/null | wc -l)
            
            if [ "$RUNNING" -eq 4 ] && [ "$TOTAL" -eq 4 ]; then
                echo -e "${GREEN}✓${NC} 4/4 servicios corriendo (backend, frontend, db, n8n)"
            elif [ "$RUNNING" -gt 0 ]; then
                echo -e "${YELLOW}⚠${NC}  Solo $RUNNING/$TOTAL servicios corriendo"
                echo -e "  ${YELLOW}→${NC} Ejecuta: ${BLUE}docker compose up -d${NC}"
                WARNINGS=$((WARNINGS+1))
            else
                echo -e "${RED}✗${NC} Servicios no están corriendo"
                echo -e "  ${YELLOW}→${NC} Ejecuta: ${BLUE}docker compose up -d${NC}"
                ERRORS=$((ERRORS+1))
            fi
        else
            warn "Docker Compose no puede verificar servicios"
        fi
    else
        echo -e "${RED}✗${NC} Docker Compose no disponible"
        ERRORS=$((ERRORS+1))
    fi
else
    echo -e "${RED}✗${NC} Docker no instalado"
    ERRORS=$((ERRORS+1))
fi
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. BACKEND DJANGO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo -e "${BLUE}🐍 4. Backend Django${NC}"
echo "────────────────────────────────────────"
check_dir "backend" "backend/"
check_file "backend/manage.py" "backend/manage.py"
check_dir "backend/config" "backend/config/"
check_dir "backend/apps" "backend/apps/"

# Virtual environment
if [ -d "backend/venv" ] || [ -d "backend/.venv" ]; then
    echo -e "${GREEN}✓${NC} Virtual environment encontrado"
else
    echo -e "${YELLOW}⚠${NC}  Virtual environment no encontrado"
    echo -e "  ${YELLOW}→${NC} Ejecuta: ${BLUE}cd backend && python -m venv venv${NC}"
    WARNINGS=$((WARNINGS+1))
fi

# Archivo .env
if [ -f "backend/.env" ]; then
    echo -e "${GREEN}✓${NC} backend/.env"
    
    # Verificar variables críticas
    if grep -q "SECRET_KEY" backend/.env 2>/dev/null; then
        echo -e "  ${GREEN}→${NC} SECRET_KEY configurado"
    else
        warn "SECRET_KEY no encontrado en .env"
    fi
    
    if grep -q "DATABASE_URL" backend/.env 2>/dev/null; then
        echo -e "  ${GREEN}→${NC} DATABASE_URL configurado"
    else
        warn "DATABASE_URL no encontrado en .env"
    fi
else
    echo -e "${RED}✗${NC} backend/.env faltante"
    if [ -f "backend/.env.example" ]; then
        echo -e "  ${YELLOW}→${NC} Ejecuta: ${BLUE}cp backend/.env.example backend/.env${NC}"
    else
        echo -e "  ${YELLOW}→${NC} Crea backend/.env con las variables necesarias"
    fi
    ERRORS=$((ERRORS+1))
fi

# requirements.txt
check_file "backend/requirements.txt" "backend/requirements.txt"

# Contar apps Django
if [ -d "backend/apps" ]; then
    APP_COUNT=$(find backend/apps -mindepth 1 -maxdepth 1 -type d | wc -l)
    echo -e "  ${GREEN}→${NC} $APP_COUNT Django apps encontradas"
fi
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. FRONTEND ANGULAR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo -e "${BLUE}⚡ 5. Frontend Angular${NC}"
echo "────────────────────────────────────────"
check_dir "frontend" "frontend/"
check_file "frontend/package.json" "frontend/package.json"
check_file "frontend/angular.json" "frontend/angular.json"
check_file "frontend/tsconfig.json" "frontend/tsconfig.json"

# node_modules
if [ -d "frontend/node_modules" ]; then
    echo -e "${GREEN}✓${NC} frontend/node_modules"
else
    echo -e "${YELLOW}⚠${NC}  frontend/node_modules no encontrado"
    echo -e "  ${YELLOW}→${NC} Ejecuta: ${BLUE}cd frontend && npm install${NC}"
    WARNINGS=$((WARNINGS+1))
fi

# Verificar structure Angular
check_dir "frontend/src" "frontend/src/"
check_dir "frontend/src/app" "frontend/src/app/"

if [ -d "frontend/src/app" ]; then
    if [ -d "frontend/src/app/core" ]; then
        echo -e "${GREEN}✓${NC} frontend/src/app/core/"
    else
        warn "frontend/src/app/core/ no encontrado (recomendado)"
    fi
    
    if [ -d "frontend/src/app/shared" ]; then
        echo -e "${GREEN}✓${NC} frontend/src/app/shared/"
    else
        warn "frontend/src/app/shared/ no encontrado (recomendado)"
    fi
    
    if [ -d "frontend/src/app/features" ]; then
        echo -e "${GREEN}✓${NC} frontend/src/app/features/"
        FEATURE_COUNT=$(find frontend/src/app/features -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l)
        echo -e "  ${GREEN}→${NC} $FEATURE_COUNT feature modules encontrados"
    else
        warn "frontend/src/app/features/ no encontrado (recomendado)"
    fi
fi

# Environment files
if [ -f "frontend/src/environments/environment.ts" ]; then
    echo -e "${GREEN}✓${NC} frontend/src/environments/environment.ts"
else
    echo -e "${RED}✗${NC} frontend/src/environments/environment.ts faltante"
    ERRORS=$((ERRORS+1))
fi
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. N8N
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo -e "${BLUE}🔄 6. n8n${NC}"
echo "────────────────────────────────────────"
check_dir "n8n" "n8n/"
check_dir "n8n/workflows" "n8n/workflows/"

if [ -d "n8n/workflows" ]; then
    WORKFLOW_COUNT=$(ls n8n/workflows/*.json 2>/dev/null | wc -l)
    if [ "$WORKFLOW_COUNT" -gt 0 ]; then
        echo -e "${GREEN}✓${NC} $WORKFLOW_COUNT workflows encontrados"
    else
        warn "No hay workflows en n8n/workflows/"
    fi
fi
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 7. CONFIGURACIÓN CLAUDE CODE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo -e "${BLUE}🤖 7. Configuración Claude Code${NC}"
echo "────────────────────────────────────────"
check_dir ".claude" ".claude/"
check_file ".claude/config.json" ".claude/config.json"

if [ -f ".claude/config.json" ]; then
    # Verificar que sea JSON válido
    if python3 -m json.tool .claude/config.json > /dev/null 2>&1 || jq empty .claude/config.json > /dev/null 2>&1; then
        echo -e "  ${GREEN}→${NC} JSON válido"
        
        # Verificar context_files
        if grep -q "CLAUDE.md" .claude/config.json; then
            echo -e "  ${GREEN}→${NC} CLAUDE.md en context_files"
        else
            warn "CLAUDE.md no está en context_files"
        fi
    else
        echo -e "${RED}✗${NC} .claude/config.json tiene errores de sintaxis"
        ERRORS=$((ERRORS+1))
    fi
fi

# Scripts de sesión
if [ -f "scripts/session-banner.sh" ]; then
    echo -e "${GREEN}✓${NC} scripts/session-banner.sh"
else
    warn "scripts/session-banner.sh no encontrado (recomendado)"
fi
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 8. SCRIPTS DE VERIFICACIÓN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo -e "${BLUE}📜 8. Scripts de Verificación${NC}"
echo "────────────────────────────────────────"
check_dir "scripts" "scripts/"
check_file "scripts/verify-setup.sh" "scripts/verify-setup.sh (este script)"

if [ -f "scripts/verify-docs.sh" ]; then
    echo -e "${GREEN}✓${NC} scripts/verify-docs.sh"
else
    warn "scripts/verify-docs.sh no encontrado (necesario para validar docs)"
fi

if [ -f "scripts/setup-claude-config.sh" ]; then
    echo -e "${GREEN}✓${NC} scripts/setup-claude-config.sh"
else
    warn "scripts/setup-claude-config.sh no encontrado"
fi

# Verificar que los scripts sean ejecutables
if [ -f "scripts/verify-setup.sh" ] && [ ! -x "scripts/verify-setup.sh" ]; then
    warn "scripts/verify-setup.sh no es ejecutable"
    echo -e "  ${YELLOW}→${NC} Ejecuta: ${BLUE}chmod +x scripts/verify-setup.sh${NC}"
fi
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 9. GIT (Opcional)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo -e "${BLUE}📦 9. Control de Versiones (Git)${NC}"
echo "────────────────────────────────────────"
if [ -d ".git" ]; then
    echo -e "${GREEN}✓${NC} Repositorio Git inicializado"
    
    # Verificar .gitignore
    if [ -f ".gitignore" ]; then
        echo -e "${GREEN}✓${NC} .gitignore presente"
        
        # Verificar reglas críticas
        if grep -q "\.env" .gitignore 2>/dev/null; then
            echo -e "  ${GREEN}→${NC} .env ignorado (correcto)"
        else
            warn ".env no está en .gitignore (¡PELIGRO DE SEGURIDAD!)"
        fi
        
        if grep -q "node_modules" .gitignore 2>/dev/null; then
            echo -e "  ${GREEN}→${NC} node_modules ignorado (correcto)"
        else
            warn "node_modules no está en .gitignore"
        fi
    else
        warn ".gitignore no encontrado"
    fi
else
    warn "No es un repositorio Git (opcional pero recomendado)"
fi
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RESUMEN FINAL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  📊 RESUMEN DE VERIFICACIÓN${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ PERFECTO - TODO ESTÁ LISTO${NC}"
    echo ""
    echo "El proyecto Saicloud está completamente configurado."
    echo ""
    echo -e "${BLUE}Próximos pasos:${NC}"
    echo "1. Ejecuta: ${BLUE}docker compose up -d${NC} (si no está corriendo)"
    echo "2. Abre Claude Code: ${BLUE}claude code${NC}"
    echo "3. Comienza con la primera feature usando metodología secuencial"
    echo ""
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  CASI LISTO - $WARNINGS ADVERTENCIAS${NC}"
    echo ""
    echo "El proyecto está funcional pero hay mejoras recomendadas."
    echo "Revisa las advertencias arriba (marcadas con ⚠)."
    echo ""
    exit 0
else
    echo -e "${RED}❌ ERRORES ENCONTRADOS - $ERRORS CRÍTICOS, $WARNINGS ADVERTENCIAS${NC}"
    echo ""
    echo "Debes corregir los errores críticos antes de continuar."
    echo "Revisa las líneas marcadas con ✗ arriba."
    echo ""
    echo -e "${BLUE}Ayuda rápida:${NC}"
    echo ""
    
    if [ ! -f "backend/.env" ]; then
        echo "• Backend .env faltante:"
        echo "  ${BLUE}cp backend/.env.example backend/.env${NC}"
        echo ""
    fi
    
    if [ ! -f ".claude/config.json" ]; then
        echo "• Claude Code no configurado:"
        echo "  ${BLUE}./scripts/setup-claude-config.sh${NC}"
        echo ""
    fi
    
    if [ ! -d "frontend/node_modules" ]; then
        echo "• Frontend dependencias faltantes:"
        echo "  ${BLUE}cd frontend && npm install${NC}"
        echo ""
    fi
    
    echo "Ejecuta este script nuevamente después de corregir: ${BLUE}./scripts/verify-setup.sh${NC}"
    echo ""
    exit 1
fi
