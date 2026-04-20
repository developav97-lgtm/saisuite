#!/usr/bin/env bash
# session-start.sh — Hook SessionStart: imprime estado del PROGRESS activo
#
# Salida al stdout: se muestra al inicio de la sesión.
# No falla la sesión si no hay PROGRESS — solo es informativo.

set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Buscar PROGRESS con status: in_progress o blocked
ACTIVE_PROGRESS=""
while IFS= read -r pf; do
    [[ -z "$pf" ]] && continue
    status=$(awk '/^status:/ {sub(/^status: */, ""); print; exit}' "$pf" | tr -d '\r')
    if [[ "$status" == "in_progress" || "$status" == "blocked" ]]; then
        ACTIVE_PROGRESS="$pf"
        break
    fi
done < <(find "$ROOT" -maxdepth 2 -name "PROGRESS-*.md" -type f 2>/dev/null)

if [[ -z "$ACTIVE_PROGRESS" ]]; then
    # Sin PROGRESS activo — mostrar resumen de tickets recientes completados
    # y reportes generados para que el modelo tenga contexto y no duplique trabajo.
    recent_progress=$(find "$ROOT" -maxdepth 2 -name "PROGRESS-*.md" -type f -mtime -7 2>/dev/null | head -5)
    recent_reports=$(find "$ROOT/docs/plans" -maxdepth 1 -name "*.md" -type f -mtime -7 2>/dev/null | head -5)

    if [[ -n "$recent_progress" || -n "$recent_reports" ]]; then
        echo "📂 Sesión limpia — sin PROGRESS activo."
        echo ""
        if [[ -n "$recent_progress" ]]; then
            echo "  PROGRESS recientes (7 días):"
            while IFS= read -r pf; do
                [[ -z "$pf" ]] && continue
                status=$(awk '/^status:/ {sub(/^status: */, ""); print; exit}' "$pf" | tr -d '\r')
                module=$(awk '/^module:/ {sub(/^module: */, ""); print; exit}' "$pf" | tr -d '\r')
                echo "    [$status] $(basename "$pf") — módulo $module"
            done <<< "$recent_progress"
            echo ""
        fi
        if [[ -n "$recent_reports" ]]; then
            echo "  Reportes en docs/plans/ (7 días):"
            while IFS= read -r rf; do
                [[ -z "$rf" ]] && continue
                echo "    $(basename "$rf")"
            done <<< "$recent_reports"
            echo ""
        fi
        echo "  → Revisar CONTEXT.md \"Próximas prioridades\" para pendientes reales."
        echo "  → Cruzar con reportes arriba antes de clasificar como pendiente."
    fi
    exit 0
fi

# Extraer campos clave del frontmatter
module=$(awk '/^module:/ {sub(/^module: */, ""); print; exit}' "$ACTIVE_PROGRESS" | tr -d '\r')
ticket_type=$(awk '/^ticket_type:/ {sub(/^ticket_type: */, ""); print; exit}' "$ACTIVE_PROGRESS" | tr -d '\r')
current_phase=$(awk '/^current_phase:/ {sub(/^current_phase: */, ""); print; exit}' "$ACTIVE_PROGRESS" | tr -d '\r')
status=$(awk '/^status:/ {sub(/^status: */, ""); print; exit}' "$ACTIVE_PROGRESS" | tr -d '\r')
next_action=$(awk '/^next_action:/ {sub(/^next_action: */, ""); print; exit}' "$ACTIVE_PROGRESS" | tr -d '\r')
last_session=$(awk '/^last_session:/ {sub(/^last_session: */, ""); print; exit}' "$ACTIVE_PROGRESS" | tr -d '\r')

cat <<EOF
📂 PROGRESS activo detectado — $(basename "$ACTIVE_PROGRESS")

Módulo:        $module
Tipo ticket:   $ticket_type
Estado:        $status
Fase actual:   $current_phase
Última acción: $next_action
Última sesión: $last_session

→ Orquestador: revisar "$(basename "$ACTIVE_PROGRESS")" antes de arrancar nuevo trabajo.
EOF
