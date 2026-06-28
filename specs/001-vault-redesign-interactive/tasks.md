# Tasks: Interactive Obsidian Vault Redesign

**Feature**: `001-vault-redesign-interactive`  
**Branch**: `001-vault-redesign-interactive`  
**Input**: `specs/001-vault-redesign-interactive/plan.md` (updated 2026-06-28), `spec.md`, `research.md`, `data-model.md`, `quickstart.md`  
**Generated**: 2026-06-28 (updated to reflect spec clarifications — hub pages eliminated, `_System/` folder, 8 trigger buttons, inline approve/reject)  
**Status**: Phases 1–7 complete (T001–T031 done). Delta Phases A–G complete (T032–T063 done). Phase H (T064–T072) requires manual Obsidian verification.

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (targets different files, no blocking dependencies)
- **[Story]**: User Story label (US1–US5 maps to spec.md priorities)
- **No automated tests**: This is a content/config feature. Verification is manual (reading view in Obsidian). Test tasks = quickstart.md smoke tests in Phase H.

---

## Phase 1: Setup (Shared Prerequisites) ✅ COMPLETE

**Purpose**: Read current state before making any changes.

- [X] T001 Read `AI_Employee_Vault/Dashboard.md` in full and record all 22 AI_EMPLOYEE comment marker pairs with their exact surrounding content (gate for T005–T015)
- [X] T002 [P] Read `AI_Employee_Vault/Pipeline.md` in full and list all existing Kanban card wikilinks and their column placement
- [X] T003 [P] List all file names currently in `AI_Employee_Vault/Needs_Action/`, `AI_Employee_Vault/In_Progress/`, `AI_Employee_Vault/Pending_Approval/`, and `AI_Employee_Vault/Done/` for use in Pipeline card population and approval file verification

---

## Phase 2: Foundational (Blocking Gate) ✅ COMPLETE

- [X] T004 Confirm all 22 AI_EMPLOYEE marker pairs from T001 are recorded, cross-check against the plan.md marker list — count must equal 22

**Checkpoint**: 22 markers confirmed → Dashboard rewrite (Phase 3) may begin

---

## Phase 3: User Story 1 — Unified Control Center Dashboard (Priority: P1) ✅ COMPLETE

**Note**: Initial implementation done. Quick-actions were 6 navigation buttons to hub pages. Delta work (trigger buttons + `_System/` paths + inline approve/reject) is in Phase E below.

- [X] T005 [US1] Write the header section of `AI_Employee_Vault/Dashboard.md`: title, branding callout, `UPDATED` marker block
- [X] T006 [US1] Add System Status section with `> [!success]`, `> [!warning]`, `> [!danger]` callouts for each watcher (FR-003)
- [X] T007 [US1] Add Cloud Agent Status section with all 8 cloud markers preserved (FR-007)
- [X] T008 [US1] Add Quick Actions row with 6 Buttons plugin blocks navigating to hub pages (initial implementation — superseded by T053–T055)
- [X] T009 [US1] Add Live Needs Action Dataview table querying `"Needs_Action"` (initial paths — updated in T053)
- [X] T010 [US1] Add Live Pending Approvals Dataview table querying `"Pending_Approval"` LIMIT 20 (initial paths — updated in T053)
- [X] T011 [US1] Add Finance Snapshot section as `> [!info]` callout with links to Bank_Transactions and Accounting (FR-005)
- [X] T012 [US1] Add Live Recent Completions Dataview querying `"Done"` LIMIT 10 plus static markers (initial paths — updated in T053)
- [X] T013 [US1] Add Compliance Status section with all 5 compliance markers (FR-007)
- [X] T014 [US1] Add Navigation quick-links callout with wikilinks to hub pages and key vault files (initial — updated in T056)
- [X] T015 [US1] Count all AI_EMPLOYEE markers in rewritten Dashboard.md — verify count equals 22 (FR-007)

**Checkpoint**: Dashboard.md rewrite complete with 22 markers intact

---

## Phase 4: User Story 2 — Domain Hub Pages ✅ COMPLETE (Files to be deleted in Phase D)

**Note**: Hub pages were created per the original plan. Spec clarification 2026-06-28 eliminates hub pages entirely (FR-021). Deletion is in Phase D (T048–T052).

