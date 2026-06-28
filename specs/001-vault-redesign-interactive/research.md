# Research: Interactive Obsidian Vault Redesign

**Feature**: `001-vault-redesign-interactive`  
**Phase**: 0 — Research & Decision Record  
**Date**: 2026-06-28

---

## 1. Plugin Inventory & Version Analysis

All 6 required plugins are installed and enabled in `AI_Employee_Vault/.obsidian/community-plugins.json`.

| Plugin | ID | Version | Key Finding |
|--------|----|---------|-------------|
| Dataview | `dataview` | 0.5.68 | Stable; full DQL support including `startswith()`, `contains()`, `lower()`, `dateformat()`, `TABLE WITHOUT ID`, `LIST WITHOUT ID`, `LIMIT` |
| Buttons | `buttons` | 0.9.13 | Classic code block syntax; `type link` with `action [[Note Name]]` is the most stable navigation pattern |
| Meta Bind | `obsidian-meta-bind-plugin` | 1.4.15 | Modern YAML button blocks with `meta-bind-button` code fence; inline `BUTTON[id]` references allow side-by-side buttons in a text line |
| Kanban | `obsidian-kanban` | 2.0.51 | Latest 2.x series; frontmatter `kanban-plugin: board`; `## Heading` = column; `- [ ] text [[link]]` = card; supports tags and wikilinks |
| Homepage | `homepage` | 4.4.4 | Stores config in `data.json`; points to a specific note by name; `openOnStartup: true` triggers on Obsidian launch |
| Tasks | `obsidian-tasks-plugin` | latest | Standard Tasks query blocks; available if needed for task-based filtering |

**Decision**: Use Dataview as the primary query engine (most powerful for file-based vault data). Use Buttons plugin for quick-action navigation. Use Meta Bind inline `BUTTON[id]` for side-by-side button rows. Use Kanban for Pipeline board.

---

## 2. Dataview Query Patterns (Confirmed for v0.5.68)

### File name prefix filtering

```dataview
TABLE WITHOUT ID
  file.link AS "Task",
  dateformat(file.mtime, "yyyy-MM-dd HH:mm") AS "Modified"
FROM "Needs_Action"
WHERE startswith(file.name, "WA_") OR startswith(file.name, "WHATSAPP_")
SORT file.mtime ASC
```

- **Decision**: Use `startswith()` for prefix matching — cleaner than `contains()` on name.
- **Rationale**: File names created by watchers always start with the domain prefix (`WA_`, `GMAIL_`, `FINANCE_`, etc.). Prefix matching is exact and avoids false positives.
- **Alternatives considered**: `contains(file.name, "WA")` — rejected because it would match any file with "WA" anywhere in the name.

### Multi-domain filter (social)

```dataview
WHERE contains(lower(file.name), "linkedin") OR contains(lower(file.name), "facebook") OR contains(lower(file.name), "instagram") OR contains(lower(file.name), "twitter")
```

- **Decision**: Use `contains(lower())` for social platforms — approval file names contain the platform name but not as a strict prefix (e.g., `APPROVAL_20260627T120600Z_linkedin_lead-gen-post.md`).
- **Rationale**: Social approval files use the pattern `APPROVAL_<timestamp>_<platform>_<slug>`. Platform name is not the prefix but is reliably present in the name.

### Done folder with prefix filter

```dataview
LIST WITHOUT ID file.link
FROM "Done"
WHERE startswith(file.name, "DONE_WA_") OR startswith(file.name, "DONE_WHATSAPP_")
SORT file.mtime DESC
LIMIT 10
```

- **Decision**: Filter `Done/` by `DONE_<ORIGINAL_PREFIX>` pattern — watcher conventions prepend `DONE_` when moving files.
- **Rationale**: Completed files retain their original prefix inside the `DONE_` prefix. Verified against actual vault files: `DONE_WA_20260322T071112Z_Mummy.md`, `DONE_GMAIL_20260320T081250Z_*.md`.

### Performance limit

- **Decision**: `LIMIT 10` on all `Done/` queries; `LIMIT 20` on `Pending_Approval/` queries.
- **Rationale**: `Done/` already contains 100+ files and grows indefinitely. Uncapped queries cause noticeable render lag. 10 items is sufficient for the "recent" view context.

---

## 3. Buttons Plugin Syntax (v0.9.13)

Confirmed working syntax for navigation:

```
```button
name Label Text
type link
action [[Note Name]]
color blue
```
```

- **Available colors**: `blue`, `red`, `green`, `purple`, `yellow`, `default`
- **Link format**: Wikilink `[[Note Name]]` (without path prefix if file is at vault root)
- **Limitation**: Buttons render as block elements — one button per row by default.

