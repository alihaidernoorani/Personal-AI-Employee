---
id: "007"
title: Plan WhatsApp Cron Scheduler Fixes
stage: plan
date: 2026-03-15
surface: agent
model: claude-sonnet-4-6
feature: 002-silver-ai-employee
branch: 002-silver-ai-employee
user: alihaidernoorani
command: /sp.plan
labels: ["plan","whatsapp","cron","scheduler","error-handling","hitl","fr-005","fr-018","fr-020"]
links:
  spec: specs/002-silver-ai-employee/spec.md
  ticket: null
  adr: history/adr/001-hitl-approval-mechanism-folder-movement-vs-checkbox.md
  pr: null
files:
  - specs/002-silver-ai-employee/plan.md
  - specs/002-silver-ai-employee/tasks.md
tests:
  - null
---

## Prompt

Update the Silver Tier plan to fix the following four issues identified in /sp.analyze:

1. C2 — WhatsApp cron interval: Remove the "0 * * * *" (hourly) WhatsApp cron entry from Module 9. WhatsApp watcher is a persistent long-running daemon (internal 60s polling loop), not a one-shot cron job. The orchestrator starts it and keeps it alive. Cron only manages Gmail (every 5 min), LinkedIn post (Monday 8 AM), and process-needs-action (daily 9 AM).

2. I2 — Scheduler detection: Add a --cron boolean flag to orchestrator.py. Log actor: scheduler only when --cron is passed. Update the crontab entries in install-cron.sh to pass --cron. This prevents manual --watcher runs from being mislogged as scheduler events.

3. G1 — Watcher error handling: In Module 1 (GmailWatcher) and Module 2 (WhatsAppWatcher), explicitly require that check_for_updates() wraps its body in try/except. On any non-fatal exception: write Needs_Action/ERROR_<ts>_<watcher-name>.md and continue the polling loop. This satisfies FR-005.

4. G2 — execute-plan failure recovery: In Module 6 (execute-plan skill), the failure branch must also update Plans/PLAN_*.md frontmatter status back to "awaiting_approval" before writing ERROR_*.md. This satisfies FR-018 fully.

Do not change any other modules, data flows, or phases.

## Response snapshot

Eight targeted edits applied across plan.md and tasks.md — no modules added or removed.

plan.md changes:
- Module 1: Added error handling requirement (try/except + ERROR_*.md)
- Module 2: Added persistent daemon lifecycle note + error handling requirement; WhatsApp is NOT cron-managed
- Module 6: Added explicit failure branch sequence (status revert → ERROR_*.md → restore APPROVAL_*.md)
- Module 8: Added --cron flag description alongside --watcher
- Module 9: Removed WhatsApp cron entry; schedule is now 3 entries with --cron flag on Gmail

tasks.md changes:
- T007 notes: error handling requirement added
- T008 notes: persistent daemon + error handling added
- T010: description updated to cover both --watcher and --cron flags
- T017: expected outcome updated to cover failure branch
- T023: description updated to 3 cron entries (no WhatsApp); --cron flag added to Gmail entry
- T024: detection changed from --watcher presence to --cron presence

## Outcome

- ✅ Impact: C2, I2, G1, G2 all closed in plan.md and tasks.md; all 7 /sp.analyze findings now resolved
- 🧪 Tests: T025 (US4 validation) covers SC-007; T019 covers failure branch
- 📁 Files: plan.md (Modules 1, 2, 6, 8, 9 updated), tasks.md (T007, T008, T010, T017, T023, T024 updated)
- 🔁 Next prompts: /sp.analyze for final clean pass to confirm zero issues
- 🧠 Reflection: WhatsApp daemon design is the correct pattern — persistent process with internal sleep loop, not cron-managed. The --cron flag cleanly separates automated from manual invocations.

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): FR-005 coverage (G1) — PASS; FR-018 full coverage (G2) — PASS; SC-002 ≤60s (C2) — PASS; FR-020 unambiguous (I2) — PASS
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): null