- [X] T016 [P] [US2] Create `AI_Employee_Vault/Hubs/WhatsApp_Hub.md` with Dataview and navigation
- [X] T017 [P] [US2] Create `AI_Employee_Vault/Hubs/Email_Hub.md` with Dataview and navigation
- [X] T018 [P] [US2] Create `AI_Employee_Vault/Hubs/Finance_Hub.md` with Dataview and navigation
- [X] T019 [P] [US2] Create `AI_Employee_Vault/Hubs/Social_Hub.md` with Dataview and navigation
- [X] T020 [US2] Add navigation links to each hub page via `> [!abstract]` callout headers with wikilinks

---

## Phase 5: User Story 3 — Visual Kanban Pipeline Board (Priority: P2) ✅ COMPLETE

**Note**: Pipeline.md updated with 4 columns and current vault state. Card wikilinks need to be updated to `_System/<folder>` paths after Phase B folder restructure (T035–T037). Card update is task T062.

- [X] T021 [US3] Verify `AI_Employee_Vault/Pipeline.md` frontmatter is `kanban-plugin: board` and all 4 column headings are correctly formatted
- [X] T022 [US3] Sync `## 📥 Needs Action` column with current `Needs_Action/` file list from T003
- [X] T023 [US3] Sync `## 🔄 In Progress` column with current `In_Progress/` file list from T003
- [X] T024 [US3] Sync `## ✋ Pending Approval` column with current `Pending_Approval/` file list from T003
- [X] T025 [US3] Sync `## ✅ Done (Recent)` column with 10 most recent Done/ files; set `list-collapse` to collapse Done column by default

---

## Phase 6: User Story 4 — Approval Fast-Path (Priority: P2) ✅ COMPLETE

**Note**: Fast-path headers (YAML frontmatter + `> [!caution]` callout) added to all approval files. Actual Approve/Reject buttons (FR-004b) are a delta task in Phase F (T058–T059). process-needs-action skill updated with Pipeline sync.

- [X] T026 [US4] Read each file in `AI_Employee_Vault/Pending_Approval/` and identify files missing fast-path headers
- [X] T027 [US4] Prepend fast-path YAML frontmatter and `> [!caution]` callout to each file identified in T026
- [X] T028 [US4] Read `.claude/skills/process-needs-action/SKILL.md` in full to understand current processing flow
- [X] T029 [US4] Update `.claude/skills/process-needs-action/SKILL.md` to add Pipeline Sync Step (card moves across Kanban columns during processing)
- [X] T030 [US4] Update approval file template in `.claude/skills/process-needs-action/SKILL.md` to require fast-path headers on all future `APPROVAL_*.md` files

---

## Phase 7: User Story 5 — Homepage Integration (Priority: P3) ✅ COMPLETE

- [X] T031 [US5] Create `AI_Employee_Vault/.obsidian/plugins/homepage/data.json` with Homepage plugin v4 nested format: `openOnStartup: true`, `refreshDataview: true`, `kind: "File"` (FR-017)

---

## Phase A: Research (Blocking Gate for Trigger Buttons and Inline Approve/Reject)

**Purpose**: Determine the Meta Bind capability for file creation and metadata mutation before building FR-004 trigger buttons and FR-004a/b approve/reject buttons. Must resolve TA-001 and TA-002 before any trigger button or approve/reject implementation.

**⚠️ CRITICAL**: TA-001 and TA-002 MUST complete before Phase E (TE-002, TE-003) and Phase F.

**Independent Test**: After TA-001, a button click creates a `SIGNAL_*` file in `AI_Employee_Vault/_System/Needs_Action/`. After TA-002, a button click updates a `status` field in a test note's frontmatter.

- [X] T032 Test Meta Bind 1.4.15 `createNote` action: in a scratch note at vault root, write a `meta-bind-button` block with `type: createNote`, `folder: "_System/Needs_Action"`, a timestamped `noteName` — click the button in reading view and verify the file appears in `_System/Needs_Action/`. Document result (works / not available / error) in `specs/001-vault-redesign-interactive/research.md` under section "11. Trigger Button Capability"
- [X] T033 Test Meta Bind 1.4.15 `updateMetadata` action: in a scratch note with `status: pending` frontmatter, write a `meta-bind-button` block with `type: updateMetadata`, `bindTarget: "status"`, `value: "approved"` — click the button and verify `status` changes to `approved` in frontmatter. Document result in `specs/001-vault-redesign-interactive/research.md` under section "11. Trigger Button Capability"
- [X] T034 Based on T032 and T033 findings, add section "11. Trigger Button Capability" to `specs/001-vault-redesign-interactive/research.md` with the confirmed implementation pattern for (a) trigger buttons and (b) approve/reject buttons. Document the chosen approach and fallback if either action type is unavailable

