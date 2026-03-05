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

## Setup

### 1. Install dependencies

```bash
# Using uv (recommended)
uv venv && uv pip install -r requirements.txt

# Or plain pip
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — set VAULT_PATH to the absolute path of AI_Employee_Vault/
```

### 3. Open the vault in Obsidian

Open Obsidian → "Open folder as vault" → select `AI_Employee_Vault/`.

### 4. Start the watcher

```bash
python orchestrator.py
```

The watcher monitors `AI_Employee_Vault/Inbox/`. Drop any file there and it will appear in `Needs_Action/` as a structured `.md` file.

### 5. Run Claude Code on the vault

In a second terminal:

```bash
claude
```

Then trigger the skill:
> "Run the process-needs-action skill"

Claude will read `Needs_Action/`, process each item per `Company_Handbook.md` rules, update `Dashboard.md`, and move completed files to `Done/`.

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
