#!/usr/bin/env bash
# pre-push-guard.sh — Hook PreToolUse para Bash: bloquea git push si el marco no pasa validación.
#
# Input: recibe el comando Bash que se va a ejecutar como variable de entorno
#        CLAUDE_TOOL_INPUT (JSON con {"command": "..."})
#
# Salida:
#   exit 0 → permitir ejecución
#   exit 2 → bloquear y mostrar mensaje (Claude Code lee stderr como razón)
#
# Bloquea específicamente: git push, git push origin main/master, deploy commands

set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Leer el comando desde stdin (Claude Code envía JSON con el input del tool)
INPUT=$(cat || echo "{}")
CMD=$(echo "$INPUT" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('tool_input', {}).get('command', ''))" 2>/dev/null || echo "")

# Si no es una operación sensible, dejar pasar
case "$CMD" in
    *"git push"*|*"docker push"*|*"kubectl apply"*|*"terraform apply"*|*"deploy"*)
        ;;
    *)
        exit 0
        ;;
esac

# Operación sensible detectada → validar marco
echo "🛡️  Operación sensible detectada: $CMD" >&2
echo "    Ejecutando validador del marco agentic..." >&2

if ! "$ROOT/.claude/scripts/validate-marco.sh" --quick >/dev/null 2>&1; then
    RESULT=$?
    if [[ $RESULT -eq 1 ]]; then
        echo "" >&2
        echo "❌ BLOQUEADO: el marco agentic tiene errores críticos." >&2
        echo "   Ejecuta: .claude/scripts/validate-marco.sh" >&2
        echo "   Corrige los errores antes de hacer push/deploy." >&2
        exit 2
    fi
fi

# Validación extra para git push a main/master
if echo "$CMD" | grep -qE "git push.*\b(main|master|prod|production)\b"; then
    # Buscar PROGRESS activo
    ACTIVE_PROGRESS=""
    while IFS= read -r pf; do
        [[ -z "$pf" ]] && continue
        status=$(awk '/^status:/ {sub(/^status: */, ""); print; exit}' "$pf" | tr -d '\r')
        if [[ "$status" == "in_progress" || "$status" == "blocked" ]]; then
            ACTIVE_PROGRESS="$pf"
            break
        fi
    done < <(find "$ROOT" -maxdepth 2 -name "PROGRESS-*.md" -type f 2>/dev/null)

    if [[ -n "$ACTIVE_PROGRESS" ]]; then
        # Verificar que la Fase 7 (revisión final) esté aprobada
        if ! grep -qE "phases_approved:.*\b7\b" "$ACTIVE_PROGRESS"; then
            echo "" >&2
            echo "❌ BLOQUEADO: push a main sin Fase 7 (revisión final) aprobada." >&2
            echo "   PROGRESS: $(basename $ACTIVE_PROGRESS)" >&2
            echo "   Ejecuta la fase 7 (revisión final) antes de hacer push." >&2
            exit 2
        fi
    fi
fi

echo "    ✓ Marco OK — permitiendo operación" >&2
exit 0
