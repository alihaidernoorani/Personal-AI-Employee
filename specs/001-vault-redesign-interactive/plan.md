# Implementation Plan: Interactive Obsidian Vault Redesign

**Branch**: `001-vault-redesign-interactive` | **Date**: 2026-06-28 | **Spec**: [spec.md](spec.md)  
**Input**: `specs/001-vault-redesign-interactive/spec.md` (updated 2026-06-28 with clarifications)

---

## Summary

This plan governs the redesign of `AI_Employee_Vault/` from a static, navigation-heavy structure into an interactive, single-screen control center. The spec was updated on 2026-06-28 with clarifications that significantly change the approach from the initial implementation (T001–T031):

- **Hub pages eliminated** — 4 hub pages created by T016–T019 must be deleted (FR-021). Dashboard is the sole control screen.
- **`_System/` folder** — all 12 operational folders (Needs_Action/, Done/, etc.) must move under a `_System/` parent (FR-018), requiring updates to all Python watcher scripts and Dataview queries.
- **8 trigger buttons, not 6 navigation buttons** — Dashboard quick-actions must create signal files in `_System/Needs_Action/` rather than navigate to hub pages (FR-004).
- **Inline Approve/Reject interaction** — Dashboard pending-approvals table must include per-row approve/reject affordance (FR-004a); individual approval files must also have approve/reject buttons (FR-004b).
- **Reference/ folder** — `Company_Handbook.md` and `Business_Goals.md` (already moved to `Reference/`) require skill and watcher reference updates (FR-022).

**Scope expanded (clarification 2026-06-28)**: Python watcher script path updates, skill path updates, hub page deletion, and approval file inline buttons are now in scope.

Previous research and data-model artifacts (`research.md`, `data-model.md`) remain valid. The Δ-implementation (remaining tasks) builds on top of T001–T031.

---

## Technical Context

**Language/Version**: Obsidian Markdown + Dataview DQL 0.5.68 + Buttons 0.9.13 + Meta Bind 1.4.15 + Kanban 2.0.51 + Homepage 4.4.4; Python 3.13+ (watcher scripts)  
**Primary Dependencies**: 6 Obsidian community plugins (all installed and enabled); Python `watchdog>=4.0.0`  
**Storage**: Obsidian vault markdown files (`AI_Employee_Vault/`) — no external database  
**Testing**: Manual verification in Obsidian reading view (no automated tests applicable to `.md` content)  
**Target Platform**: Obsidian desktop (Windows 11); cloud VM reads vault via Syncthing  
**Performance Goals**: All Dataview tables render ≤3 seconds with 100+ files in `_System/Done/` (SC-003)  
**Constraints**: `enableJs: false` in Meta Bind (JavaScript disabled); no Templater plugin installed; buttons can navigate and run Obsidian commands but cannot execute arbitrary file-move operations natively  
**Scale/Scope**: 12 operational folders → `_System/`; 12+ Python watcher files need path updates; 13 existing approval files need inline button headers updated

---

## Constitution Check