**Checkpoint**: Implementation patterns confirmed for trigger buttons and approve/reject → Phase E and Phase F may begin

---

## Phase B: Folder Restructure (`_System/`) — Infrastructure

**Purpose**: Move all 12 operational folders under `_System/` to achieve the target vault structure. This is the highest-impact change — all downstream phases (C, E, F, G) depend on this restructure being complete.

**⚠️ CRITICAL**: All watcher scripts must be stopped before this phase to prevent them writing to old paths during the move. Restart after TC-001 is complete.

**Independent Test**: Open Obsidian file explorer. Count top-level items — exactly 7: `Dashboard.md`, `Pipeline.md`, `Bank_Transactions.md`, `Briefings/`, `Accounting/`, `Reference/`, `_System/`. Expand `_System/` and verify all 12 folders are present with their contents intact.

- [X] T035 Stop all running watcher scripts and orchestrator processes before starting the folder move (document the stop commands used so they can be restarted after T037)
- [X] T036 Create `AI_Employee_Vault/_System/` folder, then move each of the 12 operational folders into it, preserving all existing files within each folder: `Needs_Action/`, `In_Progress/`, `Pending_Approval/`, `Approved/`, `Rejected/`, `Done/`, `Inbox/`, `Plans/`, `Logs/`, `Updates/`, `Signals/`, `Sync/`
- [X] T037 Verify vault root shows exactly 7 top-level items: `Dashboard.md`, `Pipeline.md`, `Bank_Transactions.md`, `Briefings/`, `Accounting/`, `Reference/`, `_System/` (SC-007) — confirm all 12 folders exist under `_System/` with their original file counts intact

**Checkpoint**: `_System/` folder contains all 12 operational folders → watcher scripts may now be updated (Phase C) and Dataview queries updated (Phase E)

---

## Phase C: Python Watcher Path Updates — Infrastructure

**Purpose**: Update all Python watcher scripts and orchestrator to use `_System/<folder>` paths relative to `VAULT_PATH`. All changes are path constant replacements only — no logic changes.

**Independent Test**: After TC-001, restart the orchestrator and verify one watcher script correctly writes a test file to `AI_Employee_Vault/_System/Needs_Action/` (not the old root-level path). Check `AI_Employee_Vault/_System/Logs/` for audit entries at the new path.

- [X] T038 Read `watchers/base_watcher.py` in full, identify all folder path constants (e.g., `NEEDS_ACTION_FOLDER`, `DONE_FOLDER`, etc.), then update each from `<folder>` to `_System/<folder>` — this is the base class; all watcher subclasses inherit from it (FR-018)
- [X] T039 [P] Read `watchers/approval_watcher.py`, identify path constants for `Approved/`, `Rejected/`, `Pending_Approval/`, update each to `_System/Approved/`, `_System/Rejected/`, `_System/Pending_Approval/`
- [X] T040 [P] Read `watchers/filesystem_watcher.py`, update `Inbox/` path constant to `_System/Inbox/`
- [X] T041 [P] Read `watchers/finance_watcher.py`, update `Needs_Action/` and `Accounting/` path constants to `_System/Needs_Action/` (Accounting stays at root — verify in source)
- [X] T042 [P] Read `watchers/gmail_watcher.py`, update `Needs_Action/` path constant to `_System/Needs_Action/`
- [X] T043 [P] Read `watchers/gmail_api_watcher.py`, update `Needs_Action/` path constant to `_System/Needs_Action/`
- [X] T044 [P] Read `watchers/whatsapp_watcher.py`, update `Needs_Action/` path constant to `_System/Needs_Action/`
- [X] T045 [P] Read `watchers/heartbeat_writer.py`, update `Updates/` path constant to `_System/Updates/`
- [X] T046 [P] Read `watchers/signals_watcher.py`, update `Signals/` path constant to `_System/Signals/`
- [X] T047 [P] Read `watchers/stale_task_monitor.py`, update `Needs_Action/` and `In_Progress/` path constants to `_System/Needs_Action/` and `_System/In_Progress/`
- [X] T048 Grep `orchestrator.py` and all files in `scripts/` for hardcoded folder path strings (`Needs_Action`, `In_Progress`, `Pending_Approval`, `Approved`, `Rejected`, `Done`, `Inbox`, `Plans`, `Logs`, `Updates`, `Signals`, `Sync`) and update any found to their `_System/` equivalents

