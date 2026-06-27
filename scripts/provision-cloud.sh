#!/usr/bin/env bash
# provision-cloud.sh — Idempotent provisioning for Hetzner CX22 / Ubuntu 24.04 LTS.
# Run once on a fresh VM: bash provision-cloud.sh
# Requires: CLOUD_REPO_URL, VAULT_PATH, ODOO_URL env vars set in /root/.env.cloud
# Designed to be re-run safely without data loss.
set -euo pipefail

REPO_URL="${CLOUD_REPO_URL:-https://github.com/ali-haider/Personal_AI_Employee.git}"
PROJECT_DIR="/root/Personal_AI_Employee"
VENV_DIR="/root/.venv"
VAULT_PATH_DEFAULT="/root/AI_Employee_Vault"
ENV_FILE="/root/.env.cloud"

log() { echo "[provision] $*"; }

# --------------------------------------------------------------------------
# Step 1: System dependencies
# --------------------------------------------------------------------------
log "Installing system dependencies..."
apt-get update -qq
apt-get install -y -qq \
    python3.13 python3.13-venv python3.13-dev \
    python3-pip \
    git rsync curl jq \
    nginx certbot python3-certbot-nginx \
    docker.io docker-compose-plugin \
    ca-certificates gnupg \
    apt-transport-https

# --------------------------------------------------------------------------
# Step 2: Install Syncthing
# --------------------------------------------------------------------------
log "Installing Syncthing..."
if ! command -v syncthing &>/dev/null; then
    mkdir -p /etc/apt/keyrings
    curl -L -o /tmp/syncthing.gpg https://syncthing.net/release-key.gpg
    gpg --dearmor < /tmp/syncthing.gpg > /etc/apt/keyrings/syncthing-archive-keyring.gpg
    echo "deb [signed-by=/etc/apt/keyrings/syncthing-archive-keyring.gpg] https://apt.syncthing.net/ syncthing stable" \
        > /etc/apt/sources.list.d/syncthing.list
    apt-get update -qq
    apt-get install -y -qq syncthing
fi

# --------------------------------------------------------------------------
# Step 3: Clone or update project repository
# --------------------------------------------------------------------------
log "Setting up project repository..."
if [ -d "$PROJECT_DIR/.git" ]; then
    git -C "$PROJECT_DIR" pull --ff-only
else
    git clone "$REPO_URL" "$PROJECT_DIR"
fi

# --------------------------------------------------------------------------
# Step 4: Python virtualenv + dependencies
# --------------------------------------------------------------------------
log "Creating Python virtualenv..."
if [ ! -f "$VENV_DIR/bin/python" ]; then
    python3.13 -m venv "$VENV_DIR"
fi
"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet -r "$PROJECT_DIR/requirements.txt"

# --------------------------------------------------------------------------
# Step 5: Create vault folder structure
# --------------------------------------------------------------------------
log "Creating vault folders..."
VAULT="${VAULT_PATH_DEFAULT}"
for folder in \
    Inbox Needs_Action Plans Pending_Approval Approved Rejected Done Briefings \
    Accounting Logs Updates Signals Sync \
    "In_Progress/cloud" "In_Progress/local"; do
    mkdir -p "$VAULT/$folder"
    touch "$VAULT/$folder/.gitkeep" 2>/dev/null || true
done

# --------------------------------------------------------------------------
# Step 6: Write /root/.env.cloud (idempotent — only creates if missing)
# --------------------------------------------------------------------------
log "Configuring environment..."
if [ ! -f "$ENV_FILE" ]; then
    cat > "$ENV_FILE" <<EOF
AGENT_ROLE=cloud
VAULT_PATH=${VAULT}
STALE_TASK_TIMEOUT_SECONDS=600
DRY_RUN=false
ODOO_DRAFT_ONLY=true
SYNCTHING_API_KEY=
CLOUD_VM_HOST=
CLOUD_VM_USER=root
CLOUD_VAULT_PATH=${VAULT}
EOF
    log "Created $ENV_FILE — edit to add SYNCTHING_API_KEY and credentials"
fi

