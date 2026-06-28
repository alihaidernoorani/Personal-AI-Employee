# Data Model: Interactive Obsidian Vault Redesign

**Feature**: `001-vault-redesign-interactive`  
**Phase**: 1 — Design  
**Date**: 2026-06-28

---

## Overview

This feature has no traditional database. The "data model" is the set of Obsidian markdown files and their relationships. The vault folder structure IS the state machine.

**Updated 2026-06-28**: Hub pages eliminated per spec clarification. All 12 operational folders now reside under `_System/`. All Dataview `FROM` clauses updated accordingly.

---

## Entities

### Quick Action Button

A Buttons plugin code block (`button`) or Meta Bind button block (`meta-bind-button`) embedded in a markdown file.

| Attribute | Value |
|-----------|-------|
| Plugin | Meta Bind (`createNote` action) preferred; Buttons (`type link`) as fallback |
| Action type | `createNote` → creates `SIGNAL_<timestamp>_<action>.md` in `_System/Needs_Action/`; fallback: `type link` → navigates to a pre-created request note |
| Rendering | Reading view only; source view shows raw markdown |
| State | Creates a trigger file — Claude picks it up and writes a draft to `_System/Pending_Approval/` |

**Variants**:
- **Trigger CTA** (8 buttons on Dashboard): create action request signal files
- **Approve/Reject** (Meta Bind `updateMetadata`): per-approval-file buttons that set `status` in frontmatter; ApprovalWatcher detects change and moves file

---

### Dataview Query

A Dataview DQL code block embedded in a markdown file. Queries the vault file system at render time.

| Attribute | Value |
|-----------|-------|
| Query language | Dataview Query Language (DQL) v0.5.68 |
| Source | `FROM "folder"` — queries a vault folder |
| Filter | `WHERE startswith(file.name, "PREFIX")` or `contains(lower(file.name), "term")` |
| Output | `TABLE WITHOUT ID` (rows with columns) or `LIST WITHOUT ID` (simple links) |
| Refresh | Automatic when vault files change (Dataview auto-index) |
| Performance | `LIMIT 10` on Done/, `LIMIT 20` on Pending_Approval/ |

---

### Watcher File (existing entity, referenced by queries)

A `.md` file deposited by a Python watcher script into `_System/Needs_Action/`.

| Attribute | Value |
|-----------|-------|
| Location | `AI_Employee_Vault/_System/Needs_Action/<PREFIX>_<TIMESTAMP>_<slug>.md` |
| Writers | Python watcher scripts (Gmail, WhatsApp, Finance, File) |
| Readers | Claude Code (process-needs-action skill); Hub Page Dataview queries |
| Naming prefixes | `WA_`, `WHATSAPP_`, `GMAIL_`, `EMAIL_`, `FINANCE_`, `FILE_`, `TASK_`, `ERROR_` |

---

### Approval File (existing entity, referenced by queries)

A `.md` file in `_System/Pending_Approval/` representing a sensitive action awaiting human sign-off.

| Attribute | Value |
|-----------|-------|
| Location | `AI_Employee_Vault/_System/Pending_Approval/APPROVAL_<TIMESTAMP>_<type>_<slug>.md` |
| Writers | Claude Code (process-needs-action skill) |
| Readers | Human (approve or reject); Dashboard Dataview queries |
| Naming patterns | `*finance*`, `*TXN*`, `*email*`, `*gmail*`, `*linkedin*`, `*facebook*`, `*instagram*`, `*twitter*` |
| State transitions | `_System/Pending_Approval/` → `_System/Approved/` (status change or human moves) → `_System/Rejected/` |
| Button affordance | Fast-path header with `> [!caution]` callout; optional Meta Bind `updateMetadata` buttons for `status` field |

---

### Kanban Card

A checklist item inside `Pipeline.md` that represents a single work item at a specific lifecycle stage.

| Attribute | Value |
|-----------|-------|
| Format | `- [ ] [[Note Link\|Display Text]] #domain-tag` |
| State | `- [ ]` = active; `- [x]` = completed (Done column only) |
| Location | Inside `Pipeline.md`, under a column heading `## Column Name` |
| Writers | Claude Code (process-needs-action skill sync step); Human (drag to reorder) |
| Links | Wikilink to source file in vault |

