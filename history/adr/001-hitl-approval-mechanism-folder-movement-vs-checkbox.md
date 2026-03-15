# ADR-001: HITL Approval Mechanism — Folder-Movement vs Checkbox

- **Status:** Accepted
- **Date:** 2026-03-15
- **Feature:** 002-silver-ai-employee
- **Context:** The Silver Tier requires a Human-in-the-Loop (HITL) approval gate for all outbound sensitive actions (email replies, LinkedIn posts). Two distinct patterns exist: (1) in-place checkbox editing within a markdown plan file, or (2) explicit file movement between vault folders. The Bronze Tier constitution (Principle III) was drafted before Silver Tier design, and mandated the checkbox pattern. During Silver Tier planning, the folder-movement pattern was selected as the canonical approach, creating a constitution conflict that this ADR formally resolves.

## Decision

**Adopted pattern: Folder-Movement HITL**

The approval workflow operates as a strict folder-based state machine:

1. **Write**: Skill writes `Pending_Approval/APPROVAL_<ts>_<action>.md` with action type and parameters
2. **Gate**: Execution is blocked until the file moves out of `Pending_Approval/`
3. **Approve**: Human drags/moves file to `Approved/` in Obsidian → ApprovalWatcher detects → triggers `execute-plan`
4. **Reject**: Human drags/moves file to `Rejected/` → logged, archived, never executed
5. **Execute**: `execute-plan` skill reads the approved file, calls MCP tool, moves all related files to `Done/`

**Supersedes**: Constitution Principle III's `[ ] APPROVE` checkbox mandate.

**Affected components**:
- `watchers/approval_watcher.py` — polls `Approved/` for new files
- `.claude/skills/process-needs-action/SKILL.md` — writes to `Pending_Approval/`, not checkbox-in-place
- `.claude/skills/linkedin-post/SKILL.md` — same
- `.claude/skills/execute-plan/SKILL.md` — reads from `Approved/`, not from checkbox state
- `AI_Employee_Vault/`: new folders `Pending_Approval/`, `Approved/`, `Rejected/`
- `scripts/processed_approvals.json` — idempotency registry for ApprovalWatcher
- `constitution.md` Principle III — must be updated to reflect this decision

## Consequences

### Positive

- **Native Obsidian UX**: Drag-and-drop between folders is the primary Obsidian interaction model. No markdown syntax knowledge needed; any non-technical user can approve by moving a file.
- **Unambiguous state**: A file is either in `Pending_Approval/` (waiting) or `Approved/` (ready). There is no ambiguity about checkbox syntax (`[ ]` vs `[x]` vs `[X]`).
- **Reliable detection**: `ApprovalWatcher` polls `Approved/` for new files — a filesystem event with no parsing. Checkbox detection would require reading file contents and diffing markdown state, which is fragile on NTFS/PollingObserver.
- **Idempotency**: `processed_approvals.json` ensures each approval fires exactly once even if the watcher restarts mid-execution.
- **Rejection is explicit**: `Rejected/` folder captures declined actions permanently. Checkbox pattern has no equivalent rejected state.
- **Constitution alignment**: Folder-movement is consistent with Constitution Principle II (folder-based state machine). Checkboxes are an exception to the folder state model; folder-movement is an extension of it.

### Negative

- **More vault folders**: Three new folders (`Pending_Approval/`, `Approved/`, `Rejected/`) add to vault complexity vs zero new folders with the checkbox approach.
- **Requires running watcher**: Approval detection requires `ApprovalWatcher` to be running. With checkboxes, any file save could trigger detection. If the orchestrator crashes, approvals queue silently.
- **No inline review**: The human reviews approval content in `APPROVAL_*.md` separately from `Plans/PLAN_*.md`. With checkboxes, the plan and approval gate are in one file. Mitigated by: `APPROVAL_*.md` contains the full action parameters for review.
- **Constitution update required**: Constitution Principle III must be amended (MINOR bump to v1.1.0) to avoid ongoing violation flags in future `/sp.analyze` runs.

## Alternatives Considered

### Alternative A: In-Place Checkbox Editing (original constitution mandate)

Skills write `Plans/PLAN_*.md` containing `[ ] APPROVE: send email to alice@example.com`. A file-watcher reads the plan file, detects when the checkbox changes to `[X]`, and triggers execution.

**Why rejected**:
- Checkbox state detection requires parsing markdown file contents on every poll cycle — fragile, especially on PollingObserver (NTFS does not reliably surface content-change events, only create/delete/rename).
- `[ ]` vs `[x]` vs `[X]` ambiguity; users may type wrong case.
- No clean `Rejected` state — a user who does not want to approve has no action to take; items silently expire.
- Mixes the plan document (reasoning artifact) with the approval gate (action signal) in a single file — violates separation of concerns.
- Does not align with Constitution Principle II's folder state machine; requires a content-scanning side-channel instead.

### Alternative B: External Approval UI (web form, Telegram bot, email reply)

Generate an approval link or Telegram message; human clicks to approve.

**Why rejected**:
- Out of scope for Silver Tier (adds external service dependencies: web server or bot platform).
- Obsidian vault is the single source of truth per Constitution Principle II; external approval breaks this invariant.
- Introduces credential management for additional services.
- Deferred to Gold/Platinum tier if desired.

### Alternative C: Time-based auto-approval (approve after N minutes if no rejection)

**Why rejected**:
- Violates Constitution Principle III — "The following actions MUST NOT be executed autonomously under any circumstances: External communication."
- Non-starter for any tier.

## References

- Feature Spec: `specs/002-silver-ai-employee/spec.md` (FR-008, FR-016, SC-006)
- Implementation Plan: `specs/002-silver-ai-employee/plan.md` (Module 3 ApprovalWatcher, R-005 research decision)
- Research: `specs/002-silver-ai-employee/research.md` (R-005: HITL Approval — Folder-Movement Pattern)
- Constitution: `.specify/memory/constitution.md` (Principle III — requires update to v1.1.0)
- Analysis: `history/prompts/002-silver-ai-employee/0001-silver-tier-consistency-analysis.misc.prompt.md` (finding C1)
- Related ADRs: None (first ADR)