*GATE: Must pass before implementation. All 15 principles evaluated.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Production First | ✅ PASS | All deliverables are Obsidian-native; no demo-only patterns |
| II. Local First | ✅ PASS | Vault files contain no credentials; secrets remain in `.env` |
| III. Cloud Worker | ✅ PASS | Vault is the sync boundary; cloud reads/writes `_System/` via Syncthing |
| IV. Human In The Loop | ✅ PASS | FR-004a/b adds inline approve/reject to reduce friction; approval files not auto-executed |
| V. Vault Driven Architecture | ✅ PASS | Folder structure IS the state machine; `_System/` nesting preserves all state transitions |
| VI. Claim-by-Move | ✅ PASS | `_System/In_Progress/<agent>/` — same claim-by-move rule, new path |
| VII. Single Writer Rule | ✅ PASS | `Dashboard.md` remains local-agent-only; cloud writes only to `_System/Updates/`, `_System/Signals/` |
| VIII. Event Driven | ✅ PASS | No polling changes; watcher scripts continue event-driven file detection |
| IX. Modular Design | ✅ PASS | Each vault section (Dashboard, Pipeline, Reference) independently testable |
| X. Agent Skills | ✅ PASS | `process-needs-action` skill updated for `_System/` paths and Pipeline sync |
| XI. Observability | ✅ PASS | All watcher actions continue to log to `_System/Logs/`; audit trail preserved |
| XII. Reliability | ✅ PASS | Dual-layer Dashboard (Dataview live + AI_EMPLOYEE static) provides graceful degradation |
| XIII. Security | ✅ PASS | `Reference/` holds handbook/goals (no credentials); `_System/` operational files contain no secrets |
| XIV. Documentation | ✅ PASS | `quickstart.md` covers all smoke tests; plan.md documents all decisions |
| XV. Code Quality | ✅ PASS | Watcher path changes are isolated constant replacements; no logic changes |

**No gate violations. Implementation may proceed.**

---

## Project Structure

### Documentation (this feature)

```text
specs/001-vault-redesign-interactive/
├── plan.md          # This file — architecture and design decisions
├── research.md      # Phase 0 — plugin research, DQL patterns, file naming analysis
├── data-model.md    # Phase 1 — vault entities, relationships, state transitions
├── quickstart.md    # Phase 1 — smoke test checklist for Obsidian verification
└── tasks.md         # T001–T037 implementation tasks (T001–T031 complete)
```

### Vault Structure (Target — post implementation)

```text
AI_Employee_Vault/               # ← 7 top-level entries only (SC-007)
├── Dashboard.md                 # Single control screen (local-agent single-writer)
├── Pipeline.md                  # Kanban board (4 columns)
├── Bank_Transactions.md         # Finance watcher output (machine-appendable)
├── Briefings/                   # CEO briefings (watcher-written)
├── Accounting/                  # Monthly accounting files
├── Reference/                   # Human reference docs (Company_Handbook.md, Business_Goals.md)
└── _System/                     # All AI-managed operational folders (collapsed in sidebar)
    ├── Needs_Action/
    ├── In_Progress/
    ├── Pending_Approval/
    ├── Approved/
    ├── Rejected/
    ├── Done/
    ├── Inbox/
    ├── Plans/
    ├── Logs/
    ├── Updates/
    ├── Signals/
    └── Sync/
```

### Source Files Requiring Path Updates

**Python watcher scripts** (path constants change from `<folder>` to `_System/<folder>`):

```text
watchers/
├── approval_watcher.py       # watches Approved/, Rejected/
├── filesystem_watcher.py     # watches Inbox/
├── finance_watcher.py        # writes to Needs_Action/, Accounting/
├── gmail_watcher.py          # writes to Needs_Action/
├── gmail_api_watcher.py      # writes to Needs_Action/
├── whatsapp_watcher.py       # writes to Needs_Action/
├── heartbeat_writer.py       # writes to Updates/
├── signals_watcher.py        # reads/writes Signals/
├── stale_task_monitor.py     # reads Needs_Action/, In_Progress/
└── base_watcher.py           # defines VAULT_PATH-relative folder constants
```

**Skill files** (path references for handbook/goals):
```text
.claude/skills/process-needs-action/SKILL.md   # operational folder paths + Reference/ handbook path
```

---

## Phase 0: Research (Complete)

Full research documented in `research.md`. Key decisions already resolved:

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | Dataview `startswith()` for `_System/Needs_Action/` prefix filtering | Exact prefix match; no false positives |
| 2 | `contains(lower())` for social/approval filename filtering | Platform name is embedded mid-filename |
| 3 | `LIMIT 10` on Done/, `LIMIT 20` on Pending_Approval/ | Performance guard for large Done/ folder |
| 4 | Homepage data.json: `Dashboard`, `openOnStartup: true`, `refreshDataview: true` | Fresh queries on startup |
| 5 | Dual-layer Dashboard (Dataview live + AI_EMPLOYEE static markers coexist) | Resilience — both layers work independently |
| 6 | Social items query `_System/Pending_Approval/` (not `_System/Needs_Action/`) | Social posts only appear as Claude-created approval drafts |
| 7 | `process-needs-action` skill gets Pipeline.md sync step | Keeps Kanban board in sync without manual maintenance |

