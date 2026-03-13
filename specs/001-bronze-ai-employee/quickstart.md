# Quickstart: Bronze Tier Personal AI Employee

**Branch**: `001-bronze-ai-employee` | **Date**: 2026-03-06

Get the system running end-to-end in under 5 minutes.

---

## Prerequisites

- Windows 11 with WSL2 (Ubuntu)
- Python 3.12+ in WSL2 (`python3 --version`)
- Git
- Obsidian (for viewing the vault)

---

## Step 1 — Clone and enter the repo

```bash
cd ~
git clone <repo-url> "Personal AI Employee"
cd "Personal AI Employee"
```

---

## Step 2 — Create the Python environment

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

---

## Step 3 — Configure environment

```bash
cp .env.example .env
```

Edit `.env`:
```
VAULT_PATH=/mnt/c/Users/<your-name>/Documents/GitHub/Personal AI Employee/AI_Employee_Vault
DRY_RUN=true
```

---

## Step 4 — Open the vault in Obsidian

1. Open Obsidian
2. **Open folder as vault** → select `AI_Employee_Vault/`
3. You should see `Dashboard.md` and `Company_Handbook.md`

---

## Step 5 — Start the watcher

```bash
VAULT_PATH="$PWD/AI_Employee_Vault" .venv/bin/python orchestrator.py
```

Expected output:
```
[Orchestrator] INFO: AI Employee Orchestrator starting (Bronze tier)
[Orchestrator] INFO: Vault path : /mnt/c/.../AI_Employee_Vault
[Orchestrator] INFO: Dry-run    : True
[FilesystemWatcher] INFO: Watching inbox: .../AI_Employee_Vault/Inbox
```

---

## Step 6 — Drop a test file

In a second terminal:

```bash
echo "Test task content" > "/mnt/c/.../AI_Employee_Vault/Inbox/test.txt"
```

Wait 3–5 seconds. In the first terminal you should see:
```
[FilesystemWatcher] INFO: New file detected: test.txt
[FilesystemWatcher] INFO: Created action file: FILE_...test.md
```

Confirm in Obsidian: a new file appears in `Needs_Action/`.

---

## Step 7 — Run Claude to process tasks

In a third terminal:

```bash
claude
```

Then tell Claude:
> "Run the process-needs-action skill"

Claude will:
1. Read `Company_Handbook.md`
2. Process all `.md` files in `Needs_Action/`
3. Create `Plan.md` files in `Plans/`
4. Move processed tasks to `Done/`
5. Update `Dashboard.md`

---

## Step 8 — Verify

Open `Dashboard.md` in Obsidian. You should see:
- Updated timestamp
- Zero items in Needs_Action
- 1 item completed today
- Recent completions summary

Check `Logs/YYYY-MM-DD.json` — every action is recorded.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Watcher starts but no files detected | WSL2 inotify issue — confirm `PollingObserver` is used in `filesystem_watcher.py` |
| `externally-managed-environment` pip error | Use `python3 -m venv .venv` first, then `.venv/bin/pip install` |
| `VAULT_PATH not found` | Set `VAULT_PATH` in `.env` to the absolute path of `AI_Employee_Vault/` |
| Duplicate task files on watcher restart | Check `scripts/processed_inbox.json` — should list already-processed filenames |
