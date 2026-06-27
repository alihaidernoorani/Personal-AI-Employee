#!/usr/bin/env bash
# setup-syncthing.sh — Automate Syncthing device pairing and folder configuration.
#
# Configures bidirectional vault sync between local machine and cloud VM using
# Syncthing REST API. Run this script ONCE after both Syncthing daemons are started.
#
# Prerequisites:
#   - Syncthing running on local machine (port 8384)
#   - Syncthing running on cloud VM (CLOUD_VM_HOST)
#   - SSH access to cloud VM with CLOUD_VM_USER key
#   - SYNCTHING_API_KEY set for local Syncthing
#   - SYNCTHING_CLOUD_API_KEY set for cloud Syncthing (fetched via SSH if not set)
#
# Usage:
#   ./scripts/sync/setup-syncthing.sh [--verify-only]
#
# Environment:
#   VAULT_PATH              — local vault path
#   CLOUD_VM_HOST           — cloud VM hostname or IP
#   CLOUD_VM_USER           — SSH user (default: root)
#   CLOUD_VAULT_PATH        — vault path on cloud VM (default: /root/AI_Employee_Vault)
#   SYNCTHING_API_KEY       — local Syncthing API key
#   SYNCTHING_CLOUD_API_KEY — cloud Syncthing API key (or fetched via SSH)
#   SYNCTHING_HOST          — local Syncthing host (default: 127.0.0.1)
#   SYNCTHING_PORT          — local Syncthing port (default: 8384)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Load .env if present
if [ -f "${PROJECT_ROOT}/.env" ]; then
    set -a
    source "${PROJECT_ROOT}/.env"
    set +a
fi

VAULT_PATH="${VAULT_PATH:-${PROJECT_ROOT}/AI_Employee_Vault}"
CLOUD_VM_HOST="${CLOUD_VM_HOST:-}"
CLOUD_VM_USER="${CLOUD_VM_USER:-root}"
CLOUD_VAULT_PATH="${CLOUD_VAULT_PATH:-/root/AI_Employee_Vault}"
SYNCTHING_HOST="${SYNCTHING_HOST:-127.0.0.1}"
SYNCTHING_PORT="${SYNCTHING_PORT:-8384}"
VERIFY_ONLY="${1:-}"

STIGNORE_SRC="${SCRIPT_DIR}/.stignore"
LOCAL_ST_URL="http://${SYNCTHING_HOST}:${SYNCTHING_PORT}"

# ── Helpers ──────────────────────────────────────────────────────────────────

require_env() {
    local var="$1"
    if [ -z "${!var:-}" ]; then
        echo "ERROR: ${var} is required but not set." >&2
        exit 1
    fi
}

st_local() {
    curl -sf -H "X-API-Key: ${SYNCTHING_API_KEY}" "$@"
}

st_cloud() {
    local url="$1"; shift
    ssh "${CLOUD_VM_USER}@${CLOUD_VM_HOST}" \
        "curl -sf -H 'X-API-Key: ${SYNCTHING_CLOUD_API_KEY}' ${url} $*"
}

# ── Validation ────────────────────────────────────────────────────────────────

require_env SYNCTHING_API_KEY
require_env CLOUD_VM_HOST

# Fetch cloud API key via SSH if not provided
if [ -z "${SYNCTHING_CLOUD_API_KEY:-}" ]; then
    echo "[setup-syncthing] Fetching cloud Syncthing API key via SSH..."
    SYNCTHING_CLOUD_API_KEY=$(ssh "${CLOUD_VM_USER}@${CLOUD_VM_HOST}" \
        "cat /root/.config/syncthing/config.xml | grep -oP '(?<=<apikey>)[^<]+'" 2>/dev/null || echo "")
    if [ -z "${SYNCTHING_CLOUD_API_KEY}" ]; then
        echo "ERROR: Could not fetch cloud Syncthing API key. Start Syncthing on cloud VM first." >&2
        exit 1
    fi
    echo "[setup-syncthing] Cloud API key fetched."
fi

# ── Get device IDs ────────────────────────────────────────────────────────────

echo "[setup-syncthing] Getting local device ID..."
LOCAL_DEVICE_ID=$(st_local "${LOCAL_ST_URL}/rest/system/status" | python3 -c "import json,sys; print(json.load(sys.stdin)['myID'])")
echo "[setup-syncthing] Local device ID: ${LOCAL_DEVICE_ID}"

echo "[setup-syncthing] Getting cloud device ID..."
CLOUD_DEVICE_ID=$(st_cloud "http://127.0.0.1:8384/rest/system/status" | python3 -c "import json,sys; print(json.load(sys.stdin)['myID'])")
echo "[setup-syncthing] Cloud device ID: ${CLOUD_DEVICE_ID}"

