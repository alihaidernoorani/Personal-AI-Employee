# Quickstart: Platinum Tier Deployment

**Feature**: `004-platinum-ai-employee`
**Date**: 2026-06-27
**Prerequisites**: Gold tier fully operational on local machine.

---

## Overview

Platinum adds a cloud VM running a 24/7 cloud agent, connected to your local machine via Syncthing vault sync. This guide covers provisioning the cloud VM, setting up Syncthing, and verifying the system.

Estimated setup time: **45–60 minutes** (first time).

---

## Step 1: Provision the Cloud VM

### 1a. Create the VM

1. Create a Hetzner Cloud account at [console.hetzner.cloud](https://console.hetzner.cloud)
2. Create a new server:
   - **Type**: CX22 (or CX11 for budget)
   - **OS**: Ubuntu 24.04 LTS
   - **Location**: Nuremberg or Falkenstein (EU)
   - **SSH Key**: Add your local machine's public key (`~/.ssh/id_rsa.pub` or `~/.ssh/id_ed25519.pub`)
   - **No password login** (SSH key only)
3. Note the server's public IP address.

### 1b. Add to `.env`

```bash
# Add to .env on local machine:
CLOUD_VM_HOST=<your-cloud-vm-ip>
CLOUD_VM_USER=root
CLOUD_VAULT_PATH=/root/AI_Employee_Vault
STALE_TASK_TIMEOUT_SECONDS=600
```

### 1c. Run the provisioning script

```bash
# From your local machine (WSL2 or Linux terminal):
bash scripts/provision-cloud.sh
```

This script:
- SSHes to the cloud VM
- Installs Python 3.13, pip, git, Syncthing
- Creates the Python virtual environment
- Clones or copies the project codebase
- Creates the `AI_Employee_Vault/` directory structure
- Sets `AGENT_ROLE=cloud` in `/root/.env.cloud`
- Starts `cloud_orchestrator.py` as a systemd service
- Starts `syncthing` as a systemd service

**Verify completion**:
```bash
ssh root@<cloud-vm-ip> 'systemctl status cloud-agent syncthing'
# Both should show: Active: active (running)
```

---

## Step 2: Configure Vault Sync (Syncthing)

### 2a. Run the setup script

```bash
# From local machine:
bash scripts/sync/setup-syncthing.sh
```

This script:
1. Gets your local Syncthing device ID
2. Gets the cloud VM's Syncthing device ID
3. Adds each device to the other via Syncthing REST API
4. Configures folder authority modes (Send-Only / Receive-Only per [vault-sync-protocol.md](contracts/vault-sync-protocol.md))
5. Deploys `.stignore` to vault root on both machines
6. Triggers initial full sync (local → cloud)
7. Runs the post-sync verification test

**Expected output**:
```
Local device ID: XXXX-XXXX-XXXX
Cloud device ID: YYYY-YYYY-YYYY
Configuring 14 folder authority rules...
Initial sync started...
Verification: Writing test file... OK
Verification: Test file found on cloud VM (8s)... OK
Verification: .env NOT present on cloud VM... OK
Setup complete.
```

### 2b. Verify exclusions manually

```bash
ssh root@<cloud-vm-ip> 'ls -la /root/AI_Employee_Vault/.env 2>&1'
# Expected: No such file or directory

ssh root@<cloud-vm-ip> 'ls -la /root/AI_Employee_Vault/scripts/processed_gmail.json 2>&1'
# Expected: No such file or directory (excluded by .stignore)
```

---

## Step 3: Create New Vault Folders

```bash
# On local machine (these sync to cloud automatically):
mkdir -p AI_Employee_Vault/Updates
mkdir -p AI_Employee_Vault/Signals
mkdir -p AI_Employee_Vault/In_Progress/cloud
mkdir -p AI_Employee_Vault/Sync

# Rename existing In_Progress folder (only if empty):
ls AI_Employee_Vault/In_Progress/local_agent/  # Must be empty
mv AI_Employee_Vault/In_Progress/local_agent AI_Employee_Vault/In_Progress/local
```

---

## Step 4: Verify Cloud Agent is Running

### 4a. Check heartbeat

Wait 5–6 minutes after cloud agent starts, then:

```bash
ls AI_Employee_Vault/Updates/HEARTBEAT_*.md
# Should show at least one file

cat AI_Employee_Vault/Updates/HEARTBEAT_*.md | head -20
# Should show: agent_id: cloud_agent, watcher_status: all running
```

### 4b. Check Dashboard

Open `AI_Employee_Vault/Dashboard.md` in Obsidian. Look for:

```
## Cloud Agent Status
- **Status**: ONLINE
- **Last Heartbeat**: <recent timestamp>
```

### 4c. Check vault sync

```bash
tail -5 AI_Employee_Vault/Sync/sync.log
# Should show recent entries with status=ok
```

---

## Step 5: Run the End-to-End Test

```bash
# Send a test email to the monitored Gmail account
# Subject: "[PLATINUM TEST] Hello from external"

# Wait 5 minutes for cloud agent to detect and triage

# Check for cloud-prepared plan:
ls AI_Employee_Vault/Plans/PLAN_*.md
# Should show a new plan file

# Check for approval:
ls AI_Employee_Vault/Pending_Approval/APPROVAL_*.md
# Should show an approval file (if sender is unknown contact)

# Approve it:
# Move the APPROVAL_*.md to Approved/ in Obsidian, or:
mv AI_Employee_Vault/Pending_Approval/APPROVAL_*.md AI_Employee_Vault/Approved/

# Wait for local approval_watcher.py to execute:
# Check audit log:
tail -1 AI_Employee_Vault/Logs/*.json
# Should show email_send action with result: success (or dry_run if DRY_RUN=true)
```

---

## Step 6: Run Constitution Check

```bash
# In Claude Code on local machine:
# Invoke the constitution-check skill:
# "Run the constitution-check skill"

# Or wait for the next CEO briefing which will include the compliance report.
```

Expected output: `Briefings/COMPLIANCE_REPORT_<date>.md` with 15 principle results.

**Note**: Principles IX and XV will initially FAIL due to pre-existing oversized files (odoo-mcp, social-mcp, gmail_api_watcher). Fix these before re-running (see [research.md](research.md) Pre-existing Violations section).

---

## Environment Variables Reference

| Variable | Machine | Description | Example |
|----------|---------|-------------|---------|
| `VAULT_PATH` | Local | Path to Obsidian vault | `/mnt/c/Users/DELL/Documents/AI_Employee_Vault` |
| `AGENT_ROLE` | Cloud | Activates cloud mode | `cloud` |
| `CLOUD_VM_HOST` | Local | Cloud VM IP or hostname | `1.2.3.4` |
| `CLOUD_VM_USER` | Local | SSH user on cloud VM | `root` |
| `CLOUD_VAULT_PATH` | Local | Vault path on cloud VM | `/root/AI_Employee_Vault` |
| `STALE_TASK_TIMEOUT_SECONDS` | Both | Stale task threshold | `600` |
| `SYNCTHING_API_KEY` | Each machine (own) | Syncthing REST API key | `<auto-generated>` |
| `DRY_RUN` | Both | Dry-run mode | `true` (default) |

---

## Troubleshooting

### Cloud Agent OFFLINE

**Symptom**: Dashboard shows `Status: OFFLINE`; no new HEARTBEAT files in `Updates/`

**Check commands**:
```bash
ssh root@<cloud-vm-ip> 'systemctl status cloud-agent'
ssh root@<cloud-vm-ip> 'journalctl -u cloud-agent -n 50 --no-pager'
ssh root@<cloud-vm-ip> 'ls /root/AI_Employee_Vault/Updates/HEARTBEAT_*.md | tail -3'
```

**Fix**:
```bash
ssh root@<cloud-vm-ip> 'systemctl restart cloud-agent'
# If fails: check /root/.env.cloud exists and has AGENT_ROLE=cloud, VAULT_PATH
ssh root@<cloud-vm-ip> 'cat /root/.env.cloud'
# Re-run provisioning if environment is corrupt:
bash scripts/provision-cloud.sh
```

---

### Vault Sync Stalled

**Symptom**: `Signals/SYNC_STALLED_*.md` appears; files not propagating between machines

**Check commands**:
```bash
tail -5 AI_Employee_Vault/Sync/sync.log
ssh root@<cloud-vm-ip> 'systemctl status syncthing-cloud'
# Check Syncthing REST API on local (port 8384 default):
curl -H "X-API-Key: $SYNCTHING_API_KEY" http://localhost:8384/rest/system/status
```

**Fix**:
```bash
# Restart Syncthing on local (Windows):
Restart-Service SyncThing  # or via Syncthing tray icon
# Restart on cloud:
ssh root@<cloud-vm-ip> 'systemctl restart syncthing-cloud'
# Re-run setup if folder config is lost:
bash scripts/sync/setup-syncthing.sh
```

---

### .env Leaked to Cloud VM

**Symptom**: `security-boundary-test.sh` shows FAIL for `.env file under /root/`

**Check**:
```bash
ssh root@<cloud-vm-ip> 'find /root/ -name ".env" -not -name ".env.cloud" 2>/dev/null'
```

**Fix** (URGENT — security incident):
```bash
# 1. Delete the leaked file immediately:
ssh root@<cloud-vm-ip> 'rm -f /root/AI_Employee_Vault/.env'
# 2. Verify .stignore is deployed:
ssh root@<cloud-vm-ip> 'cat /root/AI_Employee_Vault/.stignore | grep .env'
# 3. If .stignore is missing, redeploy:
bash scripts/sync/setup-syncthing.sh
# 4. Rotate any credentials that may have been exposed
```

---

### Stale Task Not Recovered

**Symptom**: File stuck in `In_Progress/cloud/` for > STALE_TASK_TIMEOUT_SECONDS

**Check**:
```bash
ls -la AI_Employee_Vault/In_Progress/cloud/
ssh root@<cloud-vm-ip> 'systemctl status cloud-agent'
ssh root@<cloud-vm-ip> 'pgrep -af stale_task_monitor'
# Check the stale task monitor logs:
ssh root@<cloud-vm-ip> 'journalctl -u cloud-agent -n 100 | grep stale'
```

**Fix**:
```bash
# If cloud agent is dead: stale monitor on LOCAL watches In_Progress/cloud/
# Check local orchestrator started stale_task_monitor for cloud/:
pgrep -af stale_task_monitor
# If not running: restart local orchestrator
python orchestrator.py
# Manual recovery (last resort):
mv AI_Employee_Vault/In_Progress/cloud/STALE_TASK.md AI_Employee_Vault/Needs_Action/
```

---

### Constitution Check Failing (File Size)

**Symptom**: Principle IX/XV shows FAIL; oversized files listed

**Check**:
```bash
wc -l mcp-servers/odoo-mcp/server.py \
       mcp-servers/social-mcp/server.py \
       watchers/gmail_api_watcher.py
# Expected after T031-T033 splits: all ≤ 300 lines
```

**Fix**:
```bash
# Files should already be split per T031-T033.
# If server.py still shows 636 lines, the split tasks were not completed.
# Re-run: /sp.implement tasks T031 T032 T033
wc -l mcp-servers/odoo-mcp/server.py       # Should be ~90 lines
wc -l mcp-servers/social-mcp/server.py     # Should be ~100 lines
wc -l watchers/gmail_api_watcher.py        # Should be ~250 lines
```

---

### Single-Writer Violation Signal

**Symptom**: `Signals/SINGLE_WRITER_VIOLATION_*.md` appears

**Check**:
```bash
cat AI_Employee_Vault/Signals/SINGLE_WRITER_VIOLATION_*.md
# Note the attempted_path field
```

**Fix**:
```bash
# Find the cloud-side code that attempted the write:
grep -rn "Dashboard.md\|Done/\|Approved/\|Rejected/" \
     watchers/ cloud_orchestrator.py .claude/skills/cloud-triage/
# All cloud vault writes must go through safe_vault_write():
# from watchers.cloud_boundary import safe_vault_write
```

---

### Odoo Health Check Failing

**Symptom**: `Signals/SIGNAL_odoo_down_*.md` appears; ODOO_DRAFT tasks skipped

**Check**:
```bash
ssh root@<cloud-vm-ip> 'docker compose -f /root/odoo/docker-compose.yml ps'
ssh root@<cloud-vm-ip> 'curl -sf http://localhost:8069/web/health && echo OK'
ssh root@<cloud-vm-ip> 'docker compose -f /root/odoo/docker-compose.yml logs odoo | tail -20'
```

**Fix**:
```bash
ssh root@<cloud-vm-ip> 'docker compose -f /root/odoo/docker-compose.yml restart'
# Wait 60s then check health again
ssh root@<cloud-vm-ip> 'curl -sf http://localhost:8069/web/health && echo OK'
```
