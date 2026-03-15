#!/usr/bin/env bash
# install-cron.sh — Install Silver Tier cron entries
#
# WSL2 NOTE: cron does not auto-start on WSL2 boot.
# Run once per WSL2 session: sudo service cron start
# Or add to /etc/wsl.conf [boot] section: command = "service cron start"
#
# Usage: bash scripts/install-cron.sh
# Run again safely — will not duplicate entries.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Load VAULT_PATH from .env if present
if [ -f "$PROJECT_DIR/.env" ]; then
  # shellcheck disable=SC1090
  set -a
  source "$PROJECT_DIR/.env"
  set +a
fi

VAULT_PATH="${VAULT_PATH:-$PROJECT_DIR/AI_Employee_Vault}"
PYTHON="${PROJECT_DIR}/.venv/bin/python"

if [ ! -f "$PYTHON" ]; then
  PYTHON="python3"
fi

ORCHESTRATOR="$PROJECT_DIR/orchestrator.py"

# Build cron entries
GMAIL_CRON="*/5 * * * * VAULT_PATH=\"$VAULT_PATH\" $PYTHON $ORCHESTRATOR --watcher gmail --cron >> /tmp/ai-employee-cron.log 2>&1"
LINKEDIN_CRON="0 8 * * 1 VAULT_PATH=\"$VAULT_PATH\" claude --print \"Run the linkedin-post skill\" >> /tmp/ai-employee-cron.log 2>&1"
PROCESS_CRON="0 9 * * * VAULT_PATH=\"$VAULT_PATH\" claude --print \"Run the process-needs-action skill\" >> /tmp/ai-employee-cron.log 2>&1"

# Install without duplicating
CURRENT_CRON=$(crontab -l 2>/dev/null || true)

add_if_missing() {
  local entry="$1"
  local marker="$2"
  if echo "$CURRENT_CRON" | grep -qF "$marker"; then
    echo "  [skip] Already installed: $marker"
  else
    CURRENT_CRON="${CURRENT_CRON}"$'\n'"${entry}"
    echo "  [add]  Installed: $marker"
  fi
}

echo "Installing Silver Tier cron entries..."
add_if_missing "$GMAIL_CRON"    "--watcher gmail --cron"
add_if_missing "$LINKEDIN_CRON" "linkedin-post skill"
add_if_missing "$PROCESS_CRON"  "process-needs-action skill"

echo "$CURRENT_CRON" | crontab -

echo ""
echo "Done. Current crontab:"
crontab -l
echo ""
echo "IMPORTANT (WSL2): Run 'sudo service cron start' to activate cron in this session."
echo "Log file: /tmp/ai-employee-cron.log"
