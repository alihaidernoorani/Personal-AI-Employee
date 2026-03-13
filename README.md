# Personal AI Employee

*Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.*

An autonomous Digital FTE (Full-Time Equivalent) powered by **Claude Code** and **Obsidian**.

---

## Architecture

```
Inbox (file drop) ──► Filesystem Watcher ──► Needs_Action/
                                                    │
                                             Claude Code
                                          (process-needs-action skill)
                                                    │
                              ┌─────────────────────┼──────────────────┐
                         Safe actions          Sensitive actions    Errors
                              │                     │                  │
                           Done/           Pending_Approval/    Needs_Action/
                                                    │               ERROR_*
                                           Human approves
                                                    │
                                              Approved/ ──► MCP Action
```

**Perception:** Python Watcher scripts monitor inputs (files, Gmail, WhatsApp) and write structured `.md` files to `Needs_Action/`.

**Reasoning:** Claude Code reads the vault, applies `Company_Handbook.md` rules, and decides what to do.

**Action:** Safe actions execute directly; sensitive ones wait in `Pending_Approval/` for human sign-off before any MCP server acts.

---

## Current Tier: Bronze

| Requirement | Status |
|-------------|--------|
| `AI_Employee_Vault/` with Dashboard + Handbook | Done |
| `/Inbox`, `/Needs_Action`, `/Done` folders | Done |
| Filesystem Watcher script | Done |
| Agent Skill: `process-needs-action` | Done |

---

## Quickstart (8 steps, under 5 minutes)

**Prerequisites:** Windows 11 + WSL2 (Ubuntu), Python 3.12+, Git, Obsidian

### Step 1 — Clone and enter the repo

```bash
git clone <repo-url> "Personal AI Employee"
cd "Personal AI Employee"
```

### Step 2 — Create the Python environment

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### Step 3 — Configure environment

```bash
cp .env.example .env
```

Edit `.env`:
```
VAULT_PATH=/mnt/c/Users/<your-name>/Documents/GitHub/Personal AI Employee/AI_Employee_Vault
DRY_RUN=true
```

### Step 4 — Open the vault in Obsidian

Open Obsidian → **Open folder as vault** → select `AI_Employee_Vault/`

You should see `Dashboard.md` and `Company_Handbook.md`.

### Step 5 — Start the watcher

```bash
VAULT_PATH="$PWD/AI_Employee_Vault" .venv/bin/python orchestrator.py
```

Expected output:
```
[Orchestrator] INFO: AI Employee Orchestrator starting (Bronze tier)
[FilesystemWatcher] INFO: Watching inbox: .../AI_Employee_Vault/Inbox
```

### Step 6 — Drop a test file

In a second terminal:

```bash
echo "Test task content" > "$PWD/AI_Employee_Vault/Inbox/test.txt"
```

Within 3–5 seconds a `FILE_*.md` task file appears in `Needs_Action/`.

### Step 7 — Run Claude to process tasks

In a third terminal:

```bash
claude
```

Then tell Claude:
> "Run the process-needs-action skill"

Claude will:
1. Read `Company_Handbook.md`
2. Process all `.md` files in `Needs_Action/`
3. Create `Plans/PLAN_*.md` for each task
4. Move processed tasks to `Done/`
5. Update `Dashboard.md`

### Step 8 — Verify

Open `Dashboard.md` in Obsidian. You should see:
- Updated timestamp
- Zero items in Needs_Action
- Items completed today
- Recent completions summary

Check `Logs/YYYY-MM-DD.json` — every action is recorded.

### Troubleshooting

| Symptom | Fix |
|---------|-----|
| Watcher starts but no files detected | WSL2 inotify issue — confirm `PollingObserver` is used in `filesystem_watcher.py` |
| `externally-managed-environment` pip error | Use `python3 -m venv .venv` first, then `.venv/bin/pip install` |
| `VAULT_PATH not found` | Set `VAULT_PATH` in `.env` to the absolute path of `AI_Employee_Vault/` |
| Duplicate task files on watcher restart | Check `scripts/processed_inbox.json` — should list already-processed filenames |

---

## Vault Structure

```
AI_Employee_Vault/
├── Dashboard.md          ← Real-time status (updated by Claude after each run)
├── Company_Handbook.md   ← Rules of engagement (edit to change AI behaviour)
├── Inbox/                ← Drop files here; watcher picks them up automatically
├── Needs_Action/         ← Pending items waiting for Claude to process
├── Done/                 ← Completed items (never deleted)
└── Logs/                 ← Audit log (YYYY-MM-DD.json, one JSON line per action)
```

---

## Submission

- Tier: **Bronze**