**Decision**: Use Buttons plugin for the main quick-action row on Dashboard and hub pages.  
**Rationale**: Simple, battle-tested syntax. Works reliably in reading view without additional configuration.

---

## 4. Meta Bind Button Syntax (v1.4.15)

For side-by-side inline button rows:

**Step 1** — Define button with ID (can be anywhere in note, or in a hidden block):
```
```meta-bind-button
id: "btn-dashboard"
label: "← Dashboard"
style: secondary
hidden: true
actions:
  - type: open
    link: "[[Dashboard]]"
```
```

**Step 2** — Reference inline in text:
```
`BUTTON[btn-dashboard]` `BUTTON[btn-whatsapp]` `BUTTON[btn-finance]`
```

- **Available styles**: `primary` (filled), `secondary` (outlined), `destructive` (red), `plain`
- **Available action types**: `open` (navigate to link), `command` (run Obsidian command), `js` (JavaScript — **disabled** in current config: `enableJs: false`)
- **Decision**: Use Meta Bind inline buttons for hub page navigation rows (sibling hub links). Use standard Buttons plugin for Dashboard quick-actions (more prominent visual treatment).
- **Rationale**: Meta Bind inline syntax allows 3-4 navigation links in a single compact line. Buttons plugin blocks are better for the primary CTA buttons on Dashboard.

---

## 5. Kanban Plugin Format (v2.0.51)

Confirmed board format:

```markdown
---
kanban-plugin: board
---

## 📥 Column 1

- [ ] [[Note Link|Card Display Text]] #tag

## 🔄 Column 2

- [ ] [[Another Note|Another Card]]

%% kanban:settings
```
{"kanban-plugin":"board","list-collapse":[false,false,false,true]}
```
%%
```

- **Column headers**: `## Column Name` — each becomes a Kanban column
- **Cards**: `- [ ] text` — unchecked items are active cards; `- [x]` are completed
- **Links**: Wikilinks `[[Note]]` inside card text make cards clickable
- **Tags**: `#tag` appears as a coloured chip on the card
- **Settings block**: Embedded in `%% ... %%` comment block at file end
- **Decision**: Use Kanban for `Pipeline.md` with 4 columns (Needs Action, In Progress, Pending Approval, Done). Cards include wikilinks and domain tags.

---

## 6. Homepage Plugin Configuration (v4.4.4)

The plugin stores its configuration in `AI_Employee_Vault/.obsidian/plugins/homepage/data.json`. This file does **not currently exist** — the plugin is installed but not configured.

**Required data.json format** (confirmed from plugin source for v4.x):

```json
{
  "version": "4.4.4",
  "manualOpenMode": "active",
  "openOnStartup": true,
  "openMode": "active",
  "value": "Dashboard",
  "kind": "File",
  "commands": [],
  "alwaysApply": false,
  "revertView": false,
  "refreshDataview": true
}
```

Key fields:
- `value`: Note name without `.md` extension
- `kind`: `"File"` for a regular note
- `openOnStartup`: `true` to open on Obsidian launch
- `refreshDataview`: `true` to trigger Dataview refresh when opening the homepage
- **Decision**: Create this file during implementation with `Dashboard` as the value.
- **Rationale**: `refreshDataview: true` ensures Dataview tables are fresh when the homepage loads, preventing stale cache on startup.

---

## 7. Vault File Naming Convention Analysis

Analysed actual watcher output files across the vault to confirm domain prefix conventions:

| Domain | Needs_Action prefix | Pending_Approval suffix | Done prefix |
|--------|--------------------|-----------------------|-------------|
| WhatsApp | `WA_` | (none currently) | `DONE_WA_` |
| Gmail/Email | `GMAIL_` | `email_<address>` | `DONE_GMAIL_`, `DONE_EMAIL_` |
| Finance | `FINANCE_` | `finance_TXN*` | `DONE_FINANCE_` |
| Social (LinkedIn) | (none from watcher) | `linkedin_*` | (none) |
| Social (Facebook) | (none from watcher) | `facebook_*` | (none) |
| Files | `FILE_` | (none) | `DONE_FILE_` |
| Tasks (manual) | `TASK_` | (none) | (none) |
| Errors | `ERROR_` | (none) | (none) |
| Loop state | `LOOP_` | (none) | `DONE_LOOP_`, `LOOP_` |

**Key insight**: Social media items appear in `Pending_Approval/` (not `Needs_Action/`) because they are created by Claude as approval requests, not detected by a watcher. The social hub must therefore query `Pending_Approval/` as the primary source.

**Decision**: Hub page queries use `startswith()` for `Needs_Action/` (strict prefix) and `contains(lower())` for `Pending_Approval/` (platform name in approval filename).