**New research tasks required** (unresolved by T001–T031):

**R-001 — Trigger Button Implementation**: Determine the best mechanism for Dashboard quick-action buttons to create `SIGNAL_<timestamp>_<action>.md` files in `_System/Needs_Action/` without JavaScript:
- **Option A**: Meta Bind `createNote` action type — creates a new note in a specified folder with a template. Available in Meta Bind 1.4.15 if the action type is registered.
- **Option B**: `type: command` button triggering an Obsidian core command ("Create new note in current folder") — limited because it cannot set the folder or filename.
- **Option C** (fallback): Each button navigates to a pre-created action-request note (e.g., `_System/Signals/REQUEST_email-reply.md`) that serves as the trigger when opened. Claude detects file access and processes it.
- **Recommended**: Test Option A first. If `createNote` works with `folder: "_System/Needs_Action"` and `noteName` containing a timestamp expression, adopt it. Otherwise fall back to Option C.

**R-002 — Inline Approve/Reject Button Feasibility**: Determine the best mechanism for approve/reject buttons that move files from `_System/Pending_Approval/` to `_System/Approved/` or `_System/Rejected/` without JS:
- **Option A**: Meta Bind `type: command` triggering Obsidian's "Move file to folder" command (available if File Manager Plus or similar plugin is installed — check plugin list).
- **Option B**: Meta Bind `updateMetadata` action to set a `status` frontmatter field to `approved` or `rejected`; ApprovalWatcher detects the metadata change and performs the move.
- **Option C** (fallback): Clear visual `> [!caution]` callout with explicit instruction text: "To approve: move this file to `_System/Approved/`" — no button, just clear affordance.
- **Recommended**: Option B is cleanest — metadata change is non-destructive and fits the watcher pattern. Option C is the safe fallback if Option B proves unreliable.

---

## Phase 1: Design (Complete — with updates)

Full entity model in `data-model.md`. Updates required for `_System/` path changes:

### Updated Dataview Query Patterns

All `FROM` clauses change from `"<folder>"` to `"_System/<folder>"`:

```dataview
-- Needs Action (old)
FROM "Needs_Action" WHERE !(startswith(file.name, "ERROR"))

-- Needs Action (new)
FROM "_System/Needs_Action" WHERE !(startswith(file.name, "ERROR"))
```

```dataview
-- Pending Approval (old)
FROM "Pending_Approval" SORT file.mtime DESC LIMIT 20

-- Pending Approval (new)
FROM "_System/Pending_Approval" SORT file.mtime DESC LIMIT 20
```

```dataview
-- Done (old)
FROM "Done" SORT file.mtime DESC LIMIT 10

-- Done (new)
FROM "_System/Done" SORT file.mtime DESC LIMIT 10
```

Hub page Dataview queries reference paths that no longer exist after hub pages are deleted — this is resolved by deleting the hub page files entirely (FR-021).

### Updated File Relationship Map (no hub pages)

```
Dashboard.md (single control screen)
  │
  ├─ Dataview FROM "_System/Needs_Action"           (live needs-action table)
  ├─ Dataview FROM "_System/Pending_Approval"       (live pending-approvals table + per-row buttons)
  ├─ Dataview FROM "_System/Done" LIMIT 10          (recent completions)
  ├─ AI_EMPLOYEE:* static markers (22 pairs)        (last-processed audit snapshot)
  ├─ 8 quick-action trigger buttons                 (create signal files or navigate to request notes)
  └─ Links to: Pipeline.md, Briefings/, Bank_Transactions.md, Accounting/, Reference/

Pipeline.md (Kanban — 4 columns)
  └─ Cards link to _System/<folder>/<file>

Reference/Company_Handbook.md  ← skill files reference this path
Reference/Business_Goals.md    ← skill files reference this path
```

