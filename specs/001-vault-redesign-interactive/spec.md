# Feature Specification: Interactive Obsidian Vault Redesign

**Feature Branch**: `001-vault-redesign-interactive`  
**Created**: 2026-06-28  
**Status**: Draft  
**Input**: User description: "Redesign the Obsidian vault. It should be such that it is easier to manage, whatsapp, invoices, social media posts etc. all from the dashboard. The folder structure can be modified but it must not go against the hackathon requirements. All files should be interactive and easier to look using plugins such as Dataview, Tasks, Buttons, Meta Bind, Kanban and homepage."

---

## Clarifications

### Session 2026-06-28

- Q: What should Dashboard action buttons trigger? → A: Claude creates a draft reply/action; Ali reviews it and approves or rejects it via inline Approve/Reject buttons — no manual file-moving required.
- Q: Where should Ali approve/reject drafts? → A: Both. Dashboard shows each draft as a clickable link to open the full file AND inline Approve/Reject buttons for quick action without navigating away. Each individual draft file also has its own Approve/Reject buttons for when Ali reads the full content first.
- Q: Should the 4 domain hub pages (WhatsApp_Hub, Email_Hub, Finance_Hub, Social_Hub) be kept? → A: No — hub pages removed entirely. Dashboard is the single screen for all actions, drafts, and approvals.
- Q: Which action buttons should appear on the Dashboard? → A: All 8 — 📧 Reply to Email, 💬 Reply to WhatsApp, 📣 Post on LinkedIn, 📘 Post on Facebook, 📸 Post on Instagram, 🐦 Post on Twitter/X, 💰 Create Invoice, 📊 Run CEO Briefing.
- Q: What should the Obsidian sidebar show? → A: Option A — collapse all AI-managed operational folders into one `_System/` parent folder. Sidebar shows only: Dashboard.md, Pipeline.md, Bank_Transactions.md, Briefings/, Accounting/, Reference/, _System/ (collapsed). This requires watcher script path updates (scope expansion from original spec).

## Context & Constraints

The Obsidian vault is the GUI and long-term memory of a Platinum-tier Personal AI Employee (hackathon project). It serves as the communication bus between Python watcher scripts, Claude Code, and MCP action servers. Any redesign **must preserve**:

- All machine-writable folders that watchers and Claude create files in — they will be nested under `_System/` but must not be renamed or deleted
- All files that watcher scripts append to (`Bank_Transactions.md`, `Accounting/Current_Month.md`, `Dashboard.md`)
- The HITL approval flow: `_System/Pending_Approval/` → `_System/Approved/` → `_System/Rejected/`
- The claim-by-move rule for multi-agent coordination (`_System/In_Progress/<agent>/`)
- Single-writer rule for `Dashboard.md` (Local agent only)

**Target vault root (human-facing)**:
```
AI_Employee_Vault/
├── Dashboard.md          ← single control screen, opens on launch
├── Pipeline.md           ← Kanban board
├── Bank_Transactions.md  ← finance log (watcher-appended)
├── Briefings/            ← CEO briefings
├── Accounting/           ← monthly accounting files
├── Reference/            ← Company_Handbook.md, Business_Goals.md
└── _System/              ← all AI-managed operational folders (collapsed)
    ├── Needs_Action/
    ├── In_Progress/
    ├── Pending_Approval/
    ├── Approved/
    ├── Rejected/
    ├── Done/
    ├── Inbox/
    ├── Plans/
    ├── Logs/
    ├── Signals/
    ├── Updates/
    └── Sync/
```

**Scope expansion**: Moving operational folders under `_System/` requires updating all Python watcher script paths and Dataview queries (previously out of scope — now in scope).

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Unified Control Center Dashboard (Priority: P1)

Ali opens his laptop in the morning and wants an at-a-glance view of everything: pending WhatsApp messages, emails awaiting approval, invoices to review, social posts to approve, system health, and finance summary — all from `Dashboard.md` without navigating away.

**Why this priority**: The dashboard is the first thing opened daily. A poor dashboard means the whole system feels unusable. Fixing this delivers immediate, daily value to the primary user.

**Independent Test**: Open `Dashboard.md` in Obsidian reading view. Without clicking any links, the reader should see: system status for all watchers, count and list of Needs Action items, count and list of pending approvals, a finance net summary, and clickable quick-action buttons.

