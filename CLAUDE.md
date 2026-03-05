# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **Personal AI Employee** — a hackathon project to build a "Digital FTE" (Full-Time Equivalent) autonomous agent. The system proactively manages personal affairs (Gmail, WhatsApp, Bank) and business operations (Social Media, Payments, Project Tasks) using Claude Code as the reasoning engine and Obsidian as the management dashboard/memory.

**Tagline:** *Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.*

## Tech Stack

| Layer | Technology | Role |
|-------|-----------|------|
| Brain | Claude Code (claude-sonnet-4-6 or higher) | Reasoning engine |
| Memory/GUI | Obsidian (local Markdown vault) | Dashboard & long-term memory |
| Senses | Python 3.13+ Watcher scripts | Monitors Gmail, WhatsApp, filesystem |
| Hands | MCP servers (Node.js v24+ / Python) | External actions (email send, browser, calendar) |
| Orchestration | `orchestrator.py` (Python) | Timing, folder watching, process management |
| Automation | Playwright | Web automation for payments and WhatsApp Web |

## Obsidian Vault Structure

The vault (`AI_Employee_Vault/`) is the core state store. All inter-component communication happens via files in this structure:

```
AI_Employee_Vault/
├── Dashboard.md              # Real-time summary (bank balance, pending messages, projects)
├── Company_Handbook.md       # Rules of engagement for the agent
├── Business_Goals.md         # OKRs, revenue targets, subscription audit rules
├── Inbox/                    # Raw incoming items
├── Needs_Action/             # Watcher-created .md files awaiting Claude processing
├── In_Progress/<agent>/      # Claimed tasks (claim-by-move rule prevents double-work)
├── Pending_Approval/         # Sensitive actions waiting for human approval
├── Approved/                 # Human-approved actions; triggers MCP execution
├── Rejected/                 # Declined actions
├── Done/                     # Completed tasks (Ralph Wiggum checks here for exit)
├── Plans/                    # Claude-generated Plan.md files with checkboxes
├── Briefings/                # Weekly CEO briefing outputs (YYYY-MM-DD_Monday_Briefing.md)
├── Accounting/               # Bank transaction logs (Current_Month.md)
├── Logs/                     # Audit logs (YYYY-MM-DD.json, retain 90 days)
└── Active_Project/           # Manual drag-and-drop to trigger project-based work
```

## Core Architecture Patterns

> **WSL2 note:** `/mnt/c` NTFS mounts don't support `inotify`. `filesystem_watcher.py` uses `PollingObserver` (3s interval) instead of the default `InotifyObserver`.

### 1. Watcher Pattern (Perception Layer)
All watchers extend `BaseWatcher` (`base_watcher.py`) with two required methods:
- `check_for_updates() -> list` — polls the external source
- `create_action_file(item) -> Path` — writes a `.md` file to `/Needs_Action/`

Implemented watchers:
- `gmail_watcher.py` — Gmail API, polls every 120s for unread+important
- `whatsapp_watcher.py` — Playwright on WhatsApp Web, polls every 30s for keyword-filtered unreads
- `filesystem_watcher.py` — `watchdog` library monitors a drop folder

### 2. Ralph Wiggum Loop (Persistence Pattern)
A Claude Code Stop hook that prevents exit until a task is complete:
1. Orchestrator creates a state file with the prompt
2. Claude works; attempts exit
3. Stop hook checks if task file is in `/Done/`
4. If NO → blocks exit, re-injects prompt, continues loop
5. If YES → allows exit

Two completion strategies:
- **Promise-based (simple):** Claude outputs `<promise>TASK_COMPLETE</promise>`
- **File movement (Gold tier):** Stop hook detects task file moved to `/Done/`

### 3. Human-in-the-Loop (HITL) Pattern
For sensitive actions, Claude writes to `/Pending_Approval/` instead of acting directly. File schema:
```yaml
---
type: approval_request
action: payment          # or email_send, social_post, etc.
amount: 500.00
status: pending
expires: <ISO timestamp>
---
```
The orchestrator watches `/Approved/` and triggers the MCP action when files appear. **Banking retries always require fresh approval — never auto-retry payments.**

### 4. Claim-by-Move Rule (Multi-Agent / Platinum tier)
First agent to move an item from `/Needs_Action/` to `/In_Progress/<agent>/` owns it. Other agents must skip claimed items. `Dashboard.md` is single-writer (Local agent only).

## Security Requirements

- Credentials go in `.env` (gitignored) or OS keychain — never in the vault
- All action scripts must support `DRY_RUN=true` env flag (default: true in dev)
- Every action must be logged to `/Vault/Logs/YYYY-MM-DD.json` with `action_type`, `actor`, `approval_status`, `result`
- Permission thresholds: payments < $50 to known payees auto-approve; all new payees or > $100 always require HITL; file deletes and moves outside vault always require HITL

## Audit Log Format

```json
{
  "timestamp": "ISO-8601",
  "action_type": "email_send",
  "actor": "claude_code",
  "target": "recipient",
  "parameters": {},
  "approval_status": "approved | auto | pending",
  "approved_by": "human | system",
  "result": "success | failure"
}
```

## Development Setup

```bash
# Python environment (use uv)
uv init
uv add google-auth google-api-python-client playwright watchdog python-dotenv

# Install Playwright browsers
playwright install chromium

# Node.js MCP servers
npm install  # from the MCP server directory

# Verify Claude Code
claude --version
```

Environment variables (`.env`):
```
GMAIL_CLIENT_ID=
GMAIL_CLIENT_SECRET=
BANK_API_TOKEN=
WHATSAPP_SESSION_PATH=/secure/path/session
DRY_RUN=true
VAULT_PATH=/path/to/AI_Employee_Vault
```

## MCP Server Configuration

MCP servers are configured in `~/.config/claude-code/mcp.json`. Key servers needed:
- `filesystem` — built-in, points at vault
- `email-mcp` — Gmail send/draft/search
- `browser-mcp` — `npx @anthropic/browser-mcp` for payment portals
- `calendar-mcp` — scheduling

## Hackathon Tiers

- **Bronze:** One watcher + Claude reads/writes vault + basic folder structure
- **Silver:** 2+ watchers + LinkedIn posting + Plan.md generation + one MCP server + HITL + cron scheduling
- **Gold:** Full cross-domain + Odoo accounting integration + weekly CEO briefing + Ralph Wiggum loop + comprehensive audit logging
- **Platinum:** Cloud VM (24/7) + Cloud/Local agent split + vault sync via Git/Syncthing + Odoo on cloud

## All AI Functionality as Agent Skills

Per hackathon requirements, all AI functionality must be implemented as [Agent Skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview). Each skill lives in `.claude/skills/<skill-name>/SKILL.md` and encapsulates a repeatable capability (e.g., `process-email`, `generate-ceo-briefing`, `audit-subscriptions`).