---

## 8. Machine-Layer Preservation Analysis

Reviewed Dashboard.md for AI-writable comment markers that must be preserved:

```
<!-- AI_EMPLOYEE:UPDATED --> ... <!-- /AI_EMPLOYEE:UPDATED -->
<!-- AI_EMPLOYEE:CLOUD_STATUS --> ... <!-- /AI_EMPLOYEE:CLOUD_STATUS -->
<!-- AI_EMPLOYEE:CLOUD_AGENT_STATUS --> ... <!-- /AI_EMPLOYEE:CLOUD_AGENT_STATUS -->
<!-- AI_EMPLOYEE:CLOUD_LAST_HEARTBEAT --> ... <!-- /AI_EMPLOYEE:CLOUD_LAST_HEARTBEAT -->
<!-- AI_EMPLOYEE:IN_PROGRESS_CLOUD --> ... <!-- /AI_EMPLOYEE:IN_PROGRESS_CLOUD -->
<!-- AI_EMPLOYEE:IN_PROGRESS_LOCAL --> ... <!-- /AI_EMPLOYEE:IN_PROGRESS_LOCAL -->
<!-- AI_EMPLOYEE:VAULT_SYNC_LAST_OK --> ... <!-- /AI_EMPLOYEE:VAULT_SYNC_LAST_OK -->
<!-- AI_EMPLOYEE:CLOUD_WATCHER_STATUS --> ... <!-- /AI_EMPLOYEE:CLOUD_WATCHER_STATUS -->
<!-- AI_EMPLOYEE:CLOUD_RECENT_UPDATES --> ... <!-- /AI_EMPLOYEE:CLOUD_RECENT_UPDATES -->
<!-- AI_EMPLOYEE:COMPLIANCE_STATUS --> ... <!-- /AI_EMPLOYEE:COMPLIANCE_STATUS -->
<!-- AI_EMPLOYEE:COMPLIANCE_RESULT --> ... <!-- /AI_EMPLOYEE:COMPLIANCE_RESULT -->
<!-- AI_EMPLOYEE:COMPLIANCE_DATE --> ... <!-- /AI_EMPLOYEE:COMPLIANCE_DATE -->
<!-- AI_EMPLOYEE:COMPLIANCE_REPORT --> ... <!-- /AI_EMPLOYEE:COMPLIANCE_REPORT -->
<!-- AI_EMPLOYEE:COMPLIANCE_COUNTS --> ... <!-- /AI_EMPLOYEE:COMPLIANCE_COUNTS -->
<!-- AI_EMPLOYEE:NEEDS_ACTION_COUNT --> ... <!-- /AI_EMPLOYEE:NEEDS_ACTION_COUNT -->
<!-- AI_EMPLOYEE:DONE_TODAY_COUNT --> ... <!-- /AI_EMPLOYEE:DONE_TODAY_COUNT -->
<!-- AI_EMPLOYEE:INBOX_COUNT --> ... <!-- /AI_EMPLOYEE:INBOX_COUNT -->
<!-- AI_EMPLOYEE:ACTIVE_ITEMS --> ... <!-- /AI_EMPLOYEE:ACTIVE_ITEMS -->
<!-- AI_EMPLOYEE:RECENT_COMPLETIONS --> ... <!-- /AI_EMPLOYEE:RECENT_COMPLETIONS -->
<!-- AI_EMPLOYEE:PENDING_APPROVALS --> ... <!-- /AI_EMPLOYEE:PENDING_APPROVALS -->
<!-- AI_EMPLOYEE:PENDING_APPROVAL_LIST --> ... <!-- /AI_EMPLOYEE:PENDING_APPROVAL_LIST -->
<!-- AI_EMPLOYEE:RECENT_REJECTIONS --> ... <!-- /AI_EMPLOYEE:RECENT_REJECTIONS -->
```

**Decision**: Keep all 22 AI_EMPLOYEE marker pairs in Dashboard.md. The Dataview tables are **additive** — they coexist with the static AI-written sections. The Dataview section shows the live view; the AI-written section shows the last-processed snapshot (useful when Claude has not run recently).
**Rationale**: Having both gives resilience: if Dataview plugin is disabled, the static snapshot still works. If Claude hasn't run recently, Dataview shows the current live state.

---

## 9. Architecture Decision: Static + Live Dual-Layer Dashboard

**Decision**: Dashboard.md uses a dual-layer approach:
1. **Live layer** (Dataview queries): Auto-refreshes from vault state. Shows current reality.
2. **Static layer** (AI_EMPLOYEE markers): Updated by Claude during processing runs. Shows last-processed audit trail.