# --------------------------------------------------------------------------
# Step 7: Install systemd services
# --------------------------------------------------------------------------
log "Installing systemd services..."
cp "$PROJECT_DIR/scripts/systemd/cloud-agent.service" /etc/systemd/system/
cp "$PROJECT_DIR/scripts/systemd/syncthing-cloud.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable cloud-agent syncthing-cloud

# --------------------------------------------------------------------------
# Step 8: Odoo deployment (see scripts/odoo/)
# --------------------------------------------------------------------------
log "Setting up Odoo..."
mkdir -p /opt/odoo-backups
if [ -f "$PROJECT_DIR/scripts/odoo/docker-compose.yml" ]; then
    mkdir -p /root/odoo
    cp "$PROJECT_DIR/scripts/odoo/docker-compose.yml" /root/odoo/
    docker compose -f /root/odoo/docker-compose.yml up -d || \
        log "WARNING: Odoo docker compose failed — check logs with: docker compose -f /root/odoo/docker-compose.yml logs"

    # Wait for Odoo health check (max 2 min)
    log "Waiting for Odoo to be healthy..."
    for i in $(seq 1 24); do
        if curl -sf http://localhost:8069/web/health &>/dev/null; then
            log "Odoo health check PASS"
            break
        fi
        sleep 5
    done
fi

# Install backup cron
BACKUP_CRON="5 0 * * * root /root/Personal_AI_Employee/scripts/odoo/backup-odoo.sh >> /var/log/odoo-backup.log 2>&1"
if ! grep -qF "backup-odoo.sh" /etc/cron.d/odoo-backup 2>/dev/null; then
    echo "$BACKUP_CRON" > /etc/cron.d/odoo-backup
    chmod 644 /etc/cron.d/odoo-backup
fi

# --------------------------------------------------------------------------
# Step 9: Start services
# --------------------------------------------------------------------------
log "Starting services..."
systemctl start syncthing-cloud || log "WARNING: syncthing-cloud start failed"
systemctl start cloud-agent || log "WARNING: cloud-agent start failed"

# --------------------------------------------------------------------------
# Step 10: Smoke test
# --------------------------------------------------------------------------
log "Running smoke test..."
TS=$(date -u +%Y%m%dT%H%M%SZ)
SMOKE_FILE="$VAULT/Needs_Action/PROVISION_SMOKE_TEST_${TS}.md"
cat > "$SMOKE_FILE" <<EOF
---
type: smoke_test
priority: high
received: $(date -u +%Y-%m-%dT%H:%M:%SZ)
status: pending
---

# Provision Smoke Test

Created by provision-cloud.sh at ${TS}. Cloud agent should claim this file
within 2 minutes (move to In_Progress/cloud/).
EOF
log "Smoke test file created: $SMOKE_FILE"

# Wait up to 2 min for cloud agent to claim it
log "Waiting for cloud agent to claim smoke test task..."
for i in $(seq 1 24); do
    if ls "$VAULT/In_Progress/cloud/PROVISION_SMOKE_TEST_${TS}.md" &>/dev/null; then
        log "Smoke test PASS — cloud agent claimed task within $((i * 5)) seconds"
        break
    fi
    sleep 5
done

if ! ls "$VAULT/In_Progress/cloud/PROVISION_SMOKE_TEST_${TS}.md" &>/dev/null; then
    log "WARNING: Cloud agent did not claim smoke test task within 2 minutes"
    log "Check: systemctl status cloud-agent && journalctl -u cloud-agent -n 50"
fi

# --------------------------------------------------------------------------
# Step 11: Security boundary verification
# --------------------------------------------------------------------------
log "Running security boundary test..."
if [ -f "$PROJECT_DIR/scripts/sync/security-boundary-test.sh" ]; then
    chmod +x "$PROJECT_DIR/scripts/sync/security-boundary-test.sh"
    if ! "$PROJECT_DIR/scripts/sync/security-boundary-test.sh"; then
        log "SECURITY BOUNDARY: FAIL — review output above before going live"
        exit 1
    fi
fi

log "=== Provisioning complete ==="
log "Next steps:"
log "  1. Edit $ENV_FILE to add API credentials"
log "  2. Run: systemctl status cloud-agent syncthing-cloud"
log "  3. Configure Syncthing: scripts/sync/setup-syncthing.sh"
log "  4. Verify TLS: certbot --nginx -d <your-domain>"
