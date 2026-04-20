#!/usr/bin/env bash
# validate-marco.sh — Verifica consistencia del marco agentic SaiSuite
#
# Uso:
#   .claude/scripts/validate-marco.sh              # validación completa
#   .claude/scripts/validate-marco.sh --quick      # solo chequeos rápidos
#   .claude/scripts/validate-marco.sh --fix-perms  # corregir permisos
#
# Salida:
#   exit 0 → todo bien
#   exit 1 → error crítico (referencia rota, frontmatter inválido)
#   exit 2 → warning (posible inconsistencia, revisar)
#
# Se invoca desde hook PreToolUse cuando se va a hacer commit/push.

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
AGENTS_DIR="$ROOT/.claude/agents"
SKILLS_DIR="$ROOT/.claude/skills"
PHASE_MAP="$ROOT/.claude/PHASE-MAP.md"
ORQUESTADOR="$ROOT/.claude/skills/saicloud-orquestador/SKILL.md"
CLAUDE_MD="$ROOT/CLAUDE.md"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

ERRORS=0
WARNINGS=0
MODE="${1:-full}"

log_error() { echo -e "${RED}✗ ERROR:${NC} $1" >&2; ERRORS=$((ERRORS+1)); }
log_warn()  { echo -e "${YELLOW}⚠ WARN:${NC} $1" >&2; WARNINGS=$((WARNINGS+1)); }
log_ok()    { echo -e "${GREEN}✓${NC} $1"; }
log_section() { echo -e "\n${BOLD}== $1 ==${NC}"; }

# ────────────────────────────────────────────────────────────────
log_section "1. Archivos clave existen"
# ────────────────────────────────────────────────────────────────

for f in "$CLAUDE_MD" "$PHASE_MAP" "$ORQUESTADOR"; do
    if [[ -f "$f" ]]; then
        log_ok "$(basename $f) existe"
    else
        log_error "Falta archivo crítico: $f"
    fi
done

# ────────────────────────────────────────────────────────────────
log_section "2. Agentes project-scoped"
# ────────────────────────────────────────────────────────────────

if [[ ! -d "$AGENTS_DIR" ]]; then
    log_error "Directorio $AGENTS_DIR no existe"
    exit 1
fi

AGENT_COUNT=$(find "$AGENTS_DIR" -name "*.md" -type f | wc -l | tr -d ' ')
log_ok "$AGENT_COUNT agentes encontrados en .claude/agents/"

# Extraer nombres de frontmatter
AGENT_NAMES=()
while IFS= read -r agent_file; do
    name=$(awk '/^name:/ {sub(/^name: */, ""); print; exit}' "$agent_file" | tr -d '\r')
    if [[ -z "$name" ]]; then
        log_error "Frontmatter sin 'name:' en $(basename $agent_file)"
    else
        AGENT_NAMES+=("$name")
    fi
done < <(find "$AGENTS_DIR" -name "*.md" -type f)

# Detectar nombres duplicados
DUPS=$(printf '%s\n' "${AGENT_NAMES[@]}" | sort | uniq -d)
if [[ -n "$DUPS" ]]; then
    log_error "Nombres de agente duplicados:"$'\n'"$DUPS"
fi

# ────────────────────────────────────────────────────────────────
log_section "3. Referencias PHASE-MAP → agentes reales"
# ────────────────────────────────────────────────────────────────

# Extraer agentes mencionados en PHASE-MAP: patrón Agent(Nombre) o subagent_type="Nombre"
# Excluir placeholders (<...>) y palabras que no son nombres propios
REFERENCED_AGENTS=$(grep -oE "Agent\([A-Za-z][A-Za-z _-]+\)|subagent_type=\"[^\"]+\"" "$PHASE_MAP" 2>/dev/null | \
    sed -E 's/Agent\(([^)]+)\)/\1/; s/subagent_type="([^"]+)"/\1/' | \
    grep -v "^<" | grep -v "^[a-z_]*$" | \
    sort -u)

MISSING=0
while IFS= read -r ref; do
    [[ -z "$ref" ]] && continue
    if printf '%s\n' "${AGENT_NAMES[@]}" | grep -Fxq "$ref"; then
        :  # ok
    else
        log_warn "PHASE-MAP referencia agente '$ref' no encontrado en .claude/agents/"
        MISSING=$((MISSING+1))
    fi
done <<< "$REFERENCED_AGENTS"

[[ $MISSING -eq 0 ]] && log_ok "Todas las referencias Agent() apuntan a agentes reales"

# ────────────────────────────────────────────────────────────────
log_section "4. Referencias a skills del plugin"
# ────────────────────────────────────────────────────────────────

PLUGIN_COUNT=$(grep -hoE "anthropic-skills:[a-z][a-z0-9-]+" "$PHASE_MAP" "$ORQUESTADOR" "$CLAUDE_MD" 2>/dev/null | sort -u | wc -l | tr -d ' ')
log_ok "$PLUGIN_COUNT skills únicos del plugin referenciados"

