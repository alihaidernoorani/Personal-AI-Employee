"""email-mcp — Python MCP server (stdio transport) for Gmail.

Tools:
  - send_email(to, subject, body, reply_to_message_id?)
  - draft_reply(message_id, draft_body)
  - search_inbox(query, max_results?)

All calls are logged to AI_Employee_Vault/Logs/YYYY-MM-DD.json.
DRY_RUN=true (default) — no real emails sent during development.
"""

import json
import logging
import os
import sys
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

server = Server("email-mcp")


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
            description="Send an email via Gmail SMTP. Respects DRY_RUN env var.",
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
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "send_email":
        result = send_email(
            to=arguments["to"],
            subject=arguments["subject"],
            body=arguments["body"],
            reply_to_message_id=arguments.get("reply_to_message_id"),
        )
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

    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