**State machine**:
```
Needs Action → In Progress → Pending Approval → Done (Recent)
    (Claude picks up)  (HITL file created)  (Approved + executed)
```

---

### Homepage Configuration

The `data.json` file for the Homepage plugin.

| Attribute | Value |
|-----------|-------|
| Location | `AI_Employee_Vault/.obsidian/plugins/homepage/data.json` |
| Writer | Human (file creation); Plugin (updates on settings change) |
| Format | JSON |
| Key fields | `value: "Dashboard"`, `kind: "File"`, `openOnStartup: true`, `refreshDataview: true` |

---

## File Relationship Map

*Updated 2026-06-28: Hub pages eliminated. All operational paths now under `_System/`.*

```
Dashboard.md (single control screen) ──────────────────────────────
  │
  ├─ Dataview FROM "_System/Needs_Action"        (all pending tasks)
  ├─ Dataview FROM "_System/Pending_Approval"    (drafts awaiting sign-off)
  │    └─ per-row: approve/reject buttons (Meta Bind updateMetadata)
  ├─ Dataview FROM "_System/Done" LIMIT 10       (recent completions)
  ├─ AI_EMPLOYEE:* static markers (22 pairs)     (last-processed snapshot)
  ├─ 8 trigger buttons (Meta Bind createNote)    (create _System/Needs_Action/SIGNAL_*)
  └─ Links: Pipeline.md, Briefings/, Bank_Transactions.md,
            Accounting/Current_Month.md, Reference/Company_Handbook.md,
            Reference/Business_Goals.md

Pipeline.md (Kanban) ───────────────────────────────────────────────
  │ Column: Needs Action     → links to _System/Needs_Action/* files
  │ Column: In Progress      → links to _System/In_Progress/* files
  │ Column: Pending Approval → links to _System/Pending_Approval/* files
  │ Column: Done (Recent)    → links to _System/Done/* files (top 10)
  └───────────────────────────────────────────────────────────────-

Reference/ ─────────────────────────────────────────────────────────
  │ Company_Handbook.md  ← skill files read this for rules of engagement
  │ Business_Goals.md    ← skill files read this for OKRs and targets
  └───────────────────────────────────────────────────────────────-
```

---

## State Transitions

### Task Lifecycle (Pipeline stages)

*Updated 2026-06-28: All folder paths now under `_System/`. Approval trigger: metadata change OR file move.*

```
USER CLICK (trigger button) → _System/Needs_Action/SIGNAL_<timestamp>_<action>.md
WATCHER DETECT              → _System/Needs_Action/<PREFIX>_<timestamp>_<slug>.md
                                          │
                                   [Claude picks up]
                                          ↓
                        _System/In_Progress/<agent>/<file>  ← Kanban: card → "In Progress"
                                          │
                                   [Claude processes]
                                          ↓
                  _System/Pending_Approval/APPROVAL_*       ← Kanban: card → "Pending Approval"
                                          │
                  [Human: sets status: approved in frontmatter
                           OR moves file to _System/Approved/]
                                          ↓
                              _System/Done/<file>            ← Kanban: card → "Done"
                                          │
                        [Approval Watcher executes MCP action]
```

### Dashboard Data Flow

```
Watcher deposits file → _System/Needs_Action/
                                    ↓
                    Dataview auto-refreshes (no action required)
                                    ↓
                    Dashboard shows item in Needs Action table
                                    ↓
                    Human sees item, clicks link, reviews file
                                    ↓
                    Claude processes → _System/Pending_Approval/
                                    ↓
                    Dashboard shows draft with approve/reject buttons
                                    ↓
                    Human approves/rejects via button or file move
```

---

## Validation Rules

| Entity | Rule | Enforcement |
|--------|------|-------------|
| Hub Page | Never in a machine-writable folder | By convention; Claude skips hub pages |
| Dataview query | Must include LIMIT on Done/ | Code review of each query block |
| Watcher file | Name must start with known prefix | Existing watcher conventions; not modified |
| Kanban card | Must contain wikilink to source file | Template enforced by process-needs-action |
| Homepage config | `refreshDataview: true` | Set during implementation |
| AI_EMPLOYEE markers | Must not be removed from Dashboard.md | Preservation requirement FR-007 |