# No podemos verificar que existan en tiempo de script (son runtime),
# pero sí detectar prefijos mal escritos
# Excluir el propio script del grep para que sus regex de detección no se autoreferencien
if grep -rE "anthropic_skills:|anthropic-skill:|antrhopic-skills:" "$ROOT/.claude" "$CLAUDE_MD" \
    --exclude-dir=scripts --exclude="*.sh" >/dev/null 2>&1; then
    log_error "Prefijo mal escrito detectado (debe ser 'anthropic-skills:')"
    grep -rnE "anthropic_skills:|anthropic-skill:|antrhopic-skills:" "$ROOT/.claude" "$CLAUDE_MD" \
        --exclude-dir=scripts --exclude="*.sh" 2>/dev/null | head -5
fi

# ────────────────────────────────────────────────────────────────
log_section "5. Skills locales"
# ────────────────────────────────────────────────────────────────

if [[ -d "$SKILLS_DIR" ]]; then
    LOCAL_COUNT=$(find "$SKILLS_DIR" -name "SKILL.md" -type f 2>/dev/null | wc -l | tr -d ' ')
    log_ok "$LOCAL_COUNT skill(s) local(es) en .claude/skills/"

    # Validar frontmatter name: en cada SKILL.md
    while IFS= read -r skill_file; do
        [[ -z "$skill_file" ]] && continue
        if ! grep -q "^name:" "$skill_file"; then
            log_error "Skill sin frontmatter 'name:' en $skill_file"
        fi
    done < <(find "$SKILLS_DIR" -name "SKILL.md" -type f 2>/dev/null)
fi

# ────────────────────────────────────────────────────────────────
log_section "6. Referencias rotas a paths inexistentes"
# ────────────────────────────────────────────────────────────────

# Buscar skills fantasma — paths tipo .claude/skills/saicloud-X/SKILL.md
# que NO sean saicloud-orquestador ni brevity-mode
SUSPICIOUS=$(grep -rE "\.claude/skills/saicloud-[a-z-]+/" "$ROOT/.claude" "$CLAUDE_MD" 2>/dev/null | \
    grep -v "saicloud-orquestador\|brevity-mode" | head -5)

if [[ -n "$SUSPICIOUS" ]]; then
    log_warn "Posibles referencias a skills locales inexistentes:"
    echo "$SUSPICIOUS"
else
    log_ok "Sin referencias a skills locales fantasma"
fi

# ────────────────────────────────────────────────────────────────
log_section "7. PROGRESS files"
# ────────────────────────────────────────────────────────────────

PROGRESS_COUNT=$(find "$ROOT" -maxdepth 2 -name "PROGRESS-*.md" -type f 2>/dev/null | wc -l | tr -d ' ')

if [[ "$PROGRESS_COUNT" -gt 0 ]]; then
    log_ok "$PROGRESS_COUNT archivo(s) PROGRESS encontrado(s)"

    # Validar frontmatter en cada uno
    while IFS= read -r pf; do
        [[ -z "$pf" ]] && continue
        if ! head -5 "$pf" | grep -q "^---"; then
            log_warn "PROGRESS sin frontmatter YAML: $(basename $pf)"
        fi
    done < <(find "$ROOT" -maxdepth 2 -name "PROGRESS-*.md" -type f 2>/dev/null)
else
    log_warn "No hay archivos PROGRESS-*.md aún (normal si proyecto recién empezado)"
fi

# ────────────────────────────────────────────────────────────────
log_section "8. Tamaños de archivos del marco"
# ────────────────────────────────────────────────────────────────

check_size() {
    local f="$1"
    local max="$2"
    local name="$3"
    if [[ -f "$f" ]]; then
        local lines=$(wc -l < "$f" | tr -d ' ')
        if [[ $lines -gt $max ]]; then
            log_warn "$name tiene $lines líneas (objetivo ≤$max)"
        else
            log_ok "$name: $lines líneas (≤$max)"
        fi
    fi
}

check_size "$CLAUDE_MD" 120 "CLAUDE.md"
check_size "$PHASE_MAP" 200 "PHASE-MAP.md"
check_size "$ORQUESTADOR" 300 "saicloud-orquestador/SKILL.md"

# ────────────────────────────────────────────────────────────────
log_section "9. Permisos de scripts"
# ────────────────────────────────────────────────────────────────

SCRIPTS_DIR="$ROOT/.claude/scripts"
if [[ -d "$SCRIPTS_DIR" ]]; then
    while IFS= read -r script; do
        [[ -z "$script" ]] && continue
        if [[ ! -x "$script" ]]; then
            if [[ "${2:-}" == "--fix-perms" ]] || [[ "$MODE" == "--fix-perms" ]]; then
                chmod +x "$script"
                log_ok "Permiso +x agregado a $(basename $script)"
            else
                log_warn "$(basename $script) no es ejecutable (usa --fix-perms)"
            fi
        fi
    done < <(find "$SCRIPTS_DIR" -name "*.sh" -type f)
fi

# ────────────────────────────────────────────────────────────────
# Resumen
# ────────────────────────────────────────────────────────────────

echo
echo -e "${BOLD}═══════════════════════════════════════${NC}"
if [[ $ERRORS -eq 0 && $WARNINGS -eq 0 ]]; then
    echo -e "${GREEN}${BOLD}✓ Marco agentic consistente${NC}"
    exit 0
elif [[ $ERRORS -eq 0 ]]; then
    echo -e "${YELLOW}${BOLD}⚠ $WARNINGS warnings (marco usable)${NC}"
    exit 2
else
    echo -e "${RED}${BOLD}✗ $ERRORS errores, $WARNINGS warnings${NC}"
    exit 1
fi
