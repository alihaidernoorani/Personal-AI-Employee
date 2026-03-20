#!/usr/bin/env bash
# scheduler.sh — Cron entry point for the Personal AI Employee
#
# Runs the process-needs-action skill via Claude Code every time cron calls it.
# Designed to be invoked every 5 minutes by cron.
#
# ── CRONTAB LINE (add with: crontab -e) ────────────────────────────────────────
#
#   */5 * * * * /bin/bash /mnt/c/Users/DELL/Documents/GitHub/Personal_AI_Employee/scheduler.sh >> /tmp/ai-employee.log 2>&1
#
# ── HOW TO ADD ─────────────────────────────────────────────────────────────────
#
#   1. Open crontab editor:
#        crontab -e
#
#   2. Paste the line above (adjust path if project is in a different location).
#
#   3. Save and exit (Ctrl+O, Enter, Ctrl+X in nano).
#
#   4. Verify it was saved:
#        crontab -l
#
#   5. (WSL2 only) Start the cron service if not already running:
#        sudo service cron start
#
#   To auto-start cron on every WSL2 session, add to /etc/wsl.conf:
#        [boot]
#        command = "service cron start"
#
# ── QUICK INSTALL (non-interactive) ────────────────────────────────────────────
#
#   Run this once to install without opening an editor:
#        bash scheduler.sh --install
#
# ── LOG FILE ───────────────────────────────────────────────────────────────────
#
#   Tail live output:
#        tail -f /tmp/ai-employee.log
#
# ───────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# ── Paths ──────────────────────────────────────────────────────────────────────

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Vault is always relative to project root — avoids .env Windows path mangling
VAULT_DIR="$PROJECT_DIR/AI_Employee_Vault"

# Load .env for DRY_RUN and other non-path vars (skip VAULT_PATH — Windows backslashes break in bash)
if [ -f "$PROJECT_DIR/.env" ]; then
  while IFS='=' read -r key value; do
    [[ "$key" =~ ^#.*$ || -z "$key" ]] && continue
    [[ "$key" == "VAULT_PATH" ]] && continue  # skip — derived from PROJECT_DIR above
    export "$key"="$value"
  done < "$PROJECT_DIR/.env"
fi

PYTHON="${PROJECT_DIR}/.venv/bin/python"
if [ ! -f "$PYTHON" ]; then
  PYTHON="$(command -v python3 || command -v python)"
fi

CLAUDE="$(command -v claude 2>/dev/null || echo 'claude')"
LOG_FILE="/tmp/ai-employee.log"
TIMESTAMP="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

# ── Install mode ───────────────────────────────────────────────────────────────

if [ "${1:-}" = "--install" ]; then
  CRON_LINE="*/5 * * * * /bin/bash $PROJECT_DIR/scheduler.sh >> $LOG_FILE 2>&1"
  CURRENT="$(crontab -l 2>/dev/null || true)"

  if echo "$CURRENT" | grep -qF "scheduler.sh"; then
    echo "[$TIMESTAMP] [scheduler] Cron entry already installed — skipping."
  else
    (echo "$CURRENT"; echo "$CRON_LINE") | crontab -
    echo "[$TIMESTAMP] [scheduler] Cron entry installed:"
    echo "  $CRON_LINE"
    echo ""
    echo "Verify with: crontab -l"
    echo "WSL2 users:  sudo service cron start"
  fi
  exit 0
fi

# ── Guard: skip if vault doesn't exist ────────────────────────────────────────

if [ ! -d "$VAULT_DIR" ]; then
  echo "[$TIMESTAMP] [scheduler] ERROR: Vault not found at $VAULT_DIR — aborting." >&2
  exit 1
fi

# ── Guard: skip if already running ────────────────────────────────────────────

LOCK_FILE="/tmp/ai-employee-scheduler.lock"
if [ -f "$LOCK_FILE" ]; then
  LOCK_AGE=$(( $(date +%s) - $(date -r "$LOCK_FILE" +%s 2>/dev/null || echo 0) ))
  if [ "$LOCK_AGE" -lt 300 ]; then
    echo "[$TIMESTAMP] [scheduler] Previous run still active (lock age: ${LOCK_AGE}s) — skipping."
    exit 0
  else
    echo "[$TIMESTAMP] [scheduler] Stale lock found (${LOCK_AGE}s old) — removing."
    rm -f "$LOCK_FILE"
  fi
fi
touch "$LOCK_FILE"
trap 'rm -f "$LOCK_FILE"' EXIT

# ── Change to vault directory ──────────────────────────────────────────────────

cd "$VAULT_DIR"
echo "[$TIMESTAMP] [scheduler] Working directory: $(pwd)"

# ── Run process-needs-action ──────────────────────────────────────────────────

NEEDS_ACTION_COUNT=$(find "$VAULT_DIR/Needs_Action" -maxdepth 1 -name "*.md" 2>/dev/null | wc -l | tr -d ' ')

if [ "$NEEDS_ACTION_COUNT" -eq 0 ]; then
  echo "[$TIMESTAMP] [scheduler] Needs_Action is empty — nothing to process."
  exit 0
fi

echo "[$TIMESTAMP] [scheduler] Found $NEEDS_ACTION_COUNT item(s) in Needs_Action — running process-needs-action skill."

# Run Claude with the process-needs-action skill (cd to project root first)
cd "$PROJECT_DIR"
"$CLAUDE" \
  --print "Run the process-needs-action skill" \
  --permission-mode bypassPermissions

echo "[$TIMESTAMP] [scheduler] Run complete."