**Rationale**: This satisfies Principle XII (Reliability) — if Dataview is unavailable, the static layer still functions. If Claude hasn't run, the live layer shows what's actually in the vault.

**Alternatives considered**:
- Live-only (remove all static markers): Rejected — breaks Claude's ability to update Dashboard with its audit trail.
- Static-only (remove Dataview): Rejected — requires Claude to run to see current state; doesn't satisfy SC-001 (30-second time-to-awareness).

---

## 10. process-needs-action Skill Update Scope

**Decision**: The `process-needs-action` skill MUST be updated to sync the Pipeline.md Kanban board when processing items (move items between columns as tasks progress through the workflow).

**Rationale**: Pipeline.md is a manually-maintained Kanban board. Without skill-level updates, the board will drift out of sync with actual vault state. The skill already moves files between folders — adding a Pipeline.md sync step is a natural extension.

**Scope**: When a file is moved from `Needs_Action/` → `In_Progress/`, or from `In_Progress/` → `Done/`, the skill should update the corresponding card in Pipeline.md. This is an additive change to the existing skill with no impact on other functionality.

---

## 11. Trigger Button Capability (Phase A Research — T032/T033)

**Method**: Inspected `AI_Employee_Vault/.obsidian/plugins/obsidian-meta-bind-plugin/main.js` (1.4.15) for action type definitions and argument schemas. Both action types were found with 8 occurrences each.

### createNote — Available ✅

Confirmed action type `createNote` exists in Meta Bind 1.4.15.

**Schema**:
```yaml
- type: createNote
  folderPath: "_System/Needs_Action"   # optional, defaults to vault root
  fileName: "SIGNAL_email_request"     # required, no .md extension
  openNote: false                      # optional
  openIfAlreadyExists: false           # optional
```

**Limitation**: `fileName` is a static string — dynamic timestamps require Templater plugin (not installed) or JS (disabled: `enableJs: false`). Signal files must use fixed per-action names.

**Chosen pattern for trigger buttons**:
Each of the 8 trigger buttons creates a fixed-name signal file. The watcher detects file creation and triggers processing. Fixed names are overwritten on each click (idempotent for watcher triggers):
- `SIGNAL_email_request.md` → 📧 Reply to Email
- `SIGNAL_whatsapp_request.md` → 💬 Reply to WhatsApp
- `SIGNAL_linkedin_post.md` → 📣 Post on LinkedIn
- `SIGNAL_facebook_post.md` → 📘 Post on Facebook
- `SIGNAL_instagram_post.md` → 📸 Post on Instagram
- `SIGNAL_twitter_post.md` → 🐦 Post on Twitter/X
- `SIGNAL_invoice_create.md` → 💰 Create Invoice
- `SIGNAL_ceo_briefing.md` → 📊 Run CEO Briefing

### updateMetadata — Available ✅

Confirmed action type `updateMetadata` exists in Meta Bind 1.4.15.

**Schema**:
```yaml
- type: updateMetadata
  bindTarget: "status"     # frontmatter field name
  evaluate: false          # whether to evaluate value as JS expression
  value: "approved"        # new value to set
```

**Chosen pattern for approve/reject buttons**:
Each approval file gets YAML frontmatter with `status: pending`. Two Meta Bind buttons update it:
- Approve button: sets `status: approved`
- Reject button: sets `status: destructive`

The approval watcher monitors `_System/Pending_Approval/` for files where `status` changes to `approved`/`rejected` and moves them accordingly.

**Fallback** (if buttons fail in reading view): Keep the existing `> [!caution]` callout with explicit move instructions (`_System/Approved/` or `_System/Rejected/`).

---

## Summary of Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | Dataview for live queries; Buttons for primary CTAs; Meta Bind for inline sibling navigation | Each tool used for its strongest capability |
| 2 | `startswith()` for Needs_Action prefix filtering | Exact prefix match; no false positives |
| 3 | `contains(lower())` for social/approval filename filtering | Platform name embedded mid-filename in approval files |
| 4 | `LIMIT 10` on Done/, `LIMIT 20` on Pending_Approval/ | Performance guard; sufficient for the "recent" context |
| 5 | Homepage data.json: `Dashboard`, `openOnStartup: true`, `refreshDataview: true` | Ensures fresh queries on startup |
| 6 | Dual-layer Dashboard (Dataview live + AI_EMPLOYEE static markers coexist) | Resilience; both layers provide value independently |
| 7 | Social Hub queries Pending_Approval/ (not Needs_Action/) | Social posts only appear as approval requests, not watcher detections |
| 8 | process-needs-action skill gets Pipeline.md sync step | Keeps Kanban board in sync without manual maintenance |
