# Feature Specification: Bronze Tier Personal AI Employee Foundation

**Feature Branch**: `001-bronze-ai-employee`
**Created**: 2026-03-06
**Status**: Draft

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Event Captured as Actionable Task (Priority: P1)

A user drops any file (document, invoice, note) into the vault's Inbox folder. Without
any manual intervention, the system detects the arrival and creates a structured task
file in Needs_Action so that Claude has something concrete to work from.

**Why this priority**: This is the entry point of the entire system. Nothing downstream
can function unless incoming events are reliably detected and converted into tasks.
It delivers standalone value: the user can verify the watcher is working before any
AI processing is connected.

**Independent Test**: Drop a file into `AI_Employee_Vault/Inbox/`. Confirm a
corresponding `.md` task file appears in `AI_Employee_Vault/Needs_Action/` within
10 seconds, without any manual steps.

**Acceptance Scenarios**:

1. **Given** the watcher is running and Inbox is empty, **When** a file is dropped into Inbox, **Then** a task `.md` file appears in Needs_Action within 10 seconds containing the file's name, size, and received timestamp.
2. **Given** multiple files are dropped in quick succession, **When** the watcher processes them, **Then** a separate task file is created for each file with no duplicates.
3. **Given** a file that starts with `.` or `~` is written to Inbox (temp/hidden file), **When** the watcher detects it, **Then** no task file is created for it.
4. **Given** the watcher is restarted after previously processing files, **When** it starts up, **Then** it does not re-create task files for already-processed items.

---

### User Story 2 — Claude Analyses Task and Creates a Plan (Priority: P2)

A user invokes Claude Code to process pending tasks. Claude reads each task file in
Needs_Action, understands what the item is, applies the rules from Company_Handbook,
and produces a Plan.md in the Plans folder describing what should happen next.

**Why this priority**: This is the reasoning core. It transforms raw task files into
actionable plans with checkboxes, turning the system from a file-mover into an
intelligent assistant.

**Independent Test**: Place a pre-written task `.md` file in Needs_Action and invoke
Claude. Confirm a `Plan.md` appears in `AI_Employee_Vault/Plans/` with a human-readable
summary and at least one checkbox action step.

**Acceptance Scenarios**:

1. **Given** one or more `.md` files are present in Needs_Action, **When** the process-needs-action skill is invoked, **Then** a `Plan.md` is created in Plans for each task containing a summary and `[ ]` action checkboxes.
2. **Given** Company_Handbook defines a rule (e.g., payments > $50 require approval), **When** Claude encounters a task matching that rule, **Then** the Plan reflects that rule and marks the action as requiring human approval.
3. **Given** a task file has `priority: urgent`, **When** Claude processes the queue, **Then** it is processed before `priority: normal` items.
4. **Given** Claude cannot determine what a task requires, **When** it processes the file, **Then** it creates a Plan flagging the item for human review rather than silently skipping it.

---

### User Story 3 — Task Moved to Done and Dashboard Updated (Priority: P3)

After a task has been processed (plan created, any safe actions taken), the task file
is moved to Done and the Dashboard is updated to reflect the current state of the
vault — pending count, completed today, and a summary of the last few completions.

**Why this priority**: Completion tracking and visibility make the system trustworthy.
A user must be able to open Obsidian and immediately understand what the AI has done
and what remains.

**Independent Test**: After completing P1 and P2, invoke the skill and confirm: the
processed task file is in `Done/` with a `DONE_` prefix, and `Dashboard.md` shows
updated counts and a recent-completions entry.

**Acceptance Scenarios**:

1. **Given** a task has been analysed and a Plan created, **When** the skill completes processing, **Then** the original task `.md` file is moved to Done with a `DONE_` prefix and the original filename preserved.
2. **Given** tasks have been completed, **When** Dashboard.md is updated, **Then** it shows: count of items in Needs_Action, count of items completed today, and the last 5 completed items with one-line summaries.
3. **Given** Needs_Action is empty, **When** the skill runs, **Then** Dashboard reflects zero pending items and the system status shows as clear.
4. **Given** an error occurs while processing a specific task, **When** the error is caught, **Then** an `ERROR_<timestamp>.md` file is created in Needs_Action and processing continues for all remaining tasks.

---

### Edge Cases

