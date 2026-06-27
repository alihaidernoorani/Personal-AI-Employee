#!/usr/bin/env bash
# backup-odoo.sh — Daily Odoo PostgreSQL backup with 7-day retention.
# Install via provision-cloud.sh cron: "5 0 * * * root /root/.../backup-odoo.sh"
set -euo pipefail

BACKUP_DIR="/opt/odoo-backups"
ODOO_DB="${ODOO_DB:-odoo}"
ODOO_DB_USER="${ODOO_DB_USER:-odoo}"
VAULT_PATH="${VAULT_PATH:-/root/AI_Employee_Vault}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/odoo_${TIMESTAMP}.dump"

# Load env if available
[ -f "/root/.env.cloud" ] && source /root/.env.cloud 2>/dev/null || true

mkdir -p "$BACKUP_DIR"

# Perform backup
if ! pg_dump --format=custom --username="$ODOO_DB_USER" --host=127.0.0.1 "$ODOO_DB" > "$BACKUP_FILE"; then
    TS=$(date -u +%Y%m%dT%H%M%SZ)
    SIGNAL_FILE="$VAULT_PATH/Signals/SIGNAL_backup_failed_$(date +%s).md"
    mkdir -p "$VAULT_PATH/Signals"
    cat > "$SIGNAL_FILE" <<EOF
---
signal_type: backup_failed
severity: warning
created: $TS
agent_id: cloud_agent
requires_human_action: true
---

# Backup Failed

Odoo PostgreSQL backup failed at $TS.

**Command**: pg_dump --format=custom $ODOO_DB
**Backup file**: $BACKUP_FILE

Check PostgreSQL connectivity and disk space, then re-run manually.
EOF
    echo "ERROR: Backup failed — signal written to $SIGNAL_FILE" >&2
    exit 1
fi

echo "Backup complete: $BACKUP_FILE ($(du -sh "$BACKUP_FILE" | cut -f1))"

# Delete backups older than 7 days
find "$BACKUP_DIR" -name "odoo_*.dump" -mtime +7 -delete
echo "Retention cleanup: removed backups older than 7 days"