### Approval File Inline Button Design

Each file in `_System/Pending_Approval/` will have a standardised header:

```yaml
---
type: <action-type>
action: <description>
created: <ISO-timestamp>
status: pending
---
```

```markdown
> [!caution] ⏳ Pending Approval — <ACTION TYPE>
> **Action**: <description>
> **Key details**: <amount/recipient/content>
>
> ✅ **To approve**: change `status: pending` → `status: approved` in frontmatter OR move file to `_System/Approved/`
> ❌ **To reject**: change `status: pending` → `status: rejected` in frontmatter OR move file to `_System/Rejected/`
```

If Meta Bind `updateMetadata` buttons are feasible (R-002 Option B), the header will also include:

```markdown
`BUTTON[approve-<id>]` `BUTTON[reject-<id>]`
```

with corresponding hidden Meta Bind button definitions that set `status` in frontmatter.

---

## Δ-Implementation: Remaining Work

Tasks T001–T031 are complete. The following phases cover the delta between the old implementation and the updated spec.

### Phase A: Pre-flight Research (New)

Resolve R-001 and R-002 before building trigger buttons and approval inline buttons.

- [ ] TA-001 Test Meta Bind 1.4.15 `createNote` action: create a test button that generates a timestamped note in `_System/Needs_Action/` and verify the file appears and contains the expected content
- [ ] TA-002 Test Meta Bind `updateMetadata` action: create a test button on a scratch file that changes a `status` frontmatter field from `pending` to `approved`, verify the change is written to the file
- [ ] TA-003 Based on TA-001 and TA-002 findings, select the implementation pattern for (a) trigger buttons and (b) approve/reject buttons, and document the decision in `research.md` under section 11

### Phase B: Folder Restructure (`_System/`)

The highest-impact change — must complete before updating Dataview queries or watcher scripts.

- [ ] TB-001 Create `AI_Employee_Vault/_System/` folder (empty placeholder file if needed for Obsidian to show it)
- [ ] TB-002 Move each of the 12 operational folders into `_System/`: `Needs_Action/`, `In_Progress/`, `Pending_Approval/`, `Approved/`, `Rejected/`, `Done/`, `Inbox/`, `Plans/`, `Logs/`, `Updates/`, `Signals/`, `Sync/` — preserve all existing files within each folder
- [ ] TB-003 Verify all 12 folders now appear under `_System/` and the vault root shows exactly 7 top-level items: `Dashboard.md`, `Pipeline.md`, `Bank_Transactions.md`, `Briefings/`, `Accounting/`, `Reference/`, `_System/` (SC-007)

### Phase C: Python Watcher Path Updates

All watcher scripts must use `_System/<folder>` relative to `VAULT_PATH`. Update the path constant in each file; do not change any processing logic.

- [ ] TC-001 Update `watchers/base_watcher.py` — change all folder path constants from `<folder>` to `_System/<folder>` (base class; all subclasses inherit)
- [ ] TC-002 Update `watchers/approval_watcher.py` — update `APPROVED_FOLDER`, `REJECTED_FOLDER`, `PENDING_FOLDER` paths
- [ ] TC-003 Update `watchers/filesystem_watcher.py` — update `INBOX_FOLDER` path
- [ ] TC-004 Update `watchers/finance_watcher.py` — update `NEEDS_ACTION_FOLDER`, `ACCOUNTING_FOLDER` paths
- [ ] TC-005 Update `watchers/gmail_watcher.py` and `watchers/gmail_api_watcher.py` — update `NEEDS_ACTION_FOLDER` path
- [ ] TC-006 Update `watchers/whatsapp_watcher.py` — update `NEEDS_ACTION_FOLDER` path
- [ ] TC-007 Update `watchers/heartbeat_writer.py` — update `UPDATES_FOLDER` path
- [ ] TC-008 Update `watchers/signals_watcher.py` — update `SIGNALS_FOLDER` path
- [ ] TC-009 Update `watchers/stale_task_monitor.py` — update `NEEDS_ACTION_FOLDER`, `IN_PROGRESS_FOLDER` paths
- [ ] TC-010 Grep `orchestrator.py` and all `scripts/` files for hardcoded folder paths; update any found

