---
id: 002
title: Silver AI Employee Implementation Plan
stage: plan
date: 2026-03-13
surface: agent
model: claude-sonnet-4-6
feature: 002-silver-ai-employee
branch: 002-silver-ai-employee
user: alihaidernoorani
command: /sp.plan
labels: ["plan","silver","ai-employee","gmail","whatsapp","linkedin","email-mcp","hitl","scheduling","three-layer"]
links:
  spec: specs/002-silver-ai-employee/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/002-silver-ai-employee/plan.md
  - specs/002-silver-ai-employee/research.md
  - specs/002-silver-ai-employee/data-model.md
  - specs/002-silver-ai-employee/quickstart.md
  - specs/002-silver-ai-employee/contracts/task-file-schema.md
  - specs/002-silver-ai-employee/contracts/approval-request-schema.md
  - specs/002-silver-ai-employee/contracts/log-entry-schema.md
tests:
  - Constitution Check: 6/6 PASS
---

## Prompt

```text
Create an implementation plan for the Silver Tier Functional Assistant.

Three-layer architecture: Perception → Reasoning → Action.

Perception Layer: Gmail Watcher + WhatsApp Watcher (minimum two watchers).
Reasoning Layer: Claude Agent Skills loop reading Needs_Action, generating Plans.
Action Layer: email-mcp (required), LinkedIn via Playwright.

HITL approval: Pending_Approval/ → Approved/ / Rejected/ folder movement.
Vault: Inbox/, Needs_Action/, Plans/, Pending_Approval/, Approved/, Rejected/, Done/, Logs/.
Core files: Dashboard.md, Company_Handbook.md, Business_Goals.md.
Scheduling: cron (Linux) / Task Scheduler (Windows).
```

## Response snapshot

Dispatched 3 parallel research agents (Gmail, WhatsApp, LinkedIn). Key findings:
- Gmail: imaplib + App Password (no OAuth2 needed)
- WhatsApp: playwright Python library polling WhatsApp Web (not whatsapp-web.js)
- LinkedIn: existing browsing-with-playwright Playwright MCP (no new linkedin-mcp server)

Produced:
- `research.md` — 6 decisions (R-001 to R-006)
- `plan.md` — three-layer architecture, 9 modules, 2 data flows, 5 implementation phases
- `data-model.md` — 5 entities (TaskFile, PlanFile, ApprovalRequest, ProcessedRegistry, LogEntry)
- `quickstart.md` — 11-step setup guide with troubleshooting table
- `contracts/` — 3 schema files (task-file, approval-request, log-entry)

Constitution Check: 6/6 PASS. Key design decisions:
- HITL via folder movement (Pending_Approval → Approved/Rejected), not checkbox-in-place
- email-mcp is the required MCP server (send_email, draft_reply, search_inbox tools)
- LinkedIn posting via existing browsing-with-playwright Playwright MCP
- ApprovalWatcher polls Approved/ (PollingObserver, 5s interval)

📋 Architectural decision detected: Folder-movement HITL pattern vs checkbox-in-place approval — Document reasoning? Run `/sp.adr hitl-approval-pattern`

## Outcome

- ✅ Impact: Complete Silver Tier implementation plan. 5 phases, 9 modules, 11-step quickstart.
- 🧪 Tests: Constitution Check 6/6 PASS; 10-step end-to-end acceptance flow defined.
- 📁 Files: plan.md, research.md, data-model.md, quickstart.md, contracts/ (3 files)
- 🔁 Next prompts: `/sp.tasks` to generate the task list for implementation.
- 🧠 Reflection: Research agents confirmed no linkedin-mcp exists in the ecosystem — using existing Playwright MCP is the right call. WhatsApp Web automation via Python playwright is more stable than whatsapp-web.js.

## Evaluation notes (flywheel)

- Failure modes observed: First write attempt for plan.md was rejected by user mid-session as they had updated requirements (folder-movement HITL vs checkbox). Incorporated updated requirements correctly on retry.
- Graders run and results (PASS/FAIL): Constitution Check 6/6 PASS
- Prompt variant (if applicable): /sp.plan with explicit three-layer architecture requirements
- Next experiment: Consider ADR for HITL pattern choice