**Acceptance Scenarios**:

1. **Given** the vault has 2 items in `Needs_Action/` and 10 in `Pending_Approval/`, **When** Ali opens `Dashboard.md` in reading view, **Then** both counts appear with live Dataview tables listing each item as a clickable link.
2. **Given** a new approval file is added to `Pending_Approval/` by Claude, **When** Ali re-opens or refreshes Dashboard, **Then** the Dataview table automatically includes the new item.
3. **Given** Ali wants to navigate to a specific domain (WhatsApp, Finance, Social), **When** he views the Dashboard, **Then** dedicated quick-action buttons are visible and functional in reading view.
4. **Given** watchers are running, **When** Ali views Dashboard, **Then** each watcher shows a colour-coded status callout (green = online, yellow = degraded, red = stopped).
5. **Given** `Done/` contains many completed files, **When** Dashboard renders the Recent Completions section, **Then** only the 10 most recent items are shown (no performance lag).

---

~~### User Story 2 — Domain Hub Pages~~ *(Removed — hub pages eliminated; Dashboard is the single screen)*

---

### User Story 3 — Visual Kanban Pipeline Board (Priority: P2)

Ali wants a visual Kanban board showing all tasks across their lifecycle stages (Needs Action → In Progress → Pending Approval → Done), so he can see work-in-flight at a glance and manage workflow state visually.

**Why this priority**: The Kanban view provides spatial context that flat lists don't. It reveals bottlenecks (e.g., 10 items stuck in Pending Approval) at a glance.

**Independent Test**: Open `Pipeline.md` in Obsidian. The Kanban plugin renders 4 columns. Each column contains the current items for that stage. Cards link to their source files.

**Acceptance Scenarios**:

1. **Given** `Pipeline.md` exists with the Kanban plugin frontmatter, **When** Ali opens it, **Then** the Kanban board renders 4 columns: Needs Action, In Progress, Pending Approval, Done (Recent).
2. **Given** a task card exists in any column, **When** Ali clicks it, **Then** he is taken to the source file in the vault.
3. **Given** the current vault state with 10 pending approvals and 2 needs-action items, **When** Ali views the Pipeline, **Then** all items are represented in the correct columns.

---

### User Story 4 — Approval Fast-Path (Priority: P2)

When Ali has pending approval files, he wants to review and action them with minimal friction — each approval file should have a clear summary, the action to be taken, and unambiguous instructions for approving or rejecting.

**Why this priority**: The approval flow is the most frequent human action in the system. Friction here blocks every downstream automated action.

**Independent Test**: Open any file in `Pending_Approval/`. Without reading more than 10 lines, Ali can understand: what action is pending, the key parameters (amount, recipient, or post content), and exactly how to approve or reject it.

**Acceptance Scenarios**:

1. **Given** a finance approval file, **When** Ali opens it, **Then** he sees: action type, amount and payee, Odoo reference, and a clear "Move to Approved/ to proceed / Rejected/ to decline" instruction.
2. **Given** a social media approval file, **When** Ali opens it, **Then** the full post content, target platform, and approval instruction are visible without scrolling.
3. **Given** Ali views the Dashboard Pending Approvals Dataview table, **When** he clicks any approval link, **Then** he is taken directly to that file.

---

### User Story 5 — Homepage Integration (Priority: P3)

Ali wants `Dashboard.md` to open automatically when he launches Obsidian, so he never has to navigate there manually.

**Why this priority**: A quality-of-life improvement that reinforces the daily habit of reviewing the Dashboard. Low effort, immediate benefit.

**Independent Test**: Close and reopen Obsidian. The first file shown is `Dashboard.md`.

**Acceptance Scenarios**:

1. **Given** the Homepage plugin is configured with `Dashboard.md` as the home note, **When** Obsidian launches, **Then** `Dashboard.md` is the active tab without any manual navigation.
2. **Given** Obsidian is open on another file, **When** Ali activates the "Go Home" function (via command palette or plugin shortcut), **Then** `Dashboard.md` becomes the active view.

---

### Edge Cases

