"""email-mcp — Python MCP server (stdio transport) for Gmail.

Tools:
  - send_email(to, subject, body, reply_to_message_id?)
  - draft_reply(message_id, draft_body)
  - search_inbox(query, max_results?)
  - queue_email(to, subject, body)          [Gold tier]
  - flush_queue()                           [Gold tier]

All calls are logged to AI_Employee_Vault/Logs/YYYY-MM-DD.json.
DRY_RUN=true (default) — no real emails sent during development.
"""

import json
import logging
import os
import sys
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

# Add email-mcp directory and project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))  # for smtp_imap
sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # for project root

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from smtp_imap import send_email, draft_reply, search_inbox

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)

VAULT_PATH = Path(os.getenv("VAULT_PATH", "AI_Employee_Vault"))
SCRIPTS_DIR = Path(__file__).parent.parent.parent / "scripts"
EMAIL_QUEUE_FILE = SCRIPTS_DIR / "email_outbox_queue.json"

# Rate limit: max 10 emails per hour
_email_send_timestamps: deque = deque()
_MAX_EMAILS_PER_HOUR = 10
_RATE_WINDOW_SECONDS = 3600

server = Server("email-mcp")


def _check_rate_limit() -> bool:
    """Returns True if within rate limit, False if exceeded."""
    now = time.time()
    # Prune old timestamps
    while _email_send_timestamps and now - _email_send_timestamps[0] > _RATE_WINDOW_SECONDS:
        _email_send_timestamps.popleft()
    return len(_email_send_timestamps) < _MAX_EMAILS_PER_HOUR


def _record_send() -> None:
    """Record a send timestamp for rate limiting."""
    _email_send_timestamps.append(time.time())


def _load_queue() -> list:
    """Load the email outbox queue from disk."""
    if EMAIL_QUEUE_FILE.exists():
        try:
            return json.loads(EMAIL_QUEUE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save_queue(queue: list) -> None:
    """Persist the email outbox queue to disk."""
    SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    EMAIL_QUEUE_FILE.write_text(json.dumps(queue, indent=2), encoding="utf-8")


def _log_action(action_type: str, target: str, parameters: dict, approval_status: str, result: dict) -> None:
    """Append NDJSON audit log entry to Logs/YYYY-MM-DD.json."""
    try:
        log_dir = VAULT_PATH / "Logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.json"

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "action_type": action_type,
            "actor": "email-mcp",
            "target": target,
            "parameters": parameters,
            "approval_status": approval_status,
            "result": result.get("status", "unknown"),
        }

        with log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        logger.error(f"Failed to write log entry: {e}")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="send_email",
            description="Send an email via Gmail SMTP. Respects DRY_RUN env var. Rate limit: 10/hour.",
            inputSchema={
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient email"},
                    "subject": {"type": "string", "description": "Email subject"},
                    "body": {"type": "string", "description": "Email body"},
                    "reply_to_message_id": {"type": "string", "description": "IMAP UID to reply to (optional)"},
                },
                "required": ["to", "subject", "body"],
            },
        ),
        types.Tool(
            name="draft_reply",
            description="Save a draft reply to Gmail Drafts.",
            inputSchema={
                "type": "object",
                "properties": {
                    "message_id": {"type": "string", "description": "IMAP UID"},
                    "draft_body": {"type": "string", "description": "Draft body text"},
                },
                "required": ["message_id", "draft_body"],
            },
        ),
        types.Tool(
            name="search_inbox",
            description="Search Gmail INBOX using IMAP search query.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "IMAP search query"},
                    "max_results": {"type": "integer", "description": "Max results", "default": 10},
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="queue_email",
            description="Queue an email for sending. Appends to local outbox queue for resilience during MCP outages.",
            inputSchema={
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient email"},
                    "subject": {"type": "string", "description": "Email subject"},
                    "body": {"type": "string", "description": "Email body"},
                },
                "required": ["to", "subject", "body"],
            },
        ),
        types.Tool(
            name="flush_queue",
            description="Send all queued emails from the outbox queue. Clears successfully sent entries.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "send_email":
        # Rate limit check
        if not _check_rate_limit():
            result = {"error": "RATE_LIMIT_EXCEEDED", "retryable": False,
                      "limit": _MAX_EMAILS_PER_HOUR, "window": "1 hour"}
            _log_action("email_send", arguments["to"], arguments, "auto", {"status": "rate_limited"})
            return [types.TextContent(type="text", text=json.dumps(result))]

        result = send_email(
            to=arguments["to"],
            subject=arguments["subject"],
            body=arguments["body"],
            reply_to_message_id=arguments.get("reply_to_message_id"),
        )
        if result.get("status") not in ("error",):
            _record_send()
        _log_action("email_send", arguments["to"], arguments, "approved", result)
        return [types.TextContent(type="text", text=json.dumps(result))]

    elif name == "draft_reply":
        result = draft_reply(
            message_id=arguments["message_id"],
            draft_body=arguments["draft_body"],
        )
        _log_action("email_draft", arguments["message_id"], arguments, "approved", result)
        return [types.TextContent(type="text", text=json.dumps(result))]

    elif name == "search_inbox":
        result = search_inbox(
            query=arguments["query"],
            max_results=arguments.get("max_results", 10),
        )
        _log_action("email_search", arguments["query"], arguments, "auto", {"status": "ok"})
        return [types.TextContent(type="text", text=json.dumps(result))]

    elif name == "queue_email":
        queue = _load_queue()
        entry = {
            "queued_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "to": arguments["to"],
            "subject": arguments["subject"],
            "body": arguments["body"],
            "status": "queued",
        }
        queue.append(entry)
        _save_queue(queue)
        result = {"queued": True, "queue_position": len(queue)}
        _log_action("email_queue", arguments["to"], arguments, "auto", {"status": "queued"})
        return [types.TextContent(type="text", text=json.dumps(result))]

    elif name == "flush_queue":
        dry_run = os.getenv("DRY_RUN", "true").lower() != "false"
        queue = _load_queue()
        pending = [e for e in queue if e.get("status") == "queued"]

        if dry_run:
            result = {
                "dry_run": True,
                "sent": 0,
                "failed": 0,
                "would_have_sent": len(pending),
            }
            # Clear pending in dry-run too
            for entry in queue:
                if entry.get("status") == "queued":
                    entry["status"] = "dry_run_flushed"
            _save_queue(queue)
            _log_action("email_flush_queue", "queue", {}, "auto", {"status": "dry_run"})
            return [types.TextContent(type="text", text=json.dumps(result))]

        sent_count = 0
        failed_count = 0
        for entry in queue:
            if entry.get("status") != "queued":
                continue
            if not _check_rate_limit():
                entry["status"] = "queued"  # leave for next flush
                entry["error"] = "RATE_LIMIT_EXCEEDED"
                failed_count += 1
                continue
            send_result = send_email(
                to=entry["to"],
                subject=entry["subject"],
                body=entry["body"],
            )
            if send_result.get("status") == "sent":
                entry["status"] = "sent"
                entry["sent_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                _record_send()
                sent_count += 1
            else:
                entry["status"] = "failed"
                entry["error"] = send_result.get("error", "unknown")
                failed_count += 1

        _save_queue(queue)
        result = {"sent": sent_count, "failed": failed_count}
        _log_action("email_flush_queue", "queue", {}, "auto", {"status": "ok", **result})
        return [types.TextContent(type="text", text=json.dumps(result))]

    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
