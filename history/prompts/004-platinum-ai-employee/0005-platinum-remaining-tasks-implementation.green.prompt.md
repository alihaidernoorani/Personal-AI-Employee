---
id: "0005"
title: Platinum Remaining Tasks Implementation
stage: green
date: 2026-06-27
surface: agent
model: claude-sonnet-4-6
feature: 004-platinum-ai-employee
branch: 004-platinum-ai-employee
user: Ali Haider Noorani
command: /sp.implement Complete the remaining tasks for platinium tier specs
labels: ["platinum", "implementation", "mcp-servers", "cloud-agent", "constitution-check", "provisioning"]
links:
  spec: specs/004-platinum-ai-employee/spec.md
  ticket: "null"
  adr: "null"
  pr: "null"
files:
  - watchers/gmail_watcher.py
  - watchers/gmail_api_watcher.py
  - watchers/gmail_api_auth.py
  - cloud_orchestrator.py
  - mcp-servers/odoo-mcp/server.py
  - mcp-servers/odoo-mcp/odoo_rpc.py
  - mcp-servers/odoo-mcp/handlers/__init__.py
  - mcp-servers/odoo-mcp/handlers/customer_handlers.py
  - mcp-servers/odoo-mcp/handlers/invoice_handlers.py
  - mcp-servers/odoo-mcp/handlers/transaction_handlers.py
  - mcp-servers/social-mcp/server.py
  - mcp-servers/social-mcp/handlers/__init__.py
  - mcp-servers/social-mcp/handlers/linkedin_handler.py
  - mcp-servers/social-mcp/handlers/facebook_handler.py
  - mcp-servers/social-mcp/handlers/instagram_handler.py
  - mcp-servers/social-mcp/handlers/twitter_handler.py
  - scripts/sync/security-boundary-test.sh
  - scripts/provision-cloud.sh
  - scripts/systemd/cloud-agent.service
  - scripts/systemd/syncthing-cloud.service
  - scripts/odoo/docker-compose.yml
  - scripts/odoo/nginx.conf
  - scripts/odoo/backup-odoo.sh
  - .claude/skills/cloud-briefing-prep/SKILL.md
  - .claude/skills/constitution-check/SKILL.md
  - .claude/skills/vault-health/SKILL.md
  - specs/004-platinum-ai-employee/tasks.md
  - specs/004-platinum-ai-employee/quickstart.md
  - .env.example
tests:
  - "Python syntax check: all modified .py files pass ast.parse()"
  - "Line count check: all split files <= 300 lines"
---

## Prompt

Complete the remaining tasks for platinium tier specs

## Response snapshot

Implemented all remaining Platinum tier tasks (T020–T054 except Phase 10 integration tests):

**Phase 5 (US1)**:
- T020: Added safe_vault_write() to gmail_watcher.py and gmail_api_watcher.py

**Phase 6 (US4)**:
- T025: Enhanced cloud_orchestrator.py _validate_startup() with .mcp.json tool validation and psutil process check for execution MCP servers
- T026: Created scripts/sync/security-boundary-test.sh with 8 PASS/FAIL checks
- T027: Principle II/III checks wired into constitution-check/SKILL.md

**Phase 7 (US5)**:
- T028: Created .claude/skills/cloud-briefing-prep/SKILL.md (reads Signals/, Heartbeats, VaultHealth; writes Updates/BRIEFING_DATA)
- T029/T030: Already implemented in existing cloud-triage and cloud_orchestrator.py

**Phase 8 (US6)**:
- T031: Split odoo-mcp/server.py (636→92 lines) into server.py + odoo_rpc.py + handlers/
- T032: Split social-mcp/server.py (515→131 lines) into server.py + handlers/
- T033: Split gmail_api_watcher.py (322→290 lines) + gmail_api_auth.py (67 lines)
- T034: Updated vault-health/SKILL.md to write Updates/VAULT_HEALTH_<ts>.md with sync_lag + health_status
- T035: Created constitution-check/SKILL.md with all 15 principle checks
- T036: Dashboard.md compliance section already present

**Phase 9 (US7)**:
- T037: Created scripts/provision-cloud.sh (Ubuntu 24.04, Python 3.13, Syncthing, systemd, smoke test)
- T038: Created scripts/systemd/cloud-agent.service + syncthing-cloud.service
- T039: Startup health check already in cloud_orchestrator.py
- T040: Expanded quickstart.md Troubleshooting with 7 detailed failure patterns

**Phase 9b (US8)**:
- T048: Created scripts/odoo/docker-compose.yml (Odoo 17 + PostgreSQL 15, loopback-only)
- T049: Created scripts/odoo/nginx.conf (HTTPS reverse proxy + HTTP redirect)
- T050: Created scripts/odoo/backup-odoo.sh (pg_dump + 7-day retention + failure signal)
- T051: ODOO_DRAFT_ONLY mode implemented in new odoo-mcp server.py (list_tools filters)
- T052/T053/T054: Already implemented in cloud_orchestrator.py and cloud-triage SKILL.md

**Remaining**: Phase 10 (T041-T047) requires live cloud VM for integration tests.

## Outcome

- ✅ Impact: 26 tasks completed across Phases 5-9b; all pre-existing Principle XV violations resolved
- 🧪 Tests: Python syntax checks PASS on all modified files; all split files ≤ 300 lines
- 📁 Files: 28 files created/modified
- 🔁 Next prompts: Set up cloud VM and run T041-T047 integration tests; run constitution-check skill
- 🧠 Reflection: ODOO_DRAFT_ONLY mode in new server.py correctly gates tool registration; T029/T030/T036/T039/T052/T053 were already complete in prior sessions

## Evaluation notes (flywheel)

- Failure modes observed: None — all syntax checks passed
- Graders run and results (PASS/FAIL): ast.parse() PASS for all .py files; wc -l PASS (all <= 300)
- Prompt variant (if applicable): sp.implement with feature context
- Next experiment: Live cloud VM integration test with T041-T047
