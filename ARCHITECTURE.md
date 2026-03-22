# Architecture — Personal AI Employee (Gold Tier)

## System Overview

The Personal AI Employee is a locally-hosted autonomous agent that monitors Gmail, WhatsApp, the filesystem, and bank transactions via Python watcher daemons; reasons over events using Claude Code and agent skills; executes approved actions through domain-specific MCP servers; enforces human approval for all sensitive actions; and generates weekly CEO Briefings. All state is carried in Obsidian vault Markdown files — no external database.

---

## Components

### Perception Layer — Python Watcher Daemons (`watchers/`)

| Watcher | Source | Output |
|---------|--------|--------|
| `gmail_watcher.py` | Gmail IMAP / API | `Needs_Action/EMAIL_*.md` |
| `whatsapp_watcher.py` | WhatsApp Web (Playwright) | `Needs_Action/WHATSAPP_*.md` |
| `filesystem_watcher.py` | `AI_Employee_Vault/Inbox/` | `Needs_Action/FILE_*.md` |
| `finance_watcher.py` | Bank CSV / API | `Needs_Action/FINANCE_*.md` |
| `approval_watcher.py` | `AI_Employee_Vault/Approved/` | `Needs_Action/ACTION_*.md` |

All watchers extend `BaseWatcher` and are perception-only — no reasoning or decision logic. They poll their sources and write structured Markdown files to `Needs_Action/`. Processed IDs are tracked in `scripts/processed_*.json` for idempotency.

### Reasoning Layer — Claude Code + Agent Skills (`.claude/skills/`)

| Skill | Trigger | Output |
|-------|---------|--------|
| `process-needs-action` | Manual or scheduled (daily 08:00) | `Plans/PLAN_*.md`, `Pending_Approval/APPROVAL_*.md` |
| `execute-plan` | ApprovalWatcher creates ACTION_*.md | MCP calls, `Done/`, audit logs |
| `ceo-briefing` | Sunday 23:00 cron | `Briefings/YYYY-MM-DD_Monday_Briefing.md` |
| `linkedin-post` | Manual or scheduled | `Pending_Approval/APPROVAL_LINKEDIN_*.md` |
| `reasoning-loop` | Manual multi-step tasks | Task completion via TASK_COMPLETE promise |

### Action Layer — MCP Servers (`mcp-servers/`)

| Server | Transport | Responsibilities |
|--------|-----------|-----------------|
| `email-mcp` | Python stdio | Gmail send, draft, search, outbox queue |
| `social-mcp` | Python stdio | LinkedIn, Facebook, Instagram, Twitter post + summary |
| `odoo-mcp` | Python stdio | Odoo 19+ JSON-RPC: invoices, transactions, customers |
| Playwright MCP | npx stdio | WhatsApp Web, browser automation, payment portals |

### Orchestration Layer — `orchestrator.py`

- Starts all watcher daemons as background threads
- **Watchdog loop** (Gold): monitors watcher liveness every 60s; auto-restarts up to 3×/hour; writes `ERROR_WATCHDOG_*.md` after threshold
- **Cron scheduler** (Gold): Sunday 23:00 → ceo-briefing; daily 08:00 → process-needs-action; every 90 days → log cleanup
- **Vault health monitor** (Gold): checks vault availability every 5 min; pauses watchers and writes temp error file on failure; syncs temp files back on restoration

### State Machine — Vault Folder Flow

```
Inbox/ → Needs_Action/ → [Plans/] → Pending_Approval/ → Approved/ → Done/
                                                        ↓
                                                    Rejected/
```

- Files only move **forward** — never backward except Approved/ → Pending_Approval/ on failure
- `Dashboard.md` is single-writer (process-needs-action skill only)
- `Logs/YYYY-MM-DD.json` receives NDJSON entries from all components

---

## Key Design Decisions

### 1. MCP stdio transport for all custom servers (Python)

**Decision**: All custom MCP servers use Python stdio transport instead of HTTP/SSE.

**Rationale**: stdio transport is simpler to deploy on a single Windows machine with no networking requirements, no port management, and no firewall rules. Claude Code spawns each server as a subprocess with its environment variables injected directly from `.mcp.json`. This avoids the complexity of HTTP server lifecycle management while achieving the same MCP protocol semantics.

**Trade-off**: stdio transport cannot support multiple concurrent Claude Code sessions connecting to the same MCP instance. This is acceptable for single-user, single-machine deployment.

### 2. File-based state machine (no external database)

**Decision**: All system state is stored as Markdown files in `AI_Employee_Vault/`. No SQLite, PostgreSQL, or Redis.

**Rationale**: Markdown files are human-readable, directly editable in Obsidian, naturally versioned by git, and trivially backed up. The vault doubles as both the system's memory and its user interface. File movement between folders (Needs_Action → Plans → Pending_Approval → Approved → Done) provides a clear, auditable state machine without any database schema migrations.

**Trade-off**: File-based state does not support concurrent writes safely at high volume. At single-user, ~4 watcher scale with <1,000 files at steady state, this is not a concern.

### 3. Local email outbox queue for graceful degradation

**Decision**: `email-mcp` includes a `queue_email` + `flush_queue` tool pair backed by `scripts/email_outbox_queue.json`.

**Rationale**: If the email-mcp process is temporarily unavailable (restart, update, crash), emails must not be silently dropped. The local queue acts as a write-ahead log that survives across email-mcp restarts. This pattern mirrors standard message queue semantics without requiring Redis or RabbitMQ.

**Trade-off**: The queue is in-process memory + a single JSON file. It is not durable across machine power loss. For the single-user use case this is acceptable; production would use a proper message broker.

---

## Known Limitations and Lessons Learned

### 1. WhatsApp Web session fragility

WhatsApp Web sessions expire without warning and cannot be programmatically renewed — a QR scan is required. The system handles this by writing `ERROR_WHATSAPP_SESSION.md` and pausing the watcher, but requires manual intervention to re-establish the session. Future: investigate WhatsApp Business API for a more stable integration.

### 2. NTFS PollingObserver on WSL2

The standard `watchdog` `InotifyObserver` does not work on NTFS mounts (`/mnt/c`) under WSL2 because inotify events are not generated for cross-filesystem operations. All watchers use `PollingObserver(timeout=3)` as a workaround. This introduces up to 3 seconds of latency but is reliable. Future: consider moving the vault to a native Linux ext4 filesystem for real-time event delivery.

### 3. Odoo Community API compatibility

Odoo 19+ changed some JSON-RPC endpoint paths compared to earlier versions. The `odoo-mcp` server targets Odoo 19+ exclusively and uses `/web/dataset/call_kw` for all model operations. Testing against Odoo 16/17 will require endpoint adjustments. This is documented in `mcp-servers/odoo-mcp/server.py`.

---

## Security Model

- All credentials stored in `.env` (gitignored) or OS keychain — never in vault `.md` files
- `DRY_RUN=true` is the default across all components; `DRY_RUN=false` must be explicitly set
- Rate limits: 10 emails/hour, 3 payments/hour (enforced at MCP layer)
- HITL gate: all sensitive actions require human approval via file-move to `Approved/`
- Audit log: every action logged to `Logs/YYYY-MM-DD.json` with full schema, retained 90 days

---

## Further Reading

- [Vault structure and folder state machine](CLAUDE.md#vault-structure)
- [Watcher pattern](CLAUDE.md#watcher-pattern)
- [Ralph Wiggum loop](CLAUDE.md#ralph-wiggum-loop)
- [HITL approval flow](CLAUDE.md#human-in-the-loop)
- [MCP configuration](.mcp.json)
