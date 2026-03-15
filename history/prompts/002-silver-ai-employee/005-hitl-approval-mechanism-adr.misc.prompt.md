---
id: "005"
title: HITL Approval Mechanism ADR
stage: misc
date: 2026-03-15
surface: agent
model: claude-sonnet-4-6
feature: 002-silver-ai-employee
branch: 002-silver-ai-employee
user: alihaidernoorani
command: /sp.adr
labels: ["adr","hitl","approval","folder-movement","constitution"]
links:
  spec: specs/002-silver-ai-employee/spec.md
  ticket: null
  adr: history/adr/001-hitl-approval-mechanism-folder-movement-vs-checkbox.md
  pr: null
files:
  - history/adr/0001-hitl-approval-mechanism-folder-movement-vs-checkbox.md
tests:
  - null
---

## Prompt

/sp.adr hitl-approval-mechanism

## Response snapshot

Created ADR-0001 documenting the HITL approval mechanism decision: folder-movement pattern (Pending_Approval/ → Approved/ or Rejected/) adopted over checkbox-based in-place editing.

Decision covers: ApprovalWatcher, process-needs-action skill, linkedin-post skill, execute-plan skill, three new vault folders, processed_approvals.json registry, and required constitution Principle III update.

Three alternatives considered and rejected: checkbox editing (fragile on NTFS PollingObserver, no rejected state), external approval UI (out of scope), time-based auto-approval (violates constitution).

## Outcome

- ✅ Impact: ADR-0001 created; formally resolves C1 CRITICAL finding from /sp.analyze; justifies constitution v1.1.0 update
- 🧪 Tests: N/A
- 📁 Files: history/adr/0001-hitl-approval-mechanism-folder-movement-vs-checkbox.md created
- 🔁 Next prompts: /sp.constitution to update Principle III to v1.1.0; then /sp.specify and /sp.plan for remaining fixes
- 🧠 Reflection: All three significance tests pass — cross-cutting (affects 5 components), alternatives documented, will be revisited in Gold tier when external approval UI is considered

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): Significance checklist — PASS (impact, alternatives, cross-cutting all true)
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): null