**Checkpoint**: All watcher scripts updated → orchestrator can be restarted; verify test file created at `_System/Needs_Action/` path

---

## Phase D: Hub Page Deletion (FR-021)

**Purpose**: Delete the 4 hub page files from `AI_Employee_Vault/Hubs/` per spec clarification 2026-06-28. Dashboard is the sole control screen.

**Independent Test**: Open Obsidian file explorer — `Hubs/` folder does NOT appear. Search vault for `WhatsApp_Hub.md`, `Email_Hub.md`, `Finance_Hub.md`, `Social_Hub.md` — no results.

- [X] T049 [P] Delete `AI_Employee_Vault/Hubs/WhatsApp_Hub.md` (FR-021)
- [X] T050 [P] Delete `AI_Employee_Vault/Hubs/Email_Hub.md` (FR-021)
- [X] T051 [P] Delete `AI_Employee_Vault/Hubs/Finance_Hub.md` (FR-021)
- [X] T052 [P] Delete `AI_Employee_Vault/Hubs/Social_Hub.md` (FR-021)
- [X] T053 Remove the now-empty `AI_Employee_Vault/Hubs/` folder (after confirming it is empty) (FR-021)

**Checkpoint**: No hub pages exist in vault → Dashboard is the only control screen

---

## Phase E: Dashboard Rewrite — Updated Spec (Priority: P1 Delta)

**Purpose**: Update `AI_Employee_Vault/Dashboard.md` to: (a) fix all Dataview `FROM` clauses to use `_System/` paths, (b) replace 6 navigation buttons with 8 trigger buttons per the pattern confirmed in T034, (c) add inline approve/reject affordance to the Pending Approvals section (FR-004a), (d) remove hub page navigation links.

**⚠️ Depends on**: T037 (Phase B complete), T034 (trigger button pattern confirmed)

**Independent Test**: Open `Dashboard.md` in reading view. 8 trigger buttons render (not navigation buttons). Dataview tables show items from `_System/Needs_Action/`, `_System/Pending_Approval/`, `_System/Done/` — not the old root-level paths. No "Hub" links visible anywhere. All 22 AI_EMPLOYEE markers intact in source view.

### Implementation for Phase E

- [X] T054 [US1] Update all three Dataview `FROM` clauses in `AI_Employee_Vault/Dashboard.md`: change `FROM "Needs_Action"` → `FROM "_System/Needs_Action"`, `FROM "Pending_Approval"` → `FROM "_System/Pending_Approval"`, `FROM "Done"` → `FROM "_System/Done"` — do not touch any AI_EMPLOYEE markers or other content (FR-001, FR-002, FR-006)
- [X] T055 [US1] Replace the 6 Quick Actions button blocks in `AI_Employee_Vault/Dashboard.md` with 8 trigger buttons using the confirmed pattern from T034: 📧 Reply to Email, 💬 Reply to WhatsApp, 📣 Post on LinkedIn, 📘 Post on Facebook, 📸 Post on Instagram, 🐦 Post on Twitter/X, 💰 Create Invoice, 📊 Run CEO Briefing — each creates a `SIGNAL_<timestamp>_<action>.md` in `_System/Needs_Action/` (or uses the confirmed fallback) (FR-004)
- [X] T056 [US1] Update the Pending Approvals section of `AI_Employee_Vault/Dashboard.md`: add per-row inline approve/reject affordance below (or beside) the Dataview table using the pattern confirmed in T034 — if `updateMetadata` buttons are feasible, add Meta Bind button definitions for each current approval file; if fallback, update the `> [!caution]` callout with explicit `_System/Approved/` and `_System/Rejected/` path instructions (FR-004a)
- [X] T057 [US1] Update the `## 🔗 Quick Navigation` section of `AI_Employee_Vault/Dashboard.md`: remove all hub page wikilinks (`[[WhatsApp_Hub]]`, `[[Email_Hub]]`, `[[Finance_Hub]]`, `[[Social_Hub]]`) and replace with direct links: `[[Pipeline]]`, `[[Briefings/]]`, `[[Bank_Transactions]]`, `[[Accounting/Current_Month]]`, `[[Reference/Company_Handbook]]`, `[[Reference/Business_Goals]]` (FR-021, FR-022)
- [X] T058 [US1] Count all `<!-- AI_EMPLOYEE:` opening tags in `AI_Employee_Vault/Dashboard.md` source view — verify count equals 22. If any marker is missing, restore it before proceeding (FR-007)

