---
description: "Task list for Bronze Tier Personal AI Employee"
---

# Tasks: Bronze Tier Personal AI Employee Foundation

**Input**: Design documents from `/specs/001-bronze-ai-employee/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: No TDD tasks — validation is manual end-to-end (as specified in plan.md).

**Organization**: Tasks grouped by User Story to enable independent implementation and testing.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Repo skeleton, Python environment, and idempotency registry in place.

- [X] T001 Create `.gitignore` at repo root — exclude `.env`, `.venv/`, `__pycache__/`, `*.session`, `whatsapp_session/`
- [X] T002 Create `requirements.txt` at repo root with `watchdog>=4.0.0` and `python-dotenv>=1.0.0`
- [X] T003 Create `.env.example` at repo root with `VAULT_PATH=` and `DRY_RUN=true` placeholders
- [X] T004 [P] Create Python virtual environment: `python3 -m venv .venv` and install deps: `.venv/bin/pip install -r requirements.txt`
- [X] T005 [P] Create `scripts/` directory and initialise `scripts/processed_inbox.json` with `{"processed": []}`

---

## Phase 2: Foundational (Vault Structure — Blocking Prerequisite)

**Purpose**: Obsidian vault must exist before any watcher or skill can function.

**⚠️ CRITICAL**: User Story work cannot begin until this phase is complete.

- [X] T006 Create `AI_Employee_Vault/` directory with all five sub-folders: `Inbox/`, `Needs_Action/`, `Plans/`, `Done/`, `Logs/`
- [X] T007 [P] Create `AI_Employee_Vault/Dashboard.md` — include these exact dynamic token comments: `<!-- AI_EMPLOYEE:UPDATED -->`, `<!-- AI_EMPLOYEE:NEEDS_ACTION_COUNT -->`, `<!-- AI_EMPLOYEE:DONE_TODAY_COUNT -->`, `<!-- AI_EMPLOYEE:INBOX_COUNT -->`, `<!-- AI_EMPLOYEE:ACTIVE_ITEMS -->`, `<!-- AI_EMPLOYEE:RECENT_COMPLETIONS -->`, `<!-- AI_EMPLOYEE:PENDING_APPROVALS -->` — each inside a labelled Markdown section (System Status, Inbox Summary, Active Items, Recent Completions, Pending Approvals)
- [X] T008 [P] Create `AI_Employee_Vault/Company_Handbook.md` — must contain all 7 rule sections: Communication Standards, Financial Rules, Human-in-the-Loop Rules, Privacy & Data Rules, Task Prioritization (urgent → high → normal → low), Vault File Conventions, Error Handling

**Checkpoint**: Vault opens in Obsidian without errors. Dashboard and Handbook render correctly.

---

## Phase 3: User Story 1 — Event Captured as Actionable Task (Priority: P1) 🎯 MVP

**Goal**: File dropped in `Inbox/` → task `.md` file appears in `Needs_Action/` within 10 seconds, automatically, with no duplicates on restart.

**Independent Test**: `python3 -m venv .venv && .venv/bin/python orchestrator.py` running; `cp any_file.txt AI_Employee_Vault/Inbox/` via bash; within 10s a corresponding `FILE_*.md` appears in `Needs_Action/` with valid YAML frontmatter.

### Implementation for User Story 1

- [X] T009 [P] [US1] Create `watchers/base_watcher.py` — abstract `BaseWatcher` class with: `__init__(vault_path, check_interval)` setting `self.needs_action` and `self.logs_dir` paths; abstract `check_for_updates() -> list`; abstract `create_action_file(item) -> Path`; concrete `log_action(action_type, target, result, parameters)` that appends one JSON line to `Logs/YYYY-MM-DD.json`; concrete `run()` loop calling `check_for_updates` + `create_action_file` + `log_action` every `check_interval` seconds
- [X] T010 [P] [US1] Create `watchers/filesystem_watcher.py` — `DropFolderHandler(FileSystemEventHandler)` with `on_created` that skips files starting with `.` or `~`; `FilesystemWatcher(BaseWatcher)` with `run()` starting `PollingObserver(timeout=3)` on `AI_Employee_Vault/Inbox/`; `create_action_file(source)` that copies the file to `Needs_Action/FILE_<timestamp>_<stem><ext>` and writes a companion `.md` with YAML frontmatter (`type`, `original_name`, `copied_to`, `size_bytes`, `received`, `priority: normal`, `status: pending`) and a body section with a suggested-actions checklist
- [X] T011 [US1] Add idempotency to `watchers/filesystem_watcher.py` — on startup load `scripts/processed_inbox.json`; in `create_action_file` skip any filename already in the `processed` list and append it after successful creation; save the JSON file after each update
- [X] T012 [US1] Create `orchestrator.py` at repo root — load `.env` via `python-dotenv`; read `VAULT_PATH` and `DRY_RUN` env vars; validate that `VAULT_PATH` exists (log error and `sys.exit(1)` if not); instantiate `FilesystemWatcher(VAULT_PATH)` and call `watcher.run()`

**Checkpoint**: User Story 1 independently testable. Run:
1. `VAULT_PATH="$PWD/AI_Employee_Vault" .venv/bin/python orchestrator.py`
2. In another terminal: `echo "test" > AI_Employee_Vault/Inbox/test.txt`
3. Confirm `Needs_Action/FILE_*.md` appears within 10 seconds with valid YAML
4. Restart watcher; repeat step 2 with same filename; confirm NO duplicate task file

---

## Phase 4: User Story 2 — Claude Analyses Task and Creates a Plan (Priority: P2)

**Goal**: Invoking `process-needs-action` skill causes Claude to read `Company_Handbook.md`, process all pending tasks sorted by priority, and create `Plans/PLAN_*.md` for each with a summary and `[ ]` action checkboxes.

**Independent Test**: Manually place a pre-written `FILE_test.md` (with valid YAML frontmatter) in `Needs_Action/`; tell Claude "Run the process-needs-action skill"; confirm `Plans/PLAN_*.md` appears with at least one `[ ]` checkbox.

### Implementation for User Story 2

- [X] T013 [US2] Create/update `.claude/skills/process-needs-action/SKILL.md` — **Step 1**: read `AI_Employee_Vault/Company_Handbook.md` before processing any task
- [X] T014 [US2] Update `.claude/skills/process-needs-action/SKILL.md` — **Step 2**: list all `.md` files in `Needs_Action/` (skip files starting with `_`); sort by `priority` field (urgent first) then by `received` timestamp ascending
- [X] T015 [US2] Update `.claude/skills/process-needs-action/SKILL.md` — **Step 3 — process each item**: read YAML frontmatter; determine action by `type` (`file_drop` → summarise content; `email` → draft reply per Handbook comms rules; `error` → alert, do not auto-resolve; unknown → flag for human review); write `Plans/PLAN_<timestamp>_<stem>.md` with frontmatter (`type: plan`, `source_task`, `created_at`, `requires_approval`, `status: draft`) and body sections: Summary, Analysis, Actions (using `[ ]` for safe actions and `[ ] APPROVE:` for sensitive actions per Handbook rules), Notes
- [X] T016 [US2] Update `.claude/skills/process-needs-action/SKILL.md` — **Step 3 error path**: if processing a specific file fails, create `AI_Employee_Vault/Needs_Action/ERROR_<timestamp>_<original-stem>.md` describing the failure; log with `"result": "failure"`; continue processing remaining files

**Checkpoint**: User Story 2 independently testable.
1. Place a `FILE_test_invoice.md` (type: file_drop, priority: normal, status: pending) in `Needs_Action/`
2. Tell Claude: "Run the process-needs-action skill"
3. Confirm `Plans/PLAN_*.md` exists with `[ ]` checkboxes and a human-readable summary
4. Place a file with no YAML frontmatter in `Needs_Action/`; re-run skill; confirm `ERROR_*.md` is created and other tasks still process

---

## Phase 5: User Story 3 — Task Moved to Done and Dashboard Updated (Priority: P3)

**Goal**: After Claude creates a Plan, the source task file moves to `Done/` with a `DONE_` prefix, and `Dashboard.md` is rewritten with live counts and recent completions.

**Independent Test**: After a full skill run, confirm `Done/DONE_FILE_*.md` exists and `Dashboard.md` shows the correct pending count (0 if all processed) and a recent-completions entry for the processed task.

### Implementation for User Story 3

- [X] T017 [US3] Update `.claude/skills/process-needs-action/SKILL.md` — **Step 4**: after Plan is written for a task, move the source `.md` file from `Needs_Action/` to `Done/DONE_<original-filename>` (preserve original filename after the prefix)
- [X] T018 [US3] Update `.claude/skills/process-needs-action/SKILL.md` — **Step 5**: after all tasks are processed, rewrite `Dashboard.md` dynamic tokens — replace `<!-- AI_EMPLOYEE:UPDATED -->` with current UTC ISO timestamp; count `.md` files in `Needs_Action/` for `NEEDS_ACTION_COUNT`; count `DONE_*` files modified today for `DONE_TODAY_COUNT`; count files in `Inbox/` for `INBOX_COUNT`; replace `ACTIVE_ITEMS` with bullet list of remaining Needs_Action filenames (or default italic note if empty); replace `RECENT_COMPLETIONS` with last 5 `DONE_*` files listed with one-line summaries; if `Dashboard.md` is missing, create it from scratch with the token structure
- [X] T019 [US3] Update `.claude/skills/process-needs-action/SKILL.md` — **Step 6**: append one NDJSON log entry per processed task to `AI_Employee_Vault/Logs/YYYY-MM-DD.json` using the schema from `contracts/log-entry-schema.md` (`action_type: process_needs_action`, `actor: claude_code`, `approval_status: auto`, `result: success | deferred | failure`)
- [X] T020 [US3] Update `.claude/skills/process-needs-action/SKILL.md` — **Completion signal**: after Dashboard and Logs are updated, output `<promise>TASK_COMPLETE</promise>`

**Checkpoint**: User Story 3 independently testable (requires US1 + US2 complete).
1. Run full end-to-end: orchestrator → drop file → invoke skill
2. Confirm `Done/DONE_FILE_*.md` exists with original filename preserved
3. Confirm `Dashboard.md` shows: updated timestamp, `0` pending, `1` completed today, one entry in Recent Completions
4. Confirm `Logs/YYYY-MM-DD.json` has a `process_needs_action` entry with `"result": "success"`

---

## Phase 6: Polish & End-to-End Validation

**Purpose**: Verify all user stories work together and acceptance criteria from spec.md pass.

- [X] T021 [P] Add `AI_Employee_Vault/Plans/` directory to the vault if not already present (required by SKILL.md Step 3)
- [X] T022 [P] Verify SC-006 — scan all committed files and vault `.md` files: confirm zero API keys, tokens, or credentials appear; confirm `.env` is in `.gitignore` and not tracked by git
- [X] T023 Run the full end-to-end acceptance flow from `plan.md`:
  1. Start `orchestrator.py` with empty `Inbox/` and `Needs_Action/`
  2. Drop `test_invoice.txt` into `Inbox/` → confirm task file in `Needs_Action/` (SC-001: within 10s)
  3. Invoke "Run the process-needs-action skill" → confirm `Plans/PLAN_*.md` created (US2)
  4. Confirm task moved to `Done/DONE_*` (US3 / FR-008)
  5. Confirm `Dashboard.md` updated with counts and recent completion (FR-009 / SC-003)
  6. Restart watcher; re-drop same `test_invoice.txt` → confirm NO duplicate task (SC-004 / FR-004)
- [X] T024 Validate SC-002 — run skill on a vault with 5 pending tasks (create 5 test task files in `Needs_Action/`); confirm all 5 are processed and `Dashboard.md` updated in under 60 seconds
- [X] T025 [P] Update `README.md` with the 8-step quickstart (or confirm it matches `specs/001-bronze-ai-employee/quickstart.md`)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately; T004 and T005 can run in parallel
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories; T007 and T008 can run in parallel
- **User Story 1 (Phase 3)**: Depends on Phase 2 — T009 and T010 can run in parallel; T011 depends on T010; T012 depends on T009 and T010
- **User Story 2 (Phase 4)**: Depends on Phase 3 (needs at least one task file to test); T013–T016 are sequential (all update the same SKILL.md)
- **User Story 3 (Phase 5)**: Depends on Phase 4; T017–T020 are sequential (all update the same SKILL.md)
- **Polish (Phase 6)**: Depends on all user stories complete; T021, T022, T025 can run in parallel

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational — no dependency on other stories ← **START HERE**
- **US2 (P2)**: Can start after US1 is independently verified
- **US3 (P3)**: Can start after US2 is independently verified (US3 builds on US2's Plan output)

### Within Each User Story

- Python files (T009, T010) before orchestrator (T012)
- SKILL.md steps are additive and sequential (T013 → T014 → T015 → T016 → T017 → T018 → T019 → T020)

---

## Parallel Execution Examples

### Phase 1 Setup
```
T004: python3 -m venv .venv          (runs independently)
T005: mkdir scripts && echo {} > ...  (runs independently)
```

### Phase 2 Vault
```
T007: Create Dashboard.md             (different file from T008)
T008: Create Company_Handbook.md      (different file from T007)
```

### Phase 3 Watcher Core
```
T009: Create base_watcher.py          (different file from T010)
T010: Create filesystem_watcher.py    (different file from T009)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational Vault
3. Complete Phase 3: User Story 1 (Watcher)
4. **STOP and VALIDATE**: Drop a file into Inbox; confirm task appears in Needs_Action within 10s
5. Bronze tier is half-done at this point — watcher is independently useful

### Incremental Delivery

1. Setup + Vault → Foundation ready
2. Add Watcher → Test US1 independently → **Watcher works!**
3. Add Skill (Steps 1–3) → Test US2 independently → **Plans appear!**
4. Add Skill (Steps 4–6) → Test US3 independently → **Tasks complete, dashboard updates!**
5. Polish + End-to-End → **Bronze tier complete!**

---

## Notes

- `[P]` = parallelizable (operates on different files, no blocking dependency)
- `[US1/2/3]` maps task to user story for traceability to spec.md acceptance scenarios
- SKILL.md tasks (T013–T020) are sequential updates to the same file — cannot run in parallel
- All file paths reference the repository root
- `Plans/` directory (T021) must exist before T015 (SKILL.md step 3) can be tested
- Bronze tier has no external services — `DRY_RUN=true` means no MCP calls will fire