### Phase D: Hub Page Deletion (FR-021)

- [ ] TD-001 Delete `AI_Employee_Vault/Hubs/WhatsApp_Hub.md`
- [ ] TD-002 Delete `AI_Employee_Vault/Hubs/Email_Hub.md`
- [ ] TD-003 Delete `AI_Employee_Vault/Hubs/Finance_Hub.md`
- [ ] TD-004 Delete `AI_Employee_Vault/Hubs/Social_Hub.md`
- [ ] TD-005 Remove the `Hubs/` folder from the vault (after confirming it is empty)

### Phase E: Dashboard Rewrite (Updated Spec)

Rewrite `Dashboard.md` to: (a) update all Dataview `FROM` clauses to `_System/` paths, (b) replace 6 navigation buttons with 8 trigger buttons, (c) add inline approve/reject interaction to Pending Approvals section, (d) remove navigation links to hub pages.

- [ ] TE-001 Update all Dataview `FROM` clauses in `Dashboard.md` from `"Needs_Action"`, `"Pending_Approval"`, `"Done"` to `"_System/Needs_Action"`, `"_System/Pending_Approval"`, `"_System/Done"` — do not touch any AI_EMPLOYEE markers
- [ ] TE-002 Replace the 6 Quick Actions button blocks with 8 trigger buttons using the pattern determined in TA-001/TA-003: 📧 Reply to Email, 💬 Reply to WhatsApp, 📣 Post on LinkedIn, 📘 Post on Facebook, 📸 Post on Instagram, 🐦 Post on Twitter/X, 💰 Create Invoice, 📊 Run CEO Briefing (FR-004)
- [ ] TE-003 Update the Pending Approvals Dataview section to add per-row inline approve/reject interaction using the pattern determined in TA-002/TA-003 (FR-004a); if Option B (updateMetadata), add button definitions for each current approval file; if Option C (fallback), update the `> [!caution]` callout with explicit path-based instructions
- [ ] TE-004 Remove navigation links to hub pages from the `## 🔗 Quick Navigation` section; replace with direct links to `[[Pipeline]]`, `[[Briefings/]]`, `[[Bank_Transactions]]`, `[[Accounting/Current_Month]]`, `[[Reference/Company_Handbook]]`, `[[Reference/Business_Goals]]`
- [ ] TE-005 Verify all 22 AI_EMPLOYEE marker pairs remain intact after edits (FR-007) — count must equal 22

### Phase F: Approval Files Update (FR-004b)

Add approve/reject buttons to all existing approval files in `_System/Pending_Approval/`. Use the pattern from TA-002/TA-003.

- [ ] TF-001 Read each file in `_System/Pending_Approval/` and identify which files already have the fast-path header from T026–T027
- [ ] TF-002 For each approval file: update or add the approve/reject button pair below the `> [!caution]` callout using the chosen button pattern (Meta Bind `updateMetadata` OR explicit instruction text)

### Phase G: Skill Path Updates (FR-022)

- [ ] TG-001 Update `.claude/skills/process-needs-action/SKILL.md` to replace all operational folder path references with `_System/<folder>` equivalents
- [ ] TG-002 Update `.claude/skills/process-needs-action/SKILL.md` to reference `Reference/Company_Handbook.md` and `Reference/Business_Goals.md` instead of root-level file paths
- [ ] TG-003 Grep all other skills under `.claude/skills/` for references to `Company_Handbook`, `Business_Goals`, or any of the 12 operational folder names — update any found

