# Research: Gold Tier Personal AI Employee

**Phase**: 0 — Research & Unknown Resolution
**Date**: 2026-03-22
**Feature**: 003-gold-ai-employee

All NEEDS CLARIFICATION items from the Technical Context have been resolved below.

---

## 1. MCP Transport Protocol

**Decision**: stdio transport for all MCP servers
**Rationale**: Claude Code's MCP integration uses stdio (stdin/stdout JSON-RPC) as its native transport. HTTP/SSE transport adds a network layer and port management overhead with no benefit at single-machine scale. stdio is the pattern used by all Anthropic-provided MCP servers (email-mcp, browser-mcp) and is the default in `.claude/settings.json` registration.
**Alternatives considered**: HTTP/SSE transport — rejected because it requires running a local HTTP server, adds port conflict risk, and gains nothing at single-user local scale.

---

## 2. Python vs. Node.js for Odoo MCP

**Decision**: Python for `odoo_mcp/server.py`
**Rationale**: The Odoo 19+ external JSON-RPC API is a plain HTTP POST interface; Python's `requests` library handles it with minimal ceremony. The existing watcher layer is Python — sharing the virtualenv reduces operational complexity. The Python MCP SDK (`mcp>=1.0.0`) is mature and well-documented. Node.js would require additional tooling with no capability advantage for this use case.
**Alternatives considered**: Node.js — rejected because it adds a second runtime with no feature benefit; the Odoo JSON-RPC API has no JavaScript-specific client library advantage.

---

## 3. Watcher Polling vs. Push/Event-Driven

**Decision**: Polling with `PollingObserver` on NTFS mounts; `watchdog` library for filesystem events
**Rationale**: The constitution explicitly requires `PollingObserver` (not `InotifyObserver`) when operating on `/mnt/c` NTFS mounts in WSL2. Gmail and WhatsApp have no push API available in this architecture (Gmail Push requires a public HTTPS endpoint; WhatsApp Web has no webhook). Polling at configurable intervals (Gmail: 120 s, WhatsApp: 30 s, Finance: 300 s, filesystem: `watchdog` events) is the correct and constitution-compliant approach.
**Alternatives considered**: Gmail Push Notifications via Pub/Sub — rejected because it requires a publicly reachable HTTPS endpoint, violating the local-first architecture constraint.

---

## 4. Email Queue Implementation for Graceful Degradation

**Decision**: Local JSON file queue (`scripts/email_outbox_queue.json`)
**Rationale**: The graceful degradation requirement (FR-041) requires outgoing emails to be queued when the Email MCP is unavailable. A simple JSON array of pending email objects (to, subject, body, queued_at) satisfies this with zero additional dependencies. The Email MCP's `flush_queue()` tool reads and drains this file on service restoration. At single-user scale, queue depth will never exceed a few dozen items.
**Alternatives considered**: Redis — rejected (adds infrastructure dependency, violates local-first principle); SQLite — rejected (unnecessarily complex for a queue that may hold <100 items at peak); in-memory queue — rejected (lost on process restart, violating durability requirement).

---

## 5. WhatsApp Single-Session Enforcement

**Decision**: PID file guard + `launch_persistent_context` with session path
**Rationale**: The WhatsApp watcher writes its browser process PID to `scripts/whatsapp_browser.pid` on startup. Before launching, it checks if this PID is alive. If alive, it attaches to the existing persistent context session path rather than launching a new browser. If dead (stale PID), it cleans up and launches fresh. This guarantees exactly one browser instance per system.
**Alternatives considered**: Port-based singleton (bind a local port) — more complex, not needed; OS-level semaphore — platform-specific, harder to debug.

---

## 6. Odoo 19+ Authentication Flow

**Decision**: JSON-RPC session authentication via `/web/session/authenticate`
**Rationale**: Odoo 19+ uses the same JSON-RPC 2.0 external API as earlier versions. Authentication is performed by calling the `authenticate` method on the `common` service endpoint. The response includes a `uid` (user ID) used in subsequent calls. The Odoo MCP server performs authentication once at startup and stores the session; on `session.invalid` error it re-authenticates automatically (once).
**Alternatives considered**: API key authentication — available in Odoo 17+, simpler, but session auth is more universally supported across Odoo 19 community deployments; chosen as primary with API key as documented alternative in `.env.example`.

---

## 7. Ralph Wiggum Stop Hook Registration

**Decision**: Register in `.claude/settings.json` as a `PostToolUse` (stop) hook pointing to `stop_hook.py`
**Rationale**: Claude Code's hook system supports a Stop hook that fires when the agent is about to exit. The hook script reads the current task state file, checks completion criteria, and either blocks exit (returns non-zero) or allows it (returns 0). The state file (`TASK_<id>.state.json`) carries the iteration count, max_iterations, original prompt, and prior output. This is the documented Ralph Wiggum pattern from the hackathon document (Section 2D).
**Alternatives considered**: PreToolUse hook — fires before each tool use, not on exit; not the right hook type. External process polling — less reliable and requires a second running process.

---

## 8. Social Media API Strategy per Platform

**Decision**: Official REST APIs where available; Browser MCP as fallback

| Platform | Primary Method | Notes |
|---|---|---|
| LinkedIn | LinkedIn Marketing API (OAuth2) | Supports post creation and basic engagement metrics |
| Facebook | Facebook Graph API (Page access token) | Requires page admin token; supports post + insights |
| Instagram | Instagram Graph API (via Facebook) | Requires Facebook Page linked to Instagram Business account |
| Twitter/X | Twitter API v2 (OAuth2 Bearer token) | Free tier supports tweet creation; engagement metrics on paid tier |

**Rationale**: Official APIs are more reliable, faster, and don't risk account bans from browser automation. Browser MCP is retained as a fallback for any platform where API access is unavailable or rate-limited, consistent with the spec's browser-mcp inclusion.
**Alternatives considered**: Playwright-based posting for all platforms — rejected due to ToS risk and brittleness of UI automation vs. official APIs.

---

## 9. Temp Folder Strategy for Vault Unavailability

**Decision**: Configurable `VAULT_TEMP_PATH` in `.env`; sync via file copy on vault restoration
**Rationale**: When the vault NTFS mount is inaccessible (e.g., network drive disconnected), watchers write to a local temp path. The orchestrator's vault health check runs every 5 minutes; on restoration it copies all files from temp → vault using standard file I/O. No special sync tool is required.
**Alternatives considered**: Syncthing — overkill for a single-machine temp buffer; write-ahead log — complex, not needed at this scale.

---

## 10. CEO Briefing Trigger Mechanism

**Decision**: `schedule` library inside `orchestrator.py`; Windows Task Scheduler as production fallback
**Rationale**: The `schedule` library (pure Python, no external dependencies) provides cron-like scheduling inside the orchestrator process. This avoids the need to configure OS-level Task Scheduler entries during development. For production always-on deployments on Windows, Task Scheduler is documented in `quickstart.md` as the recommended mechanism.
**Alternatives considered**: `cron` (Linux/WSL2) — available but requires separate WSL2 cron daemon; Windows Task Scheduler — reliable but harder to configure programmatically; chosen hybrid (schedule library in dev, Task Scheduler in prod) is the most practical.