- What happens when a file is dropped to Inbox while a previous watcher cycle is still running? Each file event is handled independently; no events are lost.
- What happens when the vault path does not exist at startup? The orchestrator logs a clear error and exits with a non-zero code rather than failing silently.
- What happens when Needs_Action contains a file with no YAML frontmatter? Claude treats it as `type: unknown, priority: normal` and flags it for human review in the Plan.
- What happens when Dashboard.md is missing? Claude creates it from scratch with the current state.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a local Obsidian vault named `AI_Employee_Vault` as the sole storage and interface, containing `Dashboard.md`, `Company_Handbook.md`, and the folder structure: `Inbox/`, `Needs_Action/`, `Plans/`, `Done/`, `Logs/`.
- **FR-002**: The system MUST include a Python watcher process that monitors `Inbox/` and creates a structured `.md` task file in `Needs_Action/` within 10 seconds of a file appearing in Inbox.
- **FR-003**: Each task file created by the watcher MUST include YAML frontmatter with at minimum: `type`, `original_name`, `received` (ISO 8601 timestamp), `priority`, and `status: pending`.
- **FR-004**: The watcher MUST be idempotent — restarting it MUST NOT create duplicate task files for already-processed Inbox items.
- **FR-005**: The system MUST include a `process-needs-action` Agent Skill that reads `Company_Handbook.md` before processing any task.
- **FR-006**: The skill MUST create a `Plan.md` in `Plans/` for each processed task, containing a human-readable summary and at least one `[ ]` checkbox action step.
- **FR-007**: The skill MUST sort tasks by priority (urgent → high → normal → low) before processing.
- **FR-008**: The skill MUST move each processed task file from `Needs_Action/` to `Done/` with a `DONE_` filename prefix.
- **FR-009**: The skill MUST update `Dashboard.md` after every processing run with: last-updated timestamp, count of pending items, count of items completed today, and a list of the last 5 completions with one-line summaries.
- **FR-010**: The skill MUST append one structured log entry per processed item to `Logs/YYYY-MM-DD.json`.
- **FR-011**: On any processing error for a specific task, the system MUST create an `ERROR_<timestamp>.md` file in `Needs_Action/` and continue processing remaining tasks.
- **FR-012**: The system MUST default to `DRY_RUN=true`, preventing any real external actions during development.
- **FR-013**: All secrets and configuration MUST be stored in `.env` (gitignored); none MUST appear in vault `.md` files or committed code.

### Key Entities

- **Task File**: A `.md` file in `Needs_Action/` representing one incoming event. Attributes: type, original_name, received timestamp, priority, status, and a human-readable body section.
- **Plan**: A `.md` file in `Plans/` generated by Claude for one task. Attributes: task reference, summary, one or more `[ ]` action checkboxes, and optionally a `[ ] APPROVE` gate for sensitive actions.
- **Vault**: The `AI_Employee_Vault/` directory — the single source of truth for all system state. No external databases.
- **Dashboard**: `Dashboard.md` — the live status board updated by Claude after every processing run. Human-readable in Obsidian.
- **Handbook**: `Company_Handbook.md` — the rules of engagement loaded by Claude before every processing run. Editing this file changes AI behaviour without any code changes.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A file dropped into Inbox produces a task file in Needs_Action within 10 seconds, without any manual intervention, 100% of the time.
- **SC-002**: Running the process-needs-action skill on a vault with 5 pending tasks completes all processing and updates Dashboard in under 60 seconds.
- **SC-003**: After a full run, a user opening Obsidian can determine the complete state of the system (pending, done, errors) from Dashboard.md alone — no terminal required.
- **SC-004**: Restarting the watcher after a crash does not produce duplicate task files for any previously detected Inbox items.
- **SC-005**: A task processing error for one item does not prevent the remaining tasks in Needs_Action from being processed in the same run.
- **SC-006**: Zero credentials, API keys, or tokens appear in any committed file or vault `.md` file.

---

## Assumptions

- The user is running the system on Windows 11 with WSL2; the watcher uses polling (not inotify) due to NTFS mount limitations on `/mnt/c`.
- "No external services required" applies to the Bronze tier only; the vault structure is designed to accommodate Silver/Gold integrations without restructuring.
- Obsidian is used as a read-only viewer at this tier; the AI writes all content, the human reads and edits via Obsidian.
- A single `orchestrator.py` entry point is sufficient for Bronze; process supervision (watchdog) is a Gold-tier concern.