### Phase H: Smoke Tests (Updated)

- [ ] TH-001 Verify smoke test 1 (SC-001, SC-002): Open `Dashboard.md` in reading view — 8 trigger buttons render, all Dataview tables show `_System/` path results
- [ ] TH-002 Verify smoke test 2 (SC-003): Dataview tables render ≤3 seconds with current vault file count
- [ ] TH-003 Verify smoke test 3 (SC-004): Run `process-needs-action` skill — watcher scripts process files at `_System/<folder>` paths correctly; all 22 AI_EMPLOYEE markers intact
- [ ] TH-004 Verify smoke test 4 (SC-005): Pipeline.md Kanban board renders 4 columns; card links now point to `_System/<folder>/<file>`
- [ ] TH-005 Verify smoke test 5 (SC-006): Relaunch Obsidian — `Dashboard.md` opens automatically
- [ ] TH-006 Verify smoke test 6 (SC-007): Vault root shows exactly 7 top-level items in Obsidian sidebar
- [ ] TH-007 Verify smoke test 7 (SC-008): Each pending draft in `_System/Pending_Approval/` shows on Dashboard with per-row approve/reject affordance

---

## Key Design Decisions

### Decision 1 — _System/ Folder (FR-018)

**Decision**: Move all 12 operational folders under `_System/` by physically moving them within the vault.  
**Rationale**: Reduces sidebar clutter from 18+ top-level items to 7 (SC-007). All watchers use a `VAULT_PATH`-relative constant for each folder — updating the constant in `base_watcher.py` is a single-point change that propagates to all subclasses.  
**Alternatives considered**: CSS-hiding operational folders — rejected because Obsidian's CSS cannot hide folders from the file system, only from some views. Renaming folders with a `_` prefix — rejected because FR-018 requires the folder names remain unchanged.

### Decision 2 — Hub Pages Deleted (FR-021)

**Decision**: Delete all 4 hub page files from `Hubs/` folder.  
**Rationale**: Per clarification 2026-06-28, Dashboard is the sole control screen. Hub pages add navigation depth that increases time-to-action and contradicts SC-001 (all actions within 30 seconds from Dashboard).  
**Alternatives considered**: Keep hub pages as supplemental detail views — rejected per user clarification. Move hub page Dataview queries into Dashboard — adopted (already implemented in T009–T012 for all-items view).

### Decision 3 — Trigger Button Pattern (pending TA-001 finding)

**Primary**: Meta Bind `createNote` action creates `SIGNAL_<timestamp>_<action>.md` in `_System/Needs_Action/`. This is non-destructive (creates a new file; does not modify existing state) and fits the watcher-detection pattern.  
**Fallback**: Button navigates to a pre-created action request note (e.g., `_System/Signals/REQUEST_<action>.md`). Claude detects the file modification timestamp change and processes it as a trigger.

### Decision 4 — Inline Approve/Reject Pattern (pending TA-002 finding)

**Primary**: Meta Bind `updateMetadata` action sets `status: approved` or `status: rejected` in approval file frontmatter. ApprovalWatcher detects the metadata change and moves the file.  
**Fallback**: Clear `> [!caution]` callout with explicit file path instructions for manual move. Already implemented in T026–T027 fast-path headers.

---

## Complexity Tracking

| Item | Why Needed | Simpler Alternative Rejected Because |
|------|------------|-------------------------------------|
| Dual-layer Dashboard (Dataview + AI_EMPLOYEE markers) | Resilience — Dataview-only breaks when plugin disabled; static-only breaks when Claude hasn't run | See research.md §9 — both layers provide independent value |
| `_System/` folder nesting | Sidebar clarity; SC-007 requires ≤7 top-level items | CSS-only hide: doesn't work reliably across Obsidian versions |
| Python path update scope | Watcher scripts hardcode `Needs_Action/` etc. — moves break them silently | Symlinks: not portable across Windows/WSL/cloud; rejected for reliability |