- What happens when `Needs_Action/` is empty? Dataview tables show a styled empty state (e.g., a callout saying "Nothing pending — all clear!") rather than a blank section.
- What happens when `Done/` has hundreds of files? All Dataview queries on `Done/` include `LIMIT 10` to prevent rendering lag.
- What happens when a Dataview query references a non-existent folder? The query silently returns no results — no error shown to the user.
- How do hub pages categorise items that cross domains (e.g., an email about an invoice)? Items are categorised by file name prefix as created by the watcher (source of truth), not by content.
- What happens when the Finance Watcher appends new rows to `Bank_Transactions.md`? The machine-appendable table is preserved at the bottom; summary callouts above it are updated manually by Claude during processing runs, not by the watcher.
- What happens if a watcher creates a new file prefix not currently covered by hub page filters? The item appears in the Needs Action section of Dashboard (catch-all) but not in any domain hub — this is acceptable and expected.

---

## Requirements *(mandatory)*

### Functional Requirements

**Dashboard**

- **FR-001**: `Dashboard.md` MUST display a live Dataview table of all files in `Needs_Action/` (excluding `ERROR_*` files), sorted by modification time ascending, with each row as a clickable link.
- **FR-002**: `Dashboard.md` MUST display a live Dataview table of all files in `Pending_Approval/`, sorted by modification time descending, limited to 20 rows.
- **FR-003**: `Dashboard.md` MUST display status callouts for each system watcher using Obsidian callout syntax (`> [!success]`, `> [!warning]`, `> [!danger]`).
- **FR-004**: `Dashboard.md` MUST include exactly 8 quick-action trigger buttons: 📧 Reply to Email, 💬 Reply to WhatsApp, 📣 Post on LinkedIn, 📘 Post on Facebook, 📸 Post on Instagram, 🐦 Post on Twitter/X, 💰 Create Invoice, 📊 Run CEO Briefing. Each button creates a signal/trigger file in `Needs_Action/`; Claude processes it and writes a draft to `Pending_Approval/`.
- **FR-004a**: The Pending Approvals section on `Dashboard.md` MUST show each pending draft as a clickable link (to open the full file) AND with inline ✅ Approve and ❌ Reject buttons alongside it, so Ali can either read the full draft or approve/reject directly from the Dashboard.
- **FR-004b**: Each individual approval/draft file in `Pending_Approval/` MUST ALSO contain its own Approve and Reject buttons for when Ali opens the file to read the full draft before deciding.
- **FR-005**: `Dashboard.md` MUST display a finance summary section with current-month income, expense, and net totals.
- **FR-006**: `Dashboard.md` MUST display the 10 most recent completed items from `Done/` using a Dataview list query sorted by modification time descending.
- **FR-007**: All existing AI-writable comment markers (e.g., `<!-- AI_EMPLOYEE:UPDATED -->`, `<!-- AI_EMPLOYEE:PENDING_APPROVALS -->`) MUST be preserved in `Dashboard.md` so Claude can continue updating the file.

~~**Hub Pages**~~ *(FR-008 through FR-012 removed — hub pages eliminated per clarification 2026-06-28)*

**Kanban Pipeline**

- **FR-013**: `Pipeline.md` MUST use the Kanban plugin frontmatter (`kanban-plugin: board`) and render 4 columns: Needs Action, In Progress, Pending Approval, Done (Recent).
- **FR-014**: Each Kanban card MUST link to its source file via Obsidian wikilinks.

**Bank Transactions**

- **FR-015**: `Bank_Transactions.md` MUST retain the machine-appendable markdown table so the Finance Watcher can add rows without modification.
- **FR-016**: `Bank_Transactions.md` MUST include monthly summary callout sections above the table showing income, expense, and net totals.

**Homepage**

- **FR-017**: The Homepage plugin configuration (`homepage` field in plugin data) MUST be set to `Dashboard` so Obsidian opens `Dashboard.md` on launch.

**Preservation (Non-Negotiable)**