**Checkpoint**: Dashboard.md has 8 trigger buttons, `_System/` Dataview queries, inline approve/reject, no hub links, 22 markers intact

---

## Phase F: Approval Files — Inline Approve/Reject Buttons (FR-004b)

**Purpose**: Add approve/reject buttons (or clear affordance) to all existing files in `AI_Employee_Vault/_System/Pending_Approval/`. The fast-path headers (YAML + `> [!caution]` callout) were added in T027 — this phase upgrades them with the interactive button pattern confirmed in T034.

**⚠️ Depends on**: T034 (approve/reject button pattern confirmed), T036 (Phase B — files now at `_System/Pending_Approval/`)

**Independent Test**: Open any file in `AI_Employee_Vault/_System/Pending_Approval/` in reading view. Within the first 10 lines: action type is clear, key parameters visible, and approve/reject affordance is present (button or clear instruction). The approve path says `_System/Approved/` (not old `Approved/` root path).

- [X] T059 Read each file in `AI_Employee_Vault/_System/Pending_Approval/`, identify which files have fast-path `> [!caution]` callouts with OLD path references (`Approved/`, `Rejected/`) and update those paths to `_System/Approved/`, `_System/Rejected/` in the instruction text
- [X] T060 [P] For each file in `AI_Employee_Vault/_System/Pending_Approval/`, add the approve/reject button pair using the pattern confirmed in T034 (Meta Bind `updateMetadata` buttons OR explicit instruction text upgrade) immediately below the `> [!caution]` callout — preserve all content below the header (FR-004b)

**Checkpoint**: All existing approval files show correct `_System/` paths and approve/reject affordance

---

## Phase G: Skill and Reference Path Updates (FR-022)

**Purpose**: Update `.claude/skills/process-needs-action/SKILL.md` and any other skill files to use `_System/<folder>` operational paths and `Reference/` paths for handbook and business goals.

**⚠️ Depends on**: T036 (Phase B — folders now at `_System/`)

**Independent Test**: Run the `process-needs-action` skill. Verify it correctly reads from and writes to `_System/Needs_Action/`, `_System/In_Progress/`, `_System/Pending_Approval/`, `_System/Done/`. Verify it reads `Reference/Company_Handbook.md` and `Reference/Business_Goals.md`.

- [X] T061 Read `.claude/skills/process-needs-action/SKILL.md` in full and update every operational folder path reference from `Needs_Action/`, `In_Progress/`, `Pending_Approval/`, `Approved/`, `Rejected/`, `Done/`, `Plans/`, `Logs/` to their `_System/` equivalents (FR-018)
- [X] T062 [P] Update `.claude/skills/process-needs-action/SKILL.md` to reference `Reference/Company_Handbook.md` and `Reference/Business_Goals.md` wherever it currently references `Company_Handbook.md` or `Business_Goals.md` at vault root (FR-022)
- [X] T063 Update `AI_Employee_Vault/Pipeline.md` Kanban card wikilinks: update any cards whose links point to old root-level operational folder paths (e.g., `[[Needs_Action/FILE]]`) to point to `_System/` paths (e.g., `[[_System/Needs_Action/FILE]]`) — only update existing wikilinks, do not remove cards (US3 delta)

**Checkpoint**: process-needs-action skill runs correctly against `_System/` folder structure; Pipeline cards link to correct paths

---

## Phase H: Smoke Tests (Full System Verification)

**Purpose**: Manually verify all 9 success criteria from quickstart.md against actual Obsidian rendering. These tasks require manual verification in Obsidian desktop.

**⚠️ Depends on**: All Phases A–G complete

