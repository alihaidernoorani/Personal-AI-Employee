---
id: "005"
title: gold-tier-gap-remediation
stage: misc
date: 2026-03-22
surface: agent
model: claude-sonnet-4-6
feature: 003-gold-ai-employee
branch: 003-gold-ai-employee
user: DELL
command: resolve all gaps from sp.analyze
labels: ["remediation","spec","plan","tasks","consistency","gold-tier"]
links:
  spec: specs/003-gold-ai-employee/spec.md
  ticket: "null"
  adr: "null"
  pr: "null"
files:
  - specs/003-gold-ai-employee/spec.md
  - specs/003-gold-ai-employee/plan.md
  - specs/003-gold-ai-employee/tasks.md
tests:
  - "17/17 automated fix-verification checks"
---

## Prompt

Resolve all gaps as recommended by you, while making sure it meets the gold tier hackathon requirements

## Response snapshot

Applied all 17 fixes from the sp.analyze report across spec.md, plan.md, and tasks.md. All 17 automated verification checks passed. All 12 Gold tier hackathon requirements remain satisfied.

**Changes by file:**

**spec.md (5 changes)**:
- FR-027: Replaced "sole data sources = 2 files" with 5 explicit local data sources (Business_Goals.md, Bank_Transactions.md, Done/, Needs_Action/+In_Progress/, Logs/)
- FR-026: Enumerated all 7 mandatory CEO briefing sections including Upcoming Deadlines and Social Media Summary
- FR-017: Added "WhatsApp outbound messages (all replies and proactive messages)" to always-require-approval list
- NFR-001: Added testable acceptance criteria alongside the 7-day production SLA
- User Story 3: Added acceptance scenario 4 — WhatsApp reply HITL gate

**plan.md (7 changes)**:
- Architecture diagram: email-mcp, social-mcp labels changed from "(Node.js)" to "(Python)"
- Architecture diagram: naming changed from underscores (email_mcp/) to hyphens (email-mcp/)
- Architecture diagram: `create_payment` replaced with `post_invoice` (matches odoo-mcp contract)
- Section 2.3 execute-plan: added step 4 for `get_post_summary` call after social posts
- Section 2.3 ceo-briefing: expanded to 7 steps listing all 5 data sources with explicit section mapping
- Section 2.6: replaced `social_mcp/index.js (Node.js)` with `mcp-servers/social-mcp/server.py (Python)`
- Section 5.1/5.2 headings: corrected from Node.js to Python with correct file paths

**tasks.md (10 changes)**:
- T007: Changed "within 120 s" to "within **60 s**" to match NFR-005
- T002: Removed duplicate filesystem-watcher test (kept in T009)
- T003: Replaced `claude --mcp-list` with `.mcp.json` file inspection + server start verification
- T010b (NEW): Build `Accounting/Current_Month.md` as dual-append target alongside `Bank_Transactions.md`
- T012b (NEW): Verify no watcher contains reasoning logic (FR-006 verification gate)
- T021: Added HTTPS/NFR-012 check (grep for http:// in server code)
- T027/T034: Replaced `claude --mcp-list` with `.mcp.json` entry inspection
- T065: Added mtime-based 30s latency assertion for NFR-007
- T073: Added malformed-task silent-fail test for FR-038
- T074: Replaced impossible "no restarts" criterion with realistic stability test + kill/restart verification

## Outcome

- ✅ Impact: All 17 identified gaps resolved; spec, plan, and tasks are now mutually consistent; all 12 Gold tier hackathon requirements remain covered
- 🧪 Tests: 17/17 automated string-presence verification checks passed
- 📁 Files: spec.md, plan.md, tasks.md (all modified); no new source code files created
- 🔁 Next prompts: `/sp.implement` to begin Gold tier implementation starting from Phase 1
- 🧠 Reflection: The most impactful single fix was FR-027 — a spec clause that contradicted the implementation design would have caused a spec-compliance test failure even on a correctly built system. The WhatsApp HITL gap (M6) was a constitution violation that could have led to unsanctioned outbound messages. Both are now explicitly resolved.

## Evaluation notes (flywheel)

- Failure modes observed: Internal plan.md inconsistencies (diagram vs. text vs. contracts) arose because the ASCII diagram was updated manually while contracts were generated independently; automated diagram generation would prevent this class of drift
- Graders run and results (PASS/FAIL): 17/17 automated checks PASS; manual read of each changed section confirms semantic correctness
- Prompt variant (if applicable): Direct remediation from sp.analyze findings
- Next experiment: Add a pre-commit hook that greps for `(Node.js)`, `create_payment`, `claude --mcp-list` and similar known-bad patterns to catch regressions
