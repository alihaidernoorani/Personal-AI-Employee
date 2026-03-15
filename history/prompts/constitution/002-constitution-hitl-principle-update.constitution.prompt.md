---
id: "002"
title: Constitution HITL Principle Update
stage: constitution
date: 2026-03-15
surface: agent
model: claude-sonnet-4-6
feature: none
branch: 002-silver-ai-employee
user: alihaidernoorani
command: /sp.constitution
labels: ["constitution","hitl","approval","folder-movement","v1.1.0"]
links:
  spec: null
  ticket: null
  adr: history/adr/0001-hitl-approval-mechanism-folder-movement-vs-checkbox.md
  pr: null
files:
  - .specify/memory/constitution.md
tests:
  - null
---

## Prompt

Update Principle III (Human-in-the-Loop Safety) to replace the checkbox-based approval gate with the folder-movement pattern.

Current text to replace:
"The mandatory approval gate: skills MUST draft intents in Plans/ as .md files containing [ ] APPROVE checkboxes. Execution MUST be blocked until a human checks the box. No skill MAY poll or auto-approve its own approval request."

Replace with:
"The mandatory approval gate: skills MUST write an APPROVAL_*.md file to Pending_Approval/ alongside a Plans/PLAN_*.md draft. Execution MUST be blocked until a human explicitly moves the APPROVAL_*.md file into Approved/. No skill MAY auto-approve its own approval request. Files in Rejected/ are archived and never re-executed."

Keep all other principles unchanged. Bump version to 1.1.0 (MINOR — approval gate mechanism updated).

## Response snapshot

Constitution updated from v1.0.0 to v1.1.0. Only Principle III was modified.

Old gate: `Plans/` + `[ ] APPROVE` checkbox → execution on checkbox check
New gate: `Pending_Approval/APPROVAL_*.md` → execution on file move to `Approved/`; `Rejected/` for declined actions

All four templates reviewed — none contain hardcoded checkbox references; no template changes required.

Sync Impact Report prepended as HTML comment. ADR-0001 referenced.

Deferred: CLAUDE.md HITL section and spec FR-007 still use old language — manual follow-up needed.

## Outcome

- ✅ Impact: C1 CRITICAL finding from /sp.analyze resolved; constitution now consistent with all three Silver Tier artifacts
- 🧪 Tests: Re-run /sp.analyze after remaining fixes to confirm zero CRITICAL issues
- 📁 Files: .specify/memory/constitution.md updated (v1.0.0 → v1.1.0)
- 🔁 Next prompts: /sp.specify to fix FR-007; then manual CLAUDE.md HITL section update; then /sp.plan + /sp.tasks for C2/I2/G1/G2
- 🧠 Reflection: MINOR bump correct — approval mechanism is a clarification of how HITL works, not a removal of the principle itself

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): Version bump type — MINOR PASS (new mechanism, not principle removal); No placeholder tokens remaining — PASS
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): null
