# Implementation Plan: Bronze Tier Personal AI Employee

**Branch**: `001-bronze-ai-employee` | **Date**: 2026-03-06 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-bronze-ai-employee/spec.md`

---

## Summary

Build the minimal foundation of the Personal AI Employee: an Obsidian vault as the
state store, a Python filesystem watcher as the perception layer, and a Claude Code
Agent Skill as the reasoning layer. Incoming files flow Inbox → Needs_Action → Plans
→ Done with every action logged and Dashboard.md kept current.

---

## Technical Context

**Language/Version**: Python 3.12+ (WSL2 Ubuntu)
**Primary Dependencies**: `watchdog>=4.0.0`, `python-dotenv>=1.0.0`
**Storage**: Markdown files in `AI_Employee_Vault/` (no database)
**Testing**: Manual end-to-end validation via file drops and skill invocation
**Target Platform**: Windows 11 Pro + WSL2 (Ubuntu), `/mnt/c` NTFS mount
**Project Type**: Single project (scripts + vault + skills)
**Performance Goals**: File detected within 10 seconds; full 5-task run completes in under 60 seconds
**Constraints**: PollingObserver required (inotify unavailable on NTFS); `DRY_RUN=true` default
**Scale/Scope**: Single user, single machine, Bronze tier only

---

## Constitution Check

*GATE: Must pass before implementation. Re-checked after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|---------|
| I. Skills-First & MCP | ✅ PASS | All AI logic in `.claude/skills/process-needs-action/SKILL.md`. Watcher scripts contain zero reasoning logic. |
| II. Folder-Based State Machine | ✅ PASS | Strict one-way flow: `Inbox → Needs_Action → Plans → Done`. No skipping. |
| III. HITL Safety | ✅ PASS | Plans include `[ ] APPROVE` gates. Bronze has no external comms, so no sensitive actions fire automatically. |
| IV. Proactive Business Intelligence | N/A | CEO Briefing is a Gold tier concern. Not in scope for Bronze. |
| V. Security & Operations | ✅ PASS | `.env` for secrets, `DRY_RUN=true` default, `PollingObserver` for WSL2, forward-slash paths throughout. |

No violations. Gate passed.

---

## Project Structure

### Documentation (this feature)

```text
specs/001-bronze-ai-employee/
├── spec.md              # Feature requirements
├── plan.md              # This file
├── research.md          # Phase 0 — technology decisions
├── data-model.md        # Phase 1 — entities and state machine
├── quickstart.md        # Phase 1 — setup and verification guide
├── contracts/
│   ├── task-file-schema.md     # Task File YAML + body contract
│   ├── plan-file-schema.md     # Plan File YAML + body contract
│   └── log-entry-schema.md     # Audit log NDJSON schema
└── checklists/
    └── requirements.md  # Spec quality checklist (all pass)
```

### Source Code (repository root)

```text
AI_Employee_Vault/           # Obsidian vault — all runtime state
├── Dashboard.md
├── Company_Handbook.md
├── Inbox/
├── Needs_Action/
├── Plans/
├── Done/
└── Logs/

watchers/                    # Perception layer (pure I/O, no AI logic)
├── base_watcher.py          # Abstract base: run loop, audit logging
└── filesystem_watcher.py    # PollingObserver on Inbox/

.claude/skills/
└── process-needs-action/
    └── SKILL.md             # All AI reasoning — reads handbook, processes tasks

scripts/
└── processed_inbox.json     # Idempotency registry (watcher writes here)

