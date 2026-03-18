#!/bin/bash

# Script de inicialización completa del proyecto
# Ubicación: scripts/init-project.sh
# Uso: ./scripts/init-project.sh

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  🚀 INICIALIZACIÓN PROYECTO SAICLOUD${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Verificar que estamos en la raíz del proyecto
if [ ! -f "docker-compose.yml" ] && [ ! -d "backend" ] && [ ! -d "frontend" ]; then
    echo -e "${YELLOW}⚠${NC}  ¿Estás en la raíz del proyecto Saicloud?"
    echo ""
    read -p "¿Deseas inicializar aquí? (s/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        echo "Cancelado"
        exit 1
    fi
fi

echo "📁 Creando estructura de directorios..."
echo ""

# Crear estructura completa
mkdir -p backend/apps
mkdir -p backend/config
mkdir -p backend/docs/plans
mkdir -p backend/docs/technical/api
mkdir -p backend/docs/technical/architecture
mkdir -p backend/docs/user/guides
mkdir -p backend/docs/user/faqs
mkdir -p backend/docs/knowledge-base/chunks
mkdir -p backend/docs/knowledge-base/embeddings
mkdir -p frontend/src/app/core
mkdir -p frontend/src/app/shared
mkdir -p frontend/src/app/features
mkdir -p n8n/workflows
mkdir -p scripts
mkdir -p .claude

echo -e "${GREEN}✓${NC} Directorios creados"
echo ""

# Mover docs a raíz si estaban en backend
if [ -d "backend/docs" ] && [ ! -d "docs" ]; then
    echo "📦 Moviendo docs/ a raíz del proyecto..."
    mv backend/docs ./docs
    ln -s ../docs backend/docs
    echo -e "${GREEN}✓${NC} docs/ en raíz, symlink en backend/"
elif [ ! -d "docs" ]; then
    mkdir -p docs/plans
    mkdir -p docs/technical/api
    mkdir -p docs/technical/architecture
    mkdir -p docs/user/guides
    mkdir -p docs/user/faqs
    mkdir -p docs/knowledge-base/chunks
    echo -e "${GREEN}✓${NC} docs/ creado en raíz"
fi
echo ""

# Ejecutar setup de Claude Config
echo "🤖 Configurando Claude Code..."
if [ -f "scripts/setup-claude-config.sh" ]; then
    bash scripts/setup-claude-config.sh
else
    echo -e "${YELLOW}⚠${NC}  scripts/setup-claude-config.sh no encontrado"
    echo "   Descárgalo y ejecútalo manualmente"
fi
echo ""

# Crear .gitignore si no existe
if [ ! -f ".gitignore" ]; then
    echo "📝 Creando .gitignore..."
    cat > .gitignore << 'GITIGNORE'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
venv/
.venv/
ENV/
env/

# Django
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal
media/
staticfiles/

# Environment variables
.env
.env.local
.env.*.local

# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.npm
.eslintcache

# Angular
/frontend/dist/
/frontend/tmp/
/frontend/out-tsc/
/frontend/.angular/

# IDE
.idea/
.vscode/
*.swp
*.swo
*~
.DS_Store

# Docker
*.pid
*.seed
*.pid.lock

# Logs
logs/
*.log

# Coverage
.coverage
.coverage.*
htmlcov/
.pytest_cache/

# n8n
n8n/.n8n/

# Backups
*.bak
*.backup
GITIGNORE
    echo -e "${GREEN}✓${NC} .gitignore creado"
else
    echo -e "${GREEN}✓${NC} .gitignore ya existe"
fi
echo ""

# Crear README.md si no existe
if [ ! -f "README.md" ]; then
    echo "📄 Creando README.md..."
    cat > README.md << 'README'
# Saicloud

ERP SaaS multi-tenant desarrollado con Django + Angular + PostgreSQL + n8n

## Stack Tecnológico

- **Backend:** Django 5 + Django REST Framework + PostgreSQL 16
- **Frontend:** Angular 18 (standalone components) + PrimeNG
- **Automatización:** n8n
- **Auth:** JWT (djangorestframework-simplejwt)

## Estructura del Proyecto

```
saicloud/
├── backend/          # Django backend
├── frontend/         # Angular frontend
├── n8n/             # Workflows de automatización
├── docs/            # Documentación
│   ├── technical/   # Docs técnicas (API, arquitectura)
│   ├── user/        # Guías de usuario
│   └── knowledge-base/  # Base para chat IA
├── scripts/         # Scripts de utilidad
└── .claude/         # Configuración Claude Code
```

## Setup Rápido

```bash
# 1. Verificar configuración
./scripts/verify-setup.sh

# 2. Levantar servicios
docker compose up -d

# 3. Iniciar desarrollo con Claude Code
claude code
```

## Metodología

Seguimos una metodología secuencial de 10 fases:
1. Planificación
2. Gestión de contexto
3. Skills/MCP/APIs
4. Agente único/multiagente
5. Iteración
6. Protección de ventana
7. Revisión final
8. Panel Admin
9. Validación UI/UX
10. Despliegue

Ver `docs/methodology.md` para detalles.

## Documentación

- **Técnica:** `docs/technical/`
- **Usuario:** `docs/user/`
- **Decisiones:** `DECISIONS.md`
- **Errores resueltos:** `ERRORS.md`

## Scripts Útiles

```bash
./scripts/verify-setup.sh           # Verificar configuración completa
./scripts/verify-docs.sh {feature}  # Verificar documentación de feature
./scripts/setup-claude-config.sh    # Configurar Claude Code
```

## Contacto

ValMen Tech - Saicloud Team
README
    echo -e "${GREEN}✓${NC} README.md creado"
else
    echo -e "${GREEN}✓${NC} README.md ya existe"
fi
echo ""

# Crear archivos de logs
touch docs/sync-log.json
echo '{"features": {}, "last_sync": null}' > docs/sync-log.json
echo -e "${GREEN}✓${NC} docs/sync-log.json inicializado"
echo ""

# Resumen
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ INICIALIZACIÓN COMPLETADA${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Estructura del proyecto creada exitosamente."
echo ""
echo -e "${BLUE}Próximos pasos:${NC}"
echo ""
echo "1. Verifica la configuración:"
echo "   ${GREEN}./scripts/verify-setup.sh${NC}"
echo ""
echo "2. Si tienes backend y frontend, asegúrate de tener:"
echo "   • backend/.env (copia de .env.example)"
echo "   • frontend/node_modules (ejecuta 'npm install')"
echo ""
echo "3. Levanta los servicios:"
echo "   ${GREEN}docker compose up -d${NC}"
echo ""
echo "4. Inicia Claude Code:"
echo "   ${GREEN}claude code${NC}"
echo ""
echo "Para más información, lee README.md"
echo ""
