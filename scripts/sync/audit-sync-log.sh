#!/usr/bin/env bash
# audit-sync-log.sh — Poll Syncthing REST API and append events to Sync/sync.log.
#
# Polls GET /rest/events?since=<last_id>&types=LocalChangeDetected,RemoteChangeDetected
# every 60 seconds. Appends pipe-delimited lines per data-model.md Sync Log Entry format.
# Stores last processed event ID in scripts/sync/last_event_id to avoid reprocessing.
#
# Usage:
#   ./scripts/sync/audit-sync-log.sh
#
# Environment:
#   VAULT_PATH          — absolute path to vault (default: ./AI_Employee_Vault)
#   SYNCTHING_API_KEY   — Syncthing REST API key (from Syncthing GUI → Settings → API Key)
#   SYNCTHING_HOST      — Syncthing host (default: 127.0.0.1)
#   SYNCTHING_PORT      — Syncthing port (default: 8384)
#   MACHINE_ID          — identifier for this machine (default: hostname)
#   POLL_INTERVAL       — seconds between polls (default: 60)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

VAULT_PATH="${VAULT_PATH:-${PROJECT_ROOT}/AI_Employee_Vault}"
SYNCTHING_HOST="${SYNCTHING_HOST:-127.0.0.1}"
SYNCTHING_PORT="${SYNCTHING_PORT:-8384}"
MACHINE_ID="${MACHINE_ID:-$(hostname)}"
POLL_INTERVAL="${POLL_INTERVAL:-60}"

SYNC_LOG="${VAULT_PATH}/Sync/sync.log"
LAST_ID_FILE="${SCRIPT_DIR}/last_event_id"

# Ensure Sync/ directory and log file exist
mkdir -p "${VAULT_PATH}/Sync"
if [ ! -f "${SYNC_LOG}" ]; then
    echo "# Sync audit log | Format: timestamp|direction|file_path|size_bytes|machine_id|sync_lag_seconds" > "${SYNC_LOG}"
fi

# Load last event ID (0 = start from beginning)
LAST_ID=0
if [ -f "${LAST_ID_FILE}" ]; then
    LAST_ID="$(cat "${LAST_ID_FILE}")"
fi

echo "[audit-sync-log] Starting. VAULT=${VAULT_PATH}, HOST=${SYNCTHING_HOST}:${SYNCTHING_PORT}, MACHINE=${MACHINE_ID}"

while true; do
    if [ -z "${SYNCTHING_API_KEY:-}" ]; then
        echo "[audit-sync-log] WARN: SYNCTHING_API_KEY not set — skipping API poll" >&2
    else
        # Fetch events since last processed ID
        EVENTS_URL="http://${SYNCTHING_HOST}:${SYNCTHING_PORT}/rest/events"
        RESPONSE=$(curl -sf \
            -H "X-API-Key: ${SYNCTHING_API_KEY}" \
            "${EVENTS_URL}?since=${LAST_ID}&types=LocalChangeDetected,RemoteChangeDetected" \
            2>/dev/null || echo "[]")

        # Parse events with jq and append to sync.log
        if command -v jq &>/dev/null && [ "${RESPONSE}" != "[]" ] && [ -n "${RESPONSE}" ]; then
            NEW_MAX_ID=$(echo "${RESPONSE}" | jq -r 'if length > 0 then .[].id | tonumber | . end | max // empty' 2>/dev/null || echo "")

            echo "${RESPONSE}" | jq -r '.[] | [
                (.time // ""),
                (if .type == "RemoteChangeDetected" then "remote->local" else "local->remote" end),
                (.data.path // ""),
                (.data.size // 0 | tostring),
                "'"${MACHINE_ID}"'",
                "0"
            ] | join("|")' 2>/dev/null >> "${SYNC_LOG}" || true

            if [ -n "${NEW_MAX_ID}" ]; then
                echo "${NEW_MAX_ID}" > "${LAST_ID_FILE}"
                LAST_ID="${NEW_MAX_ID}"
            fi
        fi
    fi

    sleep "${POLL_INTERVAL}"
done