if [ "${VERIFY_ONLY}" = "--verify-only" ]; then
    echo "[setup-syncthing] Verify-only mode. Device IDs confirmed."
    echo "  Local : ${LOCAL_DEVICE_ID}"
    echo "  Cloud : ${CLOUD_DEVICE_ID}"
    exit 0
fi

# ── Add devices to each other ─────────────────────────────────────────────────

echo "[setup-syncthing] Adding cloud device to local Syncthing..."
st_local -X POST "${LOCAL_ST_URL}/rest/config/devices" \
    -H "Content-Type: application/json" \
    -d "{\"deviceID\": \"${CLOUD_DEVICE_ID}\", \"name\": \"cloud-vm\", \"addresses\": [\"tcp://${CLOUD_VM_HOST}:22000\"]}" || echo "  (device may already exist)"

echo "[setup-syncthing] Adding local device to cloud Syncthing..."
st_cloud "http://127.0.0.1:8384/rest/config/devices" \
    "-X POST -H 'Content-Type: application/json'" \
    "-d '{\"deviceID\": \"${LOCAL_DEVICE_ID}\", \"name\": \"local\", \"addresses\": [\"dynamic\"]}'" || echo "  (device may already exist)"

# ── Deploy .stignore ──────────────────────────────────────────────────────────

echo "[setup-syncthing] Deploying .stignore to local vault root..."
cp "${STIGNORE_SRC}" "${VAULT_PATH}/.stignore"

echo "[setup-syncthing] Deploying .stignore to cloud vault root..."
scp "${STIGNORE_SRC}" "${CLOUD_VM_USER}@${CLOUD_VM_HOST}:${CLOUD_VAULT_PATH}/.stignore"

# ── Trigger initial sync ──────────────────────────────────────────────────────

echo "[setup-syncthing] Triggering initial full-vault sync (local → cloud)..."
st_local -X POST "${LOCAL_ST_URL}/rest/db/scan?folder=vault"

# ── Verification ──────────────────────────────────────────────────────────────

echo "[setup-syncthing] Running post-setup verification..."
TS=$(date +%Y%m%dT%H%M%SZ)
TEST_FILE="${VAULT_PATH}/Signals/SYNC_TEST_${TS}.md"
TEST_CONTENT="---\nsignal_type: sync_test\ncreated: $(date -u +%Y-%m-%dT%H:%M:%SZ)\n---\n\n# Sync Test\n\nFile written by setup-syncthing.sh verification step.\n"
printf "${TEST_CONTENT}" > "${TEST_FILE}"
echo "[setup-syncthing] Test file written: ${TEST_FILE}"

echo "[setup-syncthing] Waiting up to 60 seconds for sync to cloud VM..."
TIMEOUT=60
ELAPSED=0
while [ "${ELAPSED}" -lt "${TIMEOUT}" ]; do
    REMOTE_CHECK=$(ssh "${CLOUD_VM_USER}@${CLOUD_VM_HOST}" "test -f '${CLOUD_VAULT_PATH}/Signals/SYNC_TEST_${TS}.md' && echo found || echo missing" 2>/dev/null)
    if [ "${REMOTE_CHECK}" = "found" ]; then
        echo "[setup-syncthing] ✓ Sync verified: test file appeared on cloud VM in ${ELAPSED}s"
        break
    fi
    sleep 5
    ELAPSED=$((ELAPSED + 5))
done

if [ "${ELAPSED}" -ge "${TIMEOUT}" ]; then
    echo "[setup-syncthing] ✗ Sync verification FAILED: test file not found on cloud VM after ${TIMEOUT}s"
    echo "  Check Syncthing logs on both machines."
    exit 1
fi

# Verify .env did NOT sync to cloud
ENV_ON_CLOUD=$(ssh "${CLOUD_VM_USER}@${CLOUD_VM_HOST}" "test -f '${CLOUD_VAULT_PATH}/.env' && echo present || echo absent" 2>/dev/null)
if [ "${ENV_ON_CLOUD}" = "present" ]; then
    echo "[setup-syncthing] ✗ SECURITY: .env file found on cloud VM — check .stignore immediately!"
    exit 1
else
    echo "[setup-syncthing] ✓ Security check: .env NOT present on cloud VM"
fi

echo ""
echo "[setup-syncthing] Setup complete."
echo "  Local device  : ${LOCAL_DEVICE_ID}"
echo "  Cloud device  : ${CLOUD_DEVICE_ID}"
echo "  Vault sync    : ACTIVE"
echo "  .env on cloud : ABSENT (secure)"