- **FR-018**: The following folders MUST NOT be renamed or deleted — they are moved under `_System/` but keep their existing names: `Inbox/`, `Needs_Action/`, `In_Progress/`, `Plans/`, `Pending_Approval/`, `Approved/`, `Rejected/`, `Done/`, `Logs/`, `Updates/`, `Signals/`, `Sync/`. All Python watcher scripts and Dataview queries must be updated to reflect the `_System/<folder>` path.
- **FR-019**: File naming conventions created by watchers MUST NOT be changed. Dataview filters rely on these prefixes: `WA_`, `WHATSAPP_`, `GMAIL_`, `EMAIL_`, `FINANCE_`, `APPROVAL_`, `DONE_`, `ERROR_`, `PLAN_`, `LOOP_`, `TASK_`, `SIGNAL_`, `HEARTBEAT_`.
- **FR-020**: `Dashboard.md` Pending Approvals section MUST render each item as: `[clickable link to draft file] [✅ Approve button] [❌ Reject button]` in a single row.
- **FR-021**: Hub page files (`WhatsApp_Hub.md`, `Email_Hub.md`, `Finance_Hub.md`, `Social_Hub.md`) MUST be deleted — the Dashboard is the single control screen.
- **FR-022**: `Reference/` folder MUST contain `Company_Handbook.md` and `Business_Goals.md`. All skill files that reference these must use path `AI_Employee_Vault/Reference/Company_Handbook.md` and `AI_Employee_Vault/Reference/Business_Goals.md`.

### Key Entities

- **Hub Page**: A human-facing `.md` file using Dataview and Buttons to aggregate domain-specific vault data. Read-only from the machine's perspective — watchers never write to hub pages.
- **Quick Action Button**: A Buttons plugin block (`type link`) that navigates to a specific note. Renders in Obsidian reading view.
- **Dataview Query**: A live-refreshing query block reading vault file metadata (name, modification time, path) to generate tables and lists. Refreshes automatically when the vault changes.
- **Watcher File**: A `.md` file created by a Python watcher in `Needs_Action/`. File name prefix identifies the source channel and is the primary classification signal.
- **Approval File**: A `.md` file in `Pending_Approval/` representing a sensitive action pending human sign-off. The only required human action is moving the file to `Approved/` or `Rejected/`.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Ali can see all pending items and take action within 30 seconds of opening Obsidian, without navigating away from `Dashboard.md`.
- **SC-002**: Ali can trigger any of the 8 task actions (email reply, WhatsApp reply, 4 social posts, invoice, briefing) from the Dashboard in exactly 1 button click.
- **SC-003**: All Dataview tables on Dashboard render within 3 seconds of the file opening, even with 100+ files in `_System/Done/`.
- **SC-004**: Zero machine-layer breakage — all watcher scripts function correctly with updated `_System/<folder>` paths, and approval workflows fire correctly via button-triggered status changes.
- **SC-005**: The Pipeline Kanban board renders with all 4 columns and all current pending items correctly placed.
- **SC-006**: Obsidian opens to `Dashboard.md` automatically on every launch (Homepage plugin configured).
- **SC-007**: The Obsidian sidebar shows 7 or fewer top-level items (Dashboard.md, Pipeline.md, Bank_Transactions.md, Briefings/, Accounting/, Reference/, _System/).
- **SC-008**: Every pending draft in `_System/Pending_Approval/` shows on Dashboard as a clickable link with inline Approve and Reject buttons.

---

## Assumptions

1. The Obsidian vault root is the `AI_Employee_Vault/` directory — all Dataview paths are relative to this root (e.g., `"Needs_Action"` not `"AI_Employee_Vault/Needs_Action"`).
2. Dataview, Buttons, Meta Bind, Tasks, Kanban, and Homepage plugins are installed and enabled — no additional plugin installation is required.
3. File name prefixes created by watchers are stable. Dataview filters use these prefixes for domain classification.
4. Hub pages are not machine-written — watchers and Claude do not modify hub pages during normal processing.
5. The `Dashboard.md` AI-writable comment markers are preserved; only content within or around them changes structurally.
6. Buttons plugin `type link` navigation is used for quick-action buttons (most stable syntax across plugin versions).
7. Dataview `LIMIT 10` on `Done/` and `LIMIT 20` on `Pending_Approval/` is sufficient for expected vault scale.
8. The Kanban Pipeline board is manually updated by Claude during `process-needs-action` skill runs — it is not auto-generated from live vault state.

---

## Out of Scope

- CSS snippet customisation for Obsidian visual theming.
- Mobile Obsidian compatibility.
- Changes to MCP server code or external service integrations.

**No longer out of scope (scope expanded via clarification 2026-06-28)**:
- Python watcher script path updates (required to support `_System/` folder nesting).
- Skill file path updates (required for `Reference/` folder).
- Hub page files (deleted, not added to).
- Approval file inline buttons (new addition to HITL format).