orchestrator.py              # Entry point — loads .env, starts watcher
requirements.txt             # watchdog, python-dotenv
.env.example                 # Template — copy to .env
.gitignore                   # Excludes .env, .venv, __pycache__, sessions
```

**Structure Decision**: Single project at repository root. Vault lives alongside
Python code. No `src/` indirection needed — the codebase is small and the vault
is the primary artefact, not the Python scripts.

---

## Implementation Phases

### Phase 1 — Project Setup

**Objective**: Repository initialised with correct folder structure and Python environment.

**Components**:
- Repository root with `.gitignore`, `.env.example`, `requirements.txt`
- Python virtualenv at `.venv/`
- `scripts/` directory with empty `processed_inbox.json`

**Dependencies**: None.

**Verification**:
- `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt` exits 0
- `.env` exists (copied from `.env.example`) with `VAULT_PATH` set and `DRY_RUN=true`
- `.venv/` and `.env` appear in `.gitignore`

---

### Phase 2 — Vault Initialisation

**Objective**: Obsidian vault `AI_Employee_Vault/` exists with all required folders and core files.

**Components**:
- `AI_Employee_Vault/Dashboard.md` — contains dynamic token placeholders
- `AI_Employee_Vault/Company_Handbook.md` — contains rules of engagement
- Empty directories: `Inbox/`, `Needs_Action/`, `Plans/`, `Done/`, `Logs/`

**Dependencies**: Phase 1 complete.

**Verification**:
- Open `AI_Employee_Vault/` as a vault in Obsidian — renders without errors
- `Dashboard.md` displays with section headings visible
- `Company_Handbook.md` contains all 7 rule sections

---

### Phase 3 — Watcher Implementation

**Objective**: A running Python process detects files dropped in `Inbox/` and creates task `.md` files in `Needs_Action/` within 10 seconds.

**Components**:
- `watchers/base_watcher.py` — abstract base with `run()` loop and `log_action()`
- `watchers/filesystem_watcher.py` — `DropFolderHandler` + `PollingObserver(timeout=3)`
- `orchestrator.py` — loads `.env`, validates vault path, starts `FilesystemWatcher`
- `scripts/processed_inbox.json` — updated on each new detection for idempotency

**Dependencies**: Phase 2 complete.

**Key design decisions** (see `research.md`):
- `PollingObserver` not `InotifyObserver` (R-001)
- Idempotency via `processed_inbox.json` (R-005)
- Temp/hidden files (`.`, `~`) silently skipped

**Verification** (maps to FR-001 through FR-004, SC-001, SC-004):
- Drop a file into `Inbox/` via `bash` `cp` or `echo >`
- Within 10 seconds: companion `.md` task file appears in `Needs_Action/` with valid YAML frontmatter
- Restart watcher; drop the same file again — no duplicate task file created
- `Logs/YYYY-MM-DD.json` contains a `file_drop_detected` entry

---

### Phase 4 — Claude Task Processing

**Objective**: Invoking the `process-needs-action` skill causes Claude to read `Company_Handbook.md`, process all `.md` files in `Needs_Action/`, and create `Plans/PLAN_*.md` for each.

**Components**:
- `.claude/skills/process-needs-action/SKILL.md` — full procedural instructions for Claude

**Dependencies**: Phase 3 complete (at least one task file must exist in Needs_Action).

**Key design decisions**:
- Handbook read first (constitution Principle I)
- Tasks sorted by priority before processing (FR-007)
- Plans include `[ ] APPROVE` for sensitive actions (constitution Principle III)
- On error: create `ERROR_*.md`, continue processing (FR-011)

**Verification** (maps to FR-005 through FR-007, FR-011):
- With one task file in Needs_Action, invoke skill
- `Plans/PLAN_*.md` appears with valid frontmatter and at least one checkbox
- A task with `priority: urgent` is processed before `priority: normal` in the same run
- Inject a malformed task file (no frontmatter) — skill creates an `ERROR_*.md` and completes the rest

---

### Phase 5 — Task Completion

**Objective**: After processing, each task file is moved from `Needs_Action/` to `Done/` with a `DONE_` prefix.

**Components**: Handled within `process-needs-action` SKILL.md (Step 4 of the skill).

**Dependencies**: Phase 4 complete.

**Verification** (maps to FR-008, SC-005):
- After skill run: `Needs_Action/` is empty (or contains only ERROR files)
- `Done/` contains `DONE_FILE_*.md` for each processed task
- Original filenames are preserved (only prefix added)
- Manually introduce a processing error for one task — other tasks still complete and appear in Done/

---

### Phase 6 — Dashboard Reporting

**Objective**: `Dashboard.md` is rewritten after every skill run with live counts, active items, and recent completions.

**Components**: Handled within `process-needs-action` SKILL.md (Step 4 of the skill).

**Dependencies**: Phase 5 complete.

**Verification** (maps to FR-009, SC-002, SC-003):
- After skill run: `Dashboard.md` shows updated `last updated` timestamp
- Pending count matches actual `.md` file count in `Needs_Action/`
- Done-today count matches files moved to `Done/` in the current run
- Recent completions lists the processed task with a one-line summary
- Opening `Dashboard.md` in Obsidian: human can determine full vault state without opening any other file

---

## End-to-End Acceptance Flow

The following sequence validates all six phases together:

```
1. Start: orchestrator.py running, Inbox/ empty, Needs_Action/ empty
2. Drop test_invoice.txt into Inbox/              → task file appears in Needs_Action/ (Phase 3)
3. Invoke: "Run the process-needs-action skill"   → Plan appears in Plans/ (Phase 4)
4. Skill completes                                → task moved to Done/ (Phase 5)
5. Skill completes                                → Dashboard.md updated (Phase 6)
6. Restart watcher; re-drop test_invoice.txt      → NO duplicate task created (idempotency)
```

All six steps must pass for Bronze tier to be declared complete.

---

## Complexity Tracking

> No constitution violations were identified. This section is intentionally blank.
