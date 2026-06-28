# Quickstart: Interactive Vault Redesign Verification

**Feature**: `001-vault-redesign-interactive`  
**Purpose**: Verify the redesign is working correctly after all delta tasks complete  
**Updated**: 2026-06-28 — reflects updated spec (hub pages removed, `_System/` folder, 8 trigger buttons, inline approve/reject)

---

## Pre-flight Checks

Before testing, verify:
1. Obsidian is open and the vault is `AI_Employee_Vault/`
2. All 6 plugins are enabled: Dataview, Buttons, Meta Bind, Kanban, Tasks, Homepage
3. Obsidian is in **Reading view** (Ctrl+E) for interactive elements to render
4. Vault root shows exactly 7 top-level items in the file explorer sidebar

---

## Test 1 — Vault Sidebar Structure (SC-007)

1. Open Obsidian file explorer sidebar
2. Count top-level items under `AI_Employee_Vault/`
3. Verify exactly 7 items: `Dashboard.md`, `Pipeline.md`, `Bank_Transactions.md`, `Briefings/`, `Accounting/`, `Reference/`, `_System/`
4. Expand `_System/` and verify all 12 operational folders are present

**Pass**: 7 top-level items; all 12 operational folders inside `_System/`  
**Fail**: More than 7 top-level items (old operational folders still at root); hub pages (`Hubs/`) still present

---

## Test 2 — Dashboard Quick Actions (SC-001, SC-002)

1. Open `Dashboard.md` in Reading view
2. Scroll to "Quick Actions" section
3. Verify 8 trigger buttons appear: 📧 Reply to Email, 💬 Reply to WhatsApp, 📣 Post on LinkedIn, 📘 Post on Facebook, 📸 Post on Instagram, 🐦 Post on Twitter/X, 💰 Create Invoice, 📊 Run CEO Briefing
4. Click one button → verify a `SIGNAL_*` file is created in `_System/Needs_Action/` (or the button navigates to the correct request note if using fallback pattern)

**Pass**: All 8 buttons render and trigger correctly  
**Fail**: Buttons show as raw markdown code blocks; fewer than 8 buttons visible; buttons navigate to hub pages instead of triggering action

---

## Test 3 — Live Dataview Tables (SC-003)

1. Open `Dashboard.md` in Reading view
2. Scroll to "Needs Action" section — verify Dataview table renders showing `_System/Needs_Action/` files
3. Scroll to "Pending Approvals" — verify Dataview table renders showing `_System/Pending_Approval/` files
4. Scroll to "Recent Completions" — verify list shows up to 10 items from `_System/Done/`
5. Time from file open to all tables rendered should be ≤3 seconds

**Pass**: Tables show live data from `_System/` paths; clicking any row link opens the target file  
**Fail**: Tables show raw DQL code; tables query old root-level paths; no data shown despite files existing in `_System/`

---

## Test 4 — Inline Approve/Reject (FR-004a, SC-008)

1. Open `Dashboard.md` in Reading view
2. Scroll to "Pending Approvals" section
3. For each pending draft row: verify there is an approve/reject affordance (button or clear instruction text)
4. Open any file in `_System/Pending_Approval/` directly
5. Verify within the first 10 lines: action type, key parameters, and approve/reject instructions are visible (FR-004b)

**Pass**: Each pending draft has visible approve/reject affordance; individual approval file has fast-path header with clear instructions  
**Fail**: Approval table shows only file links with no approve/reject affordance; approval files lack fast-path headers

---

## Test 5 — Pipeline Kanban Board (SC-005)

1. Open `Pipeline.md`
2. Verify 4 columns render: Needs Action, In Progress, Pending Approval, Done (Recent)
3. Click any card → verify it links to a file under `_System/<folder>/<filename>` (not old root-level paths)
4. Verify Done column is collapsed by default

**Pass**: Kanban renders with 4 columns; card wikilinks point to `_System/` paths  
**Fail**: Cards link to old root-level paths; Kanban shows raw markdown

---

## Test 6 — Reference Folder (FR-022)

1. Open Obsidian file explorer and navigate to `Reference/`
2. Verify `Company_Handbook.md` and `Business_Goals.md` are present
3. Open each file — verify content is intact (handbook rules, business goals)

**Pass**: Both files present and readable  
**Fail**: Files missing; still at root level

---

## Test 7 — Homepage Auto-Open (SC-006)

1. Close Obsidian completely
2. Reopen Obsidian
3. Verify `Dashboard.md` is the first file shown

**Pass**: Dashboard opens automatically on launch  
**Fail**: Last open file shows instead (homepage data.json misconfigured or plugin not enabled)

---

## Test 8 — Machine-Layer Preservation (SC-004, FR-007)

1. Run the process-needs-action skill: "Run the process-needs-action skill"
2. Verify skill completes without errors (no `ERROR_*` files created in `_System/Needs_Action/`)
3. Verify files in `_System/Needs_Action/` are processed and move to `_System/Done/`
4. Open `Dashboard.md` in source view (Ctrl+E) and count `<!-- AI_EMPLOYEE:` tags — must equal 22 pairs

**Pass**: Skill processes correctly using `_System/` paths; all 22 AI_EMPLOYEE markers intact  
**Fail**: Errors created; markers missing; skill writes to old root-level paths

---

## Test 9 — Hub Pages Deleted (FR-021)

1. Open Obsidian file explorer
2. Confirm `Hubs/` folder does NOT exist
3. Confirm no `WhatsApp_Hub.md`, `Email_Hub.md`, `Finance_Hub.md`, `Social_Hub.md` at vault root
4. Confirm Dashboard has no navigation links to hub pages

**Pass**: Hub pages absent; Dashboard links only to pipeline, briefings, bank transactions, accounting, reference  
**Fail**: Hub page files still exist; Dashboard still links to hub pages

---

## Known Limitations

- **Dataview refresh**: Tables may show slightly stale data for 1-2 seconds after a file changes — this is normal Dataview indexing behaviour.
- **Buttons in editing view**: Buttons render only in Reading view. This is by design.
- **Pipeline.md manual maintenance**: The Kanban board is updated by Claude during process-needs-action runs. Between runs, the board may lag behind actual vault state.
- **Trigger button file creation**: If Meta Bind `createNote` action is unavailable in 1.4.15, the fallback pattern (navigation to a request note) is used. Both satisfy FR-004 intent.
- **Homepage on mobile**: Homepage plugin behaviour may differ on Obsidian mobile — this is out of scope.
- **Cloud vault paths**: Cloud VM Syncthing syncs the vault. After `_System/` folder move, the cloud vault will receive the restructured vault via sync. Cloud watcher scripts must also be updated with new paths (same TC-001–TC-010 changes applied to `/root/Personal_AI_Employee/watchers/`).