- [ ] T064 [P] Verify quickstart.md Test 1 (SC-007): Open Obsidian file explorer — count exactly 7 top-level vault items: Dashboard.md, Pipeline.md, Bank_Transactions.md, Briefings/, Accounting/, Reference/, _System/. Expand _System/ and verify all 12 operational folders present
- [ ] T065 [P] Verify quickstart.md Test 2 (SC-001, SC-002): Open `Dashboard.md` in reading view — 8 trigger buttons render, one button click creates a `SIGNAL_*` file in `_System/Needs_Action/` (or navigates to the confirmed fallback request note)
- [ ] T066 [P] Verify quickstart.md Test 3 (SC-003): Confirm all 3 Dataview tables in `Dashboard.md` render within 3 seconds — each shows items from `_System/` paths; clicking any row link opens the target file
- [ ] T067 [P] Verify quickstart.md Test 4 (FR-004a, SC-008): Each pending draft in `_System/Pending_Approval/` shows an approve/reject affordance on Dashboard; open any approval file directly and verify fast-path header with `_System/Approved/` and `_System/Rejected/` paths and approve/reject buttons (FR-004b)
- [ ] T068 [P] Verify quickstart.md Test 5 (SC-005): Open `Pipeline.md` — 4 Kanban columns render; click any card link and verify it opens a file under `_System/<folder>/`; Done column is collapsed by default
- [ ] T069 [P] Verify quickstart.md Test 6 (FR-022): Open `Reference/` in file explorer — `Company_Handbook.md` and `Business_Goals.md` are present and readable
- [ ] T070 [P] Verify quickstart.md Test 7 (SC-006): Close Obsidian fully and reopen — `Dashboard.md` is the first file shown automatically
- [ ] T071 [P] Verify quickstart.md Test 9 (FR-021): Confirm `Hubs/` folder does NOT appear in file explorer; no hub page files exist anywhere in vault; Dashboard Quick Navigation has no hub page links
- [ ] T072 Run quickstart.md Test 8 (SC-004, FR-007): Execute the `process-needs-action` skill — confirm it processes files from `_System/Needs_Action/` correctly, writes to `_System/Done/`, logs to `_System/Logs/`; then inspect `Dashboard.md` source view and count `AI_EMPLOYEE:` markers — must equal 22 (FR-007)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phases 1–7 (T001–T031)**: ✅ Complete
- **Phase A (T032–T034)**: No dependencies — can start immediately. **GATES Phase E (TE-002/TE-003 = T055/T056) and Phase F**
- **Phase B (T035–T037)**: Can start immediately. **GATES Phases C, E, F, G**
- **Phase C (T038–T048)**: Depends on Phase B (T036 complete)
- **Phase D (T049–T053)**: Independent — can start immediately (no dependency on _System/ move)
- **Phase E (T054–T058)**: Depends on Phase B (T036) AND Phase A (T034)
- **Phase F (T059–T060)**: Depends on Phase B (T036) AND Phase A (T034)
- **Phase G (T061–T063)**: Depends on Phase B (T036)
- **Phase H (T064–T072)**: Depends on all Phases A–G complete

### User Story Dependencies

- **US1 Delta (Phase E)**: Blocked by Phase A gate (T034) AND Phase B (T036) — begin after both
- **US2 Cleanup (Phase D)**: Independent — can start immediately
- **US3 Delta (T063 in Phase G)**: Depends on Phase B (T036) for correct `_System/` paths
- **US4 Delta (Phase F)**: Blocked by Phase A gate (T034) AND Phase B (T036)
- **US5**: ✅ Complete — no delta work

### Within Each Phase

- **Phase A**: T032 → T033 (parallel) → T034 (sequential, after both)
- **Phase B**: T035 → T036 → T037 (sequential)
- **Phase C**: T038 (sequential first — base class) → T039–T047 [P] (all parallel after T038) → T048 (sequential last)
- **Phase D**: T049–T052 [P] (all parallel) → T053 (sequential last)
- **Phase E**: T054 → T055 → T056 → T057 → T058 (sequential; each builds on previous)
- **Phase F**: T059 → T060 [P] (parallel per file after T059)
- **Phase G**: T061 → T062 [P] parallel with T061 after reading; T063 after T036
- **Phase H**: T064–T071 [P] (all parallel) → T072 (sequential last — skill run)

### Parallel Opportunities

```
Immediately (no dependencies):
  T032 + T033 [P]   (Phase A research, parallel)
  T035              (Phase B start — stop watchers)
  T049–T052 [P]     (Phase D hub page deletion, all parallel)

After T034 (Phase A gate) AND T036 (Phase B complete):
  Phase E (T054–T058 sequential)
  Phase F (T059 → T060 [P])

After T036 (Phase B complete):
  T039–T047 [P]     (Phase C parallel watcher updates, after T038)
  T061–T062 [P]     (Phase G skill updates, parallel)
  T063              (Phase G Pipeline card path updates)

After all Phases A–G:
  T064–T071 [P]     (Phase H smoke tests, all parallel)
  T072              (Phase H machine-layer test, sequential last)
```

---

## Implementation Strategy

### MVP Scope (Highest Impact First)

1. **Phase A** (T032–T034): Research gates — confirm button capabilities
2. **Phase B** (T035–T037): `_System/` folder move — structural foundation
3. **Phase C** (T038–T048): Python watcher path updates — keeps watchers functional
4. **Phase E** (T054–T058): Dashboard rewrite — delivers SC-001/SC-002 trigger buttons + correct Dataview paths
5. **VALIDATE**: Open Dashboard.md — 8 trigger buttons render; Dataview tables show `_System/` results
6. Demo-ready after Phase E

### Full Incremental Delivery

1. Phase A → Phase B → Phase C (infrastructure foundation)
2. Phase D (hub page deletion — can overlap with A/B/C)
3. Phase E (Dashboard delta) → validate independently
4. Phase F (Approval inline buttons) → validate independently
5. Phase G (Skill + Pipeline paths) → validate with process-needs-action skill run
6. Phase H (9 smoke tests) → full system validated

---

## Task Count Summary

| Phase | Tasks | Status | Parallelizable |
|-------|-------|--------|---------------|
| Phase 1 Setup | T001–T003 | ✅ Done | T002, T003 |
| Phase 2 Foundational | T004 | ✅ Done | — |
| Phase 3 US1 Dashboard | T005–T015 | ✅ Done | — |
| Phase 4 US2 Hub Pages | T016–T020 | ✅ Done (files to delete) | T016–T019 |
| Phase 5 US3 Pipeline | T021–T025 | ✅ Done | — |
| Phase 6 US4 Approval | T026–T030 | ✅ Done | T026+T028 |
| Phase 7 US5 Homepage | T031 | ✅ Done | T031 |
| Phase A Research | T032–T034 | ✅ Done | T032+T033 |
| Phase B _System/ Folder | T035–T037 | ✅ Done | — |
| Phase C Python Watchers | T038–T048 | ✅ Done | T039–T047 |
| Phase D Hub Deletion | T049–T053 | ✅ Done | T049–T052 |
| Phase E Dashboard Delta | T054–T058 | ✅ Done | — |
| Phase F Approval Buttons | T059–T060 | ✅ Done | T060 |
| Phase G Skill Paths | T061–T063 | ✅ Done | T062 |
| Phase H Smoke Tests | T064–T072 | ☐ Manual verification needed | T064–T071 |
| **Total** | **72** | **63 done / 9 pending (manual)** | **24 parallelizable** |

---

## Notes

- No database, no server code — all deliverables are `.md`, `.json`, and `.py` path constant changes
- **Stop watchers before Phase B** (T035) — prevents stale-path writes during the folder move
- **Phase A is a research gate**: T034 must complete before building trigger buttons (T055) or approve/reject buttons (T060)
- **Phase B is a structural gate**: T036 must complete before updating watcher scripts (Phase C), Dataview queries (Phase E), skill paths (Phase G), or approval file path references (Phase F)
- **Phase D is independent**: Hub page deletion has no dependency on _System/ folder move
- All Dataview query `FROM` clause changes are isolated to `Dashboard.md` (Phases 1–7 hub page Dataview is deleted with the hub files in Phase D)
- The `process-needs-action` SKILL.md update (T061–T062) must be additive — no existing processing logic removed or reordered
- Cloud VM watcher scripts (at `/root/Personal_AI_Employee/watchers/`) also need the same path updates as Phase C — apply the same changes via SSH after local verification (out of scope for this task list but noted for post-implementation)
